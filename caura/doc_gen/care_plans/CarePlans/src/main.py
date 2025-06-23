"""
Care Plan Document Processor

This module serves as the entry point for the Care Plan document processing system.
It handles template loading, document generation, and PDF conversion.

Usage:
    python -m src.main

Author: Byron
Date: March 4, 2025
"""

import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from docxtpl import DocxTemplate
from datetime import datetime
import docx2pdf
import pandas as pd
import subprocess

def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration with sensible defaults.
    
    Args:
        log_level: Desired logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get the project root directory (one level up from src)
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "care_plan_processor.log"
    
    # Map string log level to logging constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    numeric_level = level_map.get(log_level.upper(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info(f"Logging initialized at level {log_level}")


def ensure_directory_structure() -> Dict[str, Path]:
    """
    Create and validate the project directory structure.
    
    Returns:
        Dictionary containing Path objects for each important directory
    """
    # Get the project root directory (one level up from src)
    project_root = Path(__file__).parent.parent
    
    # Define directory structure
    dirs = {
        "templates": project_root / "templates",
        "output": project_root / "output",
        "output_docx": project_root / "output/docx",
        "output_pdf": project_root / "output/pdf",
        "data": project_root / "data"
    }
    
    # Create directories if they don't exist
    for name, path in dirs.items():
        path.mkdir(exist_ok=True, parents=True)
        logging.debug(f"Ensured {name} directory exists at {path}")
    
    return dirs


def clean_value(val):
    """
    Clean a value by converting NaN or 'nan' strings to empty strings.
    
    Args:
        val: The value to clean
        
    Returns:
        Cleaned value
    """
    if isinstance(val, str) and val.lower() == 'nan':
        return ""
    return str(val) if val is not None else ""


def extract_client_data_from_excel(excel_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract client data from the Excel database and format it for care plan generation.
    
    Args:
        excel_path: Path to the Excel database file
        
    Returns:
        List of dictionaries containing client data if successful, None otherwise
    """
    
    excel_file = Path(excel_path)
    if not excel_file.exists():
        logging.error(f"Excel database not found: {excel_path}")
        return None
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Check if required columns exist
        required_columns = [
            'Type','ACN', 'GivenName', 'FamilyName', 'BirthDate', 'GenderCode',
            'AddressLine1', 'AddressLine2', 'Suburb', 'Postcode'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logging.error(f"Required columns missing from Excel file: {', '.join(missing_columns)}")
            return None
        
        # Format the date for the plan
        date_of_plan = "15/11/24"  # Fixed date as requested
        review_date = "14/11/25"   # Fixed date as requested
        
        # Process each client and format data
        clients_data = []
        for _, row in df.iterrows():
            # Format birth date
            birth_date = row['BirthDate']
            if pd.notna(birth_date):
                if isinstance(birth_date, (datetime, pd.Timestamp)):
                    birth_date = birth_date.strftime('%d/%m/%Y')
                else:
                    try:
                        birth_date = pd.to_datetime(birth_date).strftime('%d/%m/%Y')
                    except:
                        birth_date = clean_value(birth_date)
            else:
                birth_date = ""
            
            # Create client data dictionary with all values cleaned
            client_data = {
                'ACN': clean_value(row['ACN']),
                'Type': clean_value(row['Type']),
                'FirstName': clean_value(row['GivenName']),
                'LastName': clean_value(row['FamilyName']),
                'DOB': birth_date,
                'Gender': clean_value(row['GenderCode']),
                'Address1': clean_value(row['AddressLine1']),
                'Address2': clean_value(row['AddressLine2']),
                'Suburb': clean_value(row['Suburb']),
                'PostCode': clean_value(row['Postcode']),
                'DateOfPlan': date_of_plan,
                'ReviewDate': review_date,
            }
            
            clients_data.append(client_data)
        
        logging.info(f"Successfully extracted data for {len(clients_data)} clients from Excel database")
        return clients_data
    
    except Exception as e:
        logging.error(f"Failed to extract client data from Excel: {str(e)}")
        return None


def save_client_data_to_json(clients_data: List[Dict[str, Any]], output_path: Optional[str] = None) -> bool:
    """
    Save client data to a single JSON file.
    
    Args:
        clients_data: List of dictionaries containing client data
        output_path: Optional path for the JSON file (default: data/all_clients_data.json)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Clean the data - replace any 'nan' strings with empty strings
        cleaned_clients_data = []
        for client in clients_data:
            cleaned_client = {}
            for key, value in client.items():
                cleaned_client[key] = clean_value(value)
            cleaned_clients_data.append(cleaned_client)
        
        # Set default output path if not provided
        if not output_path:
            dirs = ensure_directory_structure()
            data_dir = dirs["data"]
            output_path = data_dir / "all_clients_data.json"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Save to JSON file
        with open(output_path, 'w') as f:
            json.dump(cleaned_clients_data, f, indent=4)
        
        logging.info(f"Successfully saved data for {len(cleaned_clients_data)} clients to {output_path}")
        return True
    
    except Exception as e:
        logging.error(f"Failed to save client data to JSON: {str(e)}")
        return False


def load_json_data(json_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load data from a JSON file. Expects a list of JSON objects.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        List of dictionaries if successful, None otherwise
    """
    try:
        file_path = Path(json_path)
        if not file_path.exists():
            logging.error(f"JSON file not found: {json_path}")
            return None
        
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Ensure the data is a list
        if not isinstance(data, list):
            logging.error(f"JSON data is not a list. Got {type(data)} instead.")
            return None
        
        logging.info(f"Successfully loaded {len(data)} items from {json_path}")
        return data
    
    except Exception as e:
        logging.error(f"Failed to load JSON data: {str(e)}")
        return None


def load_template(template_path: str) -> Optional[DocxTemplate]:
    """
    Load a docxtpl template.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        DocxTemplate object if successful, None otherwise
    """
    try:
        template_file = Path(template_path)
        if not template_file.exists():
            logging.error(f"Template not found: {template_path}")
            return None
        
        template = DocxTemplate(template_file)
        logging.info(f"Successfully loaded template: {template_path}")
        return template
    except Exception as e:
        logging.error(f"Failed to load template {template_path}: {str(e)}")
        return None


def process_document(template: DocxTemplate, context: Dict[str, Any], output_path: str) -> Optional[Path]:
    """
    Process a document by rendering a template with context data.
    
    Args:
        template: Loaded DocxTemplate object
        context: Dictionary containing data to render in the template
        output_path: Path for the output file
        
    Returns:
        Path to the generated document if successful, None otherwise
    """
    try:
        # Render the template with the provided context
        template.render(context)
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Save the document
        template.save(output_file)
        logging.info(f"Document successfully generated: {output_file}")
        
        return output_file
    except Exception as e:
        logging.error(f"Failed to process document: {str(e)}")
        return None
  

def convert_to_pdf(docx_path: str, pdf_path: Optional[str] = None) -> Optional[Path]:
    """
    Convert a DOCX file to PDF using LibreOffice.
    
    Args:
        docx_path: Path to the DOCX file
        pdf_path: Optional path for the PDF file (default: same name with .pdf extension in pdf directory)
        
    Returns:
        Path to the generated PDF if successful, None otherwise
    """
    
    try:
        docx_file = Path(docx_path).resolve()  # Get absolute path
        
        # Create output PDF path if not provided
        if not pdf_path:
            # Create pdf directory next to docx directory
            pdf_dir = docx_file.parent.parent / "pdf"
            pdf_dir.mkdir(exist_ok=True, parents=True)
            pdf_file = pdf_dir / docx_file.name.replace('.docx', '.pdf')
        else:
            pdf_file = Path(pdf_path)
            pdf_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Use absolute paths for reliability
        output_dir = str(pdf_file.parent.resolve())
        
        # Use PDF/A export format for better form compatibility
        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 'pdf:writer_pdf_Export:SelectPdfVersion=1',
            '--outdir', output_dir,
            str(docx_file)
        ]
        
        # Log the command for debugging
        logging.info(f"Running conversion command: {' '.join(cmd)}")
        
        # Run the process
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Log output regardless of success/failure
        logging.info(f"LibreOffice stdout: {process.stdout}")
        
        if process.returncode != 0:
            logging.error(f"LibreOffice conversion failed: {process.stderr}")
            return None
        
        # LibreOffice puts the output in the outdir with the original filename but .pdf extension
        expected_output = pdf_file.parent / docx_file.name.replace('.docx', '.pdf')
        
        # Verify the file was created
        if not expected_output.exists():
            logging.error(f"Expected output file not found: {expected_output}")
            # List directory contents for debugging
            logging.error(f"Directory contents: {os.listdir(output_dir)}")
            return None
        
        # If the output path is different from LibreOffice's default output, rename it
        if expected_output != pdf_file:
            try:
                expected_output.rename(pdf_file)
            except Exception as rename_error:
                logging.error(f"Error renaming output file: {str(rename_error)}")
                # Return the original path if rename fails
                pdf_file = expected_output
        
        logging.info(f"PDF successfully generated: {pdf_file}")
        return pdf_file
        
    except Exception as e:
        logging.error(f"Failed to convert to PDF: {str(e)}")
        logging.exception("Detailed traceback:")  # This will print the full stack trace
        return None


def process_clients(template_path: str, clients_data: List[Dict[str, Any]], output_dir: str, generate_pdf: bool = False) -> int:
    """
    Process a list of clients, generating documents for each.
    
    Args:
        template_path: Path to the template file
        clients_data: List of dictionaries containing client data
        output_dir: Directory for output files
        generate_pdf: Whether to generate PDF files
        
    Returns:
        Number of successfully processed clients
    """
    # Load template
    template = load_template(template_path)
    if not template:
        logging.error("Failed to load template. Exiting.")
        return 0
    
    # Ensure output directories exist
    output_path = Path(output_dir)
    docx_dir = output_path / "docx"
    pdf_dir = output_path / "pdf"
    docx_dir.mkdir(exist_ok=True, parents=True)
    if generate_pdf:
        pdf_dir.mkdir(exist_ok=True, parents=True)
    
    # Process each client
    success_count = 0
    for client in clients_data:
        # Make sure DateToday is set if template needs it
        if "DateOfPlan" in client and "DateToday" not in client:
            client["DateToday"] = client["DateOfPlan"]
        
        # Generate output name from client data
        if "ACN" in client and "LastName" in client:
            filename = f"{client['ACN']}_{client['LastName']}.docx"
        else:
            filename = f"client_{success_count}.docx"
        
        # Full output path for DOCX
        docx_path = docx_dir / filename
        
        # Process document
        result = process_document(template, client, docx_path)
        if not result:
            logging.warning(f"Failed to process document for client. Continuing with next client.")
            continue
        
        # Convert to PDF if requested
        if generate_pdf:
            pdf_filename = filename.replace('.docx', '.pdf')
            pdf_path = pdf_dir / pdf_filename
            convert_to_pdf(docx_path, pdf_path)
        
        success_count += 1
    
    logging.info(f"Processed documents for {success_count} out of {len(clients_data)} clients")
    return success_count


def main():
    """
    Main function for Care Plan document processing.
    Can be customized based on your specific needs.
    """
    # Set up logging
    setup_logging("INFO")
    
    # Ensure directory structure
    dirs = ensure_directory_structure()
    
    # # Example: Import from Excel
    # excel_path = "/Users/byron/Desktop/DEX-V3/database/Client-Database.xlsx"
    # clients_data = extract_client_data_from_excel(excel_path)
    
    # if clients_data:
    #     # Save to JSON file
    #     save_client_data_to_json(clients_data)
        
    #     # Process all clients with separate directories for DOCX and PDF
    #     template_path = dirs["templates"] / "care_plan_template.docx"
    #     process_clients(template_path, clients_data, dirs["output"], generate_pdf=True)
    
		# TODO: Collect Additional Information and add to the client data
    
    # Example: Load from JSON and process
    json_path = dirs["data"] / "all_clients_data.json"
    clients_data = load_json_data(json_path)
    if clients_data:
        template_path = dirs["templates"] / "care_plan_template.docx"
        process_clients(template_path, clients_data, dirs["output"], generate_pdf=True)

if __name__ == "__main__":
    main()