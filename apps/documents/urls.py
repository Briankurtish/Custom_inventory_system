from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.document_dashboard, name='document_dashboard'),

    # Template URLs
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:template_id>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:template_id>/duplicate/', views.duplicate_template, name='template_duplicate'),
    path('templates/<int:template_id>/content/', views.get_template_content, name='get_template_content'),

    # Document URLs
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/create/<int:customer_id>/', views.document_create, name='document_create_for_customer'),
    path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<int:document_id>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:document_id>/delete/', views.document_delete, name='document_delete'),
    path('documents/<int:document_id>/download/', views.document_download, name='document_download'),

    # Customer Documents
    path('customers/<int:customer_id>/documents/', views.customer_documents, name='customer_documents'),

    # Follow-up URLs
    path('follow-ups/', views.followup_list, name='followup_list'),
    path('documents/<int:document_id>/follow-ups/create/', views.followup_create, name='followup_create'),
    path('follow-ups/<int:followup_id>/edit/', views.followup_edit, name='followup_edit'),
]
