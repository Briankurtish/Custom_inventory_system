# Generated by Django 5.0.6 on 2025-02-13 23:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oldinvoice', '0025_alter_oldinvoiceorder_branch_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oldinvoiceauditlog',
            name='action',
            field=models.CharField(choices=[('create', 'Created'), ('payment', 'Payment Made'), ('delet', 'Deleted')], max_length=50),
        ),
    ]
