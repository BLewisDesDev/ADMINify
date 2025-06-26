# Document Generator Module - Claude Instructions

**Purpose**: Professional document generation system for NDIS/aged care compliance

---

## Module-Specific Context

### **Business Requirements**
- Generate industry-standard care documents during client onboarding
- Maintain document versioning and compliance standards
- Integrate with SharePoint for automated filing
- Protect PII while enabling LLM-assisted content generation

### **Document Types**
1. **Service Agreements** - Legal contracts (template provided externally)
2. **Personalised Care Plans** - Domestic Assistance & Home Maintenance services
3. **Wellness & Reablement Plans** - Goal-oriented therapy documents

### **Technical Challenges**
- **Document Versioning**: Industry-standard version control system
- **PII Obfuscation**: Anonymize data for LLM processing while maintaining document integrity
- **LLM Integration**: Generate content sections using anonymized client data
- **SharePoint Integration**: Automated filing via Microsoft Graph API
- **Template Management**: Professional template updates and validation

---

## Architecture Principles

### **Separation of Concerns**
- **Data Processing**: Client data validation and transformation
- **Document Generation**: Template processing and content creation
- **LLM Integration**: Anonymous content generation
- **File Management**: Output handling and SharePoint integration
- **Version Control**: Document versioning and audit trails

### **Security First**
- PII protection at all processing stages
- Secure data obfuscation for LLM processing
- Audit logging for compliance
- SharePoint security integration

### **Professional Standards**
- Industry-compliant document formatting
- Version control with semantic versioning
- Template validation and testing
- Error handling with user-friendly messages

---

## Development Standards

### **Code Quality**
- Follow parent project development standards
- Comprehensive error handling for document processing
- Input validation for all client data
- Resource cleanup for file operations
- Structured logging for audit trails

### **Testing Strategy**
- Template validation testing
- Document generation accuracy testing
- PII obfuscation verification
- SharePoint integration testing
- LLM content quality validation

---

## Integration Points

### **External Dependencies**
- Microsoft Graph API for SharePoint
- LLM API for content generation
- LibreOffice for PDF conversion
- Template validation tools

### **Internal Dependencies**
- Parent project data protection protocols
- Shared logging utilities
- Common configuration management

---

**Always maintain professional document standards and regulatory compliance.**