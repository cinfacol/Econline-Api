# Generated by Django 5.0 on 2024-01-11 01:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ratings', '0003_rating_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rating',
            name='product',
        ),
    ]
