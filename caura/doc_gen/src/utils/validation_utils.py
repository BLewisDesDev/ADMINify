# File: doc_gen/src/utils/validation_utils.py
"""
Validation utilities for document generation system.

Provides comprehensive input validation and data sanitization.
"""

import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from pathlib import Path
import validators

from .logging_utils import get_logger

logger = get_logger(__name__)


class ClientDataValidator:
    """
    Validates client data for document generation.
    
    Ensures data integrity and compliance with business rules.
    """
    
    # Required fields for different document types
    REQUIRED_FIELDS = {
        "care_plan": [
            "client_id", "given_name", "family_name", "date_of_birth",
            "address", "phone", "services_required"
        ],
        "service_agreement": [
            "client_id", "given_name", "family_name", "date_of_birth",
            "address", "phone", "services_agreed", "start_date"
        ],
        "wellness_plan": [
            "client_id", "given_name", "family_name", "date_of_birth",
            "address", "phone", "wellness_goals", "current_abilities"
        ]
    }
    
    # Data type validations
    DATE_FIELDS = ["date_of_birth", "start_date", "end_date", "review_date"]
    PHONE_FIELDS = ["phone", "emergency_phone", "contact_phone"]
    EMAIL_FIELDS = ["email", "emergency_email", "contact_email"]
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_client_data(self, data: Dict[str, Any], 
                           document_type: str) -> bool:
        """
        Validate client data for document generation.
        
        Args:
            data: Client data dictionary
            document_type: Type of document being generated
            
        Returns:
            True if validation passes, False otherwise
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        logger.debug(f"Validating client data for document type: {document_type}")
        
        # Check required fields
        if not self._validate_required_fields(data, document_type):
            return False
        
        # Validate data types and formats
        self._validate_data_types(data)
        
        # Validate business rules
        self._validate_business_rules(data, document_type)
        
        # Log validation results
        if self.validation_errors:
            logger.error(f"Validation failed with {len(self.validation_errors)} errors")
            for error in self.validation_errors:
                logger.error(f"Validation error: {error}")
            return False
        
        if self.validation_warnings:
            logger.warning(f"Validation completed with {len(self.validation_warnings)} warnings")
            for warning in self.validation_warnings:
                logger.warning(f"Validation warning: {warning}")
        
        logger.info("Client data validation successful")
        return True
    
    def _validate_required_fields(self, data: Dict[str, Any], 
                                 document_type: str) -> bool:
        """
        Validate that all required fields are present.
        
        Args:
            data: Client data dictionary
            document_type: Type of document
            
        Returns:
            True if all required fields present, False otherwise
        """
        required_fields = self.REQUIRED_FIELDS.get(document_type, [])
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)
        
        if missing_fields:
            self.validation_errors.append(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
            return False
        
        return True
    
    def _validate_data_types(self, data: Dict[str, Any]) -> None:
        """
        Validate data types and formats.
        
        Args:
            data: Client data dictionary
        """
        # Validate dates
        for field in self.DATE_FIELDS:
            if field in data and data[field]:
                if not self._validate_date(data[field], field):
                    self.validation_errors.append(
                        f"Invalid date format for {field}: {data[field]}"
                    )
        
        # Validate phone numbers
        for field in self.PHONE_FIELDS:
            if field in data and data[field]:
                if not self._validate_phone(data[field]):
                    self.validation_errors.append(
                        f"Invalid phone number format for {field}: {data[field]}"
                    )
        
        # Validate email addresses
        for field in self.EMAIL_FIELDS:
            if field in data and data[field]:
                if not self._validate_email(data[field]):
                    self.validation_errors.append(
                        f"Invalid email format for {field}: {data[field]}"
                    )
        
        # Validate client ID format
        if "client_id" in data:
            if not self._validate_client_id(data["client_id"]):
                self.validation_errors.append(
                    f"Invalid client ID format: {data['client_id']}"
                )
    
    def _validate_business_rules(self, data: Dict[str, Any], 
                               document_type: str) -> None:
        """
        Validate business-specific rules.
        
        Args:
            data: Client data dictionary
            document_type: Type of document
        """
        # Age validation
        if "date_of_birth" in data:
            age = self._calculate_age(data["date_of_birth"])
            if age is not None:
                if age < 18:
                    self.validation_warnings.append(
                        f"Client age is under 18: {age} years"
                    )
                elif age > 120:
                    self.validation_errors.append(
                        f"Invalid age: {age} years"
                    )
        
        # Service validation for care plans
        if document_type == "care_plan" and "services_required" in data:
            valid_services = ["domestic_assistance", "home_maintenance", 
                            "social_support", "transport", "nursing"]
            services = data["services_required"]
            if isinstance(services, list):
                invalid_services = [s for s in services if s not in valid_services]
                if invalid_services:
                    self.validation_warnings.append(
                        f"Unknown services: {', '.join(invalid_services)}"
                    )
    
    def _validate_date(self, date_value: Union[str, date, datetime], 
                      field_name: str) -> bool:
        """
        Validate date format and value.
        
        Args:
            date_value: Date to validate
            field_name: Name of the field for context
            
        Returns:
            True if valid date, False otherwise
        """
        try:
            if isinstance(date_value, (date, datetime)):
                return True
            
            if isinstance(date_value, str):
                # Try common date formats
                date_formats = [
                    "%Y-%m-%d",
                    "%d/%m/%Y", 
                    "%m/%d/%Y",
                    "%Y-%m-%d %H:%M:%S",
                    "%d/%m/%Y %H:%M:%S"
                ]
                
                for fmt in date_formats:
                    try:
                        datetime.strptime(date_value, fmt)
                        return True
                    except ValueError:
                        continue
            
            return False
            
        except Exception:
            return False
    
    def _validate_phone(self, phone: str) -> bool:
        """
        Validate Australian phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid phone format, False otherwise
        """
        try:
            # Remove common separators
            clean_phone = re.sub(r'[\s\-\(\)]+', '', phone)
            
            # Australian phone number patterns
            patterns = [
                r'^04\d{8}$',  # Mobile: 04xxxxxxxx
                r'^0[2-8]\d{8}$',  # Landline: 0xxxxxxxxx
                r'^\+61[2-9]\d{8}$',  # International: +61xxxxxxxxx
                r'^1[38]00\d{6}$',  # Free call: 1800xxxxxx or 1300xxxxxx
            ]
            
            for pattern in patterns:
                if re.match(pattern, clean_phone):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email, False otherwise
        """
        try:
            return validators.email(email)
        except Exception:
            return False
    
    def _validate_client_id(self, client_id: str) -> bool:
        """
        Validate client ID format.
        
        Args:
            client_id: Client ID to validate
            
        Returns:
            True if valid format, False otherwise
        """
        try:
            # Client ID format: C followed by 6 digits
            pattern = r'^C\d{6}$'
            return bool(re.match(pattern, client_id))
            
        except Exception:
            return False
    
    def _calculate_age(self, date_of_birth: Union[str, date, datetime]) -> Optional[int]:
        """
        Calculate age from date of birth.
        
        Args:
            date_of_birth: Date of birth
            
        Returns:
            Age in years or None if calculation fails
        """
        try:
            if isinstance(date_of_birth, str):
                # Try to parse date string
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        dob = datetime.strptime(date_of_birth, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return None
            elif isinstance(date_of_birth, datetime):
                dob = date_of_birth.date()
            elif isinstance(date_of_birth, date):
                dob = date_of_birth
            else:
                return None
            
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            return age
            
        except Exception:
            return None
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get validation summary with errors and warnings.
        
        Returns:
            Dictionary containing validation results
        """
        return {
            "is_valid": len(self.validation_errors) == 0,
            "error_count": len(self.validation_errors),
            "warning_count": len(self.validation_warnings),
            "errors": self.validation_errors.copy(),
            "warnings": self.validation_warnings.copy()
        }


class TemplateValidator:
    """
    Validates document templates for integrity and compatibility.
    """
    
    def __init__(self):
        self.validation_errors = []
    
    def validate_template(self, template_path: Union[str, Path]) -> bool:
        """
        Validate document template file.
        
        Args:
            template_path: Path to template file
            
        Returns:
            True if template is valid, False otherwise
        """
        self.validation_errors.clear()
        
        path = Path(template_path)
        
        # Check file exists
        if not path.exists():
            self.validation_errors.append(f"Template file not found: {template_path}")
            return False
        
        # Check file extension
        if path.suffix.lower() not in ['.docx', '.dotx']:
            self.validation_errors.append(f"Invalid template format: {path.suffix}")
            return False
        
        # Check file size (basic sanity check)
        file_size = path.stat().st_size
        if file_size == 0:
            self.validation_errors.append("Template file is empty")
            return False
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            self.validation_errors.append("Template file is too large (>50MB)")
            return False
        
        # Additional template-specific validations would go here
        # (e.g., checking for required template variables)
        
        logger.info(f"Template validation successful: {template_path}")
        return True
    
    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors.
        
        Returns:
            List of validation error messages
        """
        return self.validation_errors.copy()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for file system
    """
    # Remove or replace unsafe characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    safe_filename = safe_filename.strip(' .')
    
    # Limit length
    if len(safe_filename) > 200:
        name, ext = safe_filename.rsplit('.', 1) if '.' in safe_filename else (safe_filename, '')
        safe_filename = name[:190] + ('.' + ext if ext else '')
    
    # Ensure not empty
    if not safe_filename:
        safe_filename = "document"
    
    return safe_filename


def validate_document_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate document metadata structure.
    
    Args:
        metadata: Document metadata dictionary
        
    Returns:
        True if metadata is valid, False otherwise
    """
    required_fields = [
        "document_id", "document_type", "client_id", "version", 
        "created_date", "created_by"
    ]
    
    for field in required_fields:
        if field not in metadata:
            logger.error(f"Missing required metadata field: {field}")
            return False
    
    # Validate document type
    valid_types = ["care_plan", "service_agreement", "wellness_plan"]
    if metadata["document_type"] not in valid_types:
        logger.error(f"Invalid document type: {metadata['document_type']}")
        return False
    
    # Validate version format (semantic versioning)
    version_pattern = r'^\d+\.\d+\.\d+$'
    if not re.match(version_pattern, metadata["version"]):
        logger.error(f"Invalid version format: {metadata['version']}")
        return False
    
    return True