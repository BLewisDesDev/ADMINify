# Document Generator

Professional document generation system for NDIS/aged care compliance and client onboarding.

## Overview

The Document Generator automates the creation of industry-standard care documents with integrated PII protection, LLM-assisted content generation, and automated SharePoint filing.

### Document Types
- **Service Agreements** - Legal contracts between Caura and clients
- **Personalised Care Plans** - Tailored plans for Domestic Assistance and Home Maintenance
- **Wellness & Reablement Plans** - Goal-oriented therapy and support documents

## Features

- ✅ **Professional Templates** - Industry-compliant document formats
- ✅ **PII Protection** - Secure obfuscation for LLM processing
- ✅ **AI Content Generation** - LLM-assisted goals and recommendations
- ✅ **Document Versioning** - Semantic versioning with audit trails
- ✅ **SharePoint Integration** - Automated filing with metadata
- ✅ **Compliance Tracking** - Full audit logs for regulatory requirements

## Installation

```bash
cd doc_gen
pip install -r requirements.txt
```

## Quick Start

```python
from src.core.document_generator import DocumentGenerator

# Initialize generator
generator = DocumentGenerator()

# Generate care plan
result = generator.generate_care_plan(
    client_data=client_info,
    template_version="v2.1.0",
    enable_llm=True
)

print(f"Document created: {result.file_path}")
print(f"SharePoint URL: {result.sharepoint_url}")
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Microsoft Graph API
MICROSOFT_TENANT_ID=your_tenant_id
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret

# LLM Configuration
OPENAI_API_KEY=your_openai_key
LLM_MODEL=gpt-4

# SharePoint Settings
SHAREPOINT_SITE_URL=https://yourorg.sharepoint.com/sites/caura
SHAREPOINT_DOC_LIBRARY=Shared Documents
```

## Usage Examples

### Generate Care Plan with LLM Content
```python
from src.main import generate_document

result = generate_document(
    document_type="care_plan",
    client_id="C001234",
    data_source="client_database.json",
    options={
        "enable_llm": True,
        "llm_sections": ["goals", "recommendations"],
        "auto_upload": True
    }
)
```

### Batch Document Generation
```python
from src.core.batch_processor import BatchProcessor

processor = BatchProcessor()
results = processor.process_clients(
    client_list=["C001234", "C001235", "C001236"],
    document_types=["service_agreement", "care_plan"]
)
```

## API Reference

### Core Classes

#### `DocumentGenerator`
Main document generation engine.

```python
generator = DocumentGenerator(config_path="config.json")
result = generator.generate_document(
    template_path="templates/care_plan.docx",
    client_data=data,
    options=GenerationOptions()
)
```

#### `PIIObfuscator`
Privacy protection system.

```python
obfuscator = PIIObfuscator()
anonymized_data = obfuscator.obfuscate(client_data)
original_data = obfuscator.deobfuscate(anonymized_data, session_token)
```

#### `SharePointConnector`
Microsoft Graph integration.

```python
connector = SharePointConnector(credentials)
upload_result = connector.upload_document(
    file_path="output/document.docx",
    folder_path="/ClientDocuments/C001234/CarePlans/",
    metadata=document_metadata
)
```

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test category
python -m pytest tests/test_pii_protection.py -v

# Run with coverage
python -m pytest --cov=src tests/
```

## Security

- **PII Protection**: All client data is obfuscated before LLM processing
- **Audit Logging**: Complete trail of document generation and access
- **SharePoint Security**: Integrated with organizational permissions
- **Data Encryption**: Temporary data is encrypted at rest

## Compliance

This system adheres to:
- NDIS Practice Standards
- Australian Privacy Principles
- Organizational security policies
- Industry document formatting standards

## Troubleshooting

### Common Issues

**SharePoint Upload Fails**
```bash
# Check credentials and permissions
python -m src.utils.test_sharepoint_connection
```

**LLM Content Quality Issues**
```bash
# Review generated content
python -m src.utils.validate_llm_output --document-id DOC123
```

**Template Validation Errors**
```bash
# Validate template format
python -m src.utils.validate_template --template templates/care_plan.docx
```

## Development

### Project Structure
```
doc_gen/
├── src/
│   ├── core/              # Core business logic
│   ├── utils/             # Utility functions
│   └── main.py           # CLI entry point
├── templates/            # Document templates
├── output/              # Generated documents
├── tests/               # Test suite
└── docs/                # Documentation
```

### Contributing
1. Follow ADMINify development standards
2. Ensure all tests pass
3. Update documentation
4. Security review for PII handling

## License

Internal use only - Caura Aged Care Services

---

For detailed implementation guidance, see:
- `docs/roadmap.md` - Development roadmap
- `docs/project_specific_instructions.md` - Technical specifications
- `CLAUDE.md` - AI assistant instructions