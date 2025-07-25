# Generated by Django 5.2.1 on 2025-05-27 05:10

import cloudinary.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0017_order_currency'),
        ('payments', '0016_alter_payment_payment_option_delete_paymentmethod'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(help_text='SC para Stripe Card, PP para PayPal, TR para transferencia PSE, CA para Cash', max_length=10, unique=True)),
                ('label', models.CharField(help_text='Stripe Card para key SC, PayPal para key PP, Transferencia PSE para key TR, Cash para key CA', max_length=50)),
                ('icon_image', cloudinary.models.CloudinaryField(max_length=255, null=True, verbose_name='image')),
                ('alt_text', models.CharField(help_text='format: required, max-255', max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.RemoveIndex(
            model_name='payment',
            name='payments_pa_payment_76ee6e_idx',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='payment_option',
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_method',
            field=models.ForeignKey(blank=True, help_text='Método de pago utilizado.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='payments.paymentmethod'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_method'], name='payments_pa_payment_33e537_idx'),
        ),
    ]
