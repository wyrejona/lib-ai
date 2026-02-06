"""
Utility functions for the Library Support AI
"""
import re
import hashlib
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def format_file_size(bytes):
    """Format bytes to human readable size"""
    if bytes == 0: return "0 Bytes"
    size_names = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes >= 1024 and i < len(size_names) - 1:
        bytes /= 1024.0
        i += 1
    return f"{bytes:.2f} {size_names[i]}"

def extract_key_query_terms(query: str) -> List[str]:
    """Extract key terms from query for better search"""
    query_lower = query.lower()
    
    # Library-specific terms mapping
    term_mapping = {
        'myloft': ['myloft', 'mobile app', 'app', 'e-resources app', 'past exam papers app'],
        'past exam': ['past exam', 'exam papers', 'previous papers', 'old papers'],
        'borrowing': ['borrowing', 'loan', 'checkout', 'circulation', 'borrow books'],
        'library hours': ['library hours', 'opening hours', 'closing time', 'library schedule'],
        'plagiarism': ['plagiarism', 'turnitin', 'academic integrity', 'citation'],
        'citation': ['citation', 'apa', 'referencing', 'bibliography', 'reference style'],
        'e-resource': ['e-resources', 'electronic resources', 'online databases', 'e-journals'],
        'renewal': ['renewal', 'renew books', 'extend loan', 'extend due date'],
        'fine': ['fine', 'overdue fine', 'late fee', 'penalty', 'ksh 5'],
        'database': ['database', 'databases', 'e-journals', 'e-books', 'online resources']
    }
    
    keywords = []
    
    # Add query terms (skip very short words)
    for word in query_lower.split():
        if len(word) > 2 and word not in ['the', 'and', 'for', 'how', 'what', 'where', 'when']:
            keywords.append(word)
    
    # Add mapped terms
    for key, terms in term_mapping.items():
        if key in query_lower:
            keywords.extend(terms)
    
    # Remove duplicates and return
    return list(set(keywords))

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    return "".join(c for c in filename if c.isalnum() or c in ('.', '-', '_')).rstrip()

def validate_pdf_file(filepath: str) -> bool:
    """Validate if file is a PDF"""
    from pathlib import Path
    path = Path(filepath)
    return path.exists() and path.suffix.lower() == '.pdf'
