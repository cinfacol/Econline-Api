# Generated by Django 5.0.2 on 2024-04-17 09:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_rename_count_orderitem_quantity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderitem',
            old_name='quantity',
            new_name='count',
        ),
    ]
