from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedUUIDModel
from products.models import Product

User = settings.AUTH_USER_MODEL


class Rating(TimeStampedUUIDModel):
    class Range(models.IntegerChoices):
        RATING_1 = 1, _("Poor")
        RATING_2 = 2, _("Fair")
        RATING_3 = 3, _("Good")
        RATING_4 = 4, _("Very Good")
        RATING_5 = 5, _("Excellent")

    rater = models.ForeignKey(
        User,
        verbose_name=_("User that rate"),
        on_delete=models.SET_NULL,
        null=True,
    )
    product = models.ForeignKey(
        Product,
        verbose_name=_("Product"),
        related_name="product_review",
        on_delete=models.SET_NULL,
        null=True,
    )
    rating = models.PositiveIntegerField(
        verbose_name=_("Rating"),
        choices=Range.choices,
        help_text="1=Poor, 2=Fair, 3=Good, 4=Very Good, 5=Excellent",
        default=0,
    )
    comment = models.TextField(verbose_name=_("Comment"), blank=True, null=True)

    class Meta:
        unique_together = ["rater", "product"]

    def __str__(self):
        return f"{self.rater}'s {self.rating}-star rating for {self.product}"
