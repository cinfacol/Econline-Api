#!/bin/bash

echo "🧪 Probando webhooks reales con stripe_webhook endpoint..."

# Necesitamos una firma válida de Stripe para estos tests
# Por ahora, vamos a probar sin firma para ver si llega al endpoint

echo "1. Probando charge.succeeded (sin firma - esperamos error 400):"
response1=$(curl -s -w "%{http_code}" -X POST https://api.virtualeline.com/api/payments/stripe_webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_charge_succeeded_test",
    "type": "charge.succeeded",
    "data": {
      "object": {
        "id": "ch_test_charge",
        "amount": 19500,
        "currency": "usd"
      }
    }
  }')
echo "Response: $response1"

echo -e "\n2. Probando payment_intent.succeeded (sin firma - esperamos error 400):"  
response2=$(curl -s -w "%{http_code}" -X POST https://api.virtualeline.com/api/payments/stripe_webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_payment_intent_test", 
    "type": "payment_intent.succeeded",
    "data": {
      "object": {
        "id": "pi_test_123",
        "amount": 19500,
        "currency": "usd"
      }
    }
  }')
echo "Response: $response2"

echo -e "\n✅ Si ambos responden 400 (Bad Request), significa que Django está recibiendo las peticiones"
echo "✅ Si responden 502, hay un problema de conectividad antes de llegar a Django"
