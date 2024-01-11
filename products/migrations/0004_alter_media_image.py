# Generated by Django 5.0 on 2024-01-05 23:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_alter_media_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='image',
            field=models.ImageField(default='images/default.png', help_text='format: required, default-default.png', upload_to='images/', verbose_name='imagen'),
        ),
    ]