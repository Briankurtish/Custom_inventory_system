# Generated by Django 5.0.6 on 2025-02-09 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oldinvoice', '0022_alter_invoicepaymenthistory_payment_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='oldinvoiceorder',
            name='old_invoice_id',
            field=models.CharField(blank=True, help_text='Unique identifier for the old invoice', max_length=50, null=True, unique=True),
        ),
    ]
