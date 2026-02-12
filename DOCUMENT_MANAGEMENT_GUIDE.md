# Document Generation and Archiving System

## Overview

This comprehensive document management system provides robust functionality for creating, editing, attaching, and archiving Word-based letters and documents with version control, role-based access, and follow-up tracking.

## Features

### 1. Word Template Library
- **Upload and store templates**: Up to 5 initial Word templates (introductory, follow-up, billing, legal notices, generic)
- **Role-based template management**: Admin/Manager roles only for uploading/editing base templates
- **Template duplication**: Standard users can duplicate and edit templates for specific use
- **Inline editing**: CKEditor integration for rich text editing
- **File-based editing**: Support for Word document upload/download workflow

### 2. Document Creation & Editing
- **Template selection**: Choose from available templates or create from scratch
- **Inline or file-based editing**: Edit documents online or upload Word files
- **Version history**: Automatic tracking of changes with timestamps and user attribution
- **Auto-save versions**: Each edit creates a new version in the history

### 3. Client-Level Attachment
- **Attach to customer profiles**: Link documents directly to customer records
- **Multiple attachments**: Support multiple documents per client
- **Rich metadata**: Title, date created, template type, attached by (user)
- **Timeline view**: See all documents chronologically

### 4. Follow-Up & Archiving
- **Timeline view**: Chronological list of all client documents
- **Version control**: Update documents without losing history
- **Follow-up tracking**: Flag documents for follow-up with due dates
- **SMS integration**: Hooks for SMS reminders (via existing SMS module)
- **Priority levels**: Low, Medium, High, Urgent
- **Assignment**: Assign follow-ups to specific team members

### 5. Access Control
- **Role-based permissions**: Enforced via existing user management
- **Admin/Manager privileges**: 
  - Director General
  - Marketing Director
  - Central Stock Manager
  - Human Resource
- **Standard user access**: Can view, create, and edit own documents
- **Audit logging**: Complete access log for compliance

### 6. Future-Proofing
- **Placeholder support**: Generic Word docs until official templates arrive
- **Modular design**: Easy addition/replacement of templates
- **Digital signature hooks**: Ready for DocuSign API integration
- **Auto-population support**: Merge fields for client data
  - {customer_name}
  - {customer_id}
  - {contact_person}
  - {email}
  - {telephone}
  - {date}

## Installation & Setup

### 1. Database Migration

```bash
# Activate virtual environment
source /opt/myproject/bin/activate

# Navigate to project directory
cd /opt/myproject/myproject/Custom_inventory_system

# Create media directories
mkdir -p media/document_templates
mkdir -p media/client_documents
mkdir -p media/document_versions

# Set proper permissions
chmod -R 755 media/document_templates
chmod -R 755 media/client_documents
chmod -R 755 media/document_versions

# Run migrations
python3 manage.py makemigrations documents
python3 manage.py migrate documents

# Create a superuser if needed (optional)
python3 manage.py createsuperuser
```

### 2. Install Dependencies

```bash
# Install python-docx for Word file handling
pip install python-docx

# Or install all requirements
pip install -r requirements.txt
```

### 3. Collect Static Files

```bash
python3 manage.py collectstatic --noinput
```

## Usage Guide

### Accessing the System

1. **Dashboard**: Navigate to `/documents/` or click "Documents" in the main menu
2. **Templates**: Go to `/documents/templates/` to manage templates
3. **All Documents**: Browse all documents at `/documents/documents/`
4. **Follow-ups**: Track tasks at `/documents/follow-ups/`

### Creating a Template (Admin/Manager Only)

1. Navigate to **Documents → Templates**
2. Click **"New Template"**
3. Fill in:
   - Name (e.g., "Introductory Letter Template")
   - Type (select from dropdown)
   - Description
   - Choose either:
     - **HTML Editor tab**: Use rich text editor for online editing
     - **Upload Word File tab**: Upload a .docx file
4. Click **"Save Template"**

### Creating a Document for a Customer

1. Go to **Customers → Select Customer → Documents Tab**
2. Click **"New Document"**
3. Select a template (optional) - content will auto-populate
4. Edit the document:
   - Update title and description
   - Modify content in the HTML editor or upload a Word file
   - Set status (Draft, Final, Sent, Archived)
5. Set follow-up if needed:
   - Check "Requires Follow-up"
   - Set follow-up date
   - Add notes
6. Click **"Save Document"**

### Editing a Document

1. Open the document from customer's timeline or document list
2. Click **"Edit"**
3. Make changes in the editor
4. Add a **change summary** (what changed in this version)
5. Click **"Save Document"**
   - A new version is automatically created
   - Previous versions remain accessible

### Managing Follow-ups

1. Navigate to **Documents → Follow-ups**
2. View by status:
   - **Pending & In Progress** (default)
   - **Completed**
   - **My Tasks** (assigned to you)
3. Create follow-up:
   - Title and description
   - Priority (Low/Medium/High/Urgent)
   - Due date and reminder date
   - Assign to team member
4. Update status as work progresses
5. Mark complete when done

### Customer Document Timeline

Each customer has a dedicated document timeline showing:
- All documents chronologically
- Document status and type
- Quick actions (View, Edit, Download)
- Upcoming follow-ups
- Document statistics

## Role-Based Access

### Admin/Manager Roles (Full Access)
- Director General
- Marketing Director
- Central Stock Manager
- Human Resource

**Permissions**:
- Create, edit, delete templates
- Manage all documents
- View all follow-ups
- Access audit logs

### Standard Users
**Permissions**:
- View templates
- Duplicate templates for personal use
- Create documents from templates
- Edit own documents
- View customer documents
- Manage assigned follow-ups

## Technical Details

### Models

1. **DocumentTemplate**
   - Template management
   - Support for both Word and HTML content
   - Merge field configuration

2. **ClientDocument**
   - Main document storage
   - Links to customer and template
   - Status tracking
   - Follow-up integration

3. **DocumentVersion**
   - Complete version history
   - Change tracking
   - User attribution

4. **DocumentFollowUp**
   - Task management
   - Priority and status tracking
   - Assignment system
   - SMS integration hooks

5. **DocumentAccessLog**
   - Audit trail
   - Compliance tracking
   - IP logging

### Security Features

- Role-based access control
- Complete audit logging
- IP address tracking
- User attribution for all actions
- Version control prevents data loss

### Integration Points

1. **SMS Module**: Ready for reminder notifications
2. **Customer Module**: Direct customer linking
3. **Worker Module**: User management and assignments
4. **Email Module**: Future email sending capability

## Best Practices

1. **Template Management**
   - Create clear, descriptive template names
   - Use merge fields for dynamic content
   - Keep templates up to date
   - Archive unused templates (set to inactive)

2. **Document Organization**
   - Use meaningful titles
   - Add descriptions for context
   - Set appropriate status
   - Tag follow-ups when needed

3. **Version Control**
   - Always add change summaries
   - Review version history before major edits
   - Keep drafts until finalized

4. **Follow-up Management**
   - Set realistic due dates
   - Assign to appropriate team members
   - Update status regularly
   - Use priority levels effectively

## Troubleshooting

### Issue: Templates not appearing
- Check template is set to "Active"
- Verify user has appropriate role/permissions
- Clear browser cache

### Issue: Cannot upload Word files
- Ensure file is .doc or .docx format
- Check file size (should be < 10MB)
- Verify media directory permissions

### Issue: CKEditor not loading
- Check internet connection (CDN required)
- Clear browser cache
- Check browser console for errors

### Issue: Follow-ups not showing
- Verify follow-up flag is checked on document
- Check date filters
- Ensure status is not "Completed" or "Cancelled"

## API Endpoints (AJAX)

- `GET /documents/templates/<id>/content/` - Get template content
- `POST /documents/templates/<id>/duplicate/` - Duplicate template

## Future Enhancements

1. **Digital Signatures**
   - DocuSign API integration
   - E-signature tracking
   - Certificate management

2. **Auto-population**
   - Advanced merge fields
   - Data validation
   - Custom field mapping

3. **Email Integration**
   - Send documents via email
   - Track email opens
   - Automated follow-ups

4. **Advanced Reporting**
   - Document analytics
   - Follow-up reports
   - User activity reports

5. **Collaboration**
   - Document sharing
   - Comments and annotations
   - Real-time editing

## Support

For technical support or feature requests, contact your system administrator.

## License

Proprietary - GC Pharma Management System
