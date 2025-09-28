#!/bin/bash

echo "🧪 Probando webhooks secuenciales (no concurrentes)..."

send_webhook() {
    local event_type=$1
    echo "Enviando $event_type..."
    
    response=$(curl -s -w "%{http_code}" -X POST https://api.virtualeline.com/api/payments/stripe_webhook/ \
        -H "Content-Type: application/json" \
        -H "Stripe-Signature: test_signature" \
        -d "{
            \"id\": \"evt_test\",
            \"type\": \"$event_type\", 
            \"data\": {
                \"object\": {
                    \"id\": \"test_object\",
                    \"amount\": 11500,
                    \"currency\": \"usd\"
                }
            }
        }")
    
    echo "$event_type: $response"
    sleep 5  # Esperar 5 segundos entre cada webhook
}

send_webhook "payment_intent.succeeded"
send_webhook "charge.succeeded" 
send_webhook "checkout.session.completed"

echo "✅ Todos los webhooks enviados secuencialmente"
