from django.urls import path
from .views import *
urlpatterns = [
    path(
        "orders-list/",  # Path for listing orders
        order_list,  # View function for listing orders
        name="orders",  # URL name for this path
    ),
    path(
        "order-logs/", PurchaseOrderAuditLogView, name="order-logs",
    ),
    path(
        "purchase-order/<str:purchase_order_id>", view_purchase_order, name="purchase-order",
    ),
    path(
        "picking-list/<str:purchase_order_id>", picking_list_doc_view, name="picking-list",
    ),
    path(
        "invoice-logs/", InvoiceAuditLogView, name="invoice-logs",
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
        "create-payment-schedule/",  # Path for creating a new order
        create_payment_schedule,  # View function for creating orders
        name="create_payment_schedule",  # URL name for this path
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


    path(
        "add-bank/", add_bank_details_view, name="add-bank",
    ),
    path("edit-bank/<int:pk>/", edit_bank_details_view, name="edit-bank"),
    path("delete-bank/<int:pk>/", delete_bank_details_view, name="delete-bank"),


    path(
        "add-momo/", add_momo_details_view, name="add-momo",
    ),
    path("edit-momo/<int:pk>/", edit_momo_details_view, name="edit-momo"),
    path("delete-momo/<int:pk>/", delete_momo_details_view, name="delete-momo"),

    path(
        "add-check/", add_check_details_view, name="add-check",
    ),
    path("edit-check/<int:pk>/", edit_check_details_view, name="edit-check"),
    path("delete-check/<int:pk>/", delete_check_details_view, name="delete-check"),


    path(
        "add-deposit/", add_deposit_details_view, name="add-deposit",
    ),
    path("edit-deposit/<int:pk>/", edit_deposit_details_view, name="edit-deposit"),
    path("delete-deposit/<int:pk>/", delete_deposit_details_view, name="delete-deposit"),
    path("invoice/<int:invoice_id>/", invoice_doc_view, name="invoice-doc"),

    path('receipt/<str:receipt_id>/', receipt_doc_view, name='receipt_doc'),
    path('payment/<int:payment_id>/receipt/', payment_receipt_view, name='payment_receipt'),  # ✅ Find receipt

    path('invoice/<int:invoice_id>/return/', return_items, name='return_items'),
    path("returns/<int:invoice_id>/", process_return, name="process_return"),

    path("order/<int:order_id>/add-tax/", add_tax_to_order, name="add_tax_to_order"),


    path('orders/<int:order_id>/upload-document/', upload_purchase_order_document, name='upload_purchase_order_document'),
    path('documents/<int:document_id>/edit/', edit_document, name='edit_document'),
    path('documents/<int:document_id>/delete/', delete_document, name='delete_document'),


    path('invoice/<int:invoice_id>/upload/', upload_invoice_document, name='upload_invoice_document'),
    path('invoice-document/<int:document_id>/edit/', edit_invoice_document, name='edit_invoice_document'),
    path('invoice-document/<int:document_id>/delete/', delete_invoice_document, name='delete_invoice_document'),

    path("return-payment-schedule/<int:return_invoice_id>/", create_return_payment_schedule, name="create_return_payment_schedule"),
    
    path('invoice/<int:invoice_id>/return/', return_order, name='return_order'),

]
