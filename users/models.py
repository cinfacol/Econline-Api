import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .countries import Countries
from phonenumber_field.modelfields import PhoneNumberField
from common.models import TimeStampedUUIDModel
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .management.managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(verbose_name=_("Username"), max_length=255, unique=True)
    first_name = models.CharField(verbose_name=_("First Name"), max_length=50)
    last_name = models.CharField(verbose_name=_("Last Name"), max_length=50)
    email = models.EmailField(verbose_name=_("Email Address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    stripe_customer_id = models.CharField(
        verbose_name=_("Stripe Customer ID"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Customer ID from Stripe payment system"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.username

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.username

    def get_or_create_stripe_customer(self):
        """
        Obtiene o crea un customer_id de Stripe para el usuario.
        Returns:
            str: El ID del cliente en Stripe
        """
        if not self.stripe_customer_id:
            try:
                import stripe
                from django.conf import settings

                stripe.api_key = settings.STRIPE_SECRET_KEY
                customer = stripe.Customer.create(
                    email=self.email,
                    name=self.get_full_name,
                    metadata={"user_id": str(self.id), "username": self.username},
                )
                self.stripe_customer_id = customer.id
                self.save(update_fields=["stripe_customer_id"])

            except Exception as e:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    _("Could not create Stripe customer: %(error)s") % {"error": str(e)}
                )

        return self.stripe_customer_id


class Address(TimeStampedUUIDModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name=_("City"))
    state_province_region = models.CharField(max_length=100, verbose_name=_("State"))
    postal_zip_code = models.CharField(max_length=20, verbose_name=_("Zip Code"))
    country_region = models.CharField(
        verbose_name=_("Country"),
        max_length=255,
        choices=Countries.choices,
        default=Countries.Colombia,
    )
    phone_number = PhoneNumberField(
        verbose_name=_("Phone Number"), max_length=30, default="+573142544178"
    )
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_1}, {self.city}, {self.postal_zip_code}, {self.country_region}"

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")
        ordering = ("-created_at",)
