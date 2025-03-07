# Generated by Django 5.0.6 on 2024-12-27 10:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
        ('workers', '0005_privilege_worker_privileges'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='Worker who created this order', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_orders', to='workers.worker'),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='sales_rep',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales_rep_orders', to='workers.worker'),
        ),
    ]
