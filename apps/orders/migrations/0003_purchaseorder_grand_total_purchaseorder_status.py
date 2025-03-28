# Generated by Django 5.0.6 on 2024-12-28 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_purchaseorder_created_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='grand_total',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Total amount of the purchase order', max_digits=12),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Completed', 'Completed')], default='Pending', help_text='Current status of the purchase order', max_length=50),
        ),
    ]
