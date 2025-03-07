# Generated by Django 5.0.6 on 2025-01-11 11:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genericName', '0003_alter_genericname_brand_name_and_more'),
        ('products', '0015_alter_product_batch_alter_product_brand_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batch',
            name='batch_number',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='batch',
            name='generic_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='genericName.genericname'),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_code',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
