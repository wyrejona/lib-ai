#!/usr/bin/env python3
"""
ACCURATE PDF ingestion for library documents
"""
import os
import sys
from pathlib import Path
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import config
from app.core.accurate_ingestor import AccuratePDFIngestor
from app.core.vector_store import VectorStore

def main():
    """Main ingestion process"""
    try:
        # Initialize
        ingestor = AccuratePDFIngestor()
        vector_store = VectorStore()
        
        # Get PDFs
        pdfs_dir = Path(config.pdfs_dir)
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.error(f"No PDF files found in {pdfs_dir}")
            return False
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        # Clear existing store
        vector_store.clear()
        
        all_chunks = []
        
        # Process each PDF
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
            start_time = time.time()
            
            # Extract with sections
            sections = ingestor.extract_with_sections(pdf_path)
            
            if not sections:
                logger.warning(f"No sections extracted from {pdf_path.name}")
                continue
            
            # Create accurate chunks
            chunks = ingestor.create_accurate_chunks(sections)
            
            if not chunks:
                logger.warning(f"No chunks created from {pdf_path.name}")
                continue
            
            # Create embeddings
            embeddings = ingestor.create_semantic_embeddings(chunks)
            
            # Prepare chunks for storage
            storage_chunks = []
            for chunk in chunks:
                storage_chunks.append({
                    "text": chunk["text"],
                    "metadata": chunk["metadata"]
                })
            
            # Add to vector store
            vector_store.add_chunks(storage_chunks, embeddings)
            all_chunks.extend(storage_chunks)
            
            elapsed = time.time() - start_time
            logger.info(f"✓ {pdf_path.name}: {len(chunks)} chunks in {elapsed:.1f}s")
            
            # Save intermediate
            if i % 2 == 0 or i == len(pdf_files):
                vector_store.save()
        
        # Final save
        vector_store.save()
        
        # Statistics
        logger.info(f"\n✅ Ingestion complete!")
        logger.info(f"Total chunks: {len(all_chunks)}")
        
        # Show content types
        content_types = {}
        for chunk in all_chunks:
            ctype = chunk["metadata"].get("content_type", "unknown")
            content_types[ctype] = content_types.get(ctype, 0) + 1
        
        logger.info("Content types:")
        for ctype, count in sorted(content_types.items()):
            logger.info(f"  {ctype}: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
