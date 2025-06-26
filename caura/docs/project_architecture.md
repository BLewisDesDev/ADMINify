# ADMINify Project Architecture

**Last Updated**: 2025-06-26  
**Status**: Planning Phase  
**Purpose**: Define the architectural vision and modular structure for ADMINify

---

## Architecture Principles

### **Modular Library Design**
- Each major directory represents an independent project/module
- Self-contained functionality with clear interfaces
- Optional orchestration layer for chaining operations
- Language choice driven by suitability to problem domain

### **Technology Stack Strategy**
- **Primary**: Python for data processing, document generation, and business logic
- **Secondary**: TypeScript/Node.js for web interfaces and complex calculations
- **Supporting**: PHP for legacy WordPress integration, VBA for Excel automation
- **Infrastructure**: JSON for data exchange, XML for government reporting

### **Data Security Model**
- Sensitive client data never leaves local machine
- No network transmission of personal information
- Configuration and credentials isolated in `.env` files
- Data processing uses temporary files with automatic cleanup
- **Protected Access**: `.claudeignore` and `.env` files prevent access to sensitive directories and file types
- **File Type Restrictions**: `.csv`, `.xlsx`, `.xls`, `.json` files require explicit permission before access
- **Directory Isolation**: All `/data/` subdirectories are completely protected from automated access

---

## Project Structure

### **Core Modules**

#### **1. Document Generation (`doc_gen/`)**
- **Purpose**: Template-based document creation (care plans, service agreements)
- **Input**: Client data (Excel/JSON)
- **Output**: DOCX/PDF documents
- **Status**: Functional, needs refactoring to standards

#### **2. DEX Reporting (`dex/`)**
- **Purpose**: Government compliance reporting and submission
- **Input**: Session data, client information
- **Output**: XML files for DEX portal
- **Status**: In development, critical for compliance

#### **3. Business Reports (`business_reports/`)**
- **Purpose**: Financial and operational reporting
- **Input**: Timesheet data, payment records
- **Output**: Summary reports, analytics
- **Status**: Basic structure exists

#### **4. Utilities (`scripts/`)**
- **Purpose**: One-off tools and data processing scripts
- **Input**: Various data formats
- **Output**: Cleaned/processed data
- **Status**: Collection of working scripts, needs organization

#### **5. Brand Assets (`brand_kit/`)**
- **Purpose**: Corporate branding and visual identity
- **Contents**: Logos, color schemes, brand guidelines
- **Status**: Static assets, complete

#### **6. Website Integration (`Website/`)**
- **Purpose**: WordPress theme and plugin integration
- **Technology**: PHP, CSS, HTML
- **Status**: Legacy code, maintenance mode

---

## Data Flow Architecture

### **Primary Data Pipeline**
```
External Systems → Raw Data → Processed Data → Documents/Reports
     ↓               ↓            ↓              ↓
  ShiftCare       Excel/CSV    JSON/XML      PDF/DOCX
  Guardhouse      Raw Export   Structured    Compliance
  NDIS Portal     Timesheets   Data Store    Reports
```

### **Quality Gates**
1. **Input Validation**: Data type checking, required field validation
2. **Processing Verification**: Transformation accuracy, data integrity
3. **Output Validation**: Format compliance, completeness checks
4. **Error Recovery**: Graceful degradation, detailed logging

---

## Development Standards

### **Code Quality Requirements**
- Comprehensive error handling with user-friendly messages
- Structured logging (INFO, WARNING, ERROR levels)
- Input validation for all user-facing functions
- Resource cleanup (files, connections, memory)
- Documentation strings for all public functions

### **Project Structure Standards**
```
project_name/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Project documentation
├── templates/              # Document templates
├── output/                 # Generated files
├── logs/                   # Application logs
├── README.md              # Project overview
├── requirements.txt       # Dependencies
└── main.py               # Entry point
```

### **Testing Strategy**
- Manual testing with comprehensive logging
- CLI tools for direct testing of functions
- Sample data sets for reproducible testing
- Integration testing for data pipeline components

---

## Implementation Phases

### **Phase 1: Foundation (Current)**
- [ ] Document existing functionality
- [ ] Create architectural standards
- [ ] Refactor critical components (DEX, doc_gen)
- [ ] Establish testing procedures

### **Phase 2: Modularization**
- [ ] Convert each directory to proper Python project
- [ ] Implement standard interfaces between modules
- [ ] Create CLI entry points for each module
- [ ] Documentation and usage examples

### **Phase 3: Integration**
- [ ] Design orchestration layer
- [ ] Create master CLI for chaining operations
- [ ] Implement workflow automation
- [ ] Performance optimization

### **Phase 4: Enhancement**
- [ ] Web interface for common operations
- [ ] Advanced error recovery
- [ ] Automated testing suite
- [ ] Deployment packaging

---

## Technical Decisions

### **Language Selection Criteria**
- **Python**: Data processing, file manipulation, document generation
- **TypeScript**: Complex calculations, potential web interfaces
- **PHP**: WordPress integration (legacy support only)
- **VBA**: Excel automation where Python libraries insufficient

### **Dependency Management**
- Each module maintains its own `requirements.txt`
- Shared utilities in common library
- Version pinning for production stability
- Development vs. production dependency separation

### **Error Handling Philosophy**
- Fail gracefully with detailed logging
- User-friendly error messages
- Automatic recovery where possible
- Comprehensive debugging information for developers

---

## Security Considerations

### **Data Protection**
- All client data processing occurs locally
- No cloud storage or transmission of sensitive data
- Temporary files use secure deletion
- Configuration data isolated from code

### **Access Control**
- File-level permissions for sensitive directories
- Environment variable management for credentials
- Audit logging for data access
- Secure defaults for all configurations

---

## Future Considerations

### **Scalability Options**
- Container-based deployment for team use
- API interfaces for remote access
- Database backend for structured data
- Web dashboard for non-technical users

### **Integration Opportunities**
- Direct API connections to external systems
- Automated scheduling for regular reports
- Email/notification systems for alerts
- Backup and archival systems

---

**Next Steps**: Review and validate this architecture with actual implementation requirements.