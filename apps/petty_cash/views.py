from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
from decimal import Decimal
import json
from calendar import monthrange

from .models import (
    PettyCashCategory,
    PettyCashTransaction,
    PettyCashBalance,
    PettyCashSettings,
    PettyCashRefillRequest,
    PettyCashReceipt,
    PettyCashAuditLog
)
from .forms import (
    PettyCashTransactionForm,
    PettyCashApprovalForm,
    PettyCashSettingsForm,
    PettyCashRefillRequestForm,
    PettyCashRefillApprovalForm,
    PettyCashRefillCompletionForm,
    PettyCashReceiptForm,
    PettyCashReportFilterForm
)
from apps.branches.models import Branch
from apps.workers.models import Worker
from web_project import TemplateLayout


def get_client_ip(request):
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit(user, action, details, branch=None, transaction=None, refill_request=None, request=None):
    """Helper function to log audit trail"""
    ip_address = get_client_ip(request) if request else None
    PettyCashAuditLog.objects.create(
        user=user,
        action=action,
        details=details,
        branch=branch,
        transaction=transaction,
        refill_request=refill_request,
        ip_address=ip_address
    )


def get_or_create_balance(branch, channel, month_date):
    """Get or create balance record for a branch/channel/month"""
    # Ensure month_date is the first day of the month
    first_day = month_date.replace(day=1)

    balance, created = PettyCashBalance.objects.get_or_create(
        branch=branch,
        channel=channel,
        month=first_day,
        defaults={
            'opening_balance': Decimal('0.00'),
            'current_balance': Decimal('0.00'),
            'total_inflow': Decimal('0.00'),
            'total_outflow': Decimal('0.00'),
        }
    )

    # If created, try to get previous month's closing balance as opening balance
    if created:
        prev_month = first_day - timedelta(days=1)
        prev_month_first = prev_month.replace(day=1)
        try:
            prev_balance = PettyCashBalance.objects.get(
                branch=branch,
                channel=channel,
                month=prev_month_first
            )
            balance.opening_balance = prev_balance.current_balance
            balance.current_balance = prev_balance.current_balance
            balance.save()
        except PettyCashBalance.DoesNotExist:
            pass

    return balance


@login_required
def petty_cash_dashboard(request):
    """Main dashboard showing current balances and overview"""
    user = request.user
    worker = user.worker_profile

    # Get all branches or filter by user's branch (only active)
    if user.is_superuser:
        branches = Branch.objects.filter(is_active=True)
    else:
        branches = Branch.objects.filter(id=worker.branch.id, is_active=True)

    # Get current month
    today = timezone.now().date()
    current_month = today.replace(day=1)

    # Get all balances for current month
    balances = PettyCashBalance.objects.filter(month=current_month, branch__in=branches)

    # Calculate consolidated balances
    consolidated = {
        'Cash': Decimal('0.00'),
        'MTN_MoMo': Decimal('0.00'),
        'Orange_Money': Decimal('0.00'),
    }

    # Map channel names to dict keys
    channel_map = {
        'Cash': 'Cash',
        'MTN MoMo': 'MTN_MoMo',
        'Orange Money': 'Orange_Money',
    }

    for balance in balances:
        key = channel_map.get(balance.channel, balance.channel)
        consolidated[key] += balance.current_balance

    # Get balances by branch
    branch_balances = {}
    for branch in branches:
        branch_balances[branch] = {
            'Cash': Decimal('0.00'),
            'MTN_MoMo': Decimal('0.00'),
            'Orange_Money': Decimal('0.00'),
        }

        branch_bal = balances.filter(branch=branch)
        for bal in branch_bal:
            key = channel_map.get(bal.channel, bal.channel)
            branch_balances[branch][key] = bal.current_balance

    # Get low balance alerts
    alerts = []
    for branch in branches:
        try:
            settings = PettyCashSettings.objects.get(branch=branch)
            branch_bal = branch_balances[branch]

            if branch_bal['Cash'] < settings.cash_refill_threshold:
                alerts.append({
                    'branch': branch,
                    'channel': 'Cash',
                    'balance': branch_bal['Cash'],
                    'threshold': settings.cash_refill_threshold
                })

            if branch_bal['MTN_MoMo'] < settings.momo_refill_threshold:
                alerts.append({
                    'branch': branch,
                    'channel': 'MTN MoMo',
                    'balance': branch_bal['MTN_MoMo'],
                    'threshold': settings.momo_refill_threshold
                })

            if branch_bal['Orange_Money'] < settings.orange_refill_threshold:
                alerts.append({
                    'branch': branch,
                    'channel': 'Orange Money',
                    'balance': branch_bal['Orange_Money'],
                    'threshold': settings.orange_refill_threshold
                })
        except PettyCashSettings.DoesNotExist:
            pass

    # Get opening balances for current month
    opening_balances = {}
    for branch in branches:
        opening_balances[branch.id] = {}
        for channel in ['Cash', 'MTN MoMo', 'Orange Money']:
            balance_obj = PettyCashBalance.objects.filter(
                branch=branch,
                channel=channel,
                month=current_month
            ).first()
            if balance_obj:
                opening_balances[branch.id][channel] = balance_obj.opening_balance
            else:
                opening_balances[branch.id][channel] = Decimal('0.00')

    # Get recent transactions with running balance
    recent_transactions_raw = PettyCashTransaction.objects.filter(
        branch__in=branches
    ).select_related('recipient', 'recipient__user', 'category', 'branch').order_by('-created_at')[:10]

    # Calculate running balance for each transaction
    recent_transactions = []
    for txn in recent_transactions_raw:
        # Get the balance after this transaction was disbursed
        if txn.status == 'Disbursed' and txn.disbursed_at:
            balance_obj = PettyCashBalance.objects.filter(
                branch=txn.branch,
                channel=txn.channel,
                month=txn.disbursed_at.replace(day=1)
            ).first()
            running_balance = balance_obj.current_balance if balance_obj else Decimal('0.00')
        else:
            running_balance = None

        # Add recipient display name
        if txn.recipient:
            recipient_display = txn.recipient.user.get_full_name()
        elif txn.recipient_name:
            recipient_display = txn.recipient_name
        else:
            recipient_display = 'N/A'

        # Create a dict with transaction and additional info
        txn_data = {
            'transaction': txn,
            'running_balance': running_balance,
            'recipient_display': recipient_display
        }
        recent_transactions.append(txn_data)

    # Get pending approvals count
    pending_count = PettyCashTransaction.objects.filter(
        branch__in=branches,
        status='Pending'
    ).count()

    # Get pending refills count
    pending_refills = PettyCashRefillRequest.objects.filter(
        branch__in=branches,
        status='Pending'
    ).count()

    # Month-to-date statistics
    month_start = today.replace(day=1)
    mtd_stats = PettyCashTransaction.objects.filter(
        branch__in=branches,
        created_at__gte=month_start,
        status='Disbursed'
    ).aggregate(
        total_disbursed=Sum('amount'),
        transaction_count=Count('id')
    )

    view_context = {
        'consolidated_balances': consolidated,
        'branch_balances': branch_balances,
        'alerts': alerts,
        'recent_transactions': recent_transactions,
        'opening_balances': opening_balances,
        'pending_count': pending_count,
        'pending_refills': pending_refills,
        'mtd_stats': mtd_stats,
        'current_month': current_month,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/dashboard.html', context)


@login_required
def transaction_list(request):
    """List all petty cash transactions with filtering"""
    user = request.user
    worker = user.worker_profile

    # Get filter parameters
    status_filter = request.GET.get('status', '')
    channel_filter = request.GET.get('channel', '')
    category_filter = request.GET.get('category', '')
    branch_filter = request.GET.get('branch', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    search_query = request.GET.get('search_query', '')

    # Base queryset
    if user.is_superuser:
        transactions = PettyCashTransaction.objects.all()
    else:
        transactions = PettyCashTransaction.objects.filter(branch=worker.branch)

    # Apply filters
    if status_filter:
        transactions = transactions.filter(status=status_filter)

    if channel_filter:
        transactions = transactions.filter(channel=channel_filter)

    if category_filter:
        transactions = transactions.filter(category=category_filter)

    if branch_filter:
        transactions = transactions.filter(branch_id=branch_filter)

    if start_date:
        transactions = transactions.filter(created_at__gte=start_date)

    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        transactions = transactions.filter(created_at__lte=end_date_obj)

    if search_query:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search_query) |
            Q(recipient_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Order transactions chronologically for balance calculation
    transactions = transactions.order_by('-created_at')

    # Get current month and opening balances
    today = timezone.now().date()
    current_month = today.replace(day=1)

    # Get all branches accessible to user
    if user.is_superuser:
        all_branches = Branch.objects.filter(is_active=True)
    else:
        all_branches = Branch.objects.filter(id=worker.branch.id, is_active=True)

    # Filter opening balances by selected branch if applicable
    if branch_filter:
        filtered_branches = all_branches.filter(id=branch_filter)
    else:
        filtered_branches = all_branches

    # Get opening balances for current month (only for filtered branches)
    opening_balances = {}
    for branch in filtered_branches:
        opening_balances[branch.id] = {}
        for channel in ['Cash', 'MTN MoMo', 'Orange Money']:
            balance_obj = PettyCashBalance.objects.filter(
                branch=branch,
                channel=channel,
                month=current_month
            ).first()
            if balance_obj:
                opening_balances[branch.id][channel] = balance_obj.opening_balance
            else:
                opening_balances[branch.id][channel] = Decimal('0.00')

    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate running balance for transactions in current page
    if page_obj:

        # Get the last transaction on this page
        last_txn_date = page_obj[-1].created_at if page_obj else None

        if last_txn_date:
            # Get all transactions up to the last one on this page, ordered chronologically
            all_txns = PettyCashTransaction.objects.filter(
                branch__in=all_branches,
                created_at__lte=page_obj[0].created_at,
                status='Disbursed'
            ).order_by('created_at')

            # Calculate running balance
            running_balance = {}
            for branch in all_branches:
                try:
                    balance = PettyCashBalance.objects.get(branch=branch, month=current_month, channel='Cash')
                    running_balance[branch.id] = balance.opening_balance
                except PettyCashBalance.DoesNotExist:
                    running_balance[branch.id] = Decimal('0.00')

            # Build dictionary mapping transaction IDs to running balances
            transaction_balances = {}
            for txn in all_txns:
                if txn.transaction_type == 'Disbursement':
                    running_balance[txn.branch.id] -= txn.amount
                elif txn.transaction_type == 'Refill':
                    running_balance[txn.branch.id] += txn.amount
                transaction_balances[txn.id] = running_balance[txn.branch.id]

            # Attach running balance to each transaction on the page
            for txn in page_obj:
                if txn.id in transaction_balances:
                    txn.running_balance = transaction_balances[txn.id]
                else:
                    txn.running_balance = Decimal('0.00')

    # Get branches for filter (only active)
    if user.is_superuser:
        branches = Branch.objects.filter(is_active=True)
    else:
        branches = Branch.objects.filter(id=worker.branch.id, is_active=True)

    # Get categories for filter
    categories = PettyCashCategory.objects.filter(is_active=True).order_by('name')

    view_context = {
        'transactions': page_obj,
        'branches': branches,
        'opening_balances': opening_balances,
        'current_month': current_month,
        'status_filter': status_filter,
        'channel_filter': channel_filter,
        'category_filter': category_filter,
        'branch_filter': branch_filter,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
        'categories': categories,
        'CHANNEL_CHOICES': PettyCashTransaction.CHANNEL_CHOICES,
        'STATUS_CHOICES': PettyCashTransaction.STATUS_CHOICES,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/transaction_list.html', context)


@login_required
def create_transaction(request):
    """Create a new petty cash transaction"""
    user = request.user
    worker = user.worker_profile

    if request.method == 'POST':
        form = PettyCashTransactionForm(request.POST)
        if form.is_valid():
            transaction_obj = form.save(commit=False)
            transaction_obj.requested_by = worker
            transaction_obj.status = 'Pending'

            # Get override reason from POST data (submitted via modal)
            override_reason = request.POST.get('override_reason', '').strip()
            if override_reason:
                transaction_obj.override_reason = override_reason

            # Check if amount exceeds daily limit
            try:
                branch_settings = PettyCashSettings.objects.get(branch=transaction_obj.branch)

                # Get today's total for this channel
                today = timezone.now().date()
                today_start = datetime.combine(today, datetime.min.time())
                today_end = datetime.combine(today, datetime.max.time())

                today_total = PettyCashTransaction.objects.filter(
                    branch=transaction_obj.branch,
                    channel=transaction_obj.channel,
                    created_at__gte=today_start,
                    created_at__lte=today_end,
                    status__in=['Approved', 'Disbursed']
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

                # Check against limit
                limit = Decimal('0.00')
                if transaction_obj.channel == 'Cash':
                    limit = branch_settings.daily_cash_limit
                elif transaction_obj.channel == 'MTN MoMo':
                    limit = branch_settings.daily_momo_limit
                elif transaction_obj.channel == 'Orange Money':
                    limit = branch_settings.daily_orange_limit

                if (today_total + transaction_obj.amount) > limit:
                    transaction_obj.requires_override = True

            except PettyCashSettings.DoesNotExist:
                pass

            transaction_obj.save()

            # Log audit trail
            recipient_display = transaction_obj.recipient.user.get_full_name() if transaction_obj.recipient else transaction_obj.recipient_name
            log_audit(
                user=worker,
                action='Create Transaction',
                details=f"Created transaction {transaction_obj.transaction_id} for {transaction_obj.amount} CFA to {recipient_display}",
                branch=transaction_obj.branch,
                transaction=transaction_obj,
                request=request
            )

            messages.success(request, _("Transaction created successfully. Awaiting approval."))
            return redirect('transaction_details', transaction_id=transaction_obj.id)
        else:
            # Form is not valid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

            # Re-render form with errors
            employees = Worker.objects.filter(is_active=True).select_related('user')
            settings = None
            try:
                if user.is_superuser:
                    settings = PettyCashSettings.objects.first()
                else:
                    settings = PettyCashSettings.objects.get(branch=worker.branch)
            except PettyCashSettings.DoesNotExist:
                pass

            view_context = {
                'form': form,
                'employees': employees,
                'settings': settings,
            }
            context = TemplateLayout.init(request, view_context)
            return render(request, 'petty_cash/create_transaction.html', context)
    else:
        # Pre-fill branch if not superuser
        initial = {}
        if not user.is_superuser:
            initial['branch'] = worker.branch

        form = PettyCashTransactionForm(initial=initial)

    # Get all active employees with phone numbers for auto-populate
    employees = Worker.objects.filter(is_active=True).select_related('user')

    # Get settings for daily limits (for the user's branch or first branch)
    settings = None
    try:
        if user.is_superuser:
            settings = PettyCashSettings.objects.first()
        else:
            settings = PettyCashSettings.objects.get(branch=worker.branch)
    except PettyCashSettings.DoesNotExist:
        pass

    view_context = {
        'form': form,
        'employees': employees,
        'settings': settings,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/create_transaction.html', context)


@login_required
def transaction_details(request, transaction_id):
    """View details of a specific transaction"""
    user = request.user
    worker = user.worker_profile

    transaction_obj = get_object_or_404(PettyCashTransaction, id=transaction_id)

    # Check permissions
    if not user.is_superuser and transaction_obj.branch != worker.branch:
        messages.error(request, _("You don't have permission to view this transaction."))
        return redirect('transaction_list')

    # Get receipts
    receipts = transaction_obj.receipts.all()

    # Get audit logs
    audit_logs = transaction_obj.audit_logs.all()[:10]

    # Check if receipt is required
    receipt_required = False
    try:
        settings = PettyCashSettings.objects.get(branch=transaction_obj.branch)
        if transaction_obj.amount > settings.receipt_required_threshold:
            receipt_required = True
    except PettyCashSettings.DoesNotExist:
        pass

    view_context = {
        'transaction': transaction_obj,
        'receipts': receipts,
        'audit_logs': audit_logs,
        'receipt_required': receipt_required,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/transaction_details.html', context)


@login_required
def approve_transaction(request, transaction_id):
    """Approve or reject a transaction"""
    user = request.user
    worker = user.worker_profile

    transaction_obj = get_object_or_404(PettyCashTransaction, id=transaction_id)

    # Check permissions (Finance Officers and superusers can approve)
    if not user.is_superuser and transaction_obj.branch != worker.branch:
        messages.error(request, _("You don't have permission to approve this transaction."))
        return redirect('transaction_details', transaction_id=transaction_id)

    if transaction_obj.status != 'Pending':
        messages.error(request, _("This transaction has already been processed."))
        return redirect('transaction_details', transaction_id=transaction_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            # Check if override approval is needed
            if transaction_obj.requires_override:
                override_approval = request.POST.get('override_approval', False)
                if not override_approval or override_approval != 'true':
                    messages.warning(request, _("This transaction requires override approval."))
                    return redirect('transaction_details', transaction_id=transaction_id)

            transaction_obj.status = 'Approved'
            transaction_obj.approved_by = worker
            transaction_obj.approved_at = timezone.now()

            if transaction_obj.requires_override:
                transaction_obj.override_approved = True

            transaction_obj.save()

            # Log audit trail
            log_audit(
                user=worker,
                action='Approve Transaction',
                details=f"Approved transaction {transaction_obj.transaction_id}",
                branch=transaction_obj.branch,
                transaction=transaction_obj,
                request=request
            )

            messages.success(request, _("Transaction approved successfully."))

        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            if not rejection_reason:
                messages.error(request, _("Please provide a rejection reason."))
                return redirect('transaction_details', transaction_id=transaction_id)

            transaction_obj.status = 'Rejected'
            transaction_obj.approved_by = worker
            transaction_obj.approved_at = timezone.now()
            transaction_obj.rejection_reason = rejection_reason
            transaction_obj.save()

            # Log audit trail
            log_audit(
                user=worker,
                action='Reject Transaction',
                details=f"Rejected transaction {transaction_obj.transaction_id}: {rejection_reason}",
                branch=transaction_obj.branch,
                transaction=transaction_obj,
                request=request
            )

            messages.warning(request, _("Transaction rejected."))

        return redirect('transaction_details', transaction_id=transaction_id)
    else:
        form = PettyCashApprovalForm()

    view_context = {'form': form, 'transaction': transaction_obj}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/approve_transaction.html', context)


@login_required
def disburse_transaction(request, transaction_id):
    """Mark transaction as disbursed and update balances"""
    user = request.user
    worker = user.worker_profile

    transaction_obj = get_object_or_404(PettyCashTransaction, id=transaction_id)

    # Check permissions
    if not user.is_superuser and transaction_obj.branch != worker.branch:
        messages.error(request, _("You don't have permission to disburse this transaction."))
        return redirect('transaction_details', transaction_id=transaction_id)

    if transaction_obj.status != 'Approved':
        messages.error(request, _("Only approved transactions can be disbursed."))
        return redirect('transaction_details', transaction_id=transaction_id)

    if request.method == 'POST':
        # Check balance before disbursement
        today = timezone.now().date()
        current_month = today.replace(day=1)
        balance = get_or_create_balance(transaction_obj.branch, transaction_obj.channel, current_month)

        # Validate sufficient funds for disbursement
        if transaction_obj.transaction_type == 'Disbursement':
            if balance.current_balance < transaction_obj.amount:
                messages.error(
                    request,
                    _(f"Insufficient funds! Current balance for {transaction_obj.channel} is {balance.current_balance:,.2f} CFA, but transaction requires {transaction_obj.amount:,.2f} CFA.")
                )
                return redirect('transaction_details', transaction_id=transaction_id)

        with transaction.atomic():
            # Update transaction status
            transaction_obj.status = 'Disbursed'
            transaction_obj.disbursed_by = worker
            transaction_obj.disbursed_at = timezone.now()
            transaction_obj.save()

            # Update balance
            if transaction_obj.transaction_type == 'Disbursement':
                balance.current_balance -= transaction_obj.amount
                balance.total_outflow += transaction_obj.amount
            elif transaction_obj.transaction_type == 'Refill':
                balance.current_balance += transaction_obj.amount
                balance.total_inflow += transaction_obj.amount

            balance.save()

            # Log audit trail
            log_audit(
                user=worker,
                action='Disburse Transaction',
                details=f"Disbursed transaction {transaction_obj.transaction_id}. New balance: {balance.current_balance} CFA",
                branch=transaction_obj.branch,
                transaction=transaction_obj,
                request=request
            )

            messages.success(request, _("Transaction disbursed successfully. Balance updated."))
            return redirect('transaction_details', transaction_id=transaction_id)

    view_context = {'transaction': transaction_obj}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/disburse_transaction.html', context)


@login_required
def upload_receipt(request, transaction_id):
    """Upload receipt for a transaction"""
    user = request.user
    worker = user.worker_profile

    transaction_obj = get_object_or_404(PettyCashTransaction, id=transaction_id)

    if request.method == 'POST':
        form = PettyCashReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.transaction = transaction_obj
            receipt.uploaded_by = worker
            receipt.save()

            # Log audit trail
            log_audit(
                user=worker,
                action='Upload Receipt',
                details=f"Uploaded receipt for transaction {transaction_obj.transaction_id}",
                branch=transaction_obj.branch,
                transaction=transaction_obj,
                request=request
            )

            messages.success(request, _("Receipt uploaded successfully."))
            return redirect('transaction_details', transaction_id=transaction_id)
    else:
        form = PettyCashReceiptForm()

    view_context = {'form': form, 'transaction': transaction_obj}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/upload_receipt.html', context)


@login_required
def refill_request_list(request):
    """List all refill requests"""
    user = request.user
    worker = user.worker_profile

    # Filter by branch if not superuser
    if user.is_superuser:
        refill_requests = PettyCashRefillRequest.objects.all()
    else:
        refill_requests = PettyCashRefillRequest.objects.filter(branch=worker.branch)

    # Get filter parameters
    status_filter = request.GET.get('status', '')
    if status_filter:
        refill_requests = refill_requests.filter(status=status_filter)

    # Pagination
    paginator = Paginator(refill_requests, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    view_context = {
        'refill_requests': page_obj,
        'status_filter': status_filter,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/refill_request_list.html', context)


@login_required
def create_refill_request(request):
    """Create a new refill request"""
    user = request.user
    worker = user.worker_profile

    if request.method == 'POST':
        form = PettyCashRefillRequestForm(request.POST)
        if form.is_valid():
            refill_request = form.save(commit=False)
            refill_request.requested_by = worker

            # Validate branch transfer has sufficient funds
            if refill_request.source_type == 'Branch Transfer' and refill_request.source_branch:
                # Get current month balances for source branch
                today = timezone.now().date()
                current_month = today.replace(day=1)

                # Get total available balance across all channels
                source_balances = PettyCashBalance.objects.filter(
                    branch=refill_request.source_branch,
                    month=current_month
                ).aggregate(
                    total_balance=Sum('current_balance')
                )

                total_available = source_balances.get('total_balance') or 0

                if total_available < refill_request.requested_amount:
                    messages.error(
                        request,
                        _("Insufficient funds in source branch ({})! Available: {} CFA, Requested: {} CFA. Request cannot be processed.").format(
                            refill_request.source_branch.branch_name,
                            f"{total_available:,.2f}",
                            f"{refill_request.requested_amount:,.2f}"
                        )
                    )
                    view_context = {'form': form}
                    context = TemplateLayout.init(request, view_context)
                    return render(request, 'petty_cash/create_refill_request.html', context)

                # Warning if it will leave source branch with low balance
                remaining = total_available - refill_request.requested_amount
                if remaining < 50000:  # Threshold for warning
                    messages.warning(
                        request,
                        _("Warning: This transfer will leave source branch {} with only {} CFA remaining").format(
                            refill_request.source_branch.branch_name,
                            f"{remaining:,.2f}"
                        )
                    )

            refill_request.save()

            # Log audit trail
            source_info = f"from {refill_request.source_branch.branch_name}" if refill_request.source_type == 'Branch Transfer' else "from Central Finance"
            log_audit(
                user=worker,
                action='Create Refill Request',
                details=f"Created refill request {refill_request.refill_id} for {refill_request.requested_amount} CFA {source_info}",
                branch=refill_request.branch,
                refill_request=refill_request,
                request=request
            )

            messages.success(request, _("Refill request created successfully."))
            return redirect('refill_request_list')
    else:
        initial = {}
        if not user.is_superuser:
            initial['branch'] = worker.branch

        form = PettyCashRefillRequestForm(initial=initial)

    view_context = {'form': form}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/create_refill_request.html', context)


@login_required
def approve_refill_request(request, refill_id):
    """Approve/reject/complete refill request"""
    user = request.user
    worker = user.worker_profile

    refill_request = get_object_or_404(PettyCashRefillRequest, id=refill_id)

    if request.method == 'POST':
        form = PettyCashRefillApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']

            if action == 'approve' and refill_request.status == 'Pending':
                refill_request.status = 'Approved'
                refill_request.approved_by = worker
                refill_request.approved_at = timezone.now()
                refill_request.save()

                log_audit(
                    user=worker,
                    action='Approve Refill',
                    details=f"Approved refill request {refill_request.refill_id}",
                    branch=refill_request.branch,
                    refill_request=refill_request,
                    request=request
                )

                messages.success(request, _("Refill request approved. Remember to mark it as 'Completed' to update the balance."))

            elif action == 'reject':
                rejection_reason = form.cleaned_data.get('rejection_reason')
                if not rejection_reason:
                    messages.error(request, _("Please provide a rejection reason."))
                    view_context = {'form': form, 'refill_request': refill_request}
                    context = TemplateLayout.init(request, view_context)
                    return render(request, 'petty_cash/approve_refill_request.html', context)

                refill_request.status = 'Rejected'
                refill_request.approved_by = worker
                refill_request.approved_at = timezone.now()
                refill_request.rejection_reason = rejection_reason
                refill_request.save()

                log_audit(
                    user=worker,
                    action='Approve Refill',
                    details=f"Rejected refill request {refill_request.refill_id}: {rejection_reason}",
                    branch=refill_request.branch,
                    refill_request=refill_request,
                    request=request
                )

                messages.warning(request, _("Refill request rejected."))

            elif action == 'complete' and refill_request.status in ['Pending', 'Approved']:
                # Get completion amounts from form
                completion_form = PettyCashRefillCompletionForm(request.POST)
                if not completion_form.is_valid():
                    messages.error(request, _("Please provide valid amounts for channel distribution."))
                    view_context = {'form': form, 'refill_request': refill_request, 'completion_form': completion_form}
                    context = TemplateLayout.init(request, view_context)
                    return render(request, 'petty_cash/approve_refill_request.html', context)

                cash_amount = completion_form.cleaned_data.get('cash_amount', 0) or 0
                momo_amount = completion_form.cleaned_data.get('momo_amount', 0) or 0
                orange_amount = completion_form.cleaned_data.get('orange_amount', 0) or 0

                # Validate source branch has sufficient funds for branch transfer
                if refill_request.source_type == 'Branch Transfer' and refill_request.source_branch:
                    today = timezone.now().date()
                    current_month = today.replace(day=1)

                    # Check each channel has sufficient funds
                    validation_errors = []

                    if cash_amount > 0:
                        source_cash = get_or_create_balance(refill_request.source_branch, 'Cash', current_month)
                        if source_cash.current_balance < cash_amount:
                            validation_errors.append(
                                f"Cash: Available {source_cash.current_balance:,.2f} CFA, Required {cash_amount:,.2f} CFA"
                            )

                    if momo_amount > 0:
                        source_momo = get_or_create_balance(refill_request.source_branch, 'MTN MoMo', current_month)
                        if source_momo.current_balance < momo_amount:
                            validation_errors.append(
                                f"MTN MoMo: Available {source_momo.current_balance:,.2f} CFA, Required {momo_amount:,.2f} CFA"
                            )

                    if orange_amount > 0:
                        source_orange = get_or_create_balance(refill_request.source_branch, 'Orange Money', current_month)
                        if source_orange.current_balance < orange_amount:
                            validation_errors.append(
                                f"Orange Money: Available {source_orange.current_balance:,.2f} CFA, Required {orange_amount:,.2f} CFA"
                            )

                    if validation_errors:
                        messages.error(
                            request,
                            _("Insufficient funds in source branch ({})! {}").format(
                                refill_request.source_branch.branch_name,
                                " | ".join(validation_errors)
                            )
                        )
                        view_context = {'form': form, 'refill_request': refill_request, 'completion_form': completion_form}
                        context = TemplateLayout.init(request, view_context)
                        return render(request, 'petty_cash/approve_refill_request.html', context)

                with transaction.atomic():
                    # If completing from Pending, auto-approve first
                    if refill_request.status == 'Pending':
                        refill_request.approved_by = worker
                        refill_request.approved_at = timezone.now()

                    # Store the channel distribution
                    refill_request.cash_amount = cash_amount
                    refill_request.momo_amount = momo_amount
                    refill_request.orange_amount = orange_amount
                    refill_request.status = 'Completed'
                    refill_request.completed_by = worker
                    refill_request.completed_at = timezone.now()
                    refill_request.save()

                    # Update balance for each channel
                    today = timezone.now().date()
                    current_month = today.replace(day=1)

                    balance_updates = []
                    if cash_amount > 0:
                        cash_balance = get_or_create_balance(refill_request.branch, 'Cash', current_month)
                        cash_balance.current_balance += cash_amount
                        cash_balance.total_inflow += cash_amount
                        cash_balance.save()
                        balance_updates.append(f"Cash: {cash_amount:,.2f}")

                    if momo_amount > 0:
                        momo_balance = get_or_create_balance(refill_request.branch, 'MTN MoMo', current_month)
                        momo_balance.current_balance += momo_amount
                        momo_balance.total_inflow += momo_amount
                        momo_balance.save()
                        balance_updates.append(f"MTN MoMo: {momo_amount:,.2f}")

                    if orange_amount > 0:
                        orange_balance = get_or_create_balance(refill_request.branch, 'Orange Money', current_month)
                        orange_balance.current_balance += orange_amount
                        orange_balance.total_inflow += orange_amount
                        orange_balance.save()
                        balance_updates.append(f"Orange Money: {orange_amount:,.2f}")

                    # If branch transfer, deduct from source branch
                    if refill_request.source_type == 'Branch Transfer' and refill_request.source_branch:
                        # Deduct from source branch channels (proportionally or from specific channels)
                        # Strategy: Deduct proportionally from channels that have funds
                        source_deductions = []
                        total_to_deduct = cash_amount + momo_amount + orange_amount

                        if cash_amount > 0:
                            source_cash = get_or_create_balance(refill_request.source_branch, 'Cash', current_month)
                            source_cash.current_balance -= cash_amount
                            source_cash.total_outflow += cash_amount
                            source_cash.save()
                            source_deductions.append(f"Cash: {cash_amount:,.2f}")

                        if momo_amount > 0:
                            source_momo = get_or_create_balance(refill_request.source_branch, 'MTN MoMo', current_month)
                            source_momo.current_balance -= momo_amount
                            source_momo.total_outflow += momo_amount
                            source_momo.save()
                            source_deductions.append(f"MTN MoMo: {momo_amount:,.2f}")

                        if orange_amount > 0:
                            source_orange = get_or_create_balance(refill_request.source_branch, 'Orange Money', current_month)
                            source_orange.current_balance -= orange_amount
                            source_orange.total_outflow += orange_amount
                            source_orange.save()
                            source_deductions.append(f"Orange Money: {orange_amount:,.2f}")

                        log_audit(
                            user=worker,
                            action='Branch Transfer Deduction',
                            details=f"Deducted from {refill_request.source_branch.branch_name}: {', '.join(source_deductions)} CFA for refill {refill_request.refill_id}",
                            branch=refill_request.source_branch,
                            refill_request=refill_request,
                            request=request
                        )

                    log_audit(
                        user=worker,
                        action='Complete Refill',
                        details=f"Completed refill request {refill_request.refill_id}. Distributed: {', '.join(balance_updates)} CFA",
                        branch=refill_request.branch,
                        refill_request=refill_request,
                        request=request
                    )

                    messages.success(request, _("Refill completed successfully! Balances updated: {}").format(', '.join(balance_updates)))

            return redirect('refill_request_list')
    else:
        form = PettyCashRefillApprovalForm()
        completion_form = PettyCashRefillCompletionForm()

    view_context = {
        'form': form,
        'refill_request': refill_request,
        'completion_form': completion_form,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/approve_refill_request.html', context)


@login_required
def edit_refill_request(request, refill_id):
    """Edit a pending refill request"""
    refill = get_object_or_404(PettyCashRefillRequest, id=refill_id)
    user = request.user
    worker = user.worker_profile

    # Only allow editing if request is still pending
    if refill.status != 'Pending':
        messages.error(request, _("Cannot edit a refill request that has already been processed."))
        return redirect('refill_request_list')

    # Only the requestor or superuser can edit
    if not user.is_superuser and refill.requested_by != worker:
        messages.error(request, _("You don't have permission to edit this refill request."))
        return redirect('refill_request_list')

    if request.method == 'POST':
        form = PettyCashRefillRequestForm(request.POST, instance=refill)
        if form.is_valid():
            refill_request = form.save(commit=False)

            # Validate branch transfer has sufficient funds
            if refill_request.source_type == 'Branch Transfer' and refill_request.source_branch:
                # Get current month balances for source branch
                today = timezone.now().date()
                current_month = today.replace(day=1)

                # Get total available balance across all channels
                source_balances = PettyCashBalance.objects.filter(
                    branch=refill_request.source_branch,
                    month=current_month
                ).aggregate(
                    total_balance=Sum('current_balance')
                )

                total_available = source_balances.get('total_balance') or 0

                if total_available < refill_request.requested_amount:
                    messages.warning(
                        request,
                        _("Insufficient funds in source branch. Available: {} CFA, Requested: {} CFA").format(
                            f"{total_available:,.2f}",
                            f"{refill_request.requested_amount:,.2f}"
                        )
                    )
                    view_context = {
                        'form': form,
                        'refill': refill_request,
                        'is_editing': True,
                    }
                    context = TemplateLayout.init(request, view_context)
                    return render(request, 'petty_cash/create_refill_request.html', context)

                # Warning if it will leave source branch with low balance
                remaining = total_available - refill_request.requested_amount
                if remaining < 50000:  # Threshold for warning
                    messages.warning(
                        request,
                        _("Warning: This transfer will leave source branch {} with only {} CFA remaining").format(
                            refill_request.source_branch.branch_name,
                            f"{remaining:,.2f}"
                        )
                    )

            refill_request.save()

            # Log the action
            log_audit(
                user=worker,
                action='Edit Refill Request',
                details=f"Edited refill request {refill_request.refill_id} for {refill_request.branch.branch_name}",
                branch=refill_request.branch,
                refill_request=refill_request,
                request=request
            )

            messages.success(request, _("Refill request updated successfully."))
            return redirect('refill_request_list')
    else:
        form = PettyCashRefillRequestForm(instance=refill)

    view_context = {
        'form': form,
        'refill': refill,
        'is_editing': True,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/create_refill_request.html', context)


@login_required
def delete_refill_request(request, refill_id):
    """Delete a pending refill request"""
    refill = get_object_or_404(PettyCashRefillRequest, id=refill_id)
    user = request.user
    worker = user.worker_profile

    # Only allow deleting if request is still pending
    if refill.status != 'Pending':
        messages.error(request, _("Cannot delete a refill request that has already been processed."))
        return redirect('refill_request_list')

    # Only the requestor or superuser can delete
    if not user.is_superuser and refill.requested_by != worker:
        messages.error(request, _("You don't have permission to delete this refill request."))
        return redirect('refill_request_list')

    if request.method == 'POST':
        source_info = f"from {refill.source_branch.branch_name}" if refill.source_type == 'Branch Transfer' and refill.source_branch else "from Central Finance"
        refill_info = f"{refill.refill_id} - {refill.branch.branch_name} ({source_info})"

        # Log the action before deletion
        log_audit(
            user=worker,
            action='Delete Refill Request',
            details=f"Deleted refill request {refill_info}",
            branch=refill.branch,
            request=request
        )

        refill.delete()
        messages.success(request, _("Refill request deleted successfully."))
        return redirect('refill_request_list')

    view_context = {
        'refill': refill,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/delete_refill_request.html', context)


@login_required
def refill_request_logs(request):
    """View audit logs for refill requests"""
    user = request.user
    worker = user.worker_profile

    # Filter logs related to refill requests
    logs = PettyCashAuditLog.objects.filter(
        action__in=['Create Refill Request', 'Edit Refill Request', 'Delete Refill Request', 'Approve Refill', 'Reject Refill', 'Complete Refill']
    ).select_related('user', 'user__user', 'branch', 'refill_request').order_by('-timestamp')

    # Non-superusers only see logs from their branch
    if not user.is_superuser:
        logs = logs.filter(branch=worker.branch)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    paginated_logs = paginator.get_page(page_number)
    offset = (paginated_logs.number - 1) * paginator.per_page

    view_context = {
        'logs': paginated_logs,
        'offset': offset,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/refill_request_logs.html', context)


@login_required
def petty_cash_settings(request, branch_id=None):
    """View and update petty cash settings"""
    user = request.user
    worker = user.worker_profile

    # Only superusers can update settings
    if not user.is_superuser:
        messages.error(request, _("You don't have permission to update settings."))
        return redirect('petty_cash_dashboard')

    if branch_id:
        branch = get_object_or_404(Branch, id=branch_id)
    else:
        branch = Branch.objects.first()

    # Get or create settings for branch
    settings, created = PettyCashSettings.objects.get_or_create(branch=branch)

    if request.method == 'POST':
        form = PettyCashSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            settings = form.save(commit=False)
            settings.updated_by = worker
            settings.save()

            # Log audit trail
            log_audit(
                user=worker,
                action='Update Settings',
                details=f"Updated petty cash settings for {branch.branch_name}",
                branch=branch,
                request=request
            )

            messages.success(request, _("Settings updated successfully."))
            return redirect('petty_cash_settings_branch', branch_id=branch.id)
    else:
        form = PettyCashSettingsForm(instance=settings)

    # Get all branches for navigation (only active)
    branches = Branch.objects.filter(is_active=True)

    # Get categories with usage count
    from django.db.models import Count
    categories = PettyCashCategory.objects.annotate(
        usage_count=Count('transactions')
    ).order_by('name')

    view_context = {
        'form': form,
        'branch': branch,
        'branches': branches,
        'categories': categories,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/settings.html', context)


@login_required
def reports(request):
    """Generate reports with filters"""
    user = request.user
    worker = user.worker_profile

    # Initialize filter form
    form = PettyCashReportFilterForm(request.GET or None)

    # Base queryset
    if user.is_superuser:
        transactions = PettyCashTransaction.objects.filter(status='Disbursed')
    else:
        transactions = PettyCashTransaction.objects.filter(branch=worker.branch, status='Disbursed')

    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            transactions = transactions.filter(disbursed_at__gte=form.cleaned_data['start_date'])

        if form.cleaned_data.get('end_date'):
            end_date = datetime.combine(form.cleaned_data['end_date'], datetime.max.time())
            transactions = transactions.filter(disbursed_at__lte=end_date)

        if form.cleaned_data.get('branch'):
            transactions = transactions.filter(branch=form.cleaned_data['branch'])

        if form.cleaned_data.get('channel'):
            transactions = transactions.filter(channel=form.cleaned_data['channel'])

        if form.cleaned_data.get('category'):
            transactions = transactions.filter(category=form.cleaned_data['category'])

    # Generate statistics
    total_amount = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    transaction_count = transactions.count()

    # Top categories - get category name properly
    top_categories = transactions.values('category__name', 'category__id').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')[:5]

    # Top recipients - handle both employee and external recipients
    top_recipients_data = []
    for transaction in transactions.select_related('recipient'):
        recipient_display = transaction.recipient.user.get_full_name() if transaction.recipient else (transaction.recipient_name or 'Unknown')
        top_recipients_data.append({
            'recipient': recipient_display,
            'amount': transaction.amount
        })

    # Aggregate recipients
    from collections import defaultdict
    recipient_aggregates = defaultdict(lambda: {'total': Decimal('0.00'), 'count': 0})
    for item in top_recipients_data:
        recipient_aggregates[item['recipient']]['total'] += item['amount']
        recipient_aggregates[item['recipient']]['count'] += 1

    top_recipients = [
        {'recipient': name, 'total': data['total'], 'count': data['count']}
        for name, data in sorted(recipient_aggregates.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
    ]

    # By channel
    by_channel = transactions.values('channel').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    view_context = {
        'form': form,
        'transactions': transactions[:100],  # Limit for display
        'total_amount': total_amount,
        'transaction_count': transaction_count,
        'top_categories': top_categories,
        'top_recipients': top_recipients,
        'by_channel': by_channel,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/reports.html', context)


@login_required
def audit_logs(request):
    """View audit logs"""
    user = request.user
    worker = user.worker_profile

    # Filter by branch if not superuser
    if user.is_superuser:
        logs = PettyCashAuditLog.objects.all()
    else:
        logs = PettyCashAuditLog.objects.filter(branch=worker.branch)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    view_context = {'logs': page_obj}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/audit_logs.html', context)


@login_required
def add_petty_cash_category(request):
    """Add a new category"""
    if not request.user.is_superuser:
        messages.error(request, _("You don't have permission to add categories."))
        return redirect('petty_cash_settings')

    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        if category_name:
            # Check if category already exists
            if PettyCashCategory.objects.filter(name__iexact=category_name).exists():
                messages.warning(request, _(f"Category '{category_name}' already exists."))
            else:
                # Create new category
                PettyCashCategory.objects.create(
                    name=category_name,
                    created_by=request.user.worker_profile
                )
                messages.success(request, _(f"Category '{category_name}' added successfully."))

                # Log audit trail
                log_audit(
                    user=request.user.worker_profile,
                    action='Add Category',
                    details=f"Added new category: {category_name}",
                    request=request
                )
        else:
            messages.error(request, _("Category name cannot be empty."))

    return redirect('petty_cash_settings')


@login_required
def edit_petty_cash_category(request):
    """Edit an existing category"""
    if not request.user.is_superuser:
        messages.error(request, _("You don't have permission to edit categories."))
        return redirect('petty_cash_settings')

    if request.method == 'POST':
        category_id = request.POST.get('category_id', '').strip()
        new_category_name = request.POST.get('new_category', '').strip()

        if category_id and new_category_name:
            try:
                category = PettyCashCategory.objects.get(id=category_id)
                old_name = category.name

                # Check if new name already exists
                if PettyCashCategory.objects.filter(name__iexact=new_category_name).exclude(id=category_id).exists():
                    messages.warning(request, _(f"Category '{new_category_name}' already exists."))
                else:
                    category.name = new_category_name
                    category.save()

                    messages.success(request, _(f"Category renamed from '{old_name}' to '{new_category_name}'."))

                    # Log audit trail
                    log_audit(
                        user=request.user.worker_profile,
                        action='Edit Category',
                        details=f"Renamed category from '{old_name}' to '{new_category_name}'.",
                        request=request
                    )
            except PettyCashCategory.DoesNotExist:
                messages.error(request, _("Category not found."))
        else:
            messages.error(request, _("Category name is required."))

    return redirect('petty_cash_settings')


@login_required
def delete_petty_cash_category(request):
    """Delete a category (mark as inactive)"""
    if not request.user.is_superuser:
        messages.error(request, _("You don't have permission to delete categories."))
        return redirect('petty_cash_settings')

    if request.method == 'POST':
        category_id = request.POST.get('category_id', '').strip()

        if category_id:
            try:
                category = PettyCashCategory.objects.get(id=category_id)
                category_name = category.name
                usage_count = category.transactions.count()

                # Mark as inactive instead of deleting
                category.is_active = False
                category.save()

                messages.success(request, _(f"Category '{category_name}' has been deactivated. {usage_count} existing transactions will keep this category."))

                # Log audit trail
                log_audit(
                    user=request.user.worker_profile,
                    action='Delete Category',
                    details=f"Deactivated category: {category_name}. {usage_count} transactions still use this category.",
                    request=request
                )
            except PettyCashCategory.DoesNotExist:
                messages.error(request, _("Category not found."))
        else:
            messages.error(request, _("Category is required."))

    return redirect('petty_cash_settings')


@login_required
def download_petty_cash_receipt(request, transaction_id):
    """Generate and download a petty cash receipt for a transaction"""
    transaction_obj = get_object_or_404(PettyCashTransaction, id=transaction_id)

    # Check permissions
    user = request.user
    worker = user.worker_profile
    if not user.is_superuser and transaction_obj.branch != worker.branch:
        messages.error(request, _("You don't have permission to download this receipt."))
        return redirect('transaction_details', transaction_id=transaction_id)

    # Only allow downloading receipts for disbursed transactions
    if transaction_obj.status != 'Disbursed':
        messages.error(request, _("Receipts can only be generated for disbursed transactions."))
        return redirect('transaction_details', transaction_id=transaction_id)

    view_context = {
        'transaction': transaction_obj,
        'company_name': 'GC Pharma',  # You can make this dynamic
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'petty_cash/receipt_document.html', context)
