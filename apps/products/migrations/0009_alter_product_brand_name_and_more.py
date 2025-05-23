# Generated by Django 5.0.6 on 2024-12-14 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_alter_product_brand_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='brand_name',
            field=models.CharField(help_text='Designation', max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='generic_name_dosage',
            field=models.CharField(help_text='DCI et Dosage', max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='pack_size',
            field=models.CharField(help_text='Conditionnement', max_length=100),
        ),
    ]
