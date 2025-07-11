# Generated by Django 5.2.1 on 2025-05-25 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0009_remove_paymentmethod_stripe_payment_method_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Monto total del pago.', max_digits=10),
        ),
    ]
