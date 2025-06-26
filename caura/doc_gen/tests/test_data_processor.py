# File: doc_gen/tests/test_data_processor.py
"""
Test suite for data processor module.

Manual testing framework for client data processing functionality.
"""

import json
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from doc_gen module
from src.core.data_processor import ClientDataProcessor, format_client_name
from src.utils.logging_utils import setup_module_logging

logger = setup_module_logging("test_data_processor", "INFO")


def create_test_client_data():
    """Create sample client data for testing."""
    return {
        "client_id": "C123456",
        "given_name": "John",
        "family_name": "Smith",
        "date_of_birth": "1980-05-15",
        "gender": "M",
        "address_line1": "123 Test Street",
        "suburb": "Sydney",
        "postcode": "2000",
        "phone": "0412345678",
        "email": "john.smith@example.com",
        "services_required": ["domestic_assistance", "home_maintenance"],
        "current_abilities": "Independent with mobility",
        "wellness_goals": "Maintain independence at home"
    }


def test_client_data_validation():
    """Test client data validation for different document types."""
    logger.info("Testing client data validation...")
    
    processor = ClientDataProcessor()
    test_data = create_test_client_data()
    
    # Test valid data
    logger.info("Testing valid client data:")
    for doc_type in ["care_plan", "service_agreement", "wellness_plan"]:
        is_valid = processor.validate_client_data(test_data, doc_type)
        logger.info(f"  {doc_type}: {'✓ VALID' if is_valid else '✗ INVALID'}")
        
        if not is_valid:
            summary = processor.validator.get_validation_summary()
            for error in summary["errors"]:
                logger.error(f"    Error: {error}")
    
    # Test invalid data
    logger.info("Testing invalid client data (missing required fields):")
    invalid_data = test_data.copy()
    del invalid_data["client_id"]
    del invalid_data["phone"]
    
    is_valid = processor.validate_client_data(invalid_data, "care_plan")
    logger.info(f"  Missing fields: {'✓ VALID' if is_valid else '✗ INVALID (expected)'}")
    
    if not is_valid:
        summary = processor.validator.get_validation_summary()
        logger.info(f"  Validation errors found: {summary['error_count']}")


def test_data_processing():
    """Test client data processing functionality."""
    logger.info("Testing client data processing...")
    
    processor = ClientDataProcessor()
    test_clients = [create_test_client_data()]
    
    # Add second client with different data
    client2 = create_test_client_data()
    client2.update({
        "client_id": "C789012",
        "given_name": "Jane",
        "family_name": "Doe",
        "services_required": ["transport", "social_support"]
    })
    test_clients.append(client2)
    
    # Process clients for care plan
    processed_clients = processor.process_clients_for_document_type(
        test_clients, "care_plan"
    )
    
    logger.info(f"Processed {len(processed_clients)} out of {len(test_clients)} clients")
    
    for client in processed_clients:
        logger.info(f"✓ Client {client['client_id']}: {client.get('safe_filename', 'no filename')}")


def test_name_formatting():
    """Test client name formatting."""
    logger.info("Testing client name formatting...")
    
    test_cases = [
        ("John", "Smith", "John Smith"),
        ("", "Smith", "Smith"),
        ("John", "", "John"),
        ("", "", "Unknown"),
        ("  John  ", "  Smith  ", "John Smith")
    ]
    
    for given, family, expected in test_cases:
        result = format_client_name(given, family)
        status = "✓" if result == expected else "✗"
        logger.info(f"  {status} '{given}' + '{family}' = '{result}' (expected: '{expected}')")


def test_json_save_load():
    """Test JSON save and load functionality."""
    logger.info("Testing JSON save/load...")
    
    processor = ClientDataProcessor()
    test_clients = [create_test_client_data()]
    
    # Process clients
    processed_clients = processor.process_clients_for_document_type(
        test_clients, "care_plan"
    )
    
    # Save to JSON
    test_output = Path("test_output.json")
    success = processor.save_processed_data(processed_clients, test_output)
    
    if success and test_output.exists():
        logger.info("✓ JSON save successful")
        
        # Try to load it back
        loaded_data = processor.load_from_json(test_output)
        if loaded_data:
            logger.info(f"✓ JSON load successful: {len(loaded_data)} clients loaded")
        else:
            logger.error("✗ JSON load failed")
        
        # Cleanup
        test_output.unlink()
    else:
        logger.error("✗ JSON save failed")


def run_all_tests():
    """Run all data processor tests."""
    logger.info("="*60)
    logger.info("DATA PROCESSOR TEST SUITE")
    logger.info("="*60)
    
    try:
        test_client_data_validation()
        logger.info("-" * 40)
        
        test_data_processing()
        logger.info("-" * 40)
        
        test_name_formatting()
        logger.info("-" * 40)
        
        test_json_save_load()
        logger.info("-" * 40)
        
        logger.info("✓ All data processor tests completed")
        
    except Exception as e:
        logger.error(f"✗ Test suite error: {str(e)}")
        raise


if __name__ == "__main__":
    run_all_tests()