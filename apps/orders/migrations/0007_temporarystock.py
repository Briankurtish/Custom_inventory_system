# Generated by Django 5.0.6 on 2025-01-04 09:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_purchaseorder_purchase_order_id'),
        ('stock', '0003_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemporaryStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordered_quantity', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('purchase_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='temp_stocks', to='orders.purchaseorder')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.stock')),
            ],
        ),
    ]
