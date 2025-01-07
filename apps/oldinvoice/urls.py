from django.urls import path
from .views import invoice_list, create_invoice_order, add_invoice_items, old_invoice_details, add_invoice_payment, payment_history

urlpatterns = [
    path(
        "old-invoice/",  # Path for listing orders
        invoice_list,  # View function for listing orders
        name="old-invoice",  # URL name for this path
    ),
    path(
        "create-invoice-order/",  # Path for creating a new order
        create_invoice_order,  # View function for creating orders
        name="create-invoice-order",  # URL name for this path
    ),
    path(
        "add-invoice-items/",  # Path for adding items to an order
        add_invoice_items,  # View function for adding items
        name="add_invoice_items",  # URL name for this path
    ),
    
    path('old-invoice-details/<int:invoice_id>/', old_invoice_details, name='invoice_details'),
     
    path('old-invoice/<int:invoice_id>/add-old-payment/', add_invoice_payment, name='add_old_invoice_payment'),
      
    path('old-invoice/<int:invoice_id>/old-payment-history/', payment_history, name='old_payment_history'),
]
