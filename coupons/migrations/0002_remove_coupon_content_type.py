# Generated by Django 5.0.2 on 2024-04-13 22:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coupons', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coupon',
            name='content_type',
        ),
    ]