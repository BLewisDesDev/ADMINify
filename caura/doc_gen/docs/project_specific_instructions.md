# Document Generator - Project-Specific Instructions

**Last Updated**: 2025-06-26  
**Purpose**: Detailed implementation guidelines for doc_gen module

---

## Business Context

### **Client Onboarding Process**
During NDIS/aged care client onboarding, multiple compliance documents must be generated:

1. **Service Agreement** - Legal contract between Caura and client
2. **Personalised Care Plan** - Tailored plan for Domestic Assistance (DA) and Home Maintenance (HM)
3. **Wellness & Reablement Plan** - Goal-oriented therapy and support plan

### **Current Pain Points**
- ❌ Templates are outdated and non-compliant
- ❌ Manual document creation is time-consuming and error-prone
- ❌ No version control or audit trails
- ❌ Manual filing creates compliance risks
- ❌ PII handling lacks proper security protocols

### **Success Vision**
- ✅ Automated, compliant document generation in minutes
- ✅ Professional templates meeting industry standards
- ✅ Secure PII handling with LLM-assisted content creation
- ✅ Automated SharePoint filing with proper metadata
- ✅ Complete audit trails for compliance

---

## Technical Specifications

### **Document Versioning System**

#### **Semantic Versioning Format**
```
[DocumentType]_[ClientID]_[Version]_[Date].docx
Example: CarePlan_C001234_v1.2.3_20250626.docx
```

#### **Version Components**
- **Major (X.0.0)**: Template changes, compliance updates
- **Minor (0.X.0)**: Content updates, goal modifications
- **Patch (0.0.X)**: Corrections, minor edits

#### **Metadata Requirements**
```json
{
  "document_id": "unique_identifier",
  "document_type": "care_plan|service_agreement|wellness_plan",
  "client_id": "encrypted_client_reference",
  "version": "1.2.3",
  "created_date": "2025-06-26T10:30:00Z",
  "created_by": "user_id",
  "template_version": "template_v2.1.0",
  "compliance_standard": "NDIS_2025",
  "llm_sections": ["goals", "recommendations"],
  "pii_obfuscated": true,
  "sharepoint_path": "/ClientDocuments/C001234/CarePlans/"
}
```

### **PII Obfuscation System**

#### **Obfuscation Strategy**
```python
# Example obfuscation mapping
{
  "client_name": "John Smith" → "CLIENT_A",
  "address": "123 Main St, Sydney NSW 2000" → "ADDRESS_1, CITY_1 STATE_1 POSTCODE_1",
  "phone": "0412345678" → "PHONE_1",
  "dob": "1985-03-15" → "1985-XX-XX",
  "medical_conditions": ["diabetes", "arthritis"] → ["CONDITION_1", "CONDITION_2"]
}
```

#### **Reversible Mapping**
- Generate unique session tokens for each document generation
- Store obfuscation mappings in secure temporary storage
- Clear mappings after document completion
- Maintain audit log of obfuscation events

#### **LLM Data Preparation**
```python
anonymized_prompt = f"""
Generate care plan goals for CLIENT_A who is AGE_RANGE years old living in LOCATION_TYPE.
Client has CONDITION_COUNT conditions affecting MOBILITY_LEVEL.
Services required: SERVICE_LIST
Previous goals: GOAL_HISTORY (anonymized)
"""
```

### **LLM Integration Specifications**

#### **Content Generation Sections**
1. **Care Goals**: Personalized, measurable objectives
2. **Recommendations**: Evidence-based care suggestions
3. **Risk Assessments**: Contextual safety considerations
4. **Progress Indicators**: Measurable outcome metrics

#### **Prompt Templates**
```python
CARE_GOALS_PROMPT = """
Role: You are an experienced aged care coordinator creating personalized care goals.

Context: CLIENT_A is AGE_RANGE years old with CONDITION_LIST living in ACCOMMODATION_TYPE.
Current abilities: CURRENT_ABILITIES
Desired outcomes: DESIRED_OUTCOMES
Available services: SERVICE_LIST

Task: Generate 3-5 SMART goals that are:
- Specific and measurable
- Achievable within 6 months
- Relevant to client's conditions and circumstances
- Time-bound with clear milestones

Format: Return as numbered list with clear success criteria.
Tone: Professional, empathetic, person-centered.
"""
```

#### **Quality Validation**
- Content length validation (minimum/maximum word counts)
- Professional language checking
- SMART goal criteria validation
- Industry terminology compliance
- Sensitivity review for appropriate tone

### **SharePoint Integration**

#### **Microsoft Graph API Requirements**
- Application registration with appropriate permissions
- Document.ReadWrite.All scope for document operations
- Sites.ReadWrite.All scope for folder management
- User authentication with proper token management

#### **Folder Structure**
```
/Caura Shared Documents/
├── ClientDocuments/
│   ├── [ClientID]/
│   │   ├── ServiceAgreements/
│   │   │   ├── Current/
│   │   │   └── Archive/
│   │   ├── CarePlans/
│   │   │   ├── Current/
│   │   │   └── Archive/
│   │   └── WellnessPlans/
│   │       ├── Current/
│   │       └── Archive/
├── Templates/
│   ├── ServiceAgreements/
│   ├── CarePlans/
│   └── WellnessPlans/
└── Archive/
    └── [Year]/
        └── [Month]/
```

#### **Upload Workflow**
1. **Validate document** - Check format, metadata, content
2. **Create folder structure** - Auto-create client folders if needed
3. **Upload with metadata** - Include all document properties
4. **Archive previous versions** - Move superseded documents
5. **Update client record** - Log document creation event
6. **Send notifications** - Alert relevant team members

---

## Development Guidelines

### **Module Architecture**

#### **Core Modules Structure**
```python
# doc_gen/src/core/
data_processor.py      # Client data handling and validation
document_generator.py  # Template processing and assembly
pii_obfuscator.py     # Privacy protection system
llm_integrator.py     # AI content generation
sharepoint_connector.py # Microsoft Graph integration
version_manager.py     # Document versioning system
template_manager.py    # Template validation and management
```

#### **Data Flow Architecture**
```
Client Data → Validation → PII Obfuscation → LLM Processing → 
Document Assembly → Version Control → SharePoint Upload → Audit Log
```

### **Error Handling Requirements**

#### **Critical Error Scenarios**
- **PII Leakage**: Immediate halt, security notification, audit log
- **Template Corruption**: Fallback to previous template version
- **SharePoint Connectivity**: Queue for retry, notify administrator
- **LLM API Failure**: Use fallback templates, notify for manual review
- **Version Conflict**: User notification, conflict resolution workflow

#### **Error Recovery Patterns**
```python
try:
    result = process_document(client_data)
except PIILeakageError as e:
    security_alert(e)
    clear_temporary_data()
    raise  # Don't continue processing
except SharePointError as e:
    queue_for_retry(document, metadata)
    notify_admin(e)
    return local_save_path  # Continue with local save
except LLMError as e:
    log_llm_failure(e)
    return generate_fallback_content()
```

### **Testing Requirements**

#### **Security Testing**
- PII obfuscation verification with real-world data patterns
- LLM prompt injection prevention
- SharePoint permission validation
- Audit log integrity checking

#### **Integration Testing**
- End-to-end document generation workflows
- SharePoint connectivity under various network conditions
- LLM API rate limiting and error handling
- Template validation with malformed inputs

#### **Performance Testing**
- Bulk document generation (50+ documents)
- Large template processing (complex formatting)
- SharePoint upload performance
- Memory usage during obfuscation operations

---

## Compliance Requirements

### **NDIS Standards**
- Documents must meet NDIS Practice Standards
- Goal setting follows NDIS planning guidelines
- Person-centered language requirements
- Cultural sensitivity considerations

### **Privacy & Security**
- Australian Privacy Principles compliance
- NDIS Privacy and Dignity of Risk guidelines
- Secure data handling throughout pipeline
- Audit trail requirements for compliance reviews

### **Document Standards**
- Professional formatting and layout
- Consistent branding and styling
- Accessibility requirements (WCAG compliance)
- Version control and change tracking

---

## Implementation Priorities

### **Phase 1 Focus**
1. **Core Architecture** - Solid foundation with proper separation
2. **Data Security** - PII protection from day one
3. **Template System** - Robust template management
4. **Error Handling** - Comprehensive error scenarios

### **Critical Success Factors**
- **Security First**: PII protection cannot be compromised
- **Professional Quality**: Documents must meet industry standards
- **User Experience**: Simple, reliable, fast document generation
- **Compliance**: Full audit trails and version control

---

**Always prioritize client privacy and regulatory compliance over feature complexity.**