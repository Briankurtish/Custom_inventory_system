from django.db import migrations

def populate_stock_batches(apps, schema_editor):
    Stock = apps.get_model('stock', 'Stock')
    for stock in Stock.objects.all():
        if not stock.batch:  # Only update records without a batch
            # Assign the batch from the associated product
            stock.batch = stock.product.batch
            stock.save()

class Migration(migrations.Migration):
    dependencies = [
        ('stock', '0014_alter_stock_unique_together_stock_batch_and_more'),  # Replace with the last migration file name
    ]
    operations = [
        migrations.RunPython(populate_stock_batches),
    ]