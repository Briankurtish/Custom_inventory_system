from django.urls import path
from .views import invoice_list, create_invoice_order, add_invoice_items

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
    
    #  path('order/<int:order_id>/', order_details, name='order_details'),
]
