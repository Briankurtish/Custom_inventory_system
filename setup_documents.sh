#!/bin/bash

# Document Management System Setup Script
# This script sets up the document management system

echo "======================================"
echo "Document Management System Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Attempting to activate..."
    if [ -f "/opt/myproject/bin/activate" ]; then
        source /opt/myproject/bin/activate
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "${RED}✗ Could not find virtual environment${NC}"
        echo "Please activate manually: source /opt/myproject/bin/activate"
        exit 1
    fi
fi

# Navigate to project directory
cd /opt/myproject/myproject/Custom_inventory_system || exit 1
echo -e "${GREEN}✓ Changed to project directory${NC}"

# Create media directories
echo ""
echo "Creating media directories..."
mkdir -p media/document_templates
mkdir -p media/client_documents
mkdir -p media/document_versions

# Set permissions
chmod -R 755 media/document_templates
chmod -R 755 media/client_documents
chmod -R 755 media/document_versions
echo -e "${GREEN}✓ Media directories created${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install python-docx --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Make migrations
echo ""
echo "Creating migrations..."
python3 manage.py makemigrations documents
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations created${NC}"
else
    echo -e "${RED}✗ Failed to create migrations${NC}"
    exit 1
fi

# Run migrations
echo ""
echo "Running migrations..."
python3 manage.py migrate documents
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations applied${NC}"
else
    echo -e "${RED}✗ Failed to apply migrations${NC}"
    exit 1
fi

# Collect static files (optional)
echo ""
read -p "Collect static files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 manage.py collectstatic --noinput
    echo -e "${GREEN}✓ Static files collected${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Access the dashboard at: http://your-domain/documents/"
echo "2. Create your first template (Admin/Manager only)"
echo "3. Start creating documents for customers"
echo ""
echo "For detailed documentation, see: DOCUMENT_MANAGEMENT_GUIDE.md"
echo ""
