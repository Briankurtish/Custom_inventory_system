from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    # Dashboard
    path('', views.sms_dashboard, name='sms_dashboard'),

    # Templates
    path('templates/', views.sms_templates, name='sms_templates'),
    path('templates/<int:template_id>/edit/', views.edit_template, name='edit_template'),
    path('templates/<int:template_id>/delete/', views.delete_template, name='delete_template'),

    # Groups
    path('groups/', views.sms_groups, name='sms_groups'),
    path('groups/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),

    # Sending SMS
    path('send/', views.send_sms, name='send_sms'),
    path('send/bulk/', views.send_bulk_sms, name='send_bulk_sms'),

    # Messages
    path('messages/', views.sms_messages, name='sms_messages'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/resend/', views.resend_message, name='resend_message'),

    # Logs
    path('logs/', views.sms_logs, name='sms_logs'),

    # AJAX endpoints
    path('ajax/template-content/', views.get_template_content, name='get_template_content'),
    path('ajax/customer-phone/', views.get_customer_phone, name='get_customer_phone'),
    path('ajax/group-customers/', views.get_group_customers, name='get_group_customers'),
]
