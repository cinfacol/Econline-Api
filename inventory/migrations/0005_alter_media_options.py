# Generated by Django 5.1.1 on 2024-09-27 20:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_media_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='media',
            options={'ordering': ('created_at',), 'verbose_name': 'Image', 'verbose_name_plural': 'Photos'},
        ),
    ]
