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
from common.models import IsActiveQueryset
from common.models import PublishedManager

User = get_user_model()


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
    category = models.ManyToManyField(Category)
    is_active = models.BooleanField(
        default=True,
    )
    published_status = models.BooleanField(
        verbose_name=_("Published Status"), default=False
    )

    objects = IsActiveQueryset.as_manager()
    published = PublishedManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = str.title(self.name)
        self.description = str.capitalize(self.description)
        self.ref_code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=10)
        )
        super(Product, self).save(*args, **kwargs)
