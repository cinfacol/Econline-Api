# Generated by Django 5.1.1 on 2025-03-09 20:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_alter_order_address'),
        ('shipping', '0001_initial'),
        ('users', '0010_remove_address_default_address_is_default'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='shipping_name',
        ),
        migrations.RemoveField(
            model_name='order',
            name='shipping_price',
        ),
        migrations.RemoveField(
            model_name='order',
            name='shipping_time',
        ),
        migrations.AddField(
            model_name='order',
            name='shipping',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shipping.shipping'),
        ),
        migrations.AlterField(
            model_name='order',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.address'),
        ),
    ]
