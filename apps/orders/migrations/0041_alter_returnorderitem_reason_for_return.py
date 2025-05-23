# Generated by Django 5.0.6 on 2025-02-28 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0040_alter_invoice_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnorderitem',
            name='reason_for_return',
            field=models.CharField(choices=[('Non-payment', 'Non-payment'), ('Damaged product', 'Damaged product'), ('Compromised packaging', 'Compromised packaging'), ('Incorrect quantity', 'Incorrect quantity'), ('Expiry date due', 'Expiry date due'), ('Incorrect item', 'Incorrect item')], max_length=50, null=True),
        ),
    ]
