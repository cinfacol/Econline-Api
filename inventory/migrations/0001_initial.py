# Generated by Django 5.0.1 on 2024-01-26 19:57

import autoslug.fields
import django.core.validators
import django.db.models.deletion
import django.db.models.manager
import inventory.fields
import uuid
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='name', unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('units', models.IntegerField(default=0)),
                ('units_sold', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Stock',
            },
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('value', models.CharField(max_length=100)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attribute', to='inventory.attribute')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sku', models.CharField(blank=True, help_text='This field is auto-generated', max_length=20, unique=True)),
                ('upc', models.CharField(blank=True, help_text='This field is auto-generated', max_length=20, unique=True)),
                ('order', inventory.fields.OrderField(blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_default', models.BooleanField(default=False)),
                ('published_status', models.BooleanField(default=False, verbose_name='Published Status')),
                ('retail_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('store_price', models.DecimalField(decimal_places=2, max_digits=7)),
                ('is_digital', models.BooleanField(default=False)),
                ('weight', models.FloatField(blank=True, null=True)),
                ('views', models.IntegerField(default=0, verbose_name='Total Views')),
                ('attribute_values', models.ManyToManyField(related_name='attribute_values', to='inventory.attributevalue')),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='brand', to='inventory.brand')),
            ],
            options={
                'verbose_name_plural': 'Inventory',
            },
            managers=[
                ('published', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('img_url', models.ImageField(default='no_image.png', upload_to=None)),
                ('alt_text', models.CharField(max_length=255)),
                ('is_feature', models.BooleanField(default=False)),
                ('inventory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='inventory.inventory')),
            ],
            options={
                'verbose_name_plural': 'Images',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='name', unique=True)),
                ('ref_code', models.CharField(blank=True, max_length=12, unique=True, verbose_name='Product Reference Code')),
                ('description', models.TextField(blank=True)),
                ('type', models.CharField(choices=[('Home', 'Home'), ('Office', 'Office'), ('Commercial', 'Commercial'), ('Other', 'Other')], default='Other', max_length=50, verbose_name='Product Type')),
                ('is_active', models.BooleanField(default=True)),
                ('category', models.ManyToManyField(related_name='product', to='inventory.category')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
