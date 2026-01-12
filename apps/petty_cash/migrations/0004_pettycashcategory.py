# Generated manually on 2026-01-06
# Step 1: Create PettyCashCategory model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('petty_cash', '0003_pettycashtransaction_recipient_and_more'),
        ('workers', '0030_privilegechangelog'),
    ]

    operations = [
        migrations.CreateModel(
            name='PettyCashCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_petty_cash_categories', to='workers.worker')),
            ],
            options={
                'verbose_name_plural': 'Petty Cash Categories',
                'ordering': ['name'],
            },
        ),
    ]
