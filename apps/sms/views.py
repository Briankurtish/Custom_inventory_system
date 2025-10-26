from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta

from web_project import TemplateLayout
from .models import SMSTemplate, SMSMessage, SMSGroup, SMSLog
from .forms import (
    SMSTemplateForm, SMSGroupForm, SendSMSForm,
    BulkSMSForm, SMSFilterForm
)
from .services import TwilioSMSService
from apps.customers.models import Customer

@login_required
def sms_dashboard(request):
    """Main SMS dashboard view"""
    context = TemplateLayout.init(request, {})

    # Get recent statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    context.update({
        'total_messages': SMSMessage.objects.count(),
        'messages_today': SMSMessage.objects.filter(created_at__date=today).count(),
        'messages_this_week': SMSMessage.objects.filter(created_at__date__gte=week_ago).count(),
        'successful_messages': SMSMessage.objects.filter(status='sent').count(),
        'failed_messages': SMSMessage.objects.filter(status='failed').count(),
        'recent_messages': SMSMessage.objects.order_by('-created_at')[:10],
        'templates_count': SMSTemplate.objects.filter(is_active=True).count(),
        'groups_count': SMSGroup.objects.count(),
    })

    return render(request, 'sms/dashboard.html', context)

@login_required
def sms_templates(request):
    """Manage SMS templates"""
    templates = SMSTemplate.objects.all().order_by('-created_at')

    if request.method == 'POST':
        form = SMSTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user.worker_profile
            template.save()

            # Create SMS log for template creation
            SMSLog.objects.create(
                action='template_create',
                details=f'Template "{template.name}" created successfully',
                user=request.user.worker_profile,
                is_error=False
            )

            messages.success(request, 'Template created successfully!')
            return redirect('sms:sms_templates')
    else:
        form = SMSTemplateForm()

    context = TemplateLayout.init(request, {
        'templates': templates,
        'form': form
    })

    return render(request, 'sms/templates.html', context)

@login_required
def edit_template(request, template_id):
    """Edit SMS template"""
    template = get_object_or_404(SMSTemplate, id=template_id)

    if request.method == 'POST':
        form = SMSTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()

            # Create SMS log for template update
            SMSLog.objects.create(
                action='template_update',
                details=f'Template "{template.name}" updated successfully',
                user=request.user.worker_profile,
                is_error=False
            )

            messages.success(request, 'Template updated successfully!')
            return redirect('sms:sms_templates')
    else:
        form = SMSTemplateForm(instance=template)

    context = TemplateLayout.init(request, {
        'template': template,
        'form': form
    })

    return render(request, 'sms/edit_template.html', context)

@login_required
def delete_template(request, template_id):
    """Delete SMS template"""
    template = get_object_or_404(SMSTemplate, id=template_id)

    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template deleted successfully!')
        return redirect('sms:sms_templates')

    context = TemplateLayout.init(request, {
        'template': template
    })

    return render(request, 'sms/delete_template.html', context)

@login_required
def sms_groups(request):
    """Manage SMS groups"""
    groups = SMSGroup.objects.all().order_by('-created_at')

    if request.method == 'POST':
        form = SMSGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user.worker_profile
            group.save()
            form.save_m2m()  # Save many-to-many relationships

            # Create SMS log for group creation
            SMSLog.objects.create(
                action='group_create',
                details=f'Group "{group.name}" created with {group.get_customer_count()} customers',
                user=request.user.worker_profile,
                is_error=False
            )

            messages.success(request, 'Group created successfully!')
            return redirect('sms:sms_groups')
    else:
        form = SMSGroupForm()

    context = TemplateLayout.init(request, {
        'groups': groups,
        'form': form
    })

    return render(request, 'sms/groups.html', context)

@login_required
def edit_group(request, group_id):
    """Edit SMS group"""
    group = get_object_or_404(SMSGroup, id=group_id)

    if request.method == 'POST':
        form = SMSGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group updated successfully!')
            return redirect('sms:sms_groups')
    else:
        form = SMSGroupForm(instance=group)

    context = TemplateLayout.init(request, {
        'group': group,
        'form': form
    })

    return render(request, 'sms/edit_group.html', context)

@login_required
def delete_group(request, group_id):
    """Delete SMS group"""
    group = get_object_or_404(SMSGroup, id=group_id)

    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group deleted successfully!')
        return redirect('sms:sms_groups')

    context = TemplateLayout.init(request, {
        'group': group
    })

    return render(request, 'sms/delete_group.html', context)

@login_required
def send_sms(request):
    """Send individual SMS message"""
    if request.method == 'POST':
        form = SendSMSForm(request.POST)
        if form.is_valid():
            try:
                # Initialize SMS service
                sms_service = TwilioSMSService()

                # Get form data
                recipient_type = form.cleaned_data['recipient_type']
                template = form.cleaned_data.get('template')
                message_type = form.cleaned_data['message_type']
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']

                # Prepare recipient data
                if recipient_type == 'customer':
                    customer = form.cleaned_data['customer']
                    recipient_name = customer.customer_name
                    recipient_phone = customer.telephone
                else:
                    customer = None
                    recipient_name = form.cleaned_data['recipient_name']
                    recipient_phone = form.cleaned_data['recipient_phone']

                # Send SMS
                response = sms_service.send_sms(recipient_phone, message)

                # Create SMS record
                sms_message = SMSMessage.objects.create(
                    recipient_name=recipient_name,
                    recipient_phone=recipient_phone,
                    subject=subject,
                    message=message,
                    template=template,
                    customer=customer,
                    message_type=message_type,
                    sent_by=request.user.worker_profile,
                    twilio_sid=response['sid'] if response['success'] else None,
                    twilio_status=response['status'],
                    status='sent' if response['success'] else 'failed',
                    sent_at=timezone.now() if response['success'] else None,
                    error_message=response['error'] if not response['success'] else None
                )

                if response['success']:
                    # Create SMS log for successful send
                    SMSLog.objects.create(
                        action='send',
                        details=f'SMS sent successfully to {recipient_name} ({recipient_phone})',
                        user=request.user.worker_profile,
                        is_error=False
                    )
                    messages.success(request, f'SMS sent successfully to {recipient_name}!')
                else:
                    # Create SMS log for failed send
                    SMSLog.objects.create(
                        action='send',
                        details=f'Failed to send SMS to {recipient_name} ({recipient_phone}): {response["error"]}',
                        user=request.user.worker_profile,
                        is_error=True
                    )
                    messages.error(request, f'Failed to send SMS: {response["error"]}')

                return redirect('sms:sms_messages')

            except Exception as e:
                # Create SMS log for error
                SMSLog.objects.create(
                    action='error',
                    details=f'Error sending SMS: {str(e)}',
                    user=request.user.worker_profile,
                    is_error=True
                )
                messages.error(request, f'Error sending SMS: {str(e)}')
    else:
        form = SendSMSForm()

    context = TemplateLayout.init(request, {
        'form': form
    })

    return render(request, 'sms/send_sms.html', context)

@login_required
def send_bulk_sms(request):
    """Send bulk SMS messages"""
    if request.method == 'POST':
        form = BulkSMSForm(request.POST)
        if form.is_valid():
            try:
                # Initialize SMS service
                sms_service = TwilioSMSService()

                # Get form data
                recipient_type = form.cleaned_data['recipient_type']
                template = form.cleaned_data.get('template')
                message_type = form.cleaned_data['message_type']
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']

                # Prepare recipients
                recipients = []

                if recipient_type == 'group':
                    group = form.cleaned_data['group']
                    for customer in group.customers.all():
                        recipients.append({
                            'name': customer.customer_name,
                            'phone': customer.telephone,
                            'customer': customer
                        })
                elif recipient_type == 'all_customers':
                    for customer in Customer.objects.all():
                        if customer.telephone:  # Only include customers with phone numbers
                            recipients.append({
                                'name': customer.customer_name,
                                'phone': customer.telephone,
                                'customer': customer
                            })
                elif recipient_type == 'customers':
                    for customer in form.cleaned_data['customers']:
                        recipients.append({
                            'name': customer.customer_name,
                            'phone': customer.telephone,
                            'customer': customer
                        })

                if not recipients:
                    messages.error(request, 'No recipients selected!')
                    return redirect('sms:send_bulk_sms')

                # Send bulk SMS
                results = sms_service.send_bulk_sms(
                    recipients=recipients,
                    message=message,
                    template=template,
                    user=request.user.worker_profile
                )

                messages.success(
                    request,
                    f'Bulk SMS completed! Sent: {results["sent"]}, Failed: {results["failed"]}'
                )

                return redirect('sms:sms_messages')

            except Exception as e:
                # Create SMS log for bulk SMS error
                SMSLog.objects.create(
                    action='error',
                    details=f'Error sending bulk SMS: {str(e)}',
                    user=request.user.worker_profile,
                    is_error=True
                )
                messages.error(request, f'Error sending bulk SMS: {str(e)}')
    else:
        form = BulkSMSForm()

    context = TemplateLayout.init(request, {
        'form': form
    })

    return render(request, 'sms/send_bulk_sms.html', context)

@login_required
def sms_messages(request):
    """View SMS messages with filtering"""
    # Get filter form
    filter_form = SMSFilterForm(request.GET)

    # Start with all messages
    messages_qs = SMSMessage.objects.all().order_by('-created_at')

    # Apply filters
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        message_type = filter_form.cleaned_data.get('message_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')

        if status:
            messages_qs = messages_qs.filter(status=status)

        if message_type:
            messages_qs = messages_qs.filter(message_type=message_type)

        if date_from:
            messages_qs = messages_qs.filter(created_at__date__gte=date_from)

        if date_to:
            messages_qs = messages_qs.filter(created_at__date__lte=date_to)

        if search:
            messages_qs = messages_qs.filter(
                Q(recipient_name__icontains=search) |
                Q(recipient_phone__icontains=search)
            )

    # Paginate results
    paginator = Paginator(messages_qs, 20)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)

    context = TemplateLayout.init(request, {
        'messages': messages_page,
        'filter_form': filter_form,
        'total_count': messages_qs.count()
    })

    return render(request, 'sms/messages.html', context)

@login_required
def message_detail(request, message_id):
    """View detailed information about an SMS message"""
    message = get_object_or_404(SMSMessage, id=message_id)

    context = TemplateLayout.init(request, {
        'message': message
    })

    return render(request, 'sms/message_detail.html', context)

@login_required
@require_http_methods(["POST"])
def resend_message(request, message_id):
    """Resend a failed SMS message"""
    message = get_object_or_404(SMSMessage, id=message_id)

    try:
        sms_service = TwilioSMSService()
        response = sms_service.send_sms(message.recipient_phone, message.message)

        if response['success']:
            message.twilio_sid = response['sid']
            message.twilio_status = response['status']
            message.status = 'sent'
            message.sent_at = timezone.now()
            message.error_message = None
            message.save()

            messages.success(request, 'Message resent successfully!')
        else:
            message.status = 'failed'
            message.error_message = response['error']
            message.save()

            messages.error(request, f'Failed to resend message: {response["error"]}')

    except Exception as e:
        messages.error(request, f'Error resending message: {str(e)}')

    return redirect('sms:message_detail', message_id=message_id)

@login_required
def sms_logs(request):
    """View SMS operation logs"""
    logs = SMSLog.objects.all().order_by('-timestamp')

    # Paginate results
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)

    context = TemplateLayout.init(request, {
        'logs': logs_page
    })

    return render(request, 'sms/logs.html', context)

@login_required
def get_template_content(request):
    """AJAX endpoint to get template content"""
    template_id = request.GET.get('template_id')

    try:
        template = SMSTemplate.objects.get(id=template_id)
        return JsonResponse({
            'success': True,
            'subject': template.subject,
            'message': template.message,
            'message_type': template.template_type
        })
    except SMSTemplate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Template not found'
        })

@login_required
def get_customer_phone(request):
    """AJAX endpoint to get customer phone number"""
    customer_id = request.GET.get('customer_id')

    try:
        customer = Customer.objects.get(id=customer_id)
        return JsonResponse({
            'success': True,
            'phone': customer.telephone,
            'name': customer.customer_name
        })
    except Customer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Customer not found'
        })

@login_required
def get_group_customers(request):
    """AJAX endpoint to get customers in a group"""
    group_id = request.GET.get('group_id')

    try:
        group = SMSGroup.objects.get(id=group_id)
        customers = []
        for customer in group.customers.all():
            if customer.telephone:
                customers.append({
                    'id': customer.id,
                    'name': customer.customer_name,
                    'phone': customer.telephone
                })

        return JsonResponse({
            'success': True,
            'customers': customers,
            'count': len(customers)
        })
    except SMSGroup.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Group not found'
        })
