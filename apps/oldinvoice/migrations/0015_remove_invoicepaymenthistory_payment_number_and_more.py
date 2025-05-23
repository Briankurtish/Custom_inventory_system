# Generated by Django 5.0.6 on 2025-02-04 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oldinvoice', '0014_oldinvoiceauditlog'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoicepaymenthistory',
            name='payment_number',
        ),
        migrations.AddField(
            model_name='invoicepaymenthistory',
            name='installment_number',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='invoicepaymenthistory',
            name='account_paid_to',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='invoicepaymenthistory',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.AlterField(
            model_name='invoicepaymenthistory',
            name='invoice_total',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.AlterField(
            model_name='invoicepaymenthistory',
            name='payment_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='invoicepaymenthistory',
            name='payment_mode',
            field=models.CharField(choices=[('Cash', 'Cash'), ('Mobile Money', 'Mobile Money'), ('Bank Transfer', 'Bank Transfer')], max_length=50),
        ),
    ]
