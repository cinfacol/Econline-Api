# Generated by Django 5.0 on 2024-01-12 01:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='rating',
        ),
    ]