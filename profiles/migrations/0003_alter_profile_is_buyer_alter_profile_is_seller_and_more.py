# Generated by Django 5.0 on 2023-12-24 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='is_buyer',
            field=models.BooleanField(default=True, help_text='Are you looking to Buy a product?', verbose_name='Buyer'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='is_seller',
            field=models.BooleanField(default=False, help_text='Are you looking to sell a product?', verbose_name='Seller'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='license',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Store License'),
        ),
    ]