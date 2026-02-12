# Document Management System - Installation Checklist

## Pre-Installation Checks

- [ ] Virtual environment is available at `/opt/myproject/bin/activate`
- [ ] PostgreSQL database is running
- [ ] Django project is accessible
- [ ] User has appropriate permissions

## Installation Steps

### Step 1: Activate Virtual Environment
```bash
source /opt/myproject/bin/activate
```
**Expected**: Prompt shows `(myproject)` prefix

### Step 2: Navigate to Project Directory
```bash
cd /opt/myproject/myproject/Custom_inventory_system
```
**Expected**: You're in the project root with `manage.py`

### Step 3: Run Setup Script (Recommended)
```bash
./setup_documents.sh
```
**Expected**: 
- Media directories created
- Dependencies installed
- Migrations created and applied
- Success message displayed

### Alternative: Manual Installation
If setup script fails, run manually:

```bash
# Create directories
mkdir -p media/document_templates
mkdir -p media/client_documents
mkdir -p media/document_versions

# Set permissions
chmod -R 755 media/document_templates
chmod -R 755 media/client_documents
chmod -R 755 media/document_versions

# Install dependencies
pip install python-docx

# Create migrations
python3 manage.py makemigrations documents

# Apply migrations
python3 manage.py migrate documents

# Collect static files (optional)
python3 manage.py collectstatic --noinput
```

### Step 4: Verify Installation

#### Check Database Tables
```bash
python3 manage.py dbshell
```
```sql
\dt documents_*
```
**Expected**: 5 tables listed:
- documents_documenttemplate
- documents_clientdocument
- documents_documentversion
- documents_documentfollowup
- documents_documentaccesslog

#### Check Media Directories
```bash
ls -la media/
```
**Expected**: Three directories visible:
- document_templates/
- client_documents/
- document_versions/

#### Check URLs
```bash
python3 manage.py show_urls | grep documents
```
**Expected**: 20+ document URLs listed

### Step 5: Start Development Server
```bash
python3 manage.py runserver 0.0.0.0:8000
```
**Expected**: Server starts without errors

### Step 6: Access the System

Open browser and navigate to:
- Dashboard: `http://your-domain/documents/`
- Templates: `http://your-domain/documents/templates/`
- Documents: `http://your-domain/documents/documents/`

**Expected**: Pages load without 404 errors

### Step 7: Test Basic Functionality

#### As Admin/Manager:
1. [ ] Navigate to Templates
2. [ ] Click "New Template"
3. [ ] Fill in form and save
4. [ ] Template appears in list

#### As Any User:
1. [ ] Navigate to Customers
2. [ ] Select a customer
3. [ ] Go to Documents tab
4. [ ] Click "New Document"
5. [ ] Select template
6. [ ] Edit and save
7. [ ] Document appears in timeline

#### Test Follow-ups:
1. [ ] Open a document
2. [ ] Click "Add Follow-up"
3. [ ] Fill in details
4. [ ] Save
5. [ ] Follow-up appears in list

## Troubleshooting

### Issue: Migration Fails
**Solution**: Check database connection in `config/settings.py`
```bash
python3 manage.py dbshell
# If this fails, database connection is the issue
```

### Issue: Permission Denied on Media Directories
**Solution**: Fix permissions
```bash
sudo chmod -R 755 media/document_templates
sudo chmod -R 755 media/client_documents
sudo chmod -R 755 media/document_versions
```

### Issue: CKEditor Not Loading
**Solution**: Check internet connection (CDN required)
```bash
curl -I https://cdn.ckeditor.com/4.25.1/standard/ckeditor.js
```

### Issue: 404 on Document URLs
**Solution**: Verify URL configuration
```bash
grep -r "documents/" config/urls.py
# Should show: path("documents/", include("apps.documents.urls"))
```

### Issue: Template Access Denied
**Solution**: Check user role
```bash
python3 manage.py shell
```
```python
from apps.workers.models import Worker
worker = Worker.objects.get(user__username='your_username')
print(worker.role)
# Should be one of: Director General, Marketing Director, Central Stock Manager, Human Resource
```

## Post-Installation Tasks

### 1. Create Initial Templates
- [ ] Log in as Admin/Manager
- [ ] Navigate to Templates
- [ ] Create 5 initial templates:
  - [ ] Introductory Letter
  - [ ] Follow-up Letter
  - [ ] Billing Notice
  - [ ] Legal Notice
  - [ ] Generic Document

### 2. Configure Merge Fields
For each template, add merge fields:
- `{customer_name}` - Customer name
- `{customer_id}` - Customer ID
- `{contact_person}` - Contact person name
- `{email}` - Customer email
- `{telephone}` - Customer phone
- `{date}` - Current date

### 3. Test with Real Data
- [ ] Create document for actual customer
- [ ] Add follow-up task
- [ ] Test file download
- [ ] Verify version history
- [ ] Check audit log

### 4. Train Users
- [ ] Share `DOCUMENT_MANAGEMENT_GUIDE.md` with team
- [ ] Demonstrate template selection
- [ ] Show follow-up tracking
- [ ] Explain version control

## Verification Checklist

### Functionality
- [ ] Templates can be created (Admin/Manager)
- [ ] Templates can be duplicated (All users)
- [ ] Documents can be created from templates
- [ ] Documents can be edited (versions tracked)
- [ ] Documents can be downloaded
- [ ] Follow-ups can be created and assigned
- [ ] Customer timeline displays correctly
- [ ] Search and filtering works
- [ ] Audit log records actions

### Security
- [ ] Standard users cannot create/edit templates
- [ ] Users can only edit own documents (or Admin/Manager)
- [ ] Audit log tracks all actions
- [ ] File uploads are restricted to .doc/.docx
- [ ] Role-based access is enforced

### Performance
- [ ] Pages load in < 2 seconds
- [ ] Large documents display correctly
- [ ] Pagination works for long lists
- [ ] Search is responsive

### UI/UX
- [ ] Navigation menu shows "Document Management"
- [ ] All buttons and links work
- [ ] Forms validate input
- [ ] Error messages are clear
- [ ] Success messages appear after actions

## Production Deployment

### Before Going Live:
1. [ ] Backup database
2. [ ] Test all functionality
3. [ ] Review permissions
4. [ ] Set DEBUG=False in settings.py
5. [ ] Configure proper ALLOWED_HOSTS
6. [ ] Set up proper media file serving (nginx/apache)
7. [ ] Configure HTTPS
8. [ ] Test on production-like environment

### Production Settings:
```python
# config/settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Media File Serving (nginx):
```nginx
location /media/ {
    alias /opt/myproject/myproject/Custom_inventory_system/media/;
    expires 30d;
}
```

## Support Resources

- **Full Documentation**: `DOCUMENT_MANAGEMENT_GUIDE.md`
- **Quick Start**: `apps/documents/README.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Code Comments**: Inline documentation in all files

## Success Criteria

Installation is successful when:
- ✅ All database tables created
- ✅ Media directories exist with correct permissions
- ✅ Navigation menu shows "Document Management"
- ✅ Dashboard loads without errors
- ✅ Admin/Manager can create templates
- ✅ Users can create documents
- ✅ Follow-ups can be tracked
- ✅ Audit log records actions
- ✅ Files can be uploaded and downloaded

## Next Steps After Installation

1. Create initial templates
2. Train team members
3. Start creating documents
4. Monitor audit logs
5. Gather user feedback
6. Plan for future enhancements (digital signatures, email integration)

---

**Installation Date**: _________________  
**Installed By**: _________________  
**Verified By**: _________________  
**Status**: [ ] Complete [ ] Pending [ ] Issues

**Notes**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
