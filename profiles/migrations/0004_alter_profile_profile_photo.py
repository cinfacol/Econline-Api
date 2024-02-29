# Generated by Django 5.0.2 on 2024-02-28 17:06

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_address_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_photo',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='image'),
        ),
    ]