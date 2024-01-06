import random
import string

from autoslug import AutoSlugField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from categories.models import Category
from common.models import TimeStampedUUIDModel

User = get_user_model()


class ProductPublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super(ProductPublishedManager, self)
            .get_queryset()
            .filter(published_status=True)
        )


class Product(TimeStampedUUIDModel):
    class ProductType(models.TextChoices):
        HOUSE = "House", _("House")
        APARTMENT = "Apartment", _("Apartment")
        OFFICE = "Office", _("Office")
        WAREHOUSE = "Warehouse", _("Warehouse")
        COMMERCIAL = "Commercial", _("Commercial")
        OTHER = "Other", _("Other")

    user = models.ForeignKey(
        User,
        verbose_name=_("Agent,Seller or Buyer"),
        related_name="agent_buyer",
        on_delete=models.DO_NOTHING,
    )

    title = models.CharField(verbose_name=_("Product Title"), max_length=250)
    slug = AutoSlugField(populate_from="title", unique=True, always_update=True)
    ref_code = models.CharField(
        verbose_name=_("Product Reference Code"),
        max_length=255,
        unique=True,
        blank=True,
    )
    description = models.TextField(
        verbose_name=_("Description"),
        default="Default description...update me please....",
    )
    product_number = models.IntegerField(
        verbose_name=_("Product Number"),
        validators=[MinValueValidator(1)],
        default=112,
    )
    price = models.DecimalField(
        verbose_name=_("Price"), max_digits=8, decimal_places=2, default=0.0
    )
    tax = models.DecimalField(
        verbose_name=_("Product Tax"),
        max_digits=6,
        decimal_places=2,
        default=0.15,
        help_text="15% product tax charged",
    )
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE, default=1
    )

    product_type = models.CharField(
        verbose_name=_("Product Type"),
        max_length=50,
        choices=ProductType.choices,
        default=ProductType.OTHER,
    )

    published_status = models.BooleanField(
        verbose_name=_("Published Status"), default=False
    )
    views = models.IntegerField(verbose_name=_("Total Views"), default=0)

    objects = models.Manager()
    published = ProductPublishedManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def save(self, *args, **kwargs):
        self.title = str.title(self.title)
        self.description = str.capitalize(self.description)
        self.ref_code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=10)
        )
        super(Product, self).save(*args, **kwargs)

    @property
    def final_product_price(self):
        tax_percentage = self.tax
        product_price = self.price
        tax_amount = round(tax_percentage * product_price, 2)
        price_after_tax = float(round(product_price + tax_amount, 2))
        return price_after_tax


class ProductViews(TimeStampedUUIDModel):
    ip = models.CharField(verbose_name=_("IP Address"), max_length=250)
    product = models.ForeignKey(
        Product, related_name="product_views", on_delete=models.CASCADE
    )

    def __str__(self):
        return (
            f"Total views on - {self.product.title} is - {self.product.views} view(s)"
        )

    class Meta:
        verbose_name = "Total Views on Product"
        verbose_name_plural = "Total Product Views"


class Media(models.Model):
    image = models.ImageField(
        unique=False,
        null=False,
        blank=False,
        verbose_name=_("imagen"),
        upload_to="images/",
        default="images/default.png",
        help_text=_("format: required, default-default.png"),
    )
    alt_text = models.CharField(
        max_length=255,
        unique=False,
        null=False,
        blank=False,
        verbose_name=_("texto alternativo"),
        help_text=_("format: required, max-255"),
    )
    product = models.ForeignKey(
        Product, related_name="imagenes", on_delete=models.CASCADE
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("destacado"),
        help_text=_("format: default=false, true=default image"),
    )
    default = models.BooleanField(
        default=False,
        verbose_name=_("por defecto"),
        help_text=_("format: default=false, true=default image"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name=_("creado desde"),
        help_text=_("format: Y-m-d H:M:S"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("actualizado"),
        help_text=_("format: Y-m-d H:M:S"),
    )

    def get_absolute_url(self):
        return reverse("products:products", args=[self.slug])

    class Meta:
        verbose_name = _("product image")
        verbose_name_plural = _("product images")
        ordering = ("created_at",)

    def __str__(self):
        return self.alt_text
