# Critical performance fix - adds database indexes
# Generated on 2026-02-20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0090_bondelivraisonconfig_partiallivraisonitem'),
    ]

    operations = [
        # Invoice indexes - CRITICAL for report performance
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['created_at'], name='inv_created_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['branch', 'created_at'], name='inv_branch_date_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['customer', 'created_at'], name='inv_cust_date_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['sales_rep', 'created_at'], name='inv_rep_date_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['amount_due'], name='inv_due_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['status'], name='inv_status_idx'),
        ),
        
        # PurchaseOrder indexes
        migrations.AddIndex(
            model_name='purchaseorder',
            index=models.Index(fields=['created_at'], name='po_created_idx'),
        ),
        migrations.AddIndex(
            model_name='purchaseorder',
            index=models.Index(fields=['branch', 'created_at'], name='po_branch_date_idx'),
        ),
        migrations.AddIndex(
            model_name='purchaseorder',
            index=models.Index(fields=['customer', 'created_at'], name='po_cust_date_idx'),
        ),
        migrations.AddIndex(
            model_name='purchaseorder',
            index=models.Index(fields=['sales_rep', 'created_at'], name='po_rep_date_idx'),
        ),
        
        # InvoicePayment indexes
        migrations.AddIndex(
            model_name='invoicepayment',
            index=models.Index(fields=['payment_date'], name='pay_date_idx'),
        ),
        migrations.AddIndex(
            model_name='invoicepayment',
            index=models.Index(fields=['invoice', 'payment_date'], name='pay_inv_date_idx'),
        ),
    ]
