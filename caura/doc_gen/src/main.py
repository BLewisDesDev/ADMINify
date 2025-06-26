# File: doc_gen/src/main.py
"""
Document Generator CLI Entry Point

Command-line interface for professional document generation system.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from .core.document_generator import DocumentGenerator
from .core.data_processor import ClientDataProcessor
from .core.pii_obfuscator import PIIObfuscator
from .utils.logging_utils import setup_module_logging
from .utils.file_utils import load_json_safe, save_json_safe

# Initialize logger
logger = setup_module_logging("doc_gen_cli")


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Professional Document Generator for NDIS/Aged Care",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate care plan from JSON data
  python -m src.main generate --type care_plan --input client_data.json

  # Generate multiple documents with PDF output
  python -m src.main generate --type service_agreement --input clients.json --pdf

  # Process Excel file and generate care plans
  python -m src.main generate --type care_plan --input clients.xlsx --sheet "Client Data"

  # Generate with custom template
  python -m src.main generate --type care_plan --input data.json --template custom_care_plan.docx

  # List available templates
  python -m src.main list-templates

  # Validate client data
  python -m src.main validate --input client_data.json --type care_plan
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate documents")
    generate_parser.add_argument(
        "--type", 
        required=True,
        choices=["care_plan", "service_agreement", "wellness_plan"],
        help="Type of document to generate"
    )
    generate_parser.add_argument(
        "--input", 
        required=True,
        help="Input file (JSON or Excel) containing client data"
    )
    generate_parser.add_argument(
        "--output", 
        help="Output directory (default: output/)"
    )
    generate_parser.add_argument(
        "--template", 
        help="Custom template file path"
    )
    generate_parser.add_argument(
        "--template-version", 
        help="Specific template version to use"
    )
    generate_parser.add_argument(
        "--sheet", 
        help="Excel sheet name (for Excel input files)"
    )
    generate_parser.add_argument(
        "--pdf", 
        action="store_true",
        help="Generate PDF versions of documents"
    )
    generate_parser.add_argument(
        "--enable-llm", 
        action="store_true",
        help="Enable LLM content generation (requires PII obfuscation)"
    )
    generate_parser.add_argument(
        "--client-id", 
        help="Generate document for specific client ID only"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate client data")
    validate_parser.add_argument(
        "--input", 
        required=True,
        help="Input file containing client data"
    )
    validate_parser.add_argument(
        "--type", 
        required=True,
        choices=["care_plan", "service_agreement", "wellness_plan"],
        help="Document type for validation context"
    )
    validate_parser.add_argument(
        "--sheet", 
        help="Excel sheet name (for Excel input files)"
    )
    
    # List templates command
    list_parser = subparsers.add_parser("list-templates", help="List available templates")
    list_parser.add_argument(
        "--type", 
        choices=["care_plan", "service_agreement", "wellness_plan"],
        help="Filter by document type"
    )
    
    # Process data command
    process_parser = subparsers.add_parser("process-data", help="Process and validate client data")
    process_parser.add_argument(
        "--input", 
        required=True,
        help="Input file (Excel or JSON)"
    )
    process_parser.add_argument(
        "--output", 
        required=True,
        help="Output JSON file for processed data"
    )
    process_parser.add_argument(
        "--sheet", 
        help="Excel sheet name"
    )
    
    # Global options
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    parser.add_argument(
        "--config", 
        help="Configuration file path"
    )
    
    return parser


def load_client_data(input_path: str, sheet_name: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Load client data from input file.
    
    Args:
        input_path: Path to input file
        sheet_name: Excel sheet name (if applicable)
        
    Returns:
        List of client data dictionaries or None if error
    """
    try:
        input_file = Path(input_path)
        
        if not input_file.exists():
            logger.error(f"Input file not found: {input_path}")
            return None
        
        processor = ClientDataProcessor()
        
        if input_file.suffix.lower() in ['.xlsx', '.xls']:
            # Load from Excel
            clients_data = processor.load_from_excel(input_path, sheet_name)
        elif input_file.suffix.lower() == '.json':
            # Load from JSON
            clients_data = processor.load_from_json(input_path)
        else:
            logger.error(f"Unsupported file format: {input_file.suffix}")
            return None
        
        if clients_data:
            logger.info(f"Loaded {len(clients_data)} clients from {input_path}")
        
        return clients_data
        
    except Exception as e:
        logger.error(f"Error loading client data: {str(e)}")
        return None


def generate_documents(args) -> bool:
    """
    Generate documents based on command arguments.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        True if generation successful, False otherwise
    """
    try:
        # Load client data
        clients_data = load_client_data(args.input, args.sheet)
        if not clients_data:
            return False
        
        # Filter by client ID if specified
        if args.client_id:
            clients_data = [
                client for client in clients_data 
                if client.get("client_id") == args.client_id
            ]
            if not clients_data:
                logger.error(f"Client ID not found: {args.client_id}")
                return False
        
        # Initialize document generator
        generator = DocumentGenerator()
        
        # Process clients for document type
        processor = ClientDataProcessor()
        processed_clients = processor.process_clients_for_document_type(
            clients_data, args.type
        )
        
        if not processed_clients:
            logger.error("No valid clients to process")
            return False
        
        # Generate documents for each client
        successful_generations = 0
        total_clients = len(processed_clients)
        
        logger.info(f"Generating {args.type} documents for {total_clients} clients")
        
        for i, client_data in enumerate(processed_clients, 1):
            try:
                logger.info(f"Processing client {i}/{total_clients}: {client_data.get('client_id', 'unknown')}")
                
                # Generate document
                result = generator.generate_document(
                    document_type=args.type,
                    client_data=client_data,
                    template_version=args.template_version,
                    enable_pdf=args.pdf,
                    custom_template=args.template
                )
                
                if result:
                    successful_generations += 1
                    logger.info(f"✓ Generated: {result['docx_file']}")
                    if result.get('pdf_file'):
                        logger.info(f"✓ PDF: {result['pdf_file']}")
                else:
                    logger.error(f"✗ Failed to generate document for client {client_data.get('client_id', 'unknown')}")
                    
            except Exception as e:
                logger.error(f"Error processing client {client_data.get('client_id', 'unknown')}: {str(e)}")
        
        # Report results
        logger.info(f"Document generation completed: {successful_generations}/{total_clients} successful")
        
        if successful_generations > 0:
            generation_summary = generator.get_generation_summary()
            logger.info(f"Generated documents saved to: {generator.directories['output']}")
            
            # Save generation summary
            summary_path = generator.directories["output"] / f"generation_summary_{args.type}.json"
            save_json_safe(generation_summary, summary_path)
            logger.info(f"Generation summary saved: {summary_path}")
        
        return successful_generations > 0
        
    except Exception as e:
        logger.error(f"Error in document generation: {str(e)}")
        return False


def validate_data(args) -> bool:
    """
    Validate client data without generating documents.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        True if validation successful, False otherwise
    """
    try:
        # Load client data
        clients_data = load_client_data(args.input, args.sheet)
        if not clients_data:
            return False
        
        # Process and validate clients
        processor = ClientDataProcessor()
        processed_clients = processor.process_clients_for_document_type(
            clients_data, args.type
        )
        
        # Report validation results
        total_clients = len(clients_data)
        valid_clients = len(processed_clients)
        
        logger.info(f"Validation completed: {valid_clients}/{total_clients} clients valid for {args.type}")
        
        # Get detailed validation summary
        validation_summary = processor.get_processing_summary()
        
        if validation_summary["errors_count"] > 0:
            logger.warning(f"Validation errors found:")
            for error in validation_summary["errors"]:
                logger.warning(f"  - {error}")
        
        return valid_clients > 0
        
    except Exception as e:
        logger.error(f"Error in data validation: {str(e)}")
        return False


def list_templates(args) -> bool:
    """
    List available document templates.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        True if listing successful, False otherwise
    """
    try:
        generator = DocumentGenerator()
        
        # Get templates directory
        templates_dir = generator.directories["templates"]
        
        if args.type:
            # List templates for specific type
            type_dir = templates_dir / args.type
            if type_dir.exists():
                templates = list(type_dir.glob("*.docx"))
                logger.info(f"Templates for {args.type}:")
                for template in sorted(templates):
                    logger.info(f"  - {template.name}")
            else:
                logger.warning(f"No templates directory found for {args.type}")
        else:
            # List all templates
            logger.info("Available templates:")
            for doc_type in generator.DOCUMENT_TYPES.keys():
                type_dir = templates_dir / doc_type
                if type_dir.exists():
                    templates = list(type_dir.glob("*.docx"))
                    logger.info(f"  {doc_type}:")
                    for template in sorted(templates):
                        logger.info(f"    - {template.name}")
                else:
                    logger.info(f"  {doc_type}: No templates found")
        
        return True
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        return False


def process_data_only(args) -> bool:
    """
    Process and save client data without generating documents.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        True if processing successful, False otherwise
    """
    try:
        # Load client data
        clients_data = load_client_data(args.input, args.sheet)
        if not clients_data:
            return False
        
        # Process data
        processor = ClientDataProcessor()
        
        # Save processed data
        success = processor.save_processed_data(clients_data, args.output)
        
        if success:
            logger.info(f"Processed data saved to: {args.output}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return False


def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Set up logging
        global logger
        logger = setup_module_logging("doc_gen_cli", args.log_level)
        
        # Handle commands
        if args.command == "generate":
            success = generate_documents(args)
        elif args.command == "validate":
            success = validate_data(args)
        elif args.command == "list-templates":
            success = list_templates(args)
        elif args.command == "process-data":
            success = process_data_only(args)
        else:
            parser.print_help()
            return 1
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())