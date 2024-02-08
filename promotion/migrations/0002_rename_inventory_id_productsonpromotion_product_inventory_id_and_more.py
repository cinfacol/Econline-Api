# Generated by Django 5.0.2 on 2024-02-08 03:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_remove_inventory_attribute_and_more'),
        ('promotion', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productsonpromotion',
            old_name='inventory_id',
            new_name='product_inventory_id',
        ),
        migrations.AlterUniqueTogether(
            name='productsonpromotion',
            unique_together={('product_inventory_id', 'promotion_id')},
        ),
    ]
