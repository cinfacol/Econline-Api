import random
import string
from django.db import models
from autoslug import AutoSlugField
from django.contrib.auth import get_user_model
from common.models import TimeStampedUUIDModel
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

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


class AttributeValue(TimeStampedUUIDModel):
    attribute = models.ForeignKey(
        Attribute,
        related_name="attribute",
        on_delete=models.CASCADE,
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
    )
    upc = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )
    # type = models.ForeignKey(Type, related_name="type", on_delete=models.PROTECT)
    product = models.ForeignKey(
        Product, related_name="product", on_delete=models.PROTECT
    )
    brand = models.ForeignKey(
        Brand,
        related_name="brand",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    attribute_values = models.ManyToManyField(
        AttributeValue,
        related_name="attribute_values",
        # through="AttributeValues",
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

    published = ProductPublishedManager()
    objects = IsActiveQueryset.as_manager()

    class Meta:
        verbose_name_plural = "Inventory"

    def __str__(self):
        return self.sku

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
    img_url = models.ImageField(upload_to=None, default="no_image.png")
    alt_text = models.CharField(
        max_length=255,
    )
    is_feature = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name_plural = "Images"


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
