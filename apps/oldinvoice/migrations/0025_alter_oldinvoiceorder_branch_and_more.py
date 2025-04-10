# Generated by Django 5.0.6 on 2025-02-13 23:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('branches', '0008_remove_branchauditlog_branch_and_more'),
        ('customers', '0019_customerauditlog'),
        ('oldinvoice', '0024_alter_oldinvoiceorder_old_invoice_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oldinvoiceorder',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='branches.branch'),
        ),
        migrations.AlterField(
            model_name='oldinvoiceorder',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='customers.customer'),
        ),
    ]
