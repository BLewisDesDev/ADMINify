# ADMINify Development Standards

**Last Updated**: 2025-06-26  
**Purpose**: Code quality and development standards for ADMINify project

---

## Code Quality Standards

### **Python Code Standards**

#### **File Structure**
```python
"""
Module Name: Brief description

Detailed description of what this module does.

Usage:
    from module import function
    result = function(args)

Author: Byron
Date: YYYY-MM-DD
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Module-level constants
DEFAULT_CONFIG = {...}

def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration with sensible defaults."""
    pass

class ModuleClass:
    """Brief class description."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize with configuration."""
        pass
    
    def public_method(self, param: str) -> Optional[str]:
        """
        Brief method description.
        
        Args:
            param: Description of parameter
            
        Returns:
            Description of return value or None if error
            
        Raises:
            ValueError: When parameter is invalid
        """
        pass

def main() -> None:
    """Main function for CLI usage."""
    pass

if __name__ == "__main__":
    main()
```

#### **Error Handling Pattern**
```python
def process_data(input_path: str) -> Optional[Dict[str, Any]]:
    """Process data with comprehensive error handling."""
    try:
        # Validate inputs
        if not input_path or not Path(input_path).exists():
            logging.error(f"Invalid input path: {input_path}")
            return None
        
        # Main processing logic
        result = do_processing(input_path)
        
        logging.info(f"Successfully processed {input_path}")
        return result
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        return None
    except PermissionError as e:
        logging.error(f"Permission denied: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error processing {input_path}: {str(e)}")
        logging.exception("Detailed traceback:")
        return None
```

#### **Logging Standards**
```python
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Standard logging setup for all modules."""
    
    # Determine log file path
    if not log_file:
        project_root = Path(__file__).parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{Path(__file__).stem}.log"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

### **Data Processing Standards**

#### **Input Validation**
```python
def validate_client_data(data: Dict[str, Any]) -> bool:
    """Validate client data structure and content."""
    required_fields = ["ACN", "GivenName", "FamilyName", "BirthDate"]
    
    # Check required fields exist
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logging.error(f"Missing required fields: {', '.join(missing_fields)}")
        return False
    
    # Check data types and formats
    if not isinstance(data["ACN"], str) or len(data["ACN"]) != 10:
        logging.error("ACN must be 10-character string")
        return False
    
    return True
```

#### **Data Cleaning**
```python
def clean_value(val: Any) -> str:
    """Clean a value by handling NaN, None, and empty values."""
    if val is None:
        return ""
    
    if isinstance(val, str):
        val = val.strip()
        if val.lower() in ['nan', 'null', 'none', '']:
            return ""
    
    return str(val)
```

### **File Operations Standards**

#### **Directory Management**
```python
def ensure_directory_structure(project_root: Path) -> Dict[str, Path]:
    """Create and validate project directory structure."""
    dirs = {
        "src": project_root / "src",
        "tests": project_root / "tests",
        "docs": project_root / "docs", 
        "templates": project_root / "templates",
        "output": project_root / "output",
        "logs": project_root / "logs"
    }
    
    for name, path in dirs.items():
        path.mkdir(exist_ok=True, parents=True)
        logging.debug(f"Ensured {name} directory exists at {path}")
    
    return dirs
```

#### **File Processing**
```python
def process_file_safely(file_path: Path, processor_func) -> bool:
    """Process file with proper error handling and resource management."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            result = processor_func(file)
            
        logging.info(f"Successfully processed {file_path}")
        return True
        
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return False
    except PermissionError:
        logging.error(f"Permission denied: {file_path}")
        return False
    except UnicodeDecodeError:
        logging.error(f"Encoding error in file: {file_path}")
        return False
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        return False
```

---

## Project Standards

### **Project Structure Template**
```
project_name/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── core/                # Core business logic
│   │   ├── __init__.py
│   │   ├── models.py        # Data models
│   │   ├── processors.py    # Data processing
│   │   └── validators.py    # Input validation
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── file_utils.py
│       └── logging_utils.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_data/           # Sample data for testing
├── templates/               # Document templates
├── output/                  # Generated files
│   ├── logs/               # Log files
│   └── temp/               # Temporary files
├── docs/
│   ├── README.md
│   ├── usage.md
│   └── api.md
├── requirements.txt
├── setup.py                 # Optional: for installable packages
└── .gitignore
```

### **README Template**
```markdown
# Project Name

Brief description of what this project does.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line
```bash
python -m src.main --help
```

### Python Module
```python
from src.core import MainProcessor
processor = MainProcessor()
result = processor.process_data(input_path)
```

## Configuration

Configuration options and environment variables.

## Testing

How to test the project.

## Troubleshooting

Common issues and solutions.
```

### **Requirements.txt Standards**
```
# Core dependencies
pandas>=1.5.0
pathlib>=1.0.0
logging>=0.4.9.6

# Document processing
python-docx>=0.8.11
docxtpl>=0.16.0

# Development dependencies (optional)
pytest>=7.0.0
black>=22.0.0
flake8>=5.0.0
```

---

## Testing Standards

### **Manual Testing Approach**
```python
def test_function_manually():
    """Manual test function with sample data."""
    # Setup test data
    test_data = {
        "ACN": "1234567890",
        "GivenName": "John",
        "FamilyName": "Doe",
        "BirthDate": "1990-01-01"
    }
    
    # Test the function
    result = process_client_data(test_data)
    
    # Verify results
    if result:
        print("✓ Test passed")
        print(f"Result: {result}")
    else:
        print("✗ Test failed")
    
    return result is not None
```

### **CLI Testing Commands**
```bash
# Test with sample data
python -m src.main --input tests/test_data/sample.json --output output/test

# Test error handling
python -m src.main --input nonexistent.json

# Test with verbose logging
python -m src.main --input sample.json --log-level DEBUG
```

---

## Documentation Standards

### **Function Documentation**
```python
def process_document(template_path: str, data: Dict[str, Any], output_path: str) -> Optional[Path]:
    """
    Process a document template with provided data.
    
    Args:
        template_path: Path to the Word template file
        data: Dictionary containing replacement data
        output_path: Path for the generated document
        
    Returns:
        Path to generated document if successful, None if error
        
    Raises:
        FileNotFoundError: If template file doesn't exist
        PermissionError: If unable to write to output path
        
    Examples:
        >>> result = process_document("template.docx", {"name": "John"}, "output.docx")
        >>> if result:
        ...     print(f"Document created: {result}")
    """
    pass
```

### **Module Documentation**
```python
"""
Document Processor Module

This module handles document generation using Word templates and client data.
It provides functionality for:
- Loading and validating templates
- Processing client data
- Generating documents in DOCX and PDF formats
- Error handling and logging

Key Classes:
    DocumentProcessor: Main class for document operations
    
Key Functions:
    process_document: Generate single document
    process_batch: Generate multiple documents
    
Usage:
    from src.document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    result = processor.process_document(template, data, output)

Author: Byron
Created: 2025-06-26
"""
```

---

## Git Standards

### **.gitignore Template**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
logs/
output/
temp/
*.log

# Security
.env
.env.local
config/credentials.json
```

### **Commit Message Standards**
```
feat: add new document processing feature
fix: resolve template loading error
docs: update API documentation
refactor: improve error handling in processor
test: add manual testing for validation
```

---

## Security Standards

### **Sensitive Data Handling**
- Never commit sensitive data to version control
- Use environment variables for configuration
- Implement secure file deletion for temporary files
- Log access to sensitive operations (without logging the data itself)

### **Error Messages**
- Don't expose internal paths in user-facing errors
- Sanitize error messages to prevent information leakage
- Use generic error messages for security-sensitive operations

---

**Next Steps**: Apply these standards to existing code during refactoring phase.