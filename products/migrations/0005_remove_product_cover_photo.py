# Generated by Django 5.0 on 2024-01-06 01:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_media_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='cover_photo',
        ),
    ]
