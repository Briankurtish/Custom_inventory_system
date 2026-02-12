# Document Management System

A comprehensive document generation and archiving system for client correspondences.

## Quick Start

### 1. Run Setup Script

```bash
cd /opt/myproject/myproject/Custom_inventory_system
./setup_documents.sh
```

### 2. Access the System

- **Dashboard**: http://your-domain/documents/
- **Templates**: http://your-domain/documents/templates/
- **Follow-ups**: http://your-domain/documents/follow-ups/

### 3. Create Your First Template (Admin/Manager)

1. Go to Templates → New Template
2. Add name, type, and content
3. Save template

### 4. Create a Document

1. Go to Customers → Select Customer
2. Click on Documents tab
3. Click "New Document"
4. Select template or create from scratch
5. Edit and save

## Features

✅ **Template Library** - Store reusable document templates  
✅ **Rich Text Editor** - CKEditor integration for online editing  
✅ **Word File Support** - Upload and download .docx files  
✅ **Version Control** - Complete document history  
✅ **Follow-up Tracking** - Task management with reminders  
✅ **Role-Based Access** - Admin/Manager controls  
✅ **Customer Integration** - Direct linking to customers  
✅ **Timeline View** - Chronological document history  
✅ **Audit Logging** - Complete access tracking  
✅ **Digital Signature Ready** - Hooks for future integration  

## File Structure

```
apps/documents/
├── models.py              # Database models
├── views.py               # View functions with role-based access
├── forms.py               # Form definitions
├── urls.py                # URL routing
├── admin.py               # Django admin interface
├── templates/
│   └── documents/         # HTML templates
│       ├── dashboard.html
│       ├── document_list.html
│       ├── document_detail.html
│       ├── document_form.html
│       ├── template_list.html
│       ├── template_form.html
│       ├── template_detail.html
│       ├── followup_list.html
│       ├── followup_form.html
│       ├── customer_documents.html
│       └── *_confirm_delete.html
└── migrations/
    └── 0001_initial.py    # Initial database schema
```

## Models

1. **DocumentTemplate** - Template storage
2. **ClientDocument** - Main documents
3. **DocumentVersion** - Version history
4. **DocumentFollowUp** - Task tracking
5. **DocumentAccessLog** - Audit trail

## Permissions

### Admin/Manager Roles (Full Access)
- Director General
- Marketing Director
- Central Stock Manager
- Human Resource

### Standard Users
- View and duplicate templates
- Create and edit documents
- Manage follow-ups

## Integration

- ✅ Customer Module - Direct customer linking
- ✅ Worker Module - User management
- 🔄 SMS Module - Ready for SMS reminders
- 🔄 Email Module - Ready for email sending

## Manual Setup (if script fails)

```bash
# Activate virtual environment
source /opt/myproject/bin/activate

# Navigate to project
cd /opt/myproject/myproject/Custom_inventory_system

# Create directories
mkdir -p media/{document_templates,client_documents,document_versions}

# Install dependencies
pip install python-docx

# Run migrations
python3 manage.py makemigrations documents
python3 manage.py migrate documents

# Collect static files
python3 manage.py collectstatic --noinput
```

## Configuration

The app is already configured in:
- `config/settings.py` - Added to INSTALLED_APPS
- `config/urls.py` - URLs mounted at `/documents/`
- `requirements.txt` - Dependencies listed

## Usage Examples

### Create Template
```python
from apps.documents.models import DocumentTemplate

template = DocumentTemplate.objects.create(
    name="Welcome Letter",
    template_type="introductory",
    html_content="<h1>Welcome {customer_name}!</h1><p>...</p>",
    created_by=worker,
    updated_by=worker
)
```

### Create Document
```python
from apps.documents.models import ClientDocument

document = ClientDocument.objects.create(
    customer=customer,
    template=template,
    title="Welcome Letter - ACME Corp",
    html_content="<h1>Welcome ACME Corp!</h1>",
    status="draft",
    created_by=worker
)
```

### Add Follow-up
```python
from apps.documents.models import DocumentFollowUp
from datetime import date, timedelta

followup = DocumentFollowUp.objects.create(
    document=document,
    title="Follow up on welcome letter",
    description="Check if customer received letter",
    priority="medium",
    due_date=date.today() + timedelta(days=7),
    assigned_to=sales_rep,
    created_by=manager
)
```

## API Endpoints

- `GET /documents/` - Dashboard
- `GET /documents/templates/` - Template list
- `POST /documents/templates/create/` - Create template
- `GET /documents/documents/` - Document list
- `POST /documents/documents/create/` - Create document
- `GET /documents/follow-ups/` - Follow-up list
- `GET /documents/customers/<id>/documents/` - Customer documents
- `GET /documents/templates/<id>/content/` - AJAX: Get template content
- `POST /documents/templates/<id>/duplicate/` - Duplicate template

## Troubleshooting

**Media files not accessible**
```bash
chmod -R 755 media/document_templates
chmod -R 755 media/client_documents
```

**CKEditor not loading**
- Check internet connection (uses CDN)
- Clear browser cache

**Permission denied**
- Check user role in Worker model
- Verify ROLE_CHOICES includes admin roles

## Support

See `DOCUMENT_MANAGEMENT_GUIDE.md` for complete documentation.

## License

Proprietary - GC Pharma Management System
