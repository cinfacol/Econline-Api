# Generated by Django 5.0.1 on 2024-02-07 08:14

import autoslug.fields
import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='format: required, unique, max-255', max_length=255, unique=True, verbose_name='brand name')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(default='images/default.png', help_text='format: required, default-default.png', upload_to='images/', verbose_name='imagen')),
                ('alt_text', models.CharField(help_text='format: required, max-255', max_length=255, verbose_name='texto alternativo')),
                ('is_featured', models.BooleanField(default=False, help_text='format: default=false, true=default image', verbose_name='destacado')),
                ('default', models.BooleanField(default=False, help_text='format: default=false, true=default image', verbose_name='por defecto')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='format: Y-m-d H:M:S', verbose_name='creado desde')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='format: Y-m-d H:M:S', verbose_name='actualizado')),
            ],
            options={
                'verbose_name': 'product image',
                'verbose_name_plural': 'product images',
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='ProductViews',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ip', models.CharField(max_length=250, verbose_name='IP Address')),
            ],
            options={
                'verbose_name': 'Total Views on Product',
                'verbose_name_plural': 'Total Product Views',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=250, verbose_name='Product Title')),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='title', unique=True)),
                ('ref_code', models.CharField(blank=True, max_length=255, unique=True, verbose_name='Product Reference Code')),
                ('description', models.TextField(default='Default description...update me please....', verbose_name='Description')),
                ('product_number', models.IntegerField(default=112, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Product Number')),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=8, verbose_name='Price')),
                ('tax', models.DecimalField(decimal_places=2, default=0.15, help_text='15% product tax charged', max_digits=6, verbose_name='Product Tax')),
                ('product_type', models.CharField(choices=[('House', 'House'), ('Apartment', 'Apartment'), ('Office', 'Office'), ('Warehouse', 'Warehouse'), ('Commercial', 'Commercial'), ('Other', 'Other')], default='Other', max_length=50, verbose_name='Product Type')),
                ('published_status', models.BooleanField(default=False, verbose_name='Published Status')),
                ('views', models.IntegerField(default=0, verbose_name='Total Views')),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='brand', to='products.brand')),
                ('category', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='categories.category')),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
            },
        ),
    ]
