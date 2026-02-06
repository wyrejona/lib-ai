#!/usr/bin/env python3
"""
Simple ingestion script for PDF documents
"""
import os
import sys
from pathlib import Path
import logging

# Add app to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.config import config
from app.utils import chunk_text, clean_text
import PyPDF2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return clean_text(text)
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def main():
    """Main ingestion function"""
    logger.info("Starting ingestion process...")
    
    # Check for PDFs
    pdf_files = list(config.pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        logger.info("No PDF files found in pdfs/ directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    all_chunks = []
    all_metadata = []
    
    # Process each PDF
    for i, pdf_path in enumerate(pdf_files):
        logger.info(f"Processing {pdf_path.name} ({i+1}/{len(pdf_files)})")
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {pdf_path.name}")
            continue
        
        # Chunk text
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        
        # Create metadata
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadata.append({
                "source": pdf_path.name,
                "page": "unknown"  # PyPDF2 doesn't track page numbers well
            })
    
    logger.info(f"Extracted {len(all_chunks)} chunks from {len(pdf_files)} PDFs")
    
    # TODO: Generate embeddings (simplified - just save chunks for now)
    if all_chunks:
        # Create simple vector store
        from app.core.vector_store import SimpleVectorStore
        store = SimpleVectorStore()
        
        # Create dummy embeddings (384-dimensional like nomic-embed-text)
        dummy_embeddings = [[0.1] * 384 for _ in all_chunks]
        
        # Create and save store
        store.create(all_chunks, dummy_embeddings, all_metadata)
        logger.info("Vector store created (with dummy embeddings)")
    else:
        logger.warning("No chunks to store")
    
    logger.info("Ingestion complete!")

if __name__ == "__main__":
    main()