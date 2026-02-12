# Generated migration for documents app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '__first__'),
        ('workers', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_id', models.CharField(editable=False, max_length=50, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('template_type', models.CharField(choices=[('introductory', 'Introductory Letter'), ('follow_up', 'Follow-Up Letter'), ('billing', 'Billing Notice'), ('legal', 'Legal Notice'), ('generic', 'Generic Document')], default='generic', max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('word_file', models.FileField(blank=True, null=True, upload_to='document_templates/')),
                ('html_content', models.TextField(blank=True, help_text='HTML content for inline editing', null=True)),
                ('merge_fields', models.JSONField(blank=True, default=dict, help_text='Available merge fields: {customer_name}, {customer_id}, {contact_person}, {email}, {telephone}, {date}, etc.')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_templates', to='workers.worker')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_templates', to='workers.worker')),
            ],
            options={
                'verbose_name': 'Document Template',
                'verbose_name_plural': 'Document Templates',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_id', models.CharField(editable=False, max_length=50, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('word_file', models.FileField(blank=True, null=True, upload_to='client_documents/')),
                ('html_content', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('final', 'Final'), ('sent', 'Sent'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('requires_follow_up', models.BooleanField(default=False)),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                ('follow_up_notes', models.TextField(blank=True, null=True)),
                ('is_signed', models.BooleanField(default=False)),
                ('signature_data', models.JSONField(blank=True, default=dict, help_text='Digital signature metadata')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='customers.customer')),
                ('template', models.ForeignKey(blank=True, help_text='Template used to create this document', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_documents', to='documents.documenttemplate')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_documents', to='workers.worker')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_documents', to='workers.worker')),
            ],
            options={
                'verbose_name': 'Client Document',
                'verbose_name_plural': 'Client Documents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DocumentVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.IntegerField()),
                ('word_file', models.FileField(blank=True, null=True, upload_to='document_versions/')),
                ('html_content', models.TextField(blank=True, null=True)),
                ('change_summary', models.TextField(blank=True, help_text='Description of changes made', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='documents.clientdocument')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='document_versions', to='workers.worker')),
            ],
            options={
                'verbose_name': 'Document Version',
                'verbose_name_plural': 'Document Versions',
                'ordering': ['-version_number'],
                'unique_together': {('document', 'version_number')},
            },
        ),
        migrations.CreateModel(
            name='DocumentFollowUp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('due_date', models.DateField()),
                ('reminder_date', models.DateField(blank=True, help_text='Date to send reminder', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('sms_reminder_sent', models.BooleanField(default=False)),
                ('sms_sent_at', models.DateTimeField(blank=True, null=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follow_ups', to='documents.clientdocument')),
                ('assigned_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_followups', to='workers.worker')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_followups', to='workers.worker')),
            ],
            options={
                'verbose_name': 'Document Follow-Up',
                'verbose_name_plural': 'Document Follow-Ups',
                'ordering': ['due_date', '-priority'],
            },
        ),
        migrations.CreateModel(
            name='DocumentAccessLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('view', 'Viewed'), ('create', 'Created'), ('edit', 'Edited'), ('delete', 'Deleted'), ('download', 'Downloaded'), ('share', 'Shared')], max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('details', models.TextField(blank=True, null=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_logs', to='documents.clientdocument')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='workers.worker')),
            ],
            options={
                'verbose_name': 'Document Access Log',
                'verbose_name_plural': 'Document Access Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='clientdocument',
            index=models.Index(fields=['customer', '-created_at'], name='documents_c_custome_a49e7a_idx'),
        ),
        migrations.AddIndex(
            model_name='clientdocument',
            index=models.Index(fields=['status', '-created_at'], name='documents_c_status_7c0ab0_idx'),
        ),
        migrations.AddIndex(
            model_name='documentfollowup',
            index=models.Index(fields=['status', 'due_date'], name='documents_d_status_2a5c8e_idx'),
        ),
        migrations.AddIndex(
            model_name='documentfollowup',
            index=models.Index(fields=['assigned_to', 'status'], name='documents_d_assigne_9b4e2d_idx'),
        ),
        migrations.AddIndex(
            model_name='documentaccesslog',
            index=models.Index(fields=['document', '-timestamp'], name='documents_d_documen_7f1c5a_idx'),
        ),
        migrations.AddIndex(
            model_name='documentaccesslog',
            index=models.Index(fields=['user', '-timestamp'], name='documents_d_user_id_1e8b4c_idx'),
        ),
    ]
