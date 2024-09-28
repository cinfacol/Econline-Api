# Generated by Django 5.1.1 on 2024-09-25 21:02

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_alter_inventory_published_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='image',
            field=cloudinary.models.CloudinaryField(max_length=255, null=True, verbose_name='image'),
        ),
    ]