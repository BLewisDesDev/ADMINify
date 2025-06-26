# File: doc_gen/src/utils/file_utils.py
"""
File operation utilities for document generation system.

Provides secure file handling with proper cleanup and validation.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import json
from datetime import datetime
import hashlib

from .logging_utils import get_logger

logger = get_logger(__name__)


class SecureFileManager:
    """
    Secure file management with automatic cleanup and validation.
    
    Handles temporary files, secure deletion, and file validation
    for document generation workflows.
    """
    
    def __init__(self, base_temp_dir: Optional[Path] = None):
        """
        Initialize secure file manager.
        
        Args:
            base_temp_dir: Base directory for temporary files
        """
        self.base_temp_dir = base_temp_dir or Path(tempfile.gettempdir()) / "doc_gen_secure"
        self.session_temp_dirs: List[Path] = []
        self.temp_files: List[Path] = []
        
        # Create secure temp directory
        self.base_temp_dir.mkdir(exist_ok=True, mode=0o700)
        logger.info(f"SecureFileManager initialized with temp dir: {self.base_temp_dir}")
    
    def create_session_temp_dir(self, session_id: str) -> Path:
        """
        Create a temporary directory for a processing session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path to the created temporary directory
        """
        session_dir = self.base_temp_dir / f"session_{session_id}"
        session_dir.mkdir(exist_ok=True, mode=0o700)
        self.session_temp_dirs.append(session_dir)
        
        logger.info(f"Created session temp directory: {session_dir}")
        return session_dir
    
    def create_temp_file(self, suffix: str = "", prefix: str = "doc_gen_", 
                        session_dir: Optional[Path] = None) -> Path:
        """
        Create a secure temporary file.
        
        Args:
            suffix: File suffix (e.g., '.json', '.docx')
            prefix: File prefix
            session_dir: Directory to create file in
            
        Returns:
            Path to the created temporary file
        """
        if session_dir:
            temp_dir = session_dir
        else:
            temp_dir = self.base_temp_dir
        
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        filename = f"{prefix}{timestamp}_{random_suffix}{suffix}"
        
        temp_file = temp_dir / filename
        temp_file.touch(mode=0o600)  # Secure permissions
        self.temp_files.append(temp_file)
        
        logger.debug(f"Created temp file: {temp_file}")
        return temp_file
    
    def validate_file_exists(self, file_path: Union[str, Path]) -> bool:
        """
        Validate that a file exists and is readable.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file exists and is readable, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            if not path.is_file():
                logger.warning(f"Path is not a file: {file_path}")
                return False
            
            if not os.access(path, os.R_OK):
                logger.warning(f"File is not readable: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {str(e)}")
            return False
    
    def validate_file_type(self, file_path: Union[str, Path], 
                          allowed_extensions: List[str]) -> bool:
        """
        Validate file type by extension.
        
        Args:
            file_path: Path to the file
            allowed_extensions: List of allowed extensions (e.g., ['.docx', '.json'])
            
        Returns:
            True if file type is allowed, False otherwise
        """
        try:
            path = Path(file_path)
            file_extension = path.suffix.lower()
            
            if file_extension not in [ext.lower() for ext in allowed_extensions]:
                logger.warning(f"File type {file_extension} not allowed. "
                             f"Allowed types: {allowed_extensions}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file type {file_path}: {str(e)}")
            return False
    
    def calculate_file_hash(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file for integrity verification.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash string or None if error
        """
        try:
            path = Path(file_path)
            if not self.validate_file_exists(path):
                return None
            
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            file_hash = sha256_hash.hexdigest()
            logger.debug(f"Calculated hash for {file_path}: {file_hash}")
            return file_hash
            
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return None
    
    def copy_file_secure(self, source: Union[str, Path], 
                        destination: Union[str, Path]) -> bool:
        """
        Securely copy a file with validation.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if copy successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Validate source file
            if not self.validate_file_exists(source_path):
                return False
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            # Set secure permissions
            os.chmod(dest_path, 0o600)
            
            # Verify copy integrity
            source_hash = self.calculate_file_hash(source_path)
            dest_hash = self.calculate_file_hash(dest_path)
            
            if source_hash != dest_hash:
                logger.error(f"File copy integrity check failed: {source} -> {destination}")
                self.secure_delete_file(dest_path)
                return False
            
            logger.info(f"File copied successfully: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file {source} -> {destination}: {str(e)}")
            return False
    
    def secure_delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        Securely delete a file by overwriting and removing.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.debug(f"File already deleted: {file_path}")
                return True
            
            if not path.is_file():
                logger.warning(f"Path is not a file: {file_path}")
                return False
            
            # Get file size for overwriting
            file_size = path.stat().st_size
            
            # Overwrite with random data (simple secure deletion)
            with open(path, "r+b") as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
            
            # Remove the file
            path.unlink()
            
            logger.debug(f"File securely deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error securely deleting file {file_path}: {str(e)}")
            return False
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up all temporary files and directories for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            session_dir = self.base_temp_dir / f"session_{session_id}"
            
            if session_dir.exists():
                # Securely delete all files in session directory
                for file_path in session_dir.rglob("*"):
                    if file_path.is_file():
                        self.secure_delete_file(file_path)
                
                # Remove directory
                shutil.rmtree(session_dir, ignore_errors=True)
                
                # Remove from tracking
                if session_dir in self.session_temp_dirs:
                    self.session_temp_dirs.remove(session_dir)
            
            logger.info(f"Session cleanup completed: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {str(e)}")
            return False
    
    def cleanup_all(self) -> bool:
        """
        Clean up all temporary files and directories.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            # Clean up tracked temp files
            for temp_file in self.temp_files:
                self.secure_delete_file(temp_file)
            
            # Clean up session directories
            for session_dir in self.session_temp_dirs:
                if session_dir.exists():
                    shutil.rmtree(session_dir, ignore_errors=True)
            
            # Clear tracking lists
            self.temp_files.clear()
            self.session_temp_dirs.clear()
            
            logger.info("All temporary files cleaned up")
            return True
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup_all()


def ensure_directory_structure(base_path: Union[str, Path]) -> Dict[str, Path]:
    """
    Create and validate project directory structure.
    
    Args:
        base_path: Base path for the project
        
    Returns:
        Dictionary containing Path objects for each directory
    """
    base = Path(base_path)
    
    dirs = {
        "templates": base / "templates",
        "output": base / "output",
        "output_docx": base / "output" / "docx",
        "output_pdf": base / "output" / "pdf",
        "logs": base / "logs",
        "temp": base / "temp"
    }
    
    # Create directories
    for name, path in dirs.items():
        path.mkdir(exist_ok=True, parents=True)
        logger.debug(f"Ensured {name} directory exists at {path}")
    
    return dirs


def load_json_safe(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Safely load JSON data with validation.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data or None if error
    """
    try:
        path = Path(file_path)
        
        # Validate file
        file_manager = SecureFileManager()
        if not file_manager.validate_file_exists(path):
            return None
        
        if not file_manager.validate_file_type(path, ['.json']):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.debug(f"Successfully loaded JSON from {file_path}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {str(e)}")
        return None


def save_json_safe(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """
    Safely save JSON data with atomic writes.
    
    Args:
        data: Data to save
        file_path: Path to save file
        
    Returns:
        True if save successful, False otherwise
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first (atomic write)
        temp_path = path.with_suffix(path.suffix + '.tmp')
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Move to final location
        temp_path.replace(path)
        
        # Set secure permissions
        os.chmod(path, 0o600)
        
        logger.debug(f"Successfully saved JSON to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {str(e)}")
        return False