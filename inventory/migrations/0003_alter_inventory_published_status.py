# Generated by Django 5.0.2 on 2024-02-25 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='published_status',
            field=models.BooleanField(default=True, verbose_name='Published Status'),
        ),
    ]
