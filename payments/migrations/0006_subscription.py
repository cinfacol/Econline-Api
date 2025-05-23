# Generated by Django 5.2.1 on 2025-05-20 22:10

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_delete_subscription'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('stripe_subscription_id', models.CharField(max_length=100)),
                ('stripe_customer_id', models.CharField(max_length=100)),
                ('stripe_price_id', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('CANCELED', 'Canceled'), ('PAST_DUE', 'Past Due'), ('UNPAID', 'Unpaid'), ('INCOMPLETE', 'Incomplete'), ('TRIALING', 'Trialing')], default='INCOMPLETE', max_length=20)),
                ('current_period_start', models.DateTimeField()),
                ('current_period_end', models.DateTimeField()),
                ('cancel_at_period_end', models.BooleanField(default=False)),
                ('canceled_at', models.DateTimeField(blank=True, null=True)),
                ('trial_start', models.DateTimeField(blank=True, null=True)),
                ('trial_end', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
