from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedUUIDModel

User = get_user_model()


class Gender(models.TextChoices):
    MALE = "Male", _("Male")
    FEMALE = "Female", _("Female")
    OTHER = "Other", _("Other")


class VerificationType(models.TextChoices):
    UNVERIFIED = "Unverified", _("Unverified")
    VERIFIED = "Verified", _("Verified")


class Profile(TimeStampedUUIDModel):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    about_me = models.TextField(
        verbose_name=_("About me"), default="say something about yourself"
    )
    license = models.CharField(
        verbose_name=_("Store License"), max_length=20, blank=True, default=""
    )
    profile_photo = models.ImageField(
        verbose_name=_("Profile Photo"),
        default="/avatar.png",
        blank=True,
        null=True,
    )
    gender = models.CharField(
        verbose_name=_("Gender"),
        choices=Gender.choices,
        default=Gender.OTHER,
        max_length=20,
    )
    verified = models.CharField(
        verbose_name=_("Verified"),
        choices=VerificationType.choices,
        default=VerificationType.UNVERIFIED,
        max_length=20,
    )
    is_buyer = models.BooleanField(
        verbose_name=_("Buyer"),
        default=True,
        help_text=_("Are you looking to Buy a product?"),
    )
    is_seller = models.BooleanField(
        verbose_name=_("Seller"),
        default=False,
        help_text=_("Are you looking to sell a product?"),
    )
    is_agent = models.BooleanField(
        verbose_name=_("Agent"), default=False, help_text=_("Are you an agent?")
    )
    top_agent = models.BooleanField(verbose_name=_("Top Agent"), default=False)
    num_reviews = models.IntegerField(
        verbose_name=_("Number of Reviews"), default=0, null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username}'s profile"
