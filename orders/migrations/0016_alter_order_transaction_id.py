# Generated by Django 5.1.1 on 2025-04-07 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0015_remove_order_shipping_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='transaction_id',
            field=models.CharField(help_text='Identificador único de la transacción', max_length=100, unique=True),
        ),
    ]
