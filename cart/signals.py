from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Cart
from config.settings import AUTH_USER_MODEL


@receiver(post_save, sender=AUTH_USER_MODEL)
def create_user_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user=instance)


@receiver(post_save, sender=AUTH_USER_MODEL)
def save_user_cart(sender, instance, **kwargs):
    instance.cart.save()
