# Generated by Django 5.0.6 on 2025-02-05 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0025_product_dosage_type_alter_product_dosage_form'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batch',
            name='batch_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='batch',
            name='expiry_date',
            field=models.DateField(blank=True, help_text='Expiration Date', null=True),
        ),
        migrations.AlterField(
            model_name='batch',
            name='prod_date',
            field=models.DateField(blank=True, help_text='Manufacturing Date', null=True),
        ),
    ]
