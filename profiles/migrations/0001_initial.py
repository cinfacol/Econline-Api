# Generated by Django 5.0.2 on 2024-02-15 04:26

import django_countries.fields
import phonenumber_field.modelfields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('address', models.CharField(max_length=255, verbose_name='Address Line 1')),
                ('address_2', models.CharField(blank=True, max_length=255, null=True, verbose_name='Address Line 2')),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(default='+573142544178', max_length=30, region=None, verbose_name='Phone Number')),
                ('country', django_countries.fields.CountryField(max_length=2, verbose_name='Country')),
                ('state', models.CharField(max_length=100, verbose_name='State')),
                ('city', models.CharField(max_length=100, verbose_name='City')),
                ('zip_code', models.CharField(max_length=20, verbose_name='Zip Code')),
                ('default', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Address',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('about_me', models.TextField(default='say something about yourself', verbose_name='About me')),
                ('license', models.CharField(blank=True, max_length=20, null=True, verbose_name='Store License')),
                ('profile_photo', models.ImageField(blank=True, default='/profile_default.png', null=True, upload_to='', verbose_name='Profile Photo')),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Other', max_length=20, verbose_name='Gender')),
                ('verified', models.CharField(choices=[('Unverified', 'Unverified'), ('Verified', 'Verified')], default='Unverified', max_length=20, verbose_name='Verified')),
                ('is_buyer', models.BooleanField(default=True, help_text='Are you looking to Buy a product?', verbose_name='Buyer')),
                ('is_seller', models.BooleanField(default=False, help_text='Are you looking to sell a product?', verbose_name='Seller')),
                ('is_agent', models.BooleanField(default=False, help_text='Are you an agent?', verbose_name='Agent')),
                ('top_agent', models.BooleanField(default=False, verbose_name='Top Agent')),
                ('num_reviews', models.IntegerField(blank=True, default=0, null=True, verbose_name='Number of Reviews')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
