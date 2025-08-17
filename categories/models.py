from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedUUIDModel
from common.models import IsActiveQueryset
from autoslug import AutoSlugField


class MeasureUnit(TimeStampedUUIDModel):

    class MeasureType(models.TextChoices):
        UNITS = "Units", _("Units")
        GRAMS = "Grams", _("Grams")
        POUNDS = "Pounds", _("Pounds")
        KILOGRAMS = "Kilograms", _("Kilograms")
        MILLILITERS = "Mililiters", _("Mililiters")
        LITERS = "Liters", _("Liters")
        OTHER = "Other", _("Other")

    description = models.CharField(
        verbose_name=_("Descripción"),
        max_length=100,  # Aumentar longitud para descripciones personalizadas
        unique=True,
    )

    # Campo para distinguir si es una unidad predefinida o personalizada
    is_custom = models.BooleanField(
        verbose_name=_("Es personalizada"),
        default=False,
        help_text=_(
            "Indica si es una unidad de medida personalizada creada por el usuario"
        ),
    )

    class Meta:
        verbose_name = _("Measure Unit")
        verbose_name_plural = _("Measure Units")

    def __str__(self):
        return self.description


class Category(TimeStampedUUIDModel):
    parent = models.ForeignKey(
        "self", related_name="children", on_delete=models.CASCADE, blank=True, null=True
    )
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    is_active = models.BooleanField(
        default=True,
    )

    measure_unit = models.ForeignKey(
        MeasureUnit,
        on_delete=models.CASCADE,
        related_name="MeasureUnit",
        verbose_name=_("Measure Unit"),
    )
    objects = IsActiveQueryset.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name
