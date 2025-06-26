# File: doc_gen/src/utils/logging_utils.py
"""
Logging utilities for document generation system.

Provides structured logging with audit trails for compliance requirements.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json


class DocumentAuditLogger:
    """
    Specialized logger for document generation audit trails.
    
    Provides structured logging for compliance and security monitoring.
    """
    
    def __init__(self, log_name: str = "doc_gen", log_level: str = "INFO"):
        self.log_name = log_name
        self.logger = logging.getLogger(log_name)
        self.setup_logging(log_level)
    
    def setup_logging(self, log_level: str) -> None:
        """
        Configure logging with audit trail requirements.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set logging level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        numeric_level = level_map.get(log_level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)
        
        # Create log directory
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # File handler for audit logs
        audit_log_file = log_dir / f"{self.log_name}_audit.log"
        file_handler = logging.FileHandler(audit_log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Structured formatter for audit trails
        audit_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Simple formatter for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(audit_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized for {self.log_name} at level {log_level}")
    
    def audit_document_event(self, event_type: str, client_id: str, 
                           document_type: str, metadata: Dict[str, Any]) -> None:
        """
        Log document-related events for compliance audit trails.
        
        Args:
            event_type: Type of event (created, modified, uploaded, accessed)
            client_id: Client identifier (should be obfuscated for PII protection)
            document_type: Type of document (care_plan, service_agreement, etc.)
            metadata: Additional event metadata
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "client_id": client_id,
            "document_type": document_type,
            "metadata": metadata
        }
        
        self.logger.info(f"AUDIT: {json.dumps(audit_entry)}")
    
    def audit_pii_event(self, event_type: str, session_id: str, 
                       data_fields: list, metadata: Dict[str, Any]) -> None:
        """
        Log PII handling events for privacy compliance.
        
        Args:
            event_type: Type of PII event (obfuscated, deobfuscated, cleared)
            session_id: Session identifier for tracking
            data_fields: List of data field types processed (not values)
            metadata: Additional event metadata
        """
        pii_audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": f"PII_{event_type}",
            "session_id": session_id,
            "data_fields": data_fields,
            "metadata": metadata
        }
        
        self.logger.info(f"PII_AUDIT: {json.dumps(pii_audit_entry)}")
    
    def audit_llm_event(self, event_type: str, session_id: str,
                       model: str, prompt_type: str, metadata: Dict[str, Any]) -> None:
        """
        Log LLM interactions for content generation audit trails.
        
        Args:
            event_type: Type of LLM event (prompt_sent, response_received, error)
            session_id: Session identifier for tracking
            model: LLM model used
            prompt_type: Type of prompt (goals, recommendations, etc.)
            metadata: Additional event metadata (no sensitive data)
        """
        llm_audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": f"LLM_{event_type}",
            "session_id": session_id,
            "model": model,
            "prompt_type": prompt_type,
            "metadata": metadata
        }
        
        self.logger.info(f"LLM_AUDIT: {json.dumps(llm_audit_entry)}")
    
    def audit_sharepoint_event(self, event_type: str, document_id: str,
                             sharepoint_path: str, metadata: Dict[str, Any]) -> None:
        """
        Log SharePoint operations for integration audit trails.
        
        Args:
            event_type: Type of SharePoint event (upload, update, error)
            document_id: Document identifier
            sharepoint_path: SharePoint folder path
            metadata: Additional event metadata
        """
        sharepoint_audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": f"SHAREPOINT_{event_type}",
            "document_id": document_id,
            "sharepoint_path": sharepoint_path,
            "metadata": metadata
        }
        
        self.logger.info(f"SHAREPOINT_AUDIT: {json.dumps(sharepoint_audit_entry)}")
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log error with optional structured data."""
        if extra_data:
            self.logger.error(f"{message} | Data: {json.dumps(extra_data)}")
        else:
            self.logger.error(message)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log warning with optional structured data."""
        if extra_data:
            self.logger.warning(f"{message} | Data: {json.dumps(extra_data)}")
        else:
            self.logger.warning(message)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log info with optional structured data."""
        if extra_data:
            self.logger.info(f"{message} | Data: {json.dumps(extra_data)}")
        else:
            self.logger.info(message)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log debug with optional structured data."""
        if extra_data:
            self.logger.debug(f"{message} | Data: {json.dumps(extra_data)}")
        else:
            self.logger.debug(message)


def setup_module_logging(module_name: str, log_level: str = "INFO") -> DocumentAuditLogger:
    """
    Set up logging for a module with audit capabilities.
    
    Args:
        module_name: Name of the module for log identification
        log_level: Desired logging level
        
    Returns:
        Configured DocumentAuditLogger instance
    """
    return DocumentAuditLogger(log_name=module_name, log_level=log_level)


def get_logger(name: str) -> DocumentAuditLogger:
    """
    Get or create a logger for the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        DocumentAuditLogger instance
    """
    return DocumentAuditLogger(log_name=name)