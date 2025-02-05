# Generated by Django 5.1.1 on 2025-02-05 00:12

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_address_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(default='+573XXXXXXXXX', max_length=30, region=None, verbose_name='Phone Number'),
        ),
    ]
