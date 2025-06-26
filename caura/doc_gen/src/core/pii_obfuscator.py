# File: doc_gen/src/core/pii_obfuscator.py
"""
PII obfuscation system for secure LLM processing.

Provides reversible anonymization of personally identifiable information
while maintaining data structure for document generation.
"""

import secrets
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date
from cryptography.fernet import Fernet
import json
import base64

from ..utils.logging_utils import get_logger
from ..utils.file_utils import SecureFileManager

logger = get_logger(__name__)


class PIIObfuscator:
    """
    Secure PII obfuscation system for LLM processing.
    
    Provides reversible anonymization that protects client privacy
    while preserving data structure for AI content generation.
    """
    
    # PII field categories for different obfuscation strategies
    DIRECT_PII_FIELDS = [
        "given_name", "family_name", "full_name", "client_id",
        "address", "address_line1", "address_line2", "suburb",
        "phone", "emergency_phone", "contact_phone",
        "email", "emergency_email", "contact_email"
    ]
    
    QUASI_PII_FIELDS = [
        "date_of_birth", "postcode", "gender"
    ]
    
    SENSITIVE_FIELDS = [
        "medical_conditions", "disabilities", "medications",
        "emergency_contact", "next_of_kin", "care_notes"
    ]
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize PII obfuscator.
        
        Args:
            encryption_key: 32-byte encryption key for reversible obfuscation
        """
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.file_manager = SecureFileManager()
        
        # Session-based obfuscation mappings
        self.session_mappings: Dict[str, Dict[str, str]] = {}
        self.reverse_mappings: Dict[str, Dict[str, str]] = {}
        
        logger.info("PII Obfuscator initialized with secure encryption")
    
    def create_obfuscation_session(self, client_data: Dict[str, Any]) -> str:
        """
        Create a new obfuscation session for a client's data.
        
        Args:
            client_data: Client data dictionary to obfuscate
            
        Returns:
            Unique session ID for tracking obfuscation
        """
        # Generate unique session ID
        session_id = self._generate_session_id()
        
        # Initialize session mappings
        self.session_mappings[session_id] = {}
        self.reverse_mappings[session_id] = {}
        
        logger.info(f"Created obfuscation session: {session_id}")
        
        # Log PII processing event
        pii_fields = self._identify_pii_fields(client_data)
        logger.audit_pii_event(
            event_type="session_created",
            session_id=session_id,
            data_fields=pii_fields,
            metadata={"field_count": len(pii_fields)}
        )
        
        return session_id
    
    def obfuscate_client_data(self, client_data: Dict[str, Any], 
                            session_id: str) -> Dict[str, Any]:
        """
        Obfuscate client data for safe LLM processing.
        
        Args:
            client_data: Original client data
            session_id: Session ID for mapping tracking
            
        Returns:
            Obfuscated data safe for LLM processing
        """
        try:
            obfuscated_data = client_data.copy()
            
            # Obfuscate direct PII
            for field in self.DIRECT_PII_FIELDS:
                if field in obfuscated_data:
                    obfuscated_data[field] = self._obfuscate_direct_pii(
                        obfuscated_data[field], field, session_id
                    )
            
            # Obfuscate quasi-identifiers
            for field in self.QUASI_PII_FIELDS:
                if field in obfuscated_data:
                    obfuscated_data[field] = self._obfuscate_quasi_pii(
                        obfuscated_data[field], field, session_id
                    )
            
            # Obfuscate sensitive information
            for field in self.SENSITIVE_FIELDS:
                if field in obfuscated_data:
                    obfuscated_data[field] = self._obfuscate_sensitive_data(
                        obfuscated_data[field], field, session_id
                    )
            
            # Add obfuscation metadata
            obfuscated_data["_obfuscation_session"] = session_id
            obfuscated_data["_obfuscated_at"] = datetime.now().isoformat()
            obfuscated_data["_pii_protected"] = True
            
            # Log obfuscation event
            pii_fields = self._identify_pii_fields(client_data)
            logger.audit_pii_event(
                event_type="data_obfuscated",
                session_id=session_id,
                data_fields=pii_fields,
                metadata={"original_fields": len(client_data), "obfuscated_fields": len(pii_fields)}
            )
            
            logger.info(f"Client data obfuscated for session: {session_id}")
            return obfuscated_data
            
        except Exception as e:
            logger.error(f"Error obfuscating client data: {str(e)}")
            raise
    
    def deobfuscate_content(self, content: str, session_id: str) -> str:
        """
        Restore original PII in generated content.
        
        Args:
            content: Content with obfuscated placeholders
            session_id: Session ID for mapping lookup
            
        Returns:
            Content with original PII restored
        """
        try:
            if session_id not in self.reverse_mappings:
                logger.error(f"Session not found for deobfuscation: {session_id}")
                return content
            
            deobfuscated_content = content
            reverse_mapping = self.reverse_mappings[session_id]
            
            # Replace obfuscated placeholders with original values
            for placeholder, original_value in reverse_mapping.items():
                deobfuscated_content = deobfuscated_content.replace(placeholder, original_value)
            
            # Log deobfuscation event
            logger.audit_pii_event(
                event_type="content_deobfuscated",
                session_id=session_id,
                data_fields=list(reverse_mapping.keys()),
                metadata={"replacements_made": len(reverse_mapping)}
            )
            
            logger.info(f"Content deobfuscated for session: {session_id}")
            return deobfuscated_content
            
        except Exception as e:
            logger.error(f"Error deobfuscating content: {str(e)}")
            return content
    
    def _obfuscate_direct_pii(self, value: Any, field_name: str, session_id: str) -> str:
        """
        Obfuscate direct PII with structured placeholders.
        
        Args:
            value: Original value
            field_name: Name of the field
            session_id: Session ID
            
        Returns:
            Obfuscated placeholder
        """
        if not value or value == "":
            return ""
        
        # Generate meaningful placeholder based on field type
        if field_name in ["given_name", "family_name", "full_name"]:
            placeholder = self._generate_name_placeholder(field_name, session_id)
        elif field_name == "client_id":
            placeholder = self._generate_id_placeholder(session_id)
        elif "address" in field_name or field_name == "suburb":
            placeholder = self._generate_address_placeholder(field_name, session_id)
        elif "phone" in field_name:
            placeholder = self._generate_phone_placeholder(field_name, session_id)
        elif "email" in field_name:
            placeholder = self._generate_email_placeholder(field_name, session_id)
        else:
            placeholder = f"[{field_name.upper()}_DATA]"
        
        # Store mapping for reversal
        self._store_mapping(session_id, placeholder, str(value))
        
        return placeholder
    
    def _obfuscate_quasi_pii(self, value: Any, field_name: str, session_id: str) -> str:
        """
        Obfuscate quasi-identifiers with preserved structure.
        
        Args:
            value: Original value
            field_name: Name of the field
            session_id: Session ID
            
        Returns:
            Obfuscated value with preserved structure
        """
        if not value:
            return ""
        
        if field_name == "date_of_birth":
            return self._obfuscate_date_of_birth(value, session_id)
        elif field_name == "postcode":
            return self._obfuscate_postcode(value, session_id)
        elif field_name == "gender":
            return self._obfuscate_gender(value, session_id)
        else:
            placeholder = f"[{field_name.upper()}]"
            self._store_mapping(session_id, placeholder, str(value))
            return placeholder
    
    def _obfuscate_sensitive_data(self, value: Any, field_name: str, session_id: str) -> str:
        """
        Obfuscate sensitive medical/care information.
        
        Args:
            value: Original value
            field_name: Name of the field
            session_id: Session ID
            
        Returns:
            Obfuscated sensitive data
        """
        if not value:
            return ""
        
        if isinstance(value, list):
            # Handle lists of sensitive items
            obfuscated_items = []
            for i, item in enumerate(value):
                placeholder = f"[{field_name.upper()}_{i+1}]"
                self._store_mapping(session_id, placeholder, str(item))
                obfuscated_items.append(placeholder)
            return obfuscated_items
        else:
            placeholder = f"[{field_name.upper()}_INFO]"
            self._store_mapping(session_id, placeholder, str(value))
            return placeholder
    
    def _generate_name_placeholder(self, field_name: str, session_id: str) -> str:
        """Generate contextual name placeholder."""
        name_mapping = {
            "given_name": "GIVEN_NAME",
            "family_name": "FAMILY_NAME", 
            "full_name": "FULL_NAME"
        }
        return f"[{name_mapping.get(field_name, 'NAME')}]"
    
    def _generate_id_placeholder(self, session_id: str) -> str:
        """Generate client ID placeholder."""
        return "[CLIENT_ID]"
    
    def _generate_address_placeholder(self, field_name: str, session_id: str) -> str:
        """Generate address placeholder."""
        address_mapping = {
            "address": "ADDRESS",
            "address_line1": "ADDRESS_LINE_1",
            "address_line2": "ADDRESS_LINE_2",
            "suburb": "SUBURB"
        }
        return f"[{address_mapping.get(field_name, 'ADDRESS')}]"
    
    def _generate_phone_placeholder(self, field_name: str, session_id: str) -> str:
        """Generate phone placeholder."""
        phone_mapping = {
            "phone": "PHONE",
            "emergency_phone": "EMERGENCY_PHONE",
            "contact_phone": "CONTACT_PHONE"
        }
        return f"[{phone_mapping.get(field_name, 'PHONE')}]"
    
    def _generate_email_placeholder(self, field_name: str, session_id: str) -> str:
        """Generate email placeholder."""
        email_mapping = {
            "email": "EMAIL",
            "emergency_email": "EMERGENCY_EMAIL",
            "contact_email": "CONTACT_EMAIL"
        }
        return f"[{email_mapping.get(field_name, 'EMAIL')}]"
    
    def _obfuscate_date_of_birth(self, dob: Any, session_id: str) -> str:
        """
        Obfuscate date of birth while preserving age context.
        
        Args:
            dob: Date of birth
            session_id: Session ID
            
        Returns:
            Age range instead of specific date
        """
        try:
            # Parse date
            if isinstance(dob, str):
                birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
            elif isinstance(dob, (date, datetime)):
                birth_date = dob if isinstance(dob, date) else dob.date()
            else:
                return "[DATE_OF_BIRTH]"
            
            # Calculate age and return range
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            # Create age ranges for privacy
            if age < 25:
                age_range = "18-25"
            elif age < 35:
                age_range = "25-35"
            elif age < 50:
                age_range = "35-50"
            elif age < 65:
                age_range = "50-65"
            elif age < 75:
                age_range = "65-75"
            elif age < 85:
                age_range = "75-85"
            else:
                age_range = "85+"
            
            placeholder = f"[AGE_RANGE_{age_range}]"
            self._store_mapping(session_id, placeholder, str(dob))
            
            return placeholder
            
        except Exception as e:
            logger.error(f"Error obfuscating date of birth: {str(e)}")
            placeholder = "[DATE_OF_BIRTH]"
            self._store_mapping(session_id, placeholder, str(dob))
            return placeholder
    
    def _obfuscate_postcode(self, postcode: Any, session_id: str) -> str:
        """
        Obfuscate postcode while preserving location context.
        
        Args:
            postcode: Original postcode
            session_id: Session ID
            
        Returns:
            Generalized location
        """
        try:
            pc_str = str(postcode)
            
            # Australian postcode state mapping (simplified)
            if pc_str.startswith('1') or pc_str.startswith('2'):
                location = "[NSW_LOCATION]"
            elif pc_str.startswith('3'):
                location = "[VIC_LOCATION]"
            elif pc_str.startswith('4'):
                location = "[QLD_LOCATION]"
            elif pc_str.startswith('5'):
                location = "[SA_LOCATION]"
            elif pc_str.startswith('6'):
                location = "[WA_LOCATION]"
            elif pc_str.startswith('7'):
                location = "[TAS_LOCATION]"
            else:
                location = "[LOCATION]"
            
            self._store_mapping(session_id, location, pc_str)
            return location
            
        except Exception:
            placeholder = "[POSTCODE]"
            self._store_mapping(session_id, placeholder, str(postcode))
            return placeholder
    
    def _obfuscate_gender(self, gender: Any, session_id: str) -> str:
        """
        Obfuscate gender while preserving for care planning.
        
        Args:
            gender: Original gender
            session_id: Session ID
            
        Returns:
            Generalized gender category
        """
        gender_str = str(gender).lower()
        
        if gender_str in ['m', 'male', 'man']:
            placeholder = "[MALE]"
        elif gender_str in ['f', 'female', 'woman']:
            placeholder = "[FEMALE]"
        else:
            placeholder = "[GENDER]"
        
        self._store_mapping(session_id, placeholder, str(gender))
        return placeholder
    
    def _store_mapping(self, session_id: str, placeholder: str, original_value: str) -> None:
        """
        Store obfuscation mapping for later reversal.
        
        Args:
            session_id: Session ID
            placeholder: Obfuscated placeholder
            original_value: Original value
        """
        if session_id not in self.session_mappings:
            self.session_mappings[session_id] = {}
            self.reverse_mappings[session_id] = {}
        
        self.session_mappings[session_id][original_value] = placeholder
        self.reverse_mappings[session_id][placeholder] = original_value
    
    def _identify_pii_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Identify PII fields in data.
        
        Args:
            data: Data dictionary
            
        Returns:
            List of PII field names found
        """
        all_pii_fields = self.DIRECT_PII_FIELDS + self.QUASI_PII_FIELDS + self.SENSITIVE_FIELDS
        return [field for field in all_pii_fields if field in data]
    
    def _generate_session_id(self) -> str:
        """
        Generate unique session ID.
        
        Returns:
            Unique session identifier
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_bytes = secrets.token_hex(8)
        return f"pii_session_{timestamp}_{random_bytes}"
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear obfuscation session data securely.
        
        Args:
            session_id: Session ID to clear
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            # Remove mappings
            if session_id in self.session_mappings:
                del self.session_mappings[session_id]
            
            if session_id in self.reverse_mappings:
                del self.reverse_mappings[session_id]
            
            # Log session cleanup
            logger.audit_pii_event(
                event_type="session_cleared",
                session_id=session_id,
                data_fields=[],
                metadata={"status": "cleared"}
            )
            
            logger.info(f"Obfuscation session cleared: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {str(e)}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an obfuscation session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information dictionary or None if not found
        """
        if session_id not in self.session_mappings:
            return None
        
        return {
            "session_id": session_id,
            "mappings_count": len(self.session_mappings[session_id]),
            "pii_fields": list(self.reverse_mappings[session_id].keys()),
            "active": True
        }
    
    def cleanup_all_sessions(self) -> bool:
        """
        Clear all obfuscation sessions.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            session_count = len(self.session_mappings)
            
            self.session_mappings.clear()
            self.reverse_mappings.clear()
            
            logger.info(f"Cleared {session_count} obfuscation sessions")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all sessions: {str(e)}")
            return False