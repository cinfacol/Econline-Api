# Generated by Django 5.1.1 on 2025-04-17 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0016_alter_order_transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='currency',
            field=models.CharField(default='USD', max_length=10),
        ),
    ]
