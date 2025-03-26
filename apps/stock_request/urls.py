from django.urls import path
from .views import *

urlpatterns = [
    path(
        "request-list/",
        ManageRequestsView,
        name="requests",
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

]
