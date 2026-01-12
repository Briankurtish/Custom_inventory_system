from django.contrib import admin
from .models import (
    PettyCashSettings,
    PettyCashBalance,
    PettyCashTransaction,
    PettyCashReceipt,
    PettyCashRefillRequest,
    PettyCashAuditLog
)


@admin.register(PettyCashSettings)
class PettyCashSettingsAdmin(admin.ModelAdmin):
    list_display = ['branch', 'daily_cash_limit', 'daily_momo_limit', 'daily_orange_limit', 'updated_at']
    list_filter = ['branch', 'updated_at']
    search_fields = ['branch__branch_name']


@admin.register(PettyCashBalance)
class PettyCashBalanceAdmin(admin.ModelAdmin):
    list_display = ['branch', 'channel', 'month', 'opening_balance', 'current_balance', 'total_inflow', 'total_outflow']
    list_filter = ['branch', 'channel', 'month']
    search_fields = ['branch__branch_name']
    date_hierarchy = 'month'


@admin.register(PettyCashTransaction)
class PettyCashTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'branch', 'transaction_type', 'channel', 'amount', 'recipient_name', 'status', 'created_at']
    list_filter = ['status', 'transaction_type', 'channel', 'branch', 'category', 'created_at']
    search_fields = ['transaction_id', 'recipient_name', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']


@admin.register(PettyCashReceipt)
class PettyCashReceiptAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['transaction__transaction_id']
    date_hierarchy = 'uploaded_at'


@admin.register(PettyCashRefillRequest)
class PettyCashRefillRequestAdmin(admin.ModelAdmin):
    list_display = ['refill_id', 'branch', 'source_type', 'requested_amount', 'status', 'requested_at']
    list_filter = ['status', 'source_type', 'branch', 'requested_at']
    search_fields = ['refill_id', 'branch__branch_name', 'source_branch__branch_name']
    date_hierarchy = 'requested_at'
    readonly_fields = ['refill_id', 'requested_at']


@admin.register(PettyCashAuditLog)
class PettyCashAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'branch', 'timestamp']
    list_filter = ['action', 'branch', 'timestamp']
    search_fields = ['user__user__username', 'details']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']
