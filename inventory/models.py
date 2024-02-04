import random
import string
from django.db import models
from autoslug import AutoSlugField

from django.contrib.auth import get_user_model
from common.models import TimeStampedUUIDModel
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from decimal import Decimal

from .fields import OrderField

from django.core.validators import MinValueValidator

User = get_user_model()


class IsActiveQueryset(models.QuerySet):
    def is_active(self):
        return self.filter(is_active=True)


class ProductPublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super(ProductPublishedManager, self)
            .get_queryset()
            .filter(published_status=True)
        )


class Category(TimeStampedUUIDModel):
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    is_active = models.BooleanField(
        default=True,
    )
    objects = IsActiveQueryset.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(TimeStampedUUIDModel):

    name = models.CharField(
        max_length=255,
    )
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    ref_code = models.CharField(
        verbose_name=_("Product Reference Code"),
        max_length=12,
        unique=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    category = models.ManyToManyField(
        Category,
        related_name="product",
    )
    views = models.IntegerField(verbose_name=_("Total Views"), default=0)
    is_active = models.BooleanField(
        default=True,
    )

    objects = IsActiveQueryset.as_manager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = str.title(self.name)
        self.description = str.capitalize(self.description)
        self.ref_code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=10)
        )
        super(Product, self).save(*args, **kwargs)


class Attribute(TimeStampedUUIDModel):
    name = models.CharField(
        max_length=100,
        unique=True,
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Type(TimeStampedUUIDModel):
    name = models.CharField(
        max_length=255,
        unique=True,
    )

    type_attributes = models.ManyToManyField(
        Attribute,
        related_name="type_attributes",
        through="TypeAttribute",
    )

    def __str__(self):
        return self.name


class AttributeValue(TimeStampedUUIDModel):
    attribute = models.ForeignKey(
        Attribute,
        related_name="attribute",
        on_delete=models.PROTECT,
    )
    value = models.CharField(
        max_length=100,
    )

    def __str__(self):
        return f"{self.attribute.name}-{self.value}"


class Brand(TimeStampedUUIDModel):
    name = models.CharField(
        max_length=255,
        unique=True,
    )

    def __str__(self):
        return self.name


class Inventory(TimeStampedUUIDModel):
    sku = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text=_("This field is auto-generated"),
    )
    upc = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text=_("This field is auto-generated"),
    )
    # type = models.ForeignKey(Type, related_name="type", on_delete=models.PROTECT)
    product = models.ForeignKey(
        Product, related_name="product", on_delete=models.PROTECT
    )
    user = models.ManyToManyField(
        User,
        verbose_name=_("Agent, Seller or Buyer"),
        related_name="product_user",
    )
    order = OrderField(unique_for_field="product", blank=True)
    brand = models.ForeignKey(
        Brand,
        related_name="brand",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    type = models.ForeignKey(
        Type, related_name="product_type", on_delete=models.PROTECT
    )
    attribute_values = models.ManyToManyField(
        AttributeValue,
        related_name="attribute_values",
        through="AttributeValues",
    )
    is_active = models.BooleanField(
        default=False,
    )
    is_default = models.BooleanField(
        default=False,
    )
    published_status = models.BooleanField(
        verbose_name=_("Published Status"), default=False
    )
    retail_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    store_price = models.DecimalField(
        max_digits=7,
        decimal_places=2,
    )
    is_digital = models.BooleanField(
        default=False,
    )
    weight = models.FloatField(
        blank=True,
        null=True,
    )
    views = models.IntegerField(verbose_name=_("Total Views"), default=0)

    published = ProductPublishedManager()
    objects = IsActiveQueryset.as_manager()

    class Meta:
        verbose_name_plural = "Inventory"

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):
        self.upc = "".join(random.choices(string.digits, k=12))
        self.sku = "".join(random.choices(string.digits, k=10))
        super(Inventory, self).save(*args, **kwargs)


class Media(TimeStampedUUIDModel):
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name="media",
    )
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

    def get_absolute_url(self):
        return reverse("products:products", args=[self.slug])

    class Meta:
        verbose_name = _("inventory image")
        verbose_name_plural = _("inventory images")
        ordering = ("created_at",)

    def __str__(self):
        return self.alt_text


class Stock(TimeStampedUUIDModel):
    inventory = models.OneToOneField(
        Inventory,
        related_name="inventory",
        on_delete=models.CASCADE,
    )
    units = models.IntegerField(
        default=0,
    )
    units_sold = models.IntegerField(
        default=0,
    )

    class Meta:
        verbose_name_plural = "Stock"


class AttributeValues(models.Model):
    attributevalues = models.ForeignKey(
        "AttributeValue",
        related_name="attributevaluess",
        on_delete=models.PROTECT,
    )
    inventory = models.ForeignKey(
        Inventory,
        related_name="attributevaluess",
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = (("attributevalues", "inventory"),)


class TypeAttribute(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        related_name="type_attribute",
        on_delete=models.PROTECT,
    )
    type = models.ForeignKey(
        Type,
        related_name="type",
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = (("attribute", "type"),)
