# Generated by Django 5.0.6 on 2025-03-06 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0011_stock_fixed_beginning_inventory_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='total_inventory',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
