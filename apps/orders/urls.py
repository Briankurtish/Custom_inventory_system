from django.urls import path
from .views import order_list, create_purchase_order, add_order_items, order_details, get_customer_report, get_sales_rep_credit_history, approve_order, reject_order, edit_prices, generate_purchase_order_pdf, cancel_order, invoice_list, add_invoice_payment, payment_history

urlpatterns = [
    path(
        "orders-list/",  # Path for listing orders
        order_list,  # View function for listing orders
        name="orders",  # URL name for this path
    ),
    path(
        "invoice-list/",  # Path for listing orders
        invoice_list,  # View function for listing orders
        name="invoices",  # URL name for this path
    ),
    path(
        "create-order/",  # Path for creating a new order
        create_purchase_order,  # View function for creating orders
        name="create-order",  # URL name for this path
    ),
    path(
        "add-order-items/",  # Path for adding items to an order
        add_order_items,  # View function for adding items
        name="add_order_items",  # URL name for this path
    ),
    
    path('order/<int:order_id>/', order_details, name='order_details'),
    
    path('customer-report/<int:customer_id>/', get_customer_report, name='customer_credit_report'),
    
    path("worker/<int:worker_id>/credit-history/", get_sales_rep_credit_history, name="sales_rep_credit_history"),
    
    path('order/<int:order_id>/approve/', approve_order, name='approve_order'),
    path('order/<int:order_id>/reject/', reject_order, name='reject_order'),
    path('orders/<int:order_id>/edit-prices/', edit_prices, name='edit_prices'),
    path('order/<int:order_id>/pdf/', generate_purchase_order_pdf, name='generate_purchase_order_pdf'),
    path('orders/<int:order_id>/cancel/', cancel_order, name='cancel_order'),
    
    path('invoice/<int:invoice_id>/add-payment/', add_invoice_payment, name='add_invoice_payment'),
    
    path('invoice/<int:invoice_id>/payment-history/', payment_history, name='payment_history'),
    
    

]
