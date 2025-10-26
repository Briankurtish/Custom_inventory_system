from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    # Dashboard
    path('', views.email_dashboard, name='email_dashboard'),

    # Send Emails
    path('send/', views.send_email, name='send_email'),
    path('send/bulk/', views.send_bulk_email, name='send_bulk_email'),

    # Templates
    path('templates/', views.email_templates, name='email_templates'),
    path('templates/create/', views.create_template, name='create_template'),
    path('templates/<int:template_id>/edit/', views.edit_template, name='edit_template'),
    path('templates/<int:template_id>/delete/', views.delete_template, name='delete_template'),

    # Groups
    path('groups/', views.email_groups, name='email_groups'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),

    # Messages
    path('messages/', views.email_messages, name='email_messages'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/resend/', views.resend_message, name='resend_message'),

    # Logs
    path('logs/', views.email_logs, name='email_logs'),
]
