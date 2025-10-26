from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from web_project import TemplateLayout
from .models import EmailTemplate, EmailMessage, EmailGroup, EmailLog
from .forms import EmailTemplateForm, EmailGroupForm, SendEmailForm, BulkEmailForm
from .services import EmailService
from apps.customers.models import Customer

@login_required
def email_dashboard(request):
    """Email dashboard with statistics and recent activity"""

    context = TemplateLayout.init(request, {})

    # Get statistics
    total_emails = EmailMessage.objects.count()
    emails_today = EmailMessage.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    emails_this_week = EmailMessage.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    successful_emails = EmailMessage.objects.filter(status='sent').count()

    # Get recent emails
    recent_emails = EmailMessage.objects.select_related('customer', 'template').order_by('-created_at')[:10]

    # Get template and group counts
    templates_count = EmailTemplate.objects.filter(is_active=True).count()
    groups_count = EmailGroup.objects.count()

    context.update({
        'total_emails': total_emails,
        'emails_today': emails_today,
        'emails_this_week': emails_this_week,
        'successful_emails': successful_emails,
        'recent_emails': recent_emails,
        'templates_count': templates_count,
        'groups_count': groups_count,
    })

    return render(request, 'emails/dashboard.html', context)

@login_required
def send_email(request):
    """Send individual email"""

    context = TemplateLayout.init(request, {})

    if request.method == 'POST':
        form = SendEmailForm(request.POST)
        if form.is_valid():
            email_service = EmailService()

            # Get form data
            recipient_email = form.cleaned_data['recipient_email']
            recipient_name = form.cleaned_data['recipient_name']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            template = form.cleaned_data['template']

            # Send email
            response = email_service.send_email(
                to_email=recipient_email,
                subject=subject,
                message=message
            )

            # Create email record
            EmailMessage.objects.create(
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                subject=subject,
                message=message,
                template=template,
                message_type=template.template_type if template else 'custom',
                sent_by=request.user,
                status='sent' if response['success'] else 'failed',
                sent_at=timezone.now() if response['success'] else None,
                error_message=response['error'] if not response['success'] else None
            )

            if response['success']:
                messages.success(request, 'Email sent successfully!')
            else:
                messages.error(request, f'Failed to send email: {response["error"]}')

            return redirect('emails:email_dashboard')
    else:
        form = SendEmailForm()

    context.update({'form': form})
    return render(request, 'emails/send_email.html', context)

@login_required
def send_bulk_email(request):
    """Send bulk email to multiple recipients"""

    context = TemplateLayout.init(request, {})

    if request.method == 'POST':
        form = BulkEmailForm(request.POST)
        if form.is_valid():
            email_service = EmailService()

            # Get form data
            email_type = form.cleaned_data['email_type']
            group = form.cleaned_data['group']
            customers = form.cleaned_data['customers']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            template = form.cleaned_data['template']

            # Prepare recipients based on email type
            recipients = []

            if email_type == 'all_customers':
                customers = Customer.objects.all()
            elif email_type == 'selected_group':
                customers = group.customers.all()
            elif email_type == 'selected_customers':
                customers = customers

            for customer in customers:
                if customer.email:  # Only include customers with email addresses
                    recipients.append({
                        'email': customer.email,
                        'name': customer.customer_name,
                        'customer': customer
                    })

            if recipients:
                # Send bulk email
                results = email_service.send_bulk_email(
                    recipients=recipients,
                    subject=subject,
                    message=message,
                    template=template,
                    user=request.user
                )

                if results['sent'] > 0:
                    messages.success(request, f'Bulk email sent successfully to {results["sent"]} recipients!')
                if results['failed'] > 0:
                    messages.warning(request, f'Failed to send to {results["failed"]} recipients.')
            else:
                messages.error(request, 'No valid email addresses found for the selected recipients.')

            return redirect('emails:email_dashboard')
    else:
        form = BulkEmailForm()

    context.update({'form': form})
    return render(request, 'emails/send_bulk_email.html', context)

@login_required
def email_templates(request):
    """List all email templates"""

    context = TemplateLayout.init(request, {})

    templates = EmailTemplate.objects.all().order_by('-created_at')

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(templates, 10)
    page_number = request.GET.get('page')
    templates = paginator.get_page(page_number)

    context.update({'templates': templates})
    return render(request, 'emails/templates.html', context)

@login_required
def create_template(request):
    """Create new email template"""

    context = TemplateLayout.init(request, {})

    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()

            # Log the action
            EmailLog.objects.create(
                action='template_create',
                details=f'Template "{template.name}" created',
                user=request.user
            )

            messages.success(request, 'Email template created successfully!')
            return redirect('emails:email_templates')
    else:
        form = EmailTemplateForm()

    context.update({'form': form})
    return render(request, 'emails/create_template.html', context)

@login_required
def edit_template(request, template_id):
    """Edit email template"""

    context = TemplateLayout.init(request, {})

    template = get_object_or_404(EmailTemplate, id=template_id)

    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()

            # Log the action
            EmailLog.objects.create(
                action='template_update',
                details=f'Template "{template.name}" updated',
                user=request.user
            )

            messages.success(request, 'Email template updated successfully!')
            return redirect('emails:email_templates')
    else:
        form = EmailTemplateForm(instance=template)

    context.update({'form': form, 'template': template})
    return render(request, 'emails/edit_template.html', context)

@login_required
def delete_template(request, template_id):
    """Delete email template"""

    context = TemplateLayout.init(request, {})

    template = get_object_or_404(EmailTemplate, id=template_id)

    if request.method == 'POST':
        template_name = template.name
        template.delete()

        # Log the action
        EmailLog.objects.create(
            action='template_delete',
            details=f'Template "{template_name}" deleted',
            user=request.user
        )

        messages.success(request, 'Email template deleted successfully!')
        return redirect('emails:email_templates')

    context.update({'template': template})
    return render(request, 'emails/delete_template.html', context)

@login_required
def email_groups(request):
    """List all email groups"""

    context = TemplateLayout.init(request, {})

    groups = EmailGroup.objects.annotate(
        customer_count=Count('customers')
    ).order_by('-created_at')

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(groups, 10)
    page_number = request.GET.get('page')
    groups = paginator.get_page(page_number)

    context.update({'groups': groups})
    return render(request, 'emails/groups.html', context)

@login_required
def create_group(request):
    """Create new email group"""

    context = TemplateLayout.init(request, {})

    if request.method == 'POST':
        form = EmailGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            form.save_m2m()  # Save many-to-many relationships

            # Log the action
            EmailLog.objects.create(
                action='group_create',
                details=f'Group "{group.name}" created',
                user=request.user
            )

            messages.success(request, 'Email group created successfully!')
            return redirect('emails:email_groups')
    else:
        form = EmailGroupForm()

    context.update({'form': form})
    return render(request, 'emails/create_group.html', context)

@login_required
def edit_group(request, group_id):
    """Edit email group"""

    context = TemplateLayout.init(request, {})

    group = get_object_or_404(EmailGroup, id=group_id)

    if request.method == 'POST':
        form = EmailGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()

            # Log the action
            EmailLog.objects.create(
                action='group_update',
                details=f'Group "{group.name}" updated',
                user=request.user
            )

            messages.success(request, 'Email group updated successfully!')
            return redirect('emails:email_groups')
    else:
        form = EmailGroupForm(instance=group)

    context.update({'form': form, 'group': group})
    return render(request, 'emails/edit_group.html', context)

@login_required
def delete_group(request, group_id):
    """Delete email group"""

    context = TemplateLayout.init(request, {})

    group = get_object_or_404(EmailGroup, id=group_id)

    if request.method == 'POST':
        group_name = group.name
        group.delete()

        # Log the action
        EmailLog.objects.create(
            action='group_delete',
            details=f'Group "{group_name}" deleted',
            user=request.user
        )

        messages.success(request, 'Email group deleted successfully!')
        return redirect('emails:email_groups')

    context.update({'group': group})
    return render(request, 'emails/delete_group.html', context)

@login_required
def email_messages(request):
    """List all email messages"""

    context = TemplateLayout.init(request, {})

    messages_list = EmailMessage.objects.select_related('customer', 'template', 'sent_by').order_by('-created_at')

    # Filter functionality
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    search_query = request.GET.get('search')

    if status_filter:
        messages_list = messages_list.filter(status=status_filter)

    if type_filter:
        messages_list = messages_list.filter(message_type=type_filter)

    if search_query:
        messages_list = messages_list.filter(
            Q(recipient_name__icontains=search_query) |
            Q(recipient_email__icontains=search_query) |
            Q(subject__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    messages_list = paginator.get_page(page_number)

    context.update({'email_messages': messages_list})
    return render(request, 'emails/messages.html', context)

@login_required
def message_detail(request, message_id):
    """View email message details"""

    context = TemplateLayout.init(request, {})

    message = get_object_or_404(EmailMessage, id=message_id)

    context.update({'message': message})
    return render(request, 'emails/message_detail.html', context)

@login_required
def resend_message(request, message_id):
    """Resend failed email message"""

    context = TemplateLayout.init(request, {})

    message = get_object_or_404(EmailMessage, id=message_id)

    if request.method == 'POST':
        email_service = EmailService()

        response = email_service.send_email(
            to_email=message.recipient_email,
            subject=message.subject,
            message=message.message
        )

        # Update message status
        message.status = 'sent' if response['success'] else 'failed'
        message.sent_at = timezone.now() if response['success'] else None
        message.error_message = response['error'] if not response['success'] else None
        message.save()

        if response['success']:
            messages.success(request, 'Email resent successfully!')
        else:
            messages.error(request, f'Failed to resend email: {response["error"]}')

        return redirect('emails:message_detail', message_id=message.id)

    context.update({'message': message})
    return render(request, 'emails/resend_message.html', context)

@login_required
def email_logs(request):
    """View email activity logs"""

    context = TemplateLayout.init(request, {})

    logs = EmailLog.objects.select_related('user').order_by('-created_at')

    # Filter functionality
    action_filter = request.GET.get('action')
    error_filter = request.GET.get('error')

    if action_filter:
        logs = logs.filter(action=action_filter)

    if error_filter == 'true':
        logs = logs.filter(is_error=True)
    elif error_filter == 'false':
        logs = logs.filter(is_error=False)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    context.update({'logs': logs})
    return render(request, 'emails/logs.html', context)
