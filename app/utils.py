import os
import hashlib
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def format_file_size(bytes):
    """Format bytes to human readable size"""
    if bytes == 0:
        return "0 Bytes"
    
    size_names = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes >= 1024 and i < len(size_names) - 1:
        bytes /= 1024.0
        i += 1
    
    return f"{bytes:.2f} {size_names[i]}"

def format_context(search_results: List[Dict[str, Any]], max_length: int = 3000) -> str:
    """Simple context formatting"""
    if not search_results:
        return ""
    
    context_parts = []
    current_length = 0
    
    for result in search_results[:5]:  # Use top 5 results
        content = result.get('content', '').strip()
        if not content:
            continue
        
        formatted = f"{content}\n\n"
        
        if current_length + len(formatted) > max_length:
            break
        
        context_parts.append(formatted)
        current_length += len(formatted)
    
    if not context_parts:
        return ""
    
    context = "".join(context_parts)
    return context[:max_length]

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text.strip()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to end at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for break_point in ['. ', '? ', '! ', '\n\n', '\n']:
                pos = text.rfind(break_point, start, end)
                if pos != -1:
                    end = pos + len(break_point)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move forward with overlap
        start = end - overlap
    
    return chunks