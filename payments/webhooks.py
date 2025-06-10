# payments/webhooks.py

from enum import Enum
from typing import Dict, Callable
from django.conf import settings
import stripe
from .tasks import (
    handle_checkout_session_completed_task,
    handle_payment_intent_succeeded_task,
    handle_payment_intent_payment_failed_task,
    handle_refund_succeeded_task,
    handle_subscription_created_task,
    handle_subscription_updated_task,
    handle_subscription_deleted_task,
)


class WebhookEventType(Enum):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_INTENT_FAILED = "payment_intent.payment_failed"
    CHARGE_REFUNDED = "charge.refunded"
    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"


class WebhookHandler:
    def __init__(self):
        self.handlers: Dict[str, Callable] = {
            WebhookEventType.CHECKOUT_SESSION_COMPLETED.value: handle_checkout_session_completed_task,
            WebhookEventType.PAYMENT_INTENT_SUCCEEDED.value: handle_payment_intent_succeeded_task,
            WebhookEventType.PAYMENT_INTENT_FAILED.value: handle_payment_intent_payment_failed_task,
            WebhookEventType.CHARGE_REFUNDED.value: handle_refund_succeeded_task,
            WebhookEventType.SUBSCRIPTION_CREATED.value: handle_subscription_created_task,
            WebhookEventType.SUBSCRIPTION_UPDATED.value: handle_subscription_updated_task,
            WebhookEventType.SUBSCRIPTION_DELETED.value: handle_subscription_deleted_task,
        }
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY

    def process_webhook(self, payload: bytes, sig_header: str) -> dict:
        try:
            event = self.stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )

            handler = self.handlers.get(event.type)
            if handler:
                # Procesar el webhook de forma asíncrona
                handler.delay(event.data.object)
                return {"status": "success", "event_type": event.type}

            return {"status": "ignored", "event_type": event.type}

        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")
        except Exception as e:
            raise Exception(f"Error processing webhook: {str(e)}")
