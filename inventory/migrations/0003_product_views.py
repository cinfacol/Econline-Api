# Generated by Django 5.0.1 on 2024-01-28 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='views',
            field=models.IntegerField(default=0, verbose_name='Total Views'),
        ),
    ]
