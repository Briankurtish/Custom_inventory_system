# Generated by Django 5.0.6 on 2025-02-21 14:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0037_delete_returnorderitem'),
        ('workers', '0025_worker_security_pin'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_returned', models.PositiveIntegerField()),
                ('reason_for_return', models.TextField(blank=True, null=True)),
                ('return_date', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='return_order_items_created_by', to='workers.worker')),
                ('invoice_order_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.invoiceorderitem')),
            ],
        ),
    ]
