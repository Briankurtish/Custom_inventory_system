# web_project/context_processors.py
from django.db.models import Sum
from apps.orders.models import Invoice
from apps.orders.models import PurchaseOrder
from apps.stock_request.models import StockRequest

def pending_counts(request):
    """
    A context processor to add counts of pending deposits and withdrawals to all templates.
    """
    if request.user.is_authenticated:
        # Fetch real-time counts directly from the database
        unpaid_invoices_count = Invoice.objects.filter(status='Unpaid').count()
        pending_orders_count = PurchaseOrder.objects.filter(status='Pending').count()
        pending_request_count = StockRequest.objects.filter(status='Pending').count()
        
        
        return {
            "unpaid_invoices_count": unpaid_invoices_count,
            'pending_orders_count': pending_orders_count,
            'pending_request_count': pending_request_count,
            
        }
    return {}
