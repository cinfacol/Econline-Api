# Generated by Django 5.0.2 on 2024-04-16 23:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0005_remove_cart_total_items_cart_products'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='total_items',
            field=models.IntegerField(default=0),
        ),
    ]
