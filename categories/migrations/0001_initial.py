# Generated by Django 5.0.2 on 2024-02-18 11:41

import autoslug.fields
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MeasureUnit',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('description', models.CharField(choices=[('Units', 'Units'), ('Grams', 'Grams'), ('Pounds', 'Pounds'), ('Kilograms', 'Kilograms'), ('Mililiters', 'Mililiters'), ('Liters', 'Liters'), ('Other', 'Other')], default='Units', max_length=50, unique=True, verbose_name='Descripción')),
            ],
            options={
                'verbose_name': 'Measure Unit',
                'verbose_name_plural': 'Measure Units',
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
                ('is_parent', models.BooleanField(default=False)),
                ('measure_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='MeasureUnit', to='categories.measureunit', verbose_name='Measure Unit')),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
    ]
