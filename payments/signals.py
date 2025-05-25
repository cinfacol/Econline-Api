# payments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment, Subscription
from .tasks import send_payment_success_email_task, send_subscription_welcome_email


@receiver(post_save, sender=Payment)
def payment_completed_handler(sender, instance, created, **kwargs):
    if instance.status == Payment.PaymentStatus.COMPLETED:
        if instance.user and instance.user.email:
            send_payment_success_email_task.delay(instance.user.email)


@receiver(post_save, sender=Subscription)
def subscription_created_handler(sender, instance, created, **kwargs):
    if created and instance.user and instance.user.email:
        send_subscription_welcome_email.delay(instance.user.email)
