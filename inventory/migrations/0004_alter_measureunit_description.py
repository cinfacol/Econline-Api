# Generated by Django 5.0.2 on 2024-02-10 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_alter_measureunit_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='measureunit',
            name='description',
            field=models.CharField(choices=[('Units', 'Units'), ('Grams', 'Grams'), ('Pounds', 'Pounds'), ('Kilograms', 'Kilograms'), ('Mililiters', 'Mililiters'), ('Liters', 'Liters'), ('Other', 'Other')], default='Other', max_length=50, verbose_name='Descripción'),
        ),
    ]