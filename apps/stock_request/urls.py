from django.urls import path
from .views import *

urlpatterns = [
    path(
        "request-list/",
        ManageRequestsView,
        name="requests",
    ),
    path(
        "all-request-list/",
        ManageAllRequestsView,
        name="all_requests",
    ),
    path(
        "request-logs/", RequestAuditLogView, name="request-logs",
    ),
    path(
        "create-request/",
        stock_request_view,
        name="create-request",
    ),
    path(
        "request-details/",
        stock_request_view,
        name="request-details",
    ),
    path('stock-request/<int:request_id>/', stock_request_details, name='stock_request_details'),
    path('stock-request-doc/<int:request_id>/', stock_request_doc_view, name='stock_request_doc'),
    path('tranfer-slip-doc/<int:request_id>/', transfer_slip_doc_view, name='transfer_slip_doc'),
    path('receipt=-note-doc/<int:request_id>/', goods_receipt_doc_view, name='receipt_note_doc'),
    path('stock-request/<int:request_id>/action/', approve_or_decline_request, name='approve_or_decline_request'),
     path('stock-received/<int:request_id>/', stock_received, name='stock_received'),
    path('stocks-in-transit/', stocks_in_transit, name='stocks_in_transit'),
    path('stock-movement/', stocks_movement, name='stock_movement'),
    path('stocks-received/', stocks_received_list, name='stock_received'),


    path('stock-request/<int:request_id>/upload-document/', upload_stock_request_document, name='upload_stock_request_document'),
    path('stock-request/document/<int:document_id>/edit/', edit_stock_request_document, name='edit_stock_request_document'),
    path('stock-request/document/<int:document_id>/delete/', delete_stock_request_document, name='delete_stock_request_document'),


    path('transfers/', ManageTransfersView, name='transfers'),
    path('transfer/create/', stock_transfer_view, name='create-transfer'),
    path('transfer/details/<str:transfer_id>/', stock_transfer_details_view, name='stock_transfer_details'),
    path('transfer/complete/<str:transfer_id>/', complete_transfer_view, name='complete-transfer'),  # New URL for completing a transfer

    path('picking-list-document/<str:transfer_id>/', picking_list_doc_view_transfer, name='picking_list_doc_transfer'),
    path('tranfer-slip-document/<str:transfer_id>/', transfer_slip_doc_view_transfer, name='transfer_slip_doc_transfer'),
    path('receipt-note-document/<str:transfer_id>/', goods_receipt_doc_view_transfer, name='receipt_note_doc_transfer'),

    path('transfer-logs/', StockTransferAuditLogView, name='transfer-logs'),

    path('stock-transfer/<int:transfer_id>/upload-document/', upload_stock_transfer_document, name='upload_stock_transfer_document'),
    path('stock-transfer/document/<int:document_id>/edit/', edit_stock_transfer_document, name='edit_stock_transfer_document'),
    path('stock-transfer/document/<int:document_id>/delete/', delete_stock_transfer_document, name='delete_stock_transfer_document'),
]
