# Generated by Django 5.1.1 on 2025-02-04 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_address_options_address_phone_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address_line_1',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='address',
            name='address_line_2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
