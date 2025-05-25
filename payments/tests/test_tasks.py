from django.core import mail
from payments.tasks import send_payment_success_email_task

def test_send_payment_success_email_task_sends_email(db):
    email = "testuser@example.com"
    result = send_payment_success_email_task(email)
    assert result is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [email]
    assert "Payment Successful" in mail.outbox[0].subject