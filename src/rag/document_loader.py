"""
Document loader for extracting text from various file formats.
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Load and extract text from documents."""
    
    def __init__(self):
        self.supported_extensions = {".pdf", ".txt", ".md"}
    
    def load_document(self, file_path: str) -> Dict[str, any]:
        """
        Load a document and extract its text content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with 'text', 'metadata', and 'file_path'
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == ".pdf":
            return self._load_pdf(file_path)
        elif extension == ".txt":
            return self._load_text(file_path)
        elif extension == ".md":
            return self._load_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    def _load_pdf(self, file_path: Path) -> Dict[str, any]:
        """Extract text from PDF file."""
        try:
            import pypdf
            
            text_parts = []
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": "pdf",
                "pages": 0
            }
            
            with open(file_path, "rb") as f:
                pdf_reader = pypdf.PdfReader(f)
                metadata["pages"] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    if pdf_reader.metadata.title:
                        metadata["title"] = pdf_reader.metadata.title
                    if pdf_reader.metadata.author:
                        metadata["author"] = pdf_reader.metadata.author
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            text_parts.append(f"--- Page {page_num} ---\n{text}")
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {e}")
                        continue
            
            full_text = "\n\n".join(text_parts)
            
            return {
                "text": full_text,
                "metadata": metadata
            }
            
        except ImportError:
            logger.error("pypdf not installed. Install with: pip install pypdf")
            raise
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise
    
    def _load_text(self, file_path: Path) -> Dict[str, any]:
        """Load text from plain text or markdown file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix.lower(),
            }
            
            return {
                "text": text,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {e}")
            raise
    
    def load_directory(self, directory_path: str, recursive: bool = True) -> List[Dict[str, any]]:
        """
        Load all supported documents from a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search subdirectories
            
        Returns:
            List of document dictionaries
        """
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
        
        documents = []
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    doc = self.load_document(str(file_path))
                    documents.append(doc)
                    logger.info(f"Loaded: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    continue
        
        return documents
