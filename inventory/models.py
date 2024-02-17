from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

# from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import random
import string

from autoslug import AutoSlugField
from django.contrib.auth import get_user_model

from common.models import TimeStampedUUIDModel, IsActiveQueryset, PublishedManager
from products.models import Product
from users.models import User
from .fields import OrderField

# User = get_user_model()


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
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    description = models.TextField(blank=True)

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
        return self.value


class Brand(TimeStampedUUIDModel):
    name = models.CharField(
        max_length=255,
        unique=True,
    )

    def __str__(self):
        return self.name


class Inventory(TimeStampedUUIDModel):

    class StateType(models.TextChoices):
        NEW = "New", _("New")
        USED = "Used", _("Used")
        DAMAGED = "Damaged", _("for Spare Parts")

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
    product = models.ForeignKey(
        Product, related_name="product", on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("Agent, Seller or Buyer"),
        related_name="inventory_user",
        on_delete=models.PROTECT,
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
    quality = models.CharField(
        verbose_name=_("State Type"),
        max_length=50,
        choices=StateType.choices,
        default=StateType.NEW,
    )
    attribute_values = models.ManyToManyField(
        AttributeValue,
        related_name="prod_attribute",
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
        max_digits=10,
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

    published = PublishedManager()
    objects = IsActiveQueryset.as_manager()

    class Meta:
        verbose_name_plural = "Inventory"

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):
        self.upc = "".join(random.choices(string.digits, k=12))
        self.sku = "".join(random.choices(string.digits, k=10))
        super(Inventory, self).save(*args, **kwargs)


class InventoryViews(TimeStampedUUIDModel):
    ip = models.CharField(verbose_name=_("IP Address"), max_length=250)
    inventory = models.ForeignKey(
        Inventory, related_name="inventory_views", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Total views on - {self.inventory.product.name} is - {self.inventory.views} view(s)"

    class Meta:
        verbose_name = "Inventory View"
        verbose_name_plural = "Inventory Views"


class Media(TimeStampedUUIDModel):
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.PROTECT,
        related_name="inventory_media",
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
        verbose_name=_("Featured"),
        help_text=_("format: default=false, true=default image"),
    )
    default = models.BooleanField(
        default=False,
        verbose_name=_("is default"),
        help_text=_("format: default=false, true=default image"),
    )

    class Meta:
        verbose_name = _("inventory image")
        verbose_name_plural = _("inventory images")
        ordering = ("created_at",)

    def __str__(self):
        return self.alt_text


class Stock(TimeStampedUUIDModel):
    inventory = models.OneToOneField(
        Inventory,
        related_name="inventory_stock",
        on_delete=models.PROTECT,
    )
    units = models.IntegerField(
        default=0,
    )
    units_sold = models.IntegerField(
        default=0,
    )

    class Meta:
        verbose_name_plural = _("Stock")
