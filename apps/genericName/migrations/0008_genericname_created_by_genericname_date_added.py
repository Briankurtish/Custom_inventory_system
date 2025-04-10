# Generated by Django 5.0.6 on 2025-01-26 23:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('genericName', '0007_alter_genericname_generic_name'),
        ('workers', '0019_alter_worker_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericname',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='genericname_created', to='workers.worker'),
        ),
        migrations.AddField(
            model_name='genericname',
            name='date_added',
            field=models.DateField(auto_now_add=True, null=True),
        ),
    ]
