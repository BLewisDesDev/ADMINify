# File: doc_gen/tests/test_example_usage.py
"""
Example usage and integration tests for document generator.

Demonstrates how to use the document generation system.
"""

import json
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.document_generator import DocumentGenerator
from src.core.data_processor import ClientDataProcessor
from src.core.pii_obfuscator import PIIObfuscator
from src.utils.logging_utils import setup_module_logging

logger = setup_module_logging("test_example_usage", "INFO")


def create_sample_client_data():
    """Create comprehensive sample client data."""
    return {
        "client_id": "C123456",
        "given_name": "John",
        "family_name": "Smith", 
        "date_of_birth": "1980-05-15",
        "gender": "Male",
        "address": "123 Test Street, Sydney NSW 2000",
        "phone": "0412345678",
        "email": "john.smith@example.com",
        "emergency_contact": "Jane Smith",
        "emergency_phone": "0487654321",
        "services_required": ["domestic_assistance", "home_maintenance"],
        "current_abilities": "Independent with mobility, requires assistance with heavy cleaning and garden maintenance",
        "wellness_goals": ["Maintain independence at home", "Improve mobility and strength", "Social engagement"],
        "medical_conditions": ["Mild arthritis", "Diabetes Type 2"],
        "care_notes": "Client prefers morning appointments. Has friendly dog."
    }


def example_basic_document_generation():
    """Example of basic document generation."""
    logger.info("="*60)
    logger.info("EXAMPLE: Basic Document Generation")
    logger.info("="*60)
    
    try:
        # Create sample data
        client_data = create_sample_client_data()
        
        # Initialize document generator
        generator = DocumentGenerator()
        
        logger.info("Attempting to generate care plan document...")
        logger.info(f"Client: {client_data['given_name']} {client_data['family_name']} ({client_data['client_id']})")
        
        # Note: This will fail because no template exists yet, but shows the workflow
        result = generator.generate_document(
            document_type="care_plan",
            client_data=client_data,
            enable_pdf=False  # Disable PDF for testing
        )
        
        if result:
            logger.info("✓ Document generation successful!")
            logger.info(f"  DOCX: {result['docx_file']}")
            if result.get('pdf_file'):
                logger.info(f"  PDF: {result['pdf_file']}")
        else:
            logger.warning("✗ Document generation failed (expected - no template)")
            logger.info("  This is expected if no template file exists")
        
        # Show generation summary
        summary = generator.get_generation_summary()
        logger.info(f"Generation session: {summary['session_id']}")
        logger.info(f"Documents generated: {summary['documents_generated']}")
        
    except Exception as e:
        logger.error(f"Error in basic document generation: {str(e)}")


def example_data_processing_workflow():
    """Example of complete data processing workflow."""
    logger.info("="*60)
    logger.info("EXAMPLE: Data Processing Workflow")
    logger.info("="*60)
    
    try:
        # Create sample data list
        clients_data = [
            create_sample_client_data(),
            {
                "client_id": "C789012",
                "given_name": "Jane",
                "family_name": "Doe",
                "date_of_birth": "1975-08-22",
                "gender": "Female",
                "address": "456 Another Street, Melbourne VIC 3000",
                "phone": "0398765432",
                "email": "jane.doe@example.com",
                "services_required": ["transport", "social_support"],
                "current_abilities": "Good mobility, needs transport support",
                "wellness_goals": ["Increase social activities", "Maintain health"]
            }
        ]
        
        # Initialize processor
        processor = ClientDataProcessor()
        
        logger.info(f"Processing {len(clients_data)} clients for care plan generation...")
        
        # Process and validate clients
        processed_clients = processor.process_clients_for_document_type(
            clients_data, "care_plan"
        )
        
        logger.info(f"✓ Successfully processed {len(processed_clients)} clients")
        
        # Show processing summary
        summary = processor.get_processing_summary()
        logger.info(f"Processing summary:")
        logger.info(f"  - Clients processed: {summary['clients_processed']}")
        logger.info(f"  - Errors: {summary['errors_count']}")
        
        if summary['errors']:
            for error in summary['errors']:
                logger.warning(f"    Error: {error}")
        
        # Save processed data
        output_file = Path("processed_clients_example.json")
        success = processor.save_processed_data(processed_clients, output_file)
        
        if success:
            logger.info(f"✓ Processed data saved to: {output_file}")
            
            # Clean up example file
            if output_file.exists():
                output_file.unlink()
                logger.info("✓ Example file cleaned up")
        
    except Exception as e:
        logger.error(f"Error in data processing workflow: {str(e)}")


def example_pii_obfuscation():
    """Example of PII obfuscation system."""
    logger.info("="*60)
    logger.info("EXAMPLE: PII Obfuscation for LLM Processing")
    logger.info("="*60)
    
    try:
        # Create sample data with PII
        client_data = create_sample_client_data()
        
        logger.info("Original client data:")
        logger.info(f"  Name: {client_data['given_name']} {client_data['family_name']}")
        logger.info(f"  ID: {client_data['client_id']}")
        logger.info(f"  Phone: {client_data['phone']}")
        logger.info(f"  Address: {client_data['address']}")
        
        # Initialize obfuscator
        obfuscator = PIIObfuscator()
        
        # Create obfuscation session
        session_id = obfuscator.create_obfuscation_session(client_data)
        logger.info(f"✓ Created obfuscation session: {session_id}")
        
        # Obfuscate the data
        obfuscated_data = obfuscator.obfuscate_client_data(client_data, session_id)
        
        logger.info("Obfuscated data for LLM processing:")
        logger.info(f"  Name: {obfuscated_data.get('given_name')} {obfuscated_data.get('family_name')}")
        logger.info(f"  ID: {obfuscated_data.get('client_id')}")
        logger.info(f"  Phone: {obfuscated_data.get('phone')}")
        logger.info(f"  Address: {obfuscated_data.get('address')}")
        logger.info(f"  Date of Birth: {obfuscated_data.get('date_of_birth')}")
        
        # Simulate LLM-generated content with placeholders
        llm_content = """
        Care Goals for [GIVEN_NAME] [FAMILY_NAME]:
        
        1. Support [GIVEN_NAME] to maintain independence at [ADDRESS]
        2. Provide domestic assistance services twice weekly
        3. Coordinate with emergency contact at [EMERGENCY_PHONE]
        4. Regular review of progress with client [CLIENT_ID]
        """
        
        logger.info("Simulated LLM-generated content:")
        logger.info(llm_content)
        
        # Deobfuscate the content
        deobfuscated_content = obfuscator.deobfuscate_content(llm_content, session_id)
        
        logger.info("Content after deobfuscation:")
        logger.info(deobfuscated_content)
        
        # Get session info
        session_info = obfuscator.get_session_info(session_id)
        logger.info(f"Session info: {session_info['mappings_count']} PII mappings created")
        
        # Clean up session
        obfuscator.clear_session(session_id)
        logger.info("✓ Obfuscation session cleared")
        
    except Exception as e:
        logger.error(f"Error in PII obfuscation example: {str(e)}")


def example_cli_usage():
    """Show CLI usage examples."""
    logger.info("="*60)
    logger.info("EXAMPLE: CLI Usage Commands")
    logger.info("="*60)
    
    # Create example data file
    example_data = [create_sample_client_data()]
    example_file = Path("example_clients.json")
    
    try:
        with open(example_file, 'w') as f:
            json.dump(example_data, f, indent=2)
        
        logger.info("Example CLI commands:")
        logger.info("")
        logger.info("1. Generate care plan documents:")
        logger.info("   python -m src.main generate --type care_plan --input example_clients.json")
        logger.info("")
        logger.info("2. Generate with PDF output:")
        logger.info("   python -m src.main generate --type care_plan --input example_clients.json --pdf")
        logger.info("")
        logger.info("3. Validate client data:")
        logger.info("   python -m src.main validate --input example_clients.json --type care_plan")
        logger.info("")
        logger.info("4. List available templates:")
        logger.info("   python -m src.main list-templates")
        logger.info("")
        logger.info("5. Process Excel data:")
        logger.info("   python -m src.main generate --type service_agreement --input clients.xlsx --sheet 'Client Data'")
        logger.info("")
        
        logger.info(f"✓ Example data file created: {example_file}")
        logger.info("  You can use this file to test the CLI commands above")
        
    except Exception as e:
        logger.error(f"Error creating example CLI data: {str(e)}")
    finally:
        # Note: Leaving example file for actual CLI testing
        pass


def run_all_examples():
    """Run all example demonstrations."""
    logger.info("DOCUMENT GENERATOR - EXAMPLE USAGE DEMONSTRATIONS")
    logger.info("="*80)
    
    try:
        example_basic_document_generation()
        print()  # Add spacing between examples
        
        example_data_processing_workflow()
        print()
        
        example_pii_obfuscation()
        print()
        
        example_cli_usage()
        print()
        
        logger.info("="*80)
        logger.info("✓ All examples completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Add document templates to templates/ directories")
        logger.info("2. Install LibreOffice for PDF generation")
        logger.info("3. Configure .env file for LLM and SharePoint integration")
        logger.info("4. Test with real client data using the CLI")
        
    except Exception as e:
        logger.error(f"✗ Example demonstration error: {str(e)}")
        raise


if __name__ == "__main__":
    run_all_examples()