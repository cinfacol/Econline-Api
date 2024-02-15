# Generated by Django 5.0.2 on 2024-02-15 04:26

import django.core.validators
import django.db.models.deletion
import uuid
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('coupon_code', models.CharField(max_length=20)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PromoType',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductsOnPromotion',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('promo_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('price_override', models.BooleanField(default=False)),
                ('product_inventory_id', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ProductInventoryOnPromotion', to='inventory.inventory')),
            ],
        ),
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('promo_reduction', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=False)),
                ('is_schedule', models.BooleanField(default=False)),
                ('promo_start', models.DateField()),
                ('promo_end', models.DateField()),
                ('coupon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='coupon', to='promotion.coupon')),
                ('products_on_promotion', models.ManyToManyField(related_name='products_on_promotion', through='promotion.ProductsOnPromotion', to='inventory.inventory')),
                ('promo_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='promotype', to='promotion.promotype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='productsonpromotion',
            name='promotion_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='promotion', to='promotion.promotion'),
        ),
        migrations.AlterUniqueTogether(
            name='productsonpromotion',
            unique_together={('product_inventory_id', 'promotion_id')},
        ),
    ]
