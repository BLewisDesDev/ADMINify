"""
Document Generator Module

Professional document generation system for NDIS/aged care compliance.

This module provides:
- Automated document generation from templates
- PII protection and obfuscation
- LLM-assisted content creation
- SharePoint integration for automated filing
- Document versioning and audit trails

Author: Byron Lewis
Created: 2025-06-26
"""

__version__ = "1.0.0"
__author__ = "Byron Lewis"

# Core imports for external use
from .core.document_generator import DocumentGenerator
from .core.pii_obfuscator import PIIObfuscator
# Note: SharePointConnector will be added in Phase 2

__all__ = [
    "DocumentGenerator",
    "PIIObfuscator"
]