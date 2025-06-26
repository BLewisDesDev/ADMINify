# File: doc_gen/src/core/document_generator.py
"""
Document generator core module.

Handles template processing, document assembly, and PDF generation
for professional NDIS/aged care documents.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from docxtpl import DocxTemplate
import os

from ..utils.logging_utils import get_logger
from ..utils.file_utils import SecureFileManager, ensure_directory_structure
from ..utils.validation_utils import TemplateValidator, sanitize_filename, validate_document_metadata
from .data_processor import format_client_name

logger = get_logger(__name__)


class DocumentGenerator:
    """
    Professional document generation engine.
    
    Processes templates with client data to generate compliant
    NDIS/aged care documents with proper versioning.
    """
    
    # Supported document types
    DOCUMENT_TYPES = {
        "care_plan": {
            "name": "Personalised Care Plan",
            "template_prefix": "care_plan",
            "required_sections": ["client_info", "services", "goals"]
        },
        "service_agreement": {
            "name": "Service Agreement",
            "template_prefix": "service_agreement", 
            "required_sections": ["client_info", "services", "terms"]
        },
        "wellness_plan": {
            "name": "Wellness & Reablement Plan",
            "template_prefix": "wellness_plan",
            "required_sections": ["client_info", "wellness_goals", "interventions"]
        }
    }
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        Initialize document generator.
        
        Args:
            base_path: Base path for templates and output (default: module directory)
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).parent.parent.parent
        
        # Set up directory structure
        self.directories = ensure_directory_structure(self.base_path)
        
        # Initialize components
        self.file_manager = SecureFileManager()
        self.template_validator = TemplateValidator()
        
        # Document generation tracking
        self.generation_session = None
        self.generated_documents = []
        
        logger.info(f"DocumentGenerator initialized with base path: {self.base_path}")
    
    def generate_document(self, document_type: str, client_data: Dict[str, Any],
                         template_version: Optional[str] = None,
                         enable_pdf: bool = True,
                         custom_template: Optional[Union[str, Path]] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a document from template and client data.
        
        Args:
            document_type: Type of document to generate
            client_data: Client data dictionary
            template_version: Specific template version (default: latest)
            enable_pdf: Whether to generate PDF version
            custom_template: Path to custom template file
            
        Returns:
            Generation result dictionary or None if error
        """
        try:
            # Validate document type
            if document_type not in self.DOCUMENT_TYPES:
                logger.error(f"Unsupported document type: {document_type}")
                return None
            
            # Create generation session
            session_id = self._create_generation_session()
            
            # Load and validate template
            template_path = self._resolve_template_path(document_type, template_version, custom_template)
            if not template_path:
                return None
            
            template = self._load_template(template_path)
            if not template:
                return None
            
            # Prepare document context
            document_context = self._prepare_document_context(client_data, document_type)
            
            # Generate document metadata
            document_metadata = self._generate_document_metadata(
                client_data, document_type, template_version
            )
            
            # Generate DOCX document
            docx_result = self._generate_docx(template, document_context, document_metadata)
            if not docx_result:
                return None
            
            # Generate PDF if requested
            pdf_result = None
            if enable_pdf:
                pdf_result = self._generate_pdf(docx_result["file_path"])
            
            # Prepare result
            result = {
                "session_id": session_id,
                "document_type": document_type,
                "client_id": client_data.get("client_id", "unknown"),
                "generation_date": datetime.now().isoformat(),
                "docx_file": docx_result["file_path"],
                "pdf_file": pdf_result["file_path"] if pdf_result else None,
                "metadata": document_metadata,
                "template_used": str(template_path)
            }
            
            # Track generated document
            self.generated_documents.append(result)
            
            # Log generation event
            logger.audit_document_event(
                event_type="document_generated",
                client_id=client_data.get("client_id", "unknown"),
                document_type=document_type,
                metadata={
                    "session_id": session_id,
                    "template_version": template_version,
                    "pdf_generated": enable_pdf,
                    "file_size_docx": docx_result.get("file_size", 0),
                    "file_size_pdf": pdf_result.get("file_size", 0) if pdf_result else 0
                }
            )
            
            logger.info(f"Document generated successfully: {result['docx_file']}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}")
            return None
    
    def _resolve_template_path(self, document_type: str, template_version: Optional[str],
                              custom_template: Optional[Union[str, Path]]) -> Optional[Path]:
        """
        Resolve template file path.
        
        Args:
            document_type: Type of document
            template_version: Template version
            custom_template: Custom template path
            
        Returns:
            Path to template file or None if not found
        """
        try:
            if custom_template:
                template_path = Path(custom_template)
                if template_path.exists():
                    return template_path
                else:
                    logger.error(f"Custom template not found: {custom_template}")
                    return None
            
            # Look for template in standard location
            doc_type_info = self.DOCUMENT_TYPES[document_type]
            template_prefix = doc_type_info["template_prefix"]
            
            # Template directory for document type
            template_dir = self.directories["templates"] / document_type
            
            if template_version:
                # Look for specific version
                template_name = f"{template_prefix}_{template_version}.docx"
            else:
                # Look for latest version
                template_name = f"{template_prefix}_latest.docx"
                
                # If latest doesn't exist, look for any template
                if not (template_dir / template_name).exists():
                    template_files = list(template_dir.glob(f"{template_prefix}*.docx"))
                    if template_files:
                        # Use the most recently modified template
                        template_path = max(template_files, key=os.path.getmtime)
                        logger.info(f"Using template: {template_path}")
                        return template_path
            
            template_path = template_dir / template_name
            
            if template_path.exists():
                return template_path
            else:
                logger.error(f"Template not found: {template_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error resolving template path: {str(e)}")
            return None
    
    def _load_template(self, template_path: Path) -> Optional[DocxTemplate]:
        """
        Load and validate document template.
        
        Args:
            template_path: Path to template file
            
        Returns:
            Loaded DocxTemplate or None if error
        """
        try:
            # Validate template file
            if not self.template_validator.validate_template(template_path):
                errors = self.template_validator.get_validation_errors()
                logger.error(f"Template validation failed: {errors}")
                return None
            
            # Load template
            template = DocxTemplate(template_path)
            logger.info(f"Template loaded successfully: {template_path}")
            
            return template
            
        except Exception as e:
            logger.error(f"Error loading template {template_path}: {str(e)}")
            return None
    
    def _prepare_document_context(self, client_data: Dict[str, Any], 
                                 document_type: str) -> Dict[str, Any]:
        """
        Prepare context data for template rendering.
        
        Args:
            client_data: Client data dictionary
            document_type: Type of document
            
        Returns:
            Template context dictionary
        """
        try:
            # Base context with client data
            context = client_data.copy()
            
            # Add document-specific formatting
            context["client_full_name"] = format_client_name(
                client_data.get("given_name", ""),
                client_data.get("family_name", "")
            )
            
            # Format dates
            context["today_date"] = datetime.now().strftime("%d %B %Y")
            context["generation_date"] = datetime.now().strftime("%d/%m/%Y")
            
            # Document type specific context
            if document_type == "care_plan":
                context = self._prepare_care_plan_context(context)
            elif document_type == "service_agreement":
                context = self._prepare_service_agreement_context(context)
            elif document_type == "wellness_plan":
                context = self._prepare_wellness_plan_context(context)
            
            logger.debug(f"Document context prepared for {document_type}")
            return context
            
        except Exception as e:
            logger.error(f"Error preparing document context: {str(e)}")
            return client_data
    
    def _prepare_care_plan_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare care plan specific context.
        
        Args:
            context: Base context dictionary
            
        Returns:
            Enhanced context for care plan
        """
        # Format services list
        if "services_required" in context and isinstance(context["services_required"], list):
            service_names = {
                "domestic_assistance": "Domestic Assistance",
                "home_maintenance": "Home Maintenance",
                "transport": "Transport Services",
                "social_support": "Social Support",
                "nursing": "Nursing Services",
                "personal_care": "Personal Care"
            }
            
            formatted_services = []
            for service in context["services_required"]:
                service_name = service_names.get(service, service.replace("_", " ").title())
                formatted_services.append(service_name)
            
            context["services_list"] = ", ".join(formatted_services)
            context["primary_service"] = formatted_services[0] if formatted_services else "Support Services"
        
        # Add care plan specific fields
        context["plan_period"] = "6 months"
        context["review_date"] = self._calculate_review_date(6)  # 6 months from now
        
        return context
    
    def _prepare_service_agreement_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare service agreement specific context.
        
        Args:
            context: Base context dictionary
            
        Returns:
            Enhanced context for service agreement
        """
        # Add service agreement specific fields
        context["agreement_start_date"] = context.get("start_date", datetime.now().strftime("%d/%m/%Y"))
        context["caura_abn"] = "12 345 678 901"  # Replace with actual ABN
        context["caura_address"] = "123 Care Street, Sydney NSW 2000"  # Replace with actual address
        
        return context
    
    def _prepare_wellness_plan_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare wellness plan specific context.
        
        Args:
            context: Base context dictionary
            
        Returns:
            Enhanced context for wellness plan
        """
        # Add wellness plan specific fields
        context["plan_duration"] = "12 weeks"
        context["review_frequency"] = "fortnightly"
        context["next_review_date"] = self._calculate_review_date(2)  # 2 weeks from now
        
        return context
    
    def _calculate_review_date(self, weeks: int) -> str:
        """
        Calculate review date from current date.
        
        Args:
            weeks: Number of weeks from now
            
        Returns:
            Formatted review date string
        """
        from datetime import timedelta
        review_date = datetime.now() + timedelta(weeks=weeks)
        return review_date.strftime("%d/%m/%Y")
    
    def _generate_document_metadata(self, client_data: Dict[str, Any], 
                                   document_type: str, template_version: Optional[str]) -> Dict[str, Any]:
        """
        Generate document metadata.
        
        Args:
            client_data: Client data
            document_type: Document type
            template_version: Template version
            
        Returns:
            Document metadata dictionary
        """
        # Generate unique document ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_id = client_data.get("client_id", "unknown")
        document_id = f"{document_type}_{client_id}_{timestamp}"
        
        metadata = {
            "document_id": document_id,
            "document_type": document_type,
            "client_id": client_id,
            "version": "1.0.0",  # Start with version 1.0.0
            "created_date": datetime.now().isoformat(),
            "created_by": "doc_gen_system",
            "template_version": template_version or "latest",
            "compliance_standard": "NDIS_2025",
            "pii_obfuscated": False,  # Set by PII system if used
            "generation_source": "automated"
        }
        
        return metadata
    
    def _generate_docx(self, template: DocxTemplate, context: Dict[str, Any],
                      metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate DOCX document from template.
        
        Args:
            template: Loaded template
            context: Template context
            metadata: Document metadata
            
        Returns:
            Generation result or None if error
        """
        try:
            # Render template with context
            template.render(context)
            
            # Generate filename
            client_id = metadata["client_id"]
            document_type = metadata["document_type"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = sanitize_filename(f"{document_type}_{client_id}_{timestamp}.docx")
            
            # Output path
            output_path = self.directories["output_docx"] / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save document
            template.save(output_path)
            
            # Get file size
            file_size = output_path.stat().st_size
            
            result = {
                "file_path": str(output_path),
                "filename": filename,
                "file_size": file_size,
                "format": "docx"
            }
            
            logger.info(f"DOCX document generated: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating DOCX document: {str(e)}")
            return None
    
    def _generate_pdf(self, docx_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Generate PDF from DOCX file using LibreOffice.
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            PDF generation result or None if error
        """
        try:
            docx_file = Path(docx_path)
            if not docx_file.exists():
                logger.error(f"DOCX file not found: {docx_path}")
                return None
            
            # PDF output path
            pdf_filename = docx_file.stem + ".pdf"
            pdf_output_path = self.directories["output_pdf"] / pdf_filename
            pdf_output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # LibreOffice conversion command
            output_dir = str(self.directories["output_pdf"])
            cmd = [
                'soffice',
                '--headless',
                '--convert-to', 'pdf:writer_pdf_Export',
                '--outdir', output_dir,
                str(docx_file)
            ]
            
            logger.info(f"Converting to PDF: {' '.join(cmd)}")
            
            # Run conversion
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if process.returncode != 0:
                logger.error(f"PDF conversion failed: {process.stderr}")
                return None
            
            # Check if PDF was created
            if not pdf_output_path.exists():
                logger.error(f"PDF file not created: {pdf_output_path}")
                return None
            
            # Get file size
            file_size = pdf_output_path.stat().st_size
            
            result = {
                "file_path": str(pdf_output_path),
                "filename": pdf_filename,
                "file_size": file_size,
                "format": "pdf"
            }
            
            logger.info(f"PDF document generated: {pdf_output_path}")
            return result
            
        except subprocess.TimeoutExpired:
            logger.error("PDF conversion timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def _create_generation_session(self) -> str:
        """
        Create a document generation session.
        
        Returns:
            Unique session ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import secrets
        session_id = f"doc_gen_{timestamp}_{secrets.token_hex(6)}"
        self.generation_session = session_id
        
        logger.info(f"Document generation session created: {session_id}")
        return session_id
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """
        Get summary of document generation session.
        
        Returns:
            Generation summary dictionary
        """
        return {
            "session_id": self.generation_session,
            "documents_generated": len(self.generated_documents),
            "generated_documents": self.generated_documents.copy(),
            "base_path": str(self.base_path),
            "supported_types": list(self.DOCUMENT_TYPES.keys())
        }
    
    def cleanup_session(self) -> bool:
        """
        Clean up generation session data.
        
        Returns:
            True if cleanup successful
        """
        try:
            self.generated_documents.clear()
            self.generation_session = None
            
            logger.info("Document generation session cleaned up")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up session: {str(e)}")
            return False