# Generated manually on 2026-01-06
# Step 2: Populate categories with default values

from django.db import migrations


def create_default_categories(apps, schema_editor):
    """Create default categories"""
    PettyCashCategory = apps.get_model('petty_cash', 'PettyCashCategory')

    default_categories = [
        'Transport',
        'Maintenance',
        'Staff Meals',
        'Office Supplies',
        'Utilities',
        'Communication',
        'Cleaning',
        'Emergency',
        'Repairs',
        'Fuel',
        'Miscellaneous',
    ]

    for category_name in default_categories:
        PettyCashCategory.objects.get_or_create(
            name=category_name,
            defaults={'is_active': True}
        )


def reverse_create_default_categories(apps, schema_editor):
    """Remove default categories"""
    PettyCashCategory = apps.get_model('petty_cash', 'PettyCashCategory')
    PettyCashCategory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('petty_cash', '0004_pettycashcategory'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, reverse_create_default_categories),
    ]
