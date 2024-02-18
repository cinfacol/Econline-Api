# Generated by Django 5.0.2 on 2024-02-18 11:41

import autoslug.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
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
                ('is_active', models.BooleanField(default=True)),
                ('published_status', models.BooleanField(default=False, verbose_name='Published Status')),
                ('category', models.ManyToManyField(to='categories.category')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
