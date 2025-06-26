# Document Generator Setup Guide

## Quick Start

### 1. Environment Setup
```bash
cd doc_gen

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install LibreOffice (for PDF generation)
```bash
# macOS
brew install --cask libreoffice

# Ubuntu/Debian
sudo apt-get install libreoffice

# Windows
# Download and install from https://www.libreoffice.org/
```

### 3. Run Tests
```bash
# Basic functionality tests
python tests/test_data_processor.py

# Comprehensive test suite with edge cases
python tests/run_comprehensive_tests.py

# Example usage demonstrations
python tests/test_example_usage.py
```

### 4. CLI Usage
```bash
# Generate documents (will fail without templates)
python -m src.main generate --type care_plan --input tests/test_data_comprehensive.json

# Validate test data
python -m src.main validate --input tests/test_data_comprehensive.json --type care_plan

# List available templates
python -m src.main list-templates
```

## Configuration

### Environment Variables (.env)
Copy `.env.example` to `.env` and configure:

```bash
# Microsoft Graph API (for SharePoint)
MICROSOFT_TENANT_ID=your_tenant_id
MICROSOFT_CLIENT_ID=your_client_id  
MICROSOFT_CLIENT_SECRET=your_client_secret

# LLM Configuration
OPENAI_API_KEY=your_openai_key
LLM_MODEL=gpt-4

# SharePoint Settings
SHAREPOINT_SITE_URL=https://yourorg.sharepoint.com/sites/caura
```

## Next Steps

### Required for Full Functionality

1. **Add Document Templates**
   - Place `.docx` templates in appropriate directories:
     - `templates/care_plans/`
     - `templates/service_agreements/`
     - `templates/wellness_reablement/`

2. **Template Requirements**
   - Use `{{variable_name}}` for template variables
   - Follow docxtpl template syntax
   - Include version number in filename: `care_plan_v1.0.0.docx`

3. **Test with Real Data**
   - Map real client data fields to template variables
   - Validate with comprehensive test suite
   - Test document generation pipeline

### System is Ready For:
- ✅ Professional document generation
- ✅ PII protection for LLM processing  
- ✅ Comprehensive audit logging
- ✅ Australian compliance validation
- ✅ PDF generation pipeline
- ✅ CLI interface for batch processing