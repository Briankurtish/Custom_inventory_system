# Generated by Django 5.0.6 on 2024-12-13 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0007_rename_contact_person_customer_sales_rep'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='contact_person',
            field=models.CharField(default='Unknown', help_text='Contact Person', max_length=255),
            preserve_default=False,
        ),
    ]
