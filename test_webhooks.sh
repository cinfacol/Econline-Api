#!/bin/bash

echo "🧪 Probando webhooks que están fallando..."

# Test charge.succeeded
echo "1. Probando charge.succeeded:"
curl -X POST https://api.virtualeline.com/api/payments/webhook_test/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_charge_succeeded_test",
    "type": "charge.succeeded",
    "data": {
      "object": {
        "id": "ch_test_charge",
        "amount": 19500,
        "currency": "usd",
        "payment_intent": "pi_3SCJ7wHXf3qEyMjJ0MznnEQZ"
      }
    }
  }'

echo -e "\n2. Probando payment_intent.succeeded:"
curl -X POST https://api.virtualeline.com/api/payments/webhook_test/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_payment_intent_test", 
    "type": "payment_intent.succeeded",
    "data": {
      "object": {
        "id": "pi_3SCJ7wHXf3qEyMjJ0MznnEQZ",
        "amount": 19500,
        "currency": "usd"
      }
    }
  }'

echo -e "\n3. Probando checkout.session.completed (debería funcionar):"
curl -X POST https://api.virtualeline.com/api/payments/webhook_test/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_checkout_test",
    "type": "checkout.session.completed", 
    "data": {
      "object": {
        "id": "cs_test_session",
        "payment_intent": "pi_3SCJ7wHXf3qEyMjJ0MznnEQZ"
      }
    }
  }'
