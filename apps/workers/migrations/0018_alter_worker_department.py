# Generated by Django 5.0.6 on 2025-01-25 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workers', '0017_alter_worker_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='department',
            field=models.CharField(blank=True, choices=[('Commercial | Sales & Marketing', 'Commercial | Sales & Marketing'), ('Finance', 'Finance'), ('Pharmacie | Pharmacy', 'Pharmacie | Pharmacy'), ('Ressoure Humaine | Human Resource', 'Ressoure Humaine | Human Resource')], null=True),
        ),
    ]
