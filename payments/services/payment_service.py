class PaymentService:
    def __init__(self, stripe_client):
        self.stripe_client = stripe_client
        
    def process_payment(self, payment_data):
        # Lógica de procesamiento de pago
        pass
        
    def handle_refund(self, refund_data):
        # Lógica de reembolso
        pass
