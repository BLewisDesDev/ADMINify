# File: doc_gen/src/core/data_processor.py
"""
Data processor for client information handling.

Processes and validates client data for document generation with PII protection.
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import json

from ..utils.logging_utils import get_logger
from ..utils.validation_utils import ClientDataValidator, sanitize_filename
from ..utils.file_utils import load_json_safe, save_json_safe

logger = get_logger(__name__)


class ClientDataProcessor:
    """
    Processes client data for document generation.
    
    Handles data loading, validation, transformation, and preparation
    for document template processing.
    """
    
    def __init__(self):
        self.validator = ClientDataValidator()
        self.processed_clients = []
        self.processing_errors = []
    
    def load_from_excel(self, excel_path: Union[str, Path], 
                       sheet_name: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Load client data from Excel file.
        
        Args:
            excel_path: Path to Excel file
            sheet_name: Specific sheet to load (default: first sheet)
            
        Returns:
            List of client data dictionaries or None if error
        """
        try:
            path = Path(excel_path)
            if not path.exists():
                logger.error(f"Excel file not found: {excel_path}")
                return None
            
            logger.info(f"Loading client data from Excel: {excel_path}")
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(path)
            
            # Convert to list of dictionaries
            clients_data = []
            for index, row in df.iterrows():
                client_data = self._process_excel_row(row, index + 1)
                if client_data:
                    clients_data.append(client_data)
            
            logger.info(f"Successfully loaded {len(clients_data)} clients from Excel")
            return clients_data
            
        except Exception as e:
            logger.error(f"Error loading Excel file {excel_path}: {str(e)}")
            return None
    
    def load_from_json(self, json_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
        """
        Load client data from JSON file.
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            List of client data dictionaries or None if error
        """
        try:
            data = load_json_safe(json_path)
            if data is None:
                return None
            
            # Handle both single client and multiple clients
            if isinstance(data, dict):
                clients_data = [data]
            elif isinstance(data, list):
                clients_data = data
            else:
                logger.error(f"Invalid JSON structure in {json_path}")
                return None
            
            logger.info(f"Successfully loaded {len(clients_data)} clients from JSON")
            return clients_data
            
        except Exception as e:
            logger.error(f"Error loading JSON file {json_path}: {str(e)}")
            return None
    
    def _process_excel_row(self, row: pd.Series, row_number: int) -> Optional[Dict[str, Any]]:
        """
        Process a single Excel row into client data.
        
        Args:
            row: Pandas Series representing the row
            row_number: Row number for error reporting
            
        Returns:
            Processed client data dictionary or None if error
        """
        try:
            # Map Excel columns to standard field names
            field_mapping = {
                "ACN": "client_id",
                "GivenName": "given_name", 
                "FamilyName": "family_name",
                "BirthDate": "date_of_birth",
                "GenderCode": "gender",
                "AddressLine1": "address_line1",
                "AddressLine2": "address_line2", 
                "Suburb": "suburb",
                "Postcode": "postcode",
                "Phone": "phone",
                "Email": "email",
                "EmergencyContact": "emergency_contact",
                "EmergencyPhone": "emergency_phone",
                "ServicesRequired": "services_required",
                "CurrentAbilities": "current_abilities",
                "WellnessGoals": "wellness_goals"
            }
            
            client_data = {}
            
            # Process each field with cleaning
            for excel_col, standard_field in field_mapping.items():
                if excel_col in row.index:
                    value = self._clean_value(row[excel_col])
                    if value:  # Only add non-empty values
                        client_data[standard_field] = value
            
            # Combine address fields
            if any(field in client_data for field in ["address_line1", "suburb", "postcode"]):
                address_parts = []
                if "address_line1" in client_data:
                    address_parts.append(client_data["address_line1"])
                if "address_line2" in client_data:
                    address_parts.append(client_data["address_line2"])
                if "suburb" in client_data:
                    address_parts.append(client_data["suburb"])
                if "postcode" in client_data:
                    address_parts.append(str(client_data["postcode"]))
                
                client_data["address"] = ", ".join(address_parts)
            
            # Format date of birth
            if "date_of_birth" in client_data:
                client_data["date_of_birth"] = self._format_date(client_data["date_of_birth"])
            
            # Process services list
            if "services_required" in client_data:
                client_data["services_required"] = self._process_services_list(
                    client_data["services_required"]
                )
            
            # Add metadata
            client_data["processed_date"] = datetime.now().isoformat()
            client_data["source_row"] = row_number
            
            return client_data
            
        except Exception as e:
            logger.error(f"Error processing Excel row {row_number}: {str(e)}")
            return None
    
    def _clean_value(self, value: Any) -> Optional[str]:
        """
        Clean and validate a data value.
        
        Args:
            value: Raw value from data source
            
        Returns:
            Cleaned string value or None if empty/invalid
        """
        if pd.isna(value) or value is None:
            return None
        
        # Convert to string and clean
        str_value = str(value).strip()
        
        # Check for common "empty" values
        empty_values = ["", "nan", "null", "none", "n/a", "na", "-"]
        if str_value.lower() in empty_values:
            return None
        
        return str_value
    
    def _format_date(self, date_value: Any) -> Optional[str]:
        """
        Format date value to standard ISO format.
        
        Args:
            date_value: Date value in various formats
            
        Returns:
            ISO formatted date string or None if invalid
        """
        try:
            if isinstance(date_value, (datetime, pd.Timestamp)):
                return date_value.strftime("%Y-%m-%d")
            elif isinstance(date_value, date):
                return date_value.strftime("%Y-%m-%d")
            elif isinstance(date_value, str):
                # Try to parse various date formats
                date_formats = [
                    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", 
                    "%d-%m-%Y", "%Y/%m/%d"
                ]
                
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        return parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            
            logger.warning(f"Could not parse date: {date_value}")
            return None
            
        except Exception as e:
            logger.error(f"Error formatting date {date_value}: {str(e)}")
            return None
    
    def _process_services_list(self, services_value: Any) -> List[str]:
        """
        Process services into standardized list.
        
        Args:
            services_value: Services value in various formats
            
        Returns:
            List of standardized service names
        """
        try:
            if isinstance(services_value, list):
                services = services_value
            elif isinstance(services_value, str):
                # Split by common delimiters
                services = [s.strip() for s in services_value.split(",")]
            else:
                services = [str(services_value)]
            
            # Standardize service names
            service_mapping = {
                "da": "domestic_assistance",
                "domestic assistance": "domestic_assistance",
                "hm": "home_maintenance", 
                "home maintenance": "home_maintenance",
                "transport": "transport",
                "social": "social_support",
                "social support": "social_support",
                "nursing": "nursing",
                "personal care": "personal_care"
            }
            
            standardized_services = []
            for service in services:
                service_clean = service.lower().strip()
                standardized = service_mapping.get(service_clean, service_clean)
                if standardized and standardized not in standardized_services:
                    standardized_services.append(standardized)
            
            return standardized_services
            
        except Exception as e:
            logger.error(f"Error processing services list {services_value}: {str(e)}")
            return []
    
    def validate_client_data(self, client_data: Dict[str, Any], 
                           document_type: str) -> bool:
        """
        Validate client data for document generation.
        
        Args:
            client_data: Client data dictionary
            document_type: Type of document being generated
            
        Returns:
            True if validation passes, False otherwise
        """
        return self.validator.validate_client_data(client_data, document_type)
    
    def process_clients_for_document_type(self, clients_data: List[Dict[str, Any]],
                                        document_type: str) -> List[Dict[str, Any]]:
        """
        Process and validate multiple clients for specific document type.
        
        Args:
            clients_data: List of client data dictionaries
            document_type: Type of document being generated
            
        Returns:
            List of validated client data ready for document generation
        """
        processed_clients = []
        self.processing_errors.clear()
        
        logger.info(f"Processing {len(clients_data)} clients for {document_type}")
        
        for i, client_data in enumerate(clients_data):
            try:
                # Validate client data
                if self.validate_client_data(client_data, document_type):
                    # Add document-specific metadata
                    client_data["document_type"] = document_type
                    client_data["generation_date"] = datetime.now().isoformat()
                    
                    # Generate safe filename
                    client_id = client_data.get("client_id", f"client_{i}")
                    family_name = client_data.get("family_name", "unknown")
                    safe_filename = sanitize_filename(f"{client_id}_{family_name}_{document_type}")
                    client_data["safe_filename"] = safe_filename
                    
                    processed_clients.append(client_data)
                    
                    # Log successful processing
                    logger.audit_document_event(
                        event_type="data_processed",
                        client_id=client_data.get("client_id", "unknown"),
                        document_type=document_type,
                        metadata={"status": "validated", "fields_count": len(client_data)}
                    )
                else:
                    # Log validation failure
                    validation_summary = self.validator.get_validation_summary()
                    error_msg = f"Validation failed for client {i+1}: {validation_summary['errors']}"
                    self.processing_errors.append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                error_msg = f"Error processing client {i+1}: {str(e)}"
                self.processing_errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Successfully processed {len(processed_clients)} out of {len(clients_data)} clients")
        
        if self.processing_errors:
            logger.warning(f"Processing completed with {len(self.processing_errors)} errors")
        
        return processed_clients
    
    def save_processed_data(self, processed_clients: List[Dict[str, Any]], 
                          output_path: Union[str, Path]) -> bool:
        """
        Save processed client data to JSON file.
        
        Args:
            processed_clients: List of processed client data
            output_path: Path to save the JSON file
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Add processing metadata
            output_data = {
                "processed_date": datetime.now().isoformat(),
                "client_count": len(processed_clients),
                "clients": processed_clients
            }
            
            success = save_json_safe(output_data, output_path)
            
            if success:
                logger.info(f"Processed data saved to: {output_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving processed data: {str(e)}")
            return False
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get summary of processing results.
        
        Returns:
            Dictionary containing processing statistics
        """
        return {
            "clients_processed": len(self.processed_clients),
            "errors_count": len(self.processing_errors),
            "errors": self.processing_errors.copy(),
            "validation_summary": self.validator.get_validation_summary()
        }


def clean_client_data_value(value: Any) -> str:
    """
    Utility function to clean individual data values.
    
    Args:
        value: Raw data value
        
    Returns:
        Cleaned string value
    """
    processor = ClientDataProcessor()
    cleaned = processor._clean_value(value)
    return cleaned if cleaned is not None else ""


def format_client_name(given_name: str, family_name: str) -> str:
    """
    Format client name consistently.
    
    Args:
        given_name: Client's given name
        family_name: Client's family name
        
    Returns:
        Formatted full name
    """
    given = clean_client_data_value(given_name)
    family = clean_client_data_value(family_name)
    
    if given and family:
        return f"{given} {family}"
    elif family:
        return family
    elif given:
        return given
    else:
        return "Unknown"