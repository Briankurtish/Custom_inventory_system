from django.utils import timezone
from django.db import transaction

from apps.stock.models import StockMovement
from apps.stock_request.models import StockRequest, StockRequestProduct, StockTransfer, StockTransferItem

# Function to migrate StockRequest data to StockMovement
def migrate_stock_requests():
    stock_requests = StockRequest.objects.all()
    for request in stock_requests:
        # Get all related StockRequestProduct entries
        request_products = StockRequestProduct.objects.filter(stock_request=request)
        for request_product in request_products:
            try:
                with transaction.atomic():
                    # Use requested_at for transaction_date, or current time if null
                    transaction_date = request.requested_at or timezone.now()
                    StockMovement.objects.create(
                        movement_type="REQUEST",
                        stock_request=request,
                        stock_transfer=None,
                        product=request_product.product,
                        quantity=request_product.quantity,
                        batch=request_product.batch,
                        transaction_date=transaction_date
                    )
                    print(f"Created StockMovement for StockRequest #{request.request_number} - {request_product.product}")
            except Exception as e:
                print(f"Error creating StockMovement for StockRequest #{request.request_number}: {e}")

# Function to migrate StockTransfer data to StockMovement
def migrate_stock_transfers():
    stock_transfers = StockTransfer.objects.all()
    for transfer in stock_transfers:
        # Get all related StockTransferItem entries
        transfer_items = StockTransferItem.objects.filter(transfer=transfer)
        for transfer_item in transfer_items:
            try:
                with transaction.atomic():
                    # Use date_transferred for transaction_date, or current time if null
                    transaction_date = transfer.date_transferred or timezone.now()
                    StockMovement.objects.create(
                        movement_type="TRANSFER",
                        stock_request=None,
                        stock_transfer=transfer,
                        product=transfer_item.product,
                        quantity=transfer_item.quantity,
                        batch=transfer_item.batch,
                        transaction_date=transaction_date
                    )
                    print(f"Created StockMovement for StockTransfer #{transfer.transfer_id} - {transfer_item.product}")
            except Exception as e:
                print(f"Error creating StockMovement for StockTransfer #{transfer.transfer_id}: {e}")

# Run the migration
try:
    print("Starting migration of StockRequest data to StockMovement...")
    migrate_stock_requests()
    print("Completed migration of StockRequest data.")

    print("Starting migration of StockTransfer data to StockMovement...")
    migrate_stock_transfers()
    print("Completed migration of StockTransfer data.")
except Exception as e:
    print(f"An error occurred during migration: {e}")
