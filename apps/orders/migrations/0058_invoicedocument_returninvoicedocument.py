# Generated by Django 5.0.6 on 2025-03-20 08:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0057_returnpurchaseorderdocument'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoiceDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('Invoice', 'Invoice')], max_length=50)),
                ('document', models.FileField(null=True, upload_to='invoice_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='orders.invoice')),
            ],
        ),
        migrations.CreateModel(
            name='ReturnInvoiceDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('Invoice', 'Invoice')], max_length=50)),
                ('document', models.FileField(null=True, upload_to='return_invoice_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('return_invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='orders.returninvoice')),
            ],
        ),
    ]
