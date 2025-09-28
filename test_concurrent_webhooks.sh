#!/bin/bash

echo "🧪 Simulando webhooks concurrentes como Stripe..."

# Configurar datos de prueba
PAYMENT_ID="f02a2cdf-fb51-49dc-be3a-2882adb4e8ab"
ORDER_ID="69655bb3-db53-41ff-8476-7a27ab2de8c3"

# Función para enviar webhook
send_webhook() {
    local event_type=$1
    local event_id=$2
    local delay=$3
    
    sleep $delay
    
    echo "Enviando $event_type (delay: ${delay}s)..."
    
    response=$(curl -s -w "%{http_code}" -X POST https://api.virtualeline.com/api/payments/stripe_webhook/ \
        -H "Content-Type: application/json" \
        -H "Stripe-Signature: test_signature_$event_id" \
        -d "{
            \"id\": \"$event_id\",
            \"type\": \"$event_type\", 
            \"data\": {
                \"object\": {
                    \"id\": \"test_object_$event_id\",
                    \"amount\": 11500,
                    \"currency\": \"usd\",
                    \"metadata\": {
                        \"payment_id\": \"$PAYMENT_ID\",
                        \"order_id\": \"$ORDER_ID\"
                    }
                }
            }
        }")
    
    echo "$event_type: $response"
}

# Simular el timing real de Stripe (enviar en paralelo con pequeños delays)
send_webhook "payment_intent.succeeded" "evt_pi_001" 0 &
send_webhook "charge.succeeded" "evt_charge_001" 2 &
send_webhook "checkout.session.completed" "evt_checkout_001" 2 &

# Esperar a que todos terminen
wait

echo "✅ Todos los webhooks enviados"
