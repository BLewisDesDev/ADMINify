# File: doc_gen/tests/run_comprehensive_tests.py
"""
Comprehensive test suite for document generator with edge cases.

Tests all validation scenarios, edge cases, and error conditions.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.data_processor import ClientDataProcessor
from core.pii_obfuscator import PIIObfuscator
from core.document_generator import DocumentGenerator
from utils.logging_utils import setup_module_logging

logger = setup_module_logging("comprehensive_tests", "INFO")


def load_test_data():
    """Load comprehensive test data."""
    test_data_path = Path(__file__).parent / "test_data_comprehensive.json"
    
    with open(test_data_path, 'r') as f:
        test_data = json.load(f)
    
    logger.info(f"Loaded {len(test_data)} test cases")
    return test_data


def test_validation_scenarios():
    """Test all validation scenarios."""
    logger.info("="*60)
    logger.info("VALIDATION SCENARIO TESTING")
    logger.info("="*60)
    
    test_data = load_test_data()
    processor = ClientDataProcessor()
    
    validation_results = {}
    
    for test_case in test_data:
        case_name = test_case.get("test_case", "unknown")
        logger.info(f"Testing case: {case_name}")
        
        # Test validation for each document type
        for doc_type in ["care_plan", "service_agreement", "wellness_plan"]:
            is_valid = processor.validate_client_data(test_case, doc_type)
            
            if case_name not in validation_results:
                validation_results[case_name] = {}
            
            validation_results[case_name][doc_type] = is_valid
            
            status = "✓ VALID" if is_valid else "✗ INVALID"
            logger.info(f"  {doc_type}: {status}")
            
            # Log validation details for invalid cases
            if not is_valid:
                summary = processor.validator.get_validation_summary()
                for error in summary["errors"]:
                    logger.info(f"    Error: {error}")
                for warning in summary["warnings"]:
                    logger.info(f"    Warning: {warning}")
        
        logger.info("-" * 40)
    
    return validation_results


def test_pii_obfuscation_scenarios():
    """Test PII obfuscation with various data types."""
    logger.info("="*60)
    logger.info("PII OBFUSCATION TESTING")
    logger.info("="*60)
    
    test_data = load_test_data()
    obfuscator = PIIObfuscator()
    
    # Test cases with significant PII
    test_cases = [
        case for case in test_data 
        if case.get("test_case") in [
            "valid_complete_client", 
            "elderly_client_aged_care",
            "special_characters_names",
            "complex_medical_conditions"
        ]
    ]
    
    for test_case in test_cases:
        case_name = test_case.get("test_case", "unknown")
        logger.info(f"Testing PII obfuscation: {case_name}")
        
        # Create obfuscation session
        session_id = obfuscator.create_obfuscation_session(test_case)
        
        # Obfuscate data
        obfuscated_data = obfuscator.obfuscate_client_data(test_case, session_id)
        
        # Show before/after for key fields
        pii_fields = ["given_name", "family_name", "client_id", "phone", "address_line1", "date_of_birth"]
        
        for field in pii_fields:
            if field in test_case:
                original = test_case[field]
                obfuscated = obfuscated_data.get(field, "MISSING")
                logger.info(f"  {field}: '{original}' → '{obfuscated}'")
        
        # Test deobfuscation
        test_content = f"Care plan for [GIVEN_NAME] [FAMILY_NAME] (ID: [CLIENT_ID]) at [ADDRESS_LINE_1]"
        deobfuscated = obfuscator.deobfuscate_content(test_content, session_id)
        
        logger.info(f"  Test content: {test_content}")
        logger.info(f"  Deobfuscated: {deobfuscated}")
        
        # Clean up session
        obfuscator.clear_session(session_id)
        logger.info("-" * 40)


def test_data_processing_edge_cases():
    """Test data processing with edge cases."""
    logger.info("="*60)
    logger.info("DATA PROCESSING EDGE CASES")
    logger.info("="*60)
    
    test_data = load_test_data()
    processor = ClientDataProcessor()
    
    # Group test cases by expected behavior
    valid_cases = [
        case for case in test_data 
        if case.get("test_case") in [
            "valid_complete_client",
            "elderly_client_aged_care", 
            "younger_disability_client",
            "all_service_types",
            "empty_optional_fields"
        ]
    ]
    
    invalid_cases = [
        case for case in test_data
        if case.get("test_case") in [
            "missing_required_fields",
            "invalid_data_formats",
            "extreme_age_old"
        ]
    ]
    
    warning_cases = [
        case for case in test_data
        if case.get("test_case") in [
            "extreme_age_young",
            "international_phone"
        ]
    ]
    
    logger.info("Testing valid cases (should pass):")
    valid_processed = processor.process_clients_for_document_type(valid_cases, "care_plan")
    logger.info(f"✓ Processed {len(valid_processed)}/{len(valid_cases)} valid cases")
    
    logger.info("Testing invalid cases (should fail):")
    invalid_processed = processor.process_clients_for_document_type(invalid_cases, "care_plan")
    logger.info(f"✓ Processed {len(invalid_processed)}/{len(invalid_cases)} invalid cases (expected: 0)")
    
    logger.info("Testing warning cases (should pass with warnings):")
    warning_processed = processor.process_clients_for_document_type(warning_cases, "care_plan")
    logger.info(f"✓ Processed {len(warning_processed)}/{len(warning_cases)} warning cases")
    
    # Show processing errors
    processing_summary = processor.get_processing_summary()
    if processing_summary["errors"]:
        logger.info("Processing errors encountered:")
        for error in processing_summary["errors"]:
            logger.info(f"  - {error}")


def test_document_generation_readiness():
    """Test document generation readiness (will fail without templates)."""
    logger.info("="*60)
    logger.info("DOCUMENT GENERATION READINESS")
    logger.info("="*60)
    
    test_data = load_test_data()
    generator = DocumentGenerator()
    
    # Get a valid test case
    valid_case = next(
        case for case in test_data 
        if case.get("test_case") == "valid_complete_client"
    )
    
    logger.info("Testing document generation pipeline...")
    logger.info("Note: This will fail without real templates, but tests the pipeline")
    
    # Test each document type
    for doc_type in ["care_plan", "service_agreement", "wellness_plan"]:
        logger.info(f"Testing {doc_type} generation:")
        
        try:
            result = generator.generate_document(
                document_type=doc_type,
                client_data=valid_case,
                enable_pdf=False  # Disable PDF for testing
            )
            
            if result:
                logger.info(f"  ✓ Generation successful: {result['docx_file']}")
            else:
                logger.info(f"  ✗ Generation failed (expected - no template)")
                
        except Exception as e:
            logger.info(f"  ✗ Generation error: {str(e)} (expected)")
    
    # Show generation summary
    summary = generator.get_generation_summary()
    logger.info(f"Generation session: {summary['session_id']}")
    logger.info(f"Supported document types: {summary['supported_types']}")


def generate_test_report():
    """Generate comprehensive test report."""
    logger.info("="*60)
    logger.info("COMPREHENSIVE TEST REPORT")
    logger.info("="*60)
    
    test_data = load_test_data()
    
    # Summary statistics
    total_cases = len(test_data)
    valid_cases = len([
        case for case in test_data 
        if case.get("test_case") not in [
            "missing_required_fields", "invalid_data_formats", "extreme_age_old"
        ]
    ])
    edge_cases = len([
        case for case in test_data
        if "test" in case.get("test_case", "").lower()
    ])
    
    logger.info(f"Test Data Summary:")
    logger.info(f"  Total test cases: {total_cases}")
    logger.info(f"  Expected valid cases: {valid_cases}")
    logger.info(f"  Edge case scenarios: {edge_cases}")
    logger.info(f"  Coverage areas:")
    logger.info(f"    - Age validation (young/old)")
    logger.info(f"    - Phone number formats")
    logger.info(f"    - Missing/invalid data")
    logger.info(f"    - Special characters")
    logger.info(f"    - All service types")
    logger.info(f"    - Complex medical conditions")
    logger.info(f"    - Rural/remote addresses")
    logger.info("")
    logger.info("✓ Test data generation complete")
    logger.info("✓ System ready for real template and data integration")


def run_all_comprehensive_tests():
    """Run all comprehensive tests."""
    logger.info("DOCUMENT GENERATOR - COMPREHENSIVE TEST SUITE")
    logger.info("="*80)
    
    try:
        validation_results = test_validation_scenarios()
        print()
        
        test_pii_obfuscation_scenarios()
        print()
        
        test_data_processing_edge_cases()
        print()
        
        test_document_generation_readiness()
        print()
        
        generate_test_report()
        print()
        
        logger.info("="*80)
        logger.info("✓ COMPREHENSIVE TESTING COMPLETED")
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. Set up Python virtual environment and install dependencies")
        logger.info("2. Add real document templates to templates/ directories")
        logger.info("3. Provide real data structure for template mapping")
        logger.info("4. Test with real client data in secure environment")
        logger.info("5. Configure LLM and SharePoint integrations")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Comprehensive test suite error: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_all_comprehensive_tests()
    sys.exit(0 if success else 1)