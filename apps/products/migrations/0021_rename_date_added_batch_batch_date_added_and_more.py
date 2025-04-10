# Generated by Django 5.0.6 on 2025-01-26 23:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0020_product_date_added'),
        ('workers', '0019_alter_worker_company'),
    ]

    operations = [
        migrations.RenameField(
            model_name='batch',
            old_name='date_added',
            new_name='batch_date_added',
        ),
        migrations.AddField(
            model_name='batch',
            name='batch_created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='batches_created', to='workers.worker'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products_created', to='workers.worker'),
        ),
    ]
