# Generated by Django 5.0.2 on 2024-02-15 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_alter_address_country'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.CharField(max_length=100, verbose_name='Country'),
        ),
    ]
