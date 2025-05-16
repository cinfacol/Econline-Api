from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


@shared_task()
def send_payment_success_email_task(email_address):
    """
    Celery task to send an email when payment is successfull
    """
    try:
        send_mail(
            subject=_("Payment Successful"),
            message=_("Thank you for purchasing our product!"),
            recipient_list=[email_address],
            from_email=settings.EMAIL_HOST_USER,
        )
    except Exception as e:
        logger.error(
            f"Error sending payment success email to {email_address}: {str(e)}"
        )
