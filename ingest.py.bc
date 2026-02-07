#!/usr/bin/env python3
"""
Optimized PDF ingestion script for Library Support AI.
Enhanced to capture all important information without omission.
"""
import os
import PyPDF2
import re
import shutil
import hashlib
import sys
import logging
import json
from pathlib import Path
import pickle
import numpy as np
import faiss

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.config import config
    logger = logging.getLogger(__name__)
except ImportError as e:
    print(f"Error importing config: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)

def clean_text(text: str) -> str:
    """Clean extracted text while preserving structure"""
    if not text:
        return ""
    
    # Preserve line breaks for lists and sections
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    
    # Fix hyphenated words
    text = re.sub(r'-\s+', '', text)
    
    # Remove excessive whitespace but keep meaningful line breaks
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a section header, list item, or numbered step
        is_special_line = (
            re.match(r'^(SECTION|Q:|A:|STEP|Problem|Solution|Note|Reason|Alternative|Action|Prevention):', line, re.IGNORECASE) or
            re.match(r'^\d+\.', line) or  # Numbered steps
            re.match(r'^[•\-]\s', line) or  # Bullet points
            re.match(r'^[A-Z\s]+:$', line) or  # Category headers like "UNDERGRADUATE STUDENTS:"
            re.match(r'^[a-z]\)\s', line) or  # Sub-bullets like a), b), c)
            re.match(r'^o\s', line)  # Nested bullets
        )
        
        if is_special_line:
            cleaned_lines.append(line)
        else:
            # Clean regular text
            line = re.sub(r'\s+', ' ', line)
            if line:
                cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def extract_sections(text: str) -> dict:
    """Extract sections with improved detection for library guide"""
    sections = {}
    current_section = "INTRODUCTION"
    current_content = []
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check for SECTION pattern
        section_match = re.match(r'^SECTION\s+(\d+):\s*(.+)$', line, re.IGNORECASE)
        if section_match:
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            
            # Start new section
            section_num = section_match.group(1)
            section_title = section_match.group(2)
            current_section = f"SECTION {section_num}: {section_title}"
            current_content = []
            continue
        
        # Check for subsections
        subsection_patterns = [
            r'^[A-Z][A-Z\s&]+:$',  # UPPERCASE headers
            r'^[A-Z][a-zA-Z\s&]+:$',  # Mixed case headers ending with colon
            r'^HOW TO\s+[A-Z][A-Z\s]+:$',  # HOW TO headers
            r'^[A-Z\s]+PROCEDURE:$',  # PROCEDURE headers
            r'^[A-Z\s]+SOLUTIONS?:$',  # SOLUTION headers
            r'^[A-Z\s]+RESTRICTIONS?:$',  # RESTRICTION headers
            r'^[A-Z\s]+NOTES?:$',  # NOTE headers
            r'^[A-Z\s]+FAQ:$',  # FAQ headers
            r'^TOP\s+\d+\s+',  # TOP 15 patterns
        ]
        
        is_subsection = False
        for pattern in subsection_patterns:
            if re.match(pattern, line):
                is_subsection = True
                break
        
        if is_subsection:
            # Add as a subsection within current section
            current_content.append(f"\n{line}")
        else:
            current_content.append(line)
    
    # Save the last section
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    return sections

def create_chunks(text: str, source: str) -> list:
    """Create chunks from text with intelligent splitting to preserve context"""
    chunks = []
    
    # Extract sections
    sections = extract_sections(text)
    
    for section_title, section_content in sections.items():
        if not section_content:
            continue
        
        # For FAQ sections, keep Q/A pairs together
        if 'FAQ' in section_title.upper():
            qa_pairs = extract_faq_pairs(section_content)
            for i, (question, answer) in enumerate(qa_pairs):
                chunk_id = hashlib.md5(f"{source}_{section_title}_faq_{i}".encode()).hexdigest()[:8]
                chunks.append({
                    'content': f"{section_title}\n\nQ: {question}\nA: {answer}",
                    'source': source,
                    'section': section_title,
                    'chunk_id': chunk_id,
                    'type': 'faq'
                })
            continue
        
        # For step-by-step sections, keep steps together
        if any(keyword in section_title.upper() for keyword in ['STEP', 'PROCESS', 'HOW TO', 'PROCEDURE']):
            process_chunks = extract_process_chunks(section_content, section_title, source)
            chunks.extend(process_chunks)
            continue
        
        # For borrowing matrix, keep user categories together
        if 'BORROWING MATRIX' in section_title.upper():
            matrix_chunks = extract_matrix_chunks(section_content, section_title, source)
            chunks.extend(matrix_chunks)
            continue
        
        # For database lists, keep them together
        if any(keyword in section_title.upper() for keyword in ['DATABASE', 'RESOURCES', 'JOURNALS', 'E-RESOURCES']):
            resource_chunks = extract_resource_chunks(section_content, section_title, source)
            chunks.extend(resource_chunks)
            continue
        
        # Default chunking for regular sections
        words = section_content.split()
        
        # If section is short, keep as single chunk
        if len(words) <= config.chunk_size:
            chunk_id = hashlib.md5(f"{source}_{section_title}".encode()).hexdigest()[:8]
            chunks.append({
                'content': f"{section_title}\n\n{section_content}",
                'source': source,
                'section': section_title,
                'chunk_id': chunk_id,
                'type': 'section'
            })
        else:
            # Split long sections with overlap
            for i in range(0, len(words), config.chunk_size - config.chunk_overlap):
                chunk_words = words[i:i + config.chunk_size]
                if not chunk_words:
                    continue
                    
                chunk_text = ' '.join(chunk_words)
                chunk_id = hashlib.md5(f"{source}_{section_title}_{i}".encode()).hexdigest()[:8]
                
                # Add section title to provide context
                chunk_content = f"{section_title}\n\n{chunk_text}"
                
                chunks.append({
                    'content': chunk_content,
                    'source': source,
                    'section': section_title,
                    'chunk_id': chunk_id,
                    'type': 'section_part'
                })
    
    return chunks

def extract_faq_pairs(content: str) -> list:
    """Extract Q/A pairs from FAQ content"""
    pairs = []
    lines = content.split('\n')
    
    current_q = None
    current_a = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for question pattern
        q_match = re.match(r'^Q:\s*(.+)$', line, re.IGNORECASE)
        if q_match:
            # Save previous Q/A pair
            if current_q and current_a:
                pairs.append((current_q, ' '.join(current_a)))
            
            # Start new Q/A pair
            current_q = q_match.group(1)
            current_a = []
        elif current_q and line.startswith('A:'):
            # Start of answer
            current_a.append(line[2:].strip())
        elif current_q:
            # Continuation of answer
            current_a.append(line)
    
    # Save last pair
    if current_q and current_a:
        pairs.append((current_q, ' '.join(current_a)))
    
    return pairs

def extract_process_chunks(content: str, section_title: str, source: str) -> list:
    """Extract step-by-step processes as complete chunks"""
    chunks = []
    lines = content.split('\n')
    
    # Find all step patterns (1., 2., 3., etc.)
    step_pattern = r'^(\d+)\.\s+(.+)$'
    
    current_steps = []
    current_step_num = None
    current_step_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = re.match(step_pattern, line)
        if match:
            # Save previous step if exists
            if current_step_num is not None:
                current_steps.append(f"{current_step_num}. {' '.join(current_step_text)}")
            
            # Start new step
            current_step_num = match.group(1)
            current_step_text = [match.group(2)]
        elif current_step_num is not None:
            # Continuation of current step
            current_step_text.append(line)
        elif not current_steps:
            # Content before first step (introduction)
            if not any(keyword in line.lower() for keyword in ['step', 'process', 'procedure']):
                current_steps.append(line)
    
    # Save last step
    if current_step_num is not None:
        current_steps.append(f"{current_step_num}. {' '.join(current_step_text)}")
    
    # Create chunk from all steps
    if current_steps:
        chunk_id = hashlib.md5(f"{source}_{section_title}_process".encode()).hexdigest()[:8]
        chunks.append({
            'content': f"{section_title}\n\n" + '\n'.join(current_steps),
            'source': source,
            'section': section_title,
            'chunk_id': chunk_id,
            'type': 'process'
        })
    
    return chunks

def extract_matrix_chunks(content: str, section_title: str, source: str) -> list:
    """Extract borrowing matrix user categories as chunks"""
    chunks = []
    lines = content.split('\n')
    
    current_category = None
    current_details = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for user category pattern (ends with colon)
        if re.match(r'^[A-Z][A-Z\s]+:$', line):
            # Save previous category
            if current_category and current_details:
                chunk_id = hashlib.md5(f"{source}_{section_title}_{current_category}".encode()).hexdigest()[:8]
                chunks.append({
                    'content': f"{section_title}\n\n{current_category}\n" + '\n'.join(current_details),
                    'source': source,
                    'section': section_title,
                    'chunk_id': chunk_id,
                    'type': 'matrix_category'
                })
            
            # Start new category
            current_category = line
            current_details = []
        elif current_category:
            # Add details to current category
            current_details.append(line)
    
    # Save last category
    if current_category and current_details:
        chunk_id = hashlib.md5(f"{source}_{section_title}_{current_category}".encode()).hexdigest()[:8]
        chunks.append({
            'content': f"{section_title}\n\n{current_category}\n" + '\n'.join(current_details),
            'source': source,
            'section': section_title,
            'chunk_id': chunk_id,
            'type': 'matrix_category'
        })
    
    return chunks

def extract_resource_chunks(content: str, section_title: str, source: str) -> list:
    """Extract database/resource lists as chunks"""
    chunks = []
    lines = content.split('\n')
    
    current_resource_type = None
    current_resources = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for resource type headers
        if re.match(r'^[A-Z][A-Z\s\-&]+:$', line) and len(line) < 50:
            # Save previous resource type
            if current_resource_type and current_resources:
                chunk_id = hashlib.md5(f"{source}_{section_title}_{current_resource_type}".encode()).hexdigest()[:8]
                chunks.append({
                    'content': f"{section_title}\n\n{current_resource_type}\n" + '\n'.join(current_resources),
                    'source': source,
                    'section': section_title,
                    'chunk_id': chunk_id,
                    'type': 'resource_list'
                })
            
            # Start new resource type
            current_resource_type = line
            current_resources = []
        elif current_resource_type:
            # Add resource to current type
            current_resources.append(line)
    
    # Save last resource type
    if current_resource_type and current_resources:
        chunk_id = hashlib.md5(f"{source}_{section_title}_{current_resource_type}".encode()).hexdigest()[:8]
        chunks.append({
            'content': f"{section_title}\n\n{current_resource_type}\n" + '\n'.join(current_resources),
            'source': source,
            'section': section_title,
            'chunk_id': chunk_id,
            'type': 'resource_list'
        })
    
    return chunks

def create_embeddings_with_ollama(chunks, embedding_model):
    """Create embeddings using Ollama"""
    try:
        from langchain_ollama import OllamaEmbeddings
        
        embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=config.ollama_base_url
        )
        
        print(f"Creating embeddings using {embedding_model}...")
        
        # Create embeddings in batches
        all_embeddings = []
        batch_size = config.batch_size
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_texts = [chunk['content'] for chunk in batch]
            
            print(f"  Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            
            try:
                batch_embeddings = embeddings.embed_documents(batch_texts)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"  Warning: Failed to embed batch: {e}")
                # Add zero vectors as fallback
                for _ in batch:
                    all_embeddings.append([0.0] * 384)  # Default dimension
        
        return all_embeddings
        
    except ImportError:
        print("Error: langchain_ollama not installed. Install with: pip install langchain-ollama")
        return None
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return None

def main():
    print("=" * 50)
    print("LIBRARY AI INGESTION")
    print(f"Using embedding model: {config.embedding_model}")
    print(f"PDFs directory: {config.pdfs_dir}")
    print(f"Vector store: {config.vector_store_path}")
    print("=" * 50)

    # 1. Clean old data
    if config.vector_store_path.exists():
        print("Cleaning old vector store...")
        shutil.rmtree(config.vector_store_path)
    config.vector_store_path.mkdir(parents=True, exist_ok=True)

    # 2. Check PDFs
    if not config.pdfs_dir.exists():
        print("No 'pdfs' directory found.")
        return
        
    pdf_files = [f for f in os.listdir(config.pdfs_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("No PDFs found.")
        return

    all_chunks = []

    # 3. Process Files
    for filename in pdf_files:
        print(f"Processing: {filename}")
        try:
            file_path = config.pdfs_dir / filename
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                full_text = ""
                
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += clean_text(page_text) + "\n\n"
                
                if not full_text.strip():
                    print(f"   No text extracted from {filename}")
                    continue
                
                print(f"   Extracted {len(full_text)} characters")
                
                chunks = create_chunks(full_text, filename)
                all_chunks.extend(chunks)
                print(f"   Created {len(chunks)} chunks")
                
                # Show chunk types for debugging
                chunk_types = {}
                for chunk in chunks:
                    chunk_type = chunk.get('type', 'unknown')
                    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                if chunk_types:
                    print(f"   Chunk types: {chunk_types}")
                
        except Exception as e:
            print(f"   Failed: {e}")
            import traceback
            traceback.print_exc()

    # 4. Create vector store
    if all_chunks:
        try:
            print(f"\nCreating embeddings for {len(all_chunks)} chunks...")
            
            # Create embeddings
            embeddings_list = create_embeddings_with_ollama(all_chunks, config.embedding_model)
            
            if embeddings_list is None:
                print("Failed to create embeddings. Creating dummy embeddings for testing.")
                # Create dummy embeddings for testing
                dimension = 384  # Default dimension for all-minilm
                embeddings_list = [[0.0] * dimension for _ in range(len(all_chunks))]
            
            # Convert to numpy
            embeddings_array = np.array(embeddings_list).astype('float32')
            dimension = embeddings_array.shape[1]
            
            print(f"  Embedding dimension: {dimension}")
            print(f"  Total embeddings: {embeddings_array.shape[0]}")
            
            # Create FAISS index
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_array)
            
            # Save FAISS index
            faiss.write_index(index, str(config.vector_store_path / "vector_index.bin"))
            
            # Save metadata
            with open(config.vector_store_path / "metadata.pkl", 'wb') as f:
                pickle.dump({
                    'chunks': [c['content'] for c in all_chunks],
                    'metadata': all_chunks,
                    'embedding_model': config.embedding_model,
                    'dimension': dimension
                }, f)
            
            # Save a human-readable version
            with open(config.vector_store_path / "chunks.txt", 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(all_chunks[:20]):  # Save first 20 chunks
                    f.write(f"=== Chunk {i} ===\n")
                    f.write(f"Source: {chunk['source']}\n")
                    f.write(f"Type: {chunk.get('type', 'unknown')}\n")
                    f.write(f"Content:\n{chunk['content'][:500]}...\n\n")
            
            print("\n" + "=" * 50)
            print("INGESTION COMPLETE!")
            print(f"   Total chunks: {len(all_chunks)}")
            print(f"   Embedding model: {config.embedding_model}")
            print(f"   Vector store saved to: {config.vector_store_path}")
            
            # Count important keywords
            keyword_counts = {}
            important_keywords = ['myloft', 'past exam', 'past papers', 'borrowing', 'renewal', 
                                 'fine', 'overdue', 'e-resources', 'plagiarism', 'turnitin', 'apa']
            
            for keyword in important_keywords:
                count = sum(1 for c in all_chunks if keyword.lower() in c['content'].lower())
                if count > 0:
                    keyword_counts[keyword] = count
            
            print(f"   Keyword occurrences: {keyword_counts}")
            
        except Exception as e:
            print(f"\nINDEXING FAILED: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No chunks created. Check PDF extraction.")

if __name__ == "__main__":
    main()
