from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.petty_cash_dashboard, name='petty_cash_dashboard'),

    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.create_transaction, name='create_transaction'),
    path('transactions/<int:transaction_id>/', views.transaction_details, name='transaction_details'),
    path('transactions/<int:transaction_id>/approve/', views.approve_transaction, name='approve_transaction'),
    path('transactions/<int:transaction_id>/disburse/', views.disburse_transaction, name='disburse_transaction'),
    path('transactions/<int:transaction_id>/upload-receipt/', views.upload_receipt, name='upload_receipt'),
    path('transactions/<int:transaction_id>/download-receipt/', views.download_petty_cash_receipt, name='download_petty_cash_receipt'),

    # Refill Requests
    path('refills/', views.refill_request_list, name='refill_request_list'),
    path('refills/create/', views.create_refill_request, name='create_refill_request'),
    path('refills/<int:refill_id>/', views.edit_refill_request, name='edit_refill_request'),
    path('refills/<int:refill_id>/approve/', views.approve_refill_request, name='approve_refill_request'),
    path('refills/<int:refill_id>/delete/', views.delete_refill_request, name='delete_refill_request'),
    path('refills/logs/', views.refill_request_logs, name='refill_request_logs'),

    # Settings
    path('settings/', views.petty_cash_settings, name='petty_cash_settings'),
    path('settings/<int:branch_id>/', views.petty_cash_settings, name='petty_cash_settings_branch'),
    path('settings/category/add/', views.add_petty_cash_category, name='add_petty_cash_category'),
    path('settings/category/edit/', views.edit_petty_cash_category, name='edit_petty_cash_category'),
    path('settings/category/delete/', views.delete_petty_cash_category, name='delete_petty_cash_category'),

    # Reports & Audit
    path('reports/', views.reports, name='petty_cash_reports'),
    path('audit-logs/', views.audit_logs, name='petty_cash_audit_logs'),
]
