# Generated by Django 5.0.6 on 2025-02-11 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_request', '0017_intransit_acknowleged_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='intransit',
            name='acknowleged_by',
        ),
        migrations.RemoveField(
            model_name='intransit',
            name='is_acknowledged',
        ),
        migrations.AddField(
            model_name='stockrequest',
            name='is_acknowledged',
            field=models.BooleanField(default=False, verbose_name='Acknowledge Stock'),
        ),
    ]
