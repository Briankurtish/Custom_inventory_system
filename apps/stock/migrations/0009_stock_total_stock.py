# Generated by Django 5.0.6 on 2025-02-23 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0008_stock_begining_inventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='total_stock',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
