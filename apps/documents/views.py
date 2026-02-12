from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from web_project import TemplateLayout

from .models import (
    DocumentTemplate, ClientDocument, DocumentVersion,
    DocumentFollowUp, DocumentAccessLog
)
from .forms import (
    DocumentTemplateForm, ClientDocumentForm, ClientDocumentQuickForm,
    DocumentFollowUpForm, DocumentSearchForm
)
from apps.customers.models import Customer
from apps.workers.models import Worker


# Decorator for role-based access control
def admin_manager_required(view_func):
    """Decorator to restrict access to Admin, Director General, and Managers"""
    def wrapper(request, *args, **kwargs):
        # Allow superusers to bypass role check
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if not hasattr(request.user, 'worker_profile'):
            messages.error(request, "Access denied. You must be logged in as a worker.")
            return redirect('auth-login-basic')

        worker = request.user.worker_profile
        allowed_roles = [
            'Director General', 'Marketing Director',
            'Central Stock Manager', 'Human Resource'
        ]

        if worker.role not in allowed_roles:
            messages.error(request, "Access denied. Admin or Manager role required.")
            return redirect('document_list')

        return view_func(request, *args, **kwargs)
    return wrapper


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_document_access(document, user, action, request, details=None):
    """Log document access for audit trail"""
    DocumentAccessLog.objects.create(
        document=document,
        user=user,
        action=action,
        ip_address=get_client_ip(request),
        details=details
    )


# ===================== TEMPLATE VIEWS =====================

@login_required
@admin_manager_required
def template_list(request):
    """List all document templates"""
    templates = DocumentTemplate.objects.all()

    # Filter by type if provided
    template_type = request.GET.get('type')
    if template_type:
        templates = templates.filter(template_type=template_type)

    # Search
    search_query = request.GET.get('search')
    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    paginator = Paginator(templates, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    view_context = {
        'page_obj': page_obj,
        'template_types': DocumentTemplate.TEMPLATE_TYPES,
        'current_type': template_type,
        'search_query': search_query
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/template_list.html', context)


@login_required
@admin_manager_required
def template_create(request):
    """Create a new document template"""
    if request.method == 'POST':
        form = DocumentTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user.worker_profile
            template.updated_by = request.user.worker_profile
            template.save()
            messages.success(request, f"Template '{template.name}' created successfully!")
            return redirect('template_detail', template_id=template.id)
    else:
        form = DocumentTemplateForm()

    view_context = {'form': form, 'action': 'Create'}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/template_form.html', context)


@login_required
def template_detail(request, template_id):
    """View template details"""
    template = get_object_or_404(DocumentTemplate, id=template_id)
    documents_count = template.client_documents.count()

    view_context = {
        'template': template,
        'documents_count': documents_count
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/template_detail.html', context)


@login_required
@admin_manager_required
def template_edit(request, template_id):
    """Edit an existing template"""
    template = get_object_or_404(DocumentTemplate, id=template_id)

    if request.method == 'POST':
        form = DocumentTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            template = form.save(commit=False)
            template.updated_by = request.user.worker_profile
            template.save()
            messages.success(request, f"Template '{template.name}' updated successfully!")
            return redirect('template_detail', template_id=template.id)
    else:
        form = DocumentTemplateForm(instance=template)

    view_context = {'form': form, 'template': template, 'action': 'Edit'}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/template_form.html', context)


@login_required
@admin_manager_required
def template_delete(request, template_id):
    """Delete a template"""
    template = get_object_or_404(DocumentTemplate, id=template_id)

    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f"Template '{template_name}' deleted successfully!")
        return redirect('template_list')

    view_context = {'template': template}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/template_confirm_delete.html', context)


# ===================== DOCUMENT VIEWS =====================

@login_required
def document_list(request):
    """List all client documents with filtering and search"""
    documents = ClientDocument.objects.select_related(
        'customer', 'template', 'created_by'
    ).all()

    # Apply filters
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('customer'):
            documents = documents.filter(customer=form.cleaned_data['customer'])

        if form.cleaned_data.get('status'):
            documents = documents.filter(status=form.cleaned_data['status'])

        if form.cleaned_data.get('template_type'):
            documents = documents.filter(template__template_type=form.cleaned_data['template_type'])

        if form.cleaned_data.get('date_from'):
            documents = documents.filter(created_at__gte=form.cleaned_data['date_from'])

        if form.cleaned_data.get('date_to'):
            documents = documents.filter(created_at__lte=form.cleaned_data['date_to'])

        if form.cleaned_data.get('search_query'):
            query = form.cleaned_data['search_query']
            documents = documents.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(document_id__icontains=query) |
                Q(customer__customer_name__icontains=query)
            )

    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    view_context = {
        'page_obj': page_obj,
        'form': form
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/document_list.html', context)


@login_required
def document_create(request, customer_id=None):
    """Create a new client document"""
    customer = None
    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        form = ClientDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.created_by = request.user.worker_profile
            document.updated_by = request.user.worker_profile

            # If template is selected, copy content
            if document.template:
                if document.template.html_content and not document.html_content:
                    document.html_content = document.template.html_content
                if document.template.word_file and not document.word_file:
                    document.word_file = document.template.word_file

            document.save()

            # Create initial version
            DocumentVersion.objects.create(
                document=document,
                version_number=1,
                word_file=document.word_file,
                html_content=document.html_content,
                change_summary="Initial version",
                created_by=request.user.worker_profile
            )

            # Log access
            log_document_access(
                document, request.user.worker_profile,
                'create', request,
                f"Document created: {document.title}"
            )

            messages.success(request, f"Document '{document.title}' created successfully!")
            return redirect('document_detail', document_id=document.id)
    else:
        initial = {}
        if customer:
            initial['customer'] = customer
        form = ClientDocumentForm(initial=initial)

    view_context = {
        'form': form,
        'customer': customer,
        'action': 'Create'
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/document_form.html', context)


@login_required
def document_detail(request, document_id):
    """View document details with timeline"""
    document = get_object_or_404(
        ClientDocument.objects.select_related('customer', 'template', 'created_by'),
        id=document_id
    )

    # Get versions
    versions = document.versions.select_related('created_by').all()

    # Get follow-ups
    follow_ups = document.follow_ups.select_related('assigned_to', 'created_by').all()

    # Get access logs
    access_logs = document.access_logs.select_related('user').order_by('-timestamp')[:20]

    # Log view access
    log_document_access(
        document, request.user.worker_profile,
        'view', request
    )

    view_context = {
        'document': document,
        'versions': versions,
        'follow_ups': follow_ups,
        'access_logs': access_logs
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/document_detail.html', context)


@login_required
def document_edit(request, document_id):
    """Edit an existing document"""
    document = get_object_or_404(ClientDocument, id=document_id)

    if request.method == 'POST':
        form = ClientDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            # Store old version
            old_version_number = document.versions.count()

            document = form.save(commit=False)
            document.updated_by = request.user.worker_profile
            document.save()

            # Create new version
            DocumentVersion.objects.create(
                document=document,
                version_number=old_version_number + 1,
                word_file=document.word_file,
                html_content=document.html_content,
                change_summary=request.POST.get('change_summary', 'Document updated'),
                created_by=request.user.worker_profile
            )

            # Log access
            log_document_access(
                document, request.user.worker_profile,
                'edit', request,
                f"Document updated: {document.title}"
            )

            messages.success(request, f"Document '{document.title}' updated successfully!")
            return redirect('document_detail', document_id=document.id)
    else:
        form = ClientDocumentForm(instance=document)

    view_context = {
        'form': form,
        'document': document,
        'action': 'Edit'
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/document_form.html', context)


@login_required
def document_delete(request, document_id):
    """Delete a document"""
    document = get_object_or_404(ClientDocument, id=document_id)

    # Check permissions - only creator or admin can delete
    worker = request.user.worker_profile
    allowed_roles = ['Director General', 'Marketing Director', 'Central Stock Manager']

    if document.created_by != worker and worker.role not in allowed_roles:
        messages.error(request, "You don't have permission to delete this document.")
        return redirect('document_detail', document_id=document.id)

    if request.method == 'POST':
        document_title = document.title
        customer = document.customer

        # Log deletion
        log_document_access(
            document, request.user.worker_profile,
            'delete', request,
            f"Document deleted: {document_title}"
        )

        document.delete()
        messages.success(request, f"Document '{document_title}' deleted successfully!")
        return redirect('customer_documents', customer_id=customer.id)

    view_context = {'document': document}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/document_confirm_delete.html', context)


@login_required
def document_download(request, document_id):
    """Download document file"""
    document = get_object_or_404(ClientDocument, id=document_id)

    if not document.word_file:
        messages.error(request, "No file attached to this document.")
        return redirect('document_detail', document_id=document.id)

    # Log download
    log_document_access(
        document, request.user.worker_profile,
        'download', request
    )

    response = FileResponse(document.word_file.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{document.get_file_name()}"'
    return response


# ===================== CUSTOMER DOCUMENT VIEWS =====================

@login_required
def customer_documents(request, customer_id):
    """View all documents for a specific customer with timeline"""
    customer = get_object_or_404(Customer, id=customer_id)
    documents = customer.documents.select_related(
        'template', 'created_by'
    ).order_by('-created_at')

    # Get follow-ups for this customer's documents
    document_ids = documents.values_list('id', flat=True)
    upcoming_follow_ups = DocumentFollowUp.objects.filter(
        document_id__in=document_ids,
        status__in=['pending', 'in_progress'],
        due_date__gte=timezone.now().date()
    ).select_related('document', 'assigned_to').order_by('due_date')[:5]

    view_context = {
        'customer': customer,
        'documents': documents,
        'upcoming_follow_ups': upcoming_follow_ups
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/customer_documents.html', context)


# ===================== FOLLOW-UP VIEWS =====================

@login_required
def followup_create(request, document_id):
    """Create a follow-up for a document"""
    document = get_object_or_404(ClientDocument, id=document_id)

    if request.method == 'POST':
        form = DocumentFollowUpForm(request.POST)
        if form.is_valid():
            follow_up = form.save(commit=False)
            follow_up.document = document
            follow_up.created_by = request.user.worker_profile
            follow_up.save()

            messages.success(request, "Follow-up created successfully!")
            return redirect('document_detail', document_id=document.id)
    else:
        form = DocumentFollowUpForm()

    view_context = {
        'form': form,
        'document': document
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/followup_form.html', context)


@login_required
def followup_edit(request, followup_id):
    """Edit a follow-up"""
    follow_up = get_object_or_404(DocumentFollowUp, id=followup_id)

    if request.method == 'POST':
        form = DocumentFollowUpForm(request.POST, instance=follow_up)
        if form.is_valid():
            follow_up = form.save()

            if follow_up.status == 'completed' and not follow_up.completed_at:
                follow_up.completed_at = timezone.now()
                follow_up.save()

            messages.success(request, "Follow-up updated successfully!")
            return redirect('document_detail', document_id=follow_up.document.id)
    else:
        form = DocumentFollowUpForm(instance=follow_up)

    view_context = {
        'form': form,
        'follow_up': follow_up
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/followup_form.html', context)


@login_required
def followup_list(request):
    """List all follow-ups with filtering"""
    follow_ups = DocumentFollowUp.objects.select_related(
        'document', 'document__customer', 'assigned_to', 'created_by'
    ).all()

    # Filter by status
    status = request.GET.get('status')
    if status:
        follow_ups = follow_ups.filter(status=status)
    else:
        # Default to showing only pending and in_progress
        follow_ups = follow_ups.filter(status__in=['pending', 'in_progress'])

    # Filter by assigned user
    if request.GET.get('my_tasks'):
        follow_ups = follow_ups.filter(assigned_to=request.user.worker_profile)

    # Sort by due date
    follow_ups = follow_ups.order_by('due_date', '-priority')

    paginator = Paginator(follow_ups, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    view_context = {
        'page_obj': page_obj,
        'status': status
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/followup_list.html', context)


# ===================== DASHBOARD & ANALYTICS =====================

@login_required
def document_dashboard(request):
    """Dashboard with document statistics and analytics"""
    worker = request.user.worker_profile

    # Get counts
    total_documents = ClientDocument.objects.count()
    total_templates = DocumentTemplate.objects.filter(is_active=True).count()
    pending_follow_ups = DocumentFollowUp.objects.filter(
        status__in=['pending', 'in_progress']
    ).count()
    overdue_follow_ups = DocumentFollowUp.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__lt=timezone.now().date()
    ).count()

    # Recent documents
    recent_documents = ClientDocument.objects.select_related(
        'customer', 'created_by'
    ).order_by('-created_at')[:10]

    # My follow-ups
    my_follow_ups = DocumentFollowUp.objects.filter(
        assigned_to=worker,
        status__in=['pending', 'in_progress']
    ).select_related('document', 'document__customer').order_by('due_date')[:10]

    # Documents by status
    documents_by_status = ClientDocument.objects.values('status').annotate(
        count=Count('id')
    )

    # Documents by template type
    documents_by_type = ClientDocument.objects.filter(
        template__isnull=False
    ).values('template__template_type').annotate(
        count=Count('id')
    )

    view_context = {
        'total_documents': total_documents,
        'total_templates': total_templates,
        'pending_follow_ups': pending_follow_ups,
        'overdue_follow_ups': overdue_follow_ups,
        'recent_documents': recent_documents,
        'my_follow_ups': my_follow_ups,
        'documents_by_status': documents_by_status,
        'documents_by_type': documents_by_type
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'documents/dashboard.html', context)


# ===================== AJAX/API VIEWS =====================

@login_required
def get_template_content(request, template_id):
    """AJAX endpoint to get template content"""
    template = get_object_or_404(DocumentTemplate, id=template_id)

    return JsonResponse({
        'success': True,
        'html_content': template.html_content or '',
        'template_type': template.template_type,
        'name': template.name
    })


@login_required
def duplicate_template(request, template_id):
    """Duplicate a template for standard users"""
    template = get_object_or_404(DocumentTemplate, id=template_id)

    if request.method == 'POST':
        new_template = DocumentTemplate.objects.create(
            name=f"{template.name} (Copy)",
            template_type=template.template_type,
            description=template.description,
            html_content=template.html_content,
            word_file=template.word_file,
            is_active=True,
            created_by=request.user.worker_profile,
            updated_by=request.user.worker_profile
        )

        messages.success(request, f"Template duplicated successfully as '{new_template.name}'!")
        return redirect('template_detail', template_id=new_template.id)

    return redirect('template_detail', template_id=template_id)
