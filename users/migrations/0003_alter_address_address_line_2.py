# Generated by Django 5.1.1 on 2025-02-03 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address_line_2',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
