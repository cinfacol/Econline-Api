# Generated by Django 5.0.1 on 2024-02-07 08:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='user',
            field=models.ManyToManyField(related_name='product_user', to=settings.AUTH_USER_MODEL, verbose_name='Agent, Seller or Buyer'),
        ),
        migrations.AddField(
            model_name='media',
            name='inventory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventory_media', to='inventory.inventory'),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ManyToManyField(to='inventory.category'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='product', to='inventory.product'),
        ),
        migrations.AddField(
            model_name='stock',
            name='inventory',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='inventory_stock', to='inventory.inventory'),
        ),
        migrations.AddField(
            model_name='type',
            name='type_attributes',
            field=models.ManyToManyField(related_name='type_attributes', to='inventory.attribute'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='product_type', to='inventory.type'),
        ),
    ]
