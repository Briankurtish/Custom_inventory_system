# Generated by Django 5.0.6 on 2025-02-04 18:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oldinvoice', '0016_remove_invoicepaymenthistory_account_paid_to_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoicepaymenthistory',
            options={'ordering': ['installment_number'], 'verbose_name': 'Invoice Payment History', 'verbose_name_plural': 'Invoice Payment Histories'},
        ),
    ]
