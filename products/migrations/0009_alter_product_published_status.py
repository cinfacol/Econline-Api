# Generated by Django 5.0 on 2024-01-21 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_alter_product_published_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='published_status',
            field=models.BooleanField(default=False, verbose_name='Published Status'),
        ),
    ]
