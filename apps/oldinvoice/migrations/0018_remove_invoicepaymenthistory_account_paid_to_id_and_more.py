# Generated by Django 5.0.6 on 2025-02-04 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oldinvoice', '0017_alter_invoicepaymenthistory_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoicepaymenthistory',
            name='account_paid_to_id',
        ),
        migrations.RemoveField(
            model_name='invoicepaymenthistory',
            name='account_paid_to_type',
        ),
    ]
