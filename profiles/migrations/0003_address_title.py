# Generated by Django 5.0.2 on 2024-02-23 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='title',
            field=models.CharField(default='My House', help_text='Title of Referene', max_length=50, verbose_name='Reference'),
        ),
    ]
