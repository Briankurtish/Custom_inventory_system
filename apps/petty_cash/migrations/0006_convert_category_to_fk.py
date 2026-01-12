# Generated manually on 2026-01-06
# Step 3: Convert category field from CharField to ForeignKey

import django.db.models.deletion
from django.db import migrations, models


def migrate_category_data(apps, schema_editor):
    """Migrate existing category data from CharField to ForeignKey"""
    PettyCashTransaction = apps.get_model('petty_cash', 'PettyCashTransaction')
    PettyCashCategory = apps.get_model('petty_cash', 'PettyCashCategory')

    for transaction in PettyCashTransaction.objects.all():
        if transaction.category_old:
            # Get or create category based on the old string value
            category, created = PettyCashCategory.objects.get_or_create(
                name=transaction.category_old,
                defaults={'is_active': True}
            )
            transaction.category = category
            transaction.save(update_fields=['category'])


def reverse_migrate_category_data(apps, schema_editor):
    """Reverse migration: copy category names back to old field"""
    PettyCashTransaction = apps.get_model('petty_cash', 'PettyCashTransaction')

    for transaction in PettyCashTransaction.objects.all():
        if transaction.category:
            transaction.category_old = transaction.category.name
            transaction.save(update_fields=['category_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('petty_cash', '0005_populate_categories'),
    ]

    operations = [
        # Step 1: Rename old category field
        migrations.RenameField(
            model_name='pettycashtransaction',
            old_name='category',
            new_name='category_old',
        ),
        # Step 2: Add new category FK field
        migrations.AddField(
            model_name='pettycashtransaction',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transactions',
                to='petty_cash.pettycashcategory'
            ),
        ),
        # Step 3: Migrate data
        migrations.RunPython(migrate_category_data, reverse_migrate_category_data),
        # Step 4: Remove old field
        migrations.RemoveField(
            model_name='pettycashtransaction',
            name='category_old',
        ),
    ]
