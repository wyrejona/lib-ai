"""
Vector store implementation using FAISS and Ollama embeddings
"""
import faiss
import numpy as np
import pickle
import os
import logging
from typing import List, Dict, Any, Optional
import hashlib
from pathlib import Path

from app.config import config

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks = []
        self.metadata = []
        self.loaded = False
        
        # Use config settings
        self.embedding_model = config.embedding_model
        self.ollama_base_url = config.ollama_base_url
        
        # Initialize embeddings
        self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize embeddings with fallback options"""
        try:
            # First try the newer langchain-ollama
            try:
                from langchain_ollama import OllamaEmbeddings
                self.embeddings = OllamaEmbeddings(
                    model=self.embedding_model,
                    base_url=self.ollama_base_url
                )
                logger.info(f"Using langchain_ollama embeddings with model: {self.embedding_model}")
            except ImportError:
                # Fallback to langchain_community
                try:
                    from langchain_community.embeddings import OllamaEmbeddings
                    self.embeddings = OllamaEmbeddings(
                        model=self.embedding_model,
                        base_url=self.ollama_base_url
                    )
                    logger.info(f"Using langchain_community embeddings with model: {self.embedding_model}")
                except ImportError:
                    logger.error("Neither langchain_ollama nor langchain_community available")
                    self.embeddings = None
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            self.embeddings = None
    
    def create_index(self, texts: List[str], metadata_list: List[Dict] = None):
        """Create FAISS index using configured embedding model"""
        if not self.embeddings:
            logger.error("Embeddings not available. Please install langchain-ollama or langchain-community")
            logger.info("Run: pip install langchain-ollama")
            return
        
        try:
            logger.info(f"Creating embeddings for {len(texts)} chunks using {self.embedding_model}")
            
            # Process in batches to avoid memory issues
            batch_size = config.batch_size
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
                
                try:
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                except Exception as e:
                    logger.error(f"Failed to embed batch {i//batch_size + 1}: {e}")
                    # Try embedding each document individually
                    for j, text in enumerate(batch):
                        try:
                            single_embedding = self.embeddings.embed_documents([text])
                            all_embeddings.extend(single_embedding)
                        except Exception as e2:
                            logger.error(f"Failed to embed individual document {i + j}: {e2}")
                            # Add zero vector as placeholder
                            all_embeddings.append([0.0] * 384)  # Default dimension
            
            # Convert to numpy
            embeddings_array = np.array(all_embeddings).astype('float32')
            
            # Debug: Check embedding dimensions
            logger.info(f"Embedding dimension: {embeddings_array.shape[1]}")
            logger.info(f"Total embeddings: {embeddings_array.shape[0]}")
            
            # Create FAISS index
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_array)
            
            # Store metadata
            self.chunks = texts
            self.metadata = metadata_list if metadata_list else [{} for _ in texts]
            self.loaded = True
            
            # Save
            self.save()
            
            logger.info(f"Created index with {len(texts)} chunks, dimension {dimension}")
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise
    
    def save(self):
        """Save to configured vector store path"""
        if not self.index:
            logger.warning("No index to save")
            return
            
        os.makedirs(config.vector_store_path, exist_ok=True)
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(config.vector_store_path / "vector_index.bin"))
            
            # Save metadata
            with open(config.vector_store_path / "metadata.pkl", 'wb') as f:
                pickle.dump({
                    'chunks': self.chunks,
                    'metadata': self.metadata,
                    'embedding_model': self.embedding_model
                }, f)
            
            logger.info(f"Saved vector store to {config.vector_store_path}")
            
            # Also save a human-readable version for debugging
            with open(config.vector_store_path / "chunks_debug.txt", 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(self.chunks[:50]):  # Save first 50 chunks
                    f.write(f"=== Chunk {i} ===\n")
                    f.write(chunk[:500])  # First 500 chars
                    f.write("\n\n")
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
    
    def load(self):
        """Load from configured vector store path"""
        index_path = config.vector_store_path / "vector_index.bin"
        metadata_path = config.vector_store_path / "metadata.pkl"
        
        if not index_path.exists() or not metadata_path.exists():
            logger.warning(f"Vector store not found at {config.vector_store_path}")
            logger.info("Run ingestion first: python ingest.py")
            return
            
        try:
            # Load FAISS index
            logger.info(f"Loading FAISS index from {index_path}")
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            logger.info(f"Loading metadata from {metadata_path}")
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.chunks = data['chunks']
                self.metadata = data['metadata']
                stored_model = data.get('embedding_model', 'unknown')
                logger.info(f"Stored with embedding model: {stored_model}")
            
            # Reinitialize embeddings
            self._init_embeddings()
            
            self.loaded = True
            logger.info(f"Loaded vector store with {len(self.chunks)} chunks")
            
            # Debug: Show sample chunks with important content
            logger.info("Sample chunks with important keywords:")
            important_keywords = ['myloft', 'past exam', 'step 1', 'q:', 'undergraduate students:']
            
            for keyword in important_keywords:
                matching_chunks = [i for i, chunk in enumerate(self.chunks) 
                                 if keyword.lower() in chunk.lower()]
                if matching_chunks:
                    logger.info(f"  '{keyword}' found in chunks: {matching_chunks[:3]}...")
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            self.loaded = False
    
    def search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """Search using configured settings with enhanced query expansion"""
        if not self.loaded:
            logger.warning("Vector store not loaded")
            return []
            
        if not self.embeddings:
            logger.warning("Embeddings not available")
            return []
        
        # Use config default if k not specified
        if k is None:
            k = config.search_default_k
        
        try:
            # Expand query based on common library terms
            expanded_queries = self._expand_query(query)
            
            all_results = []
            
            for expanded_query in expanded_queries:
                # Get query embedding
                query_embedding = self.embeddings.embed_query(expanded_query)
                query_vector = np.array([query_embedding]).astype('float32')
                
                # Search with more results initially
                search_k = min(k * 3, self.index.ntotal) if self.index.ntotal > 0 else k
                distances, indices = self.index.search(query_vector, search_k)
                
                for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                    if idx < 0 or idx >= len(self.chunks):
                        continue
                    
                    content = self.chunks[idx]
                    
                    # Calculate score (inverse of distance, higher is better)
                    score = 1.0 / (1.0 + distance)
                    
                    # Boost score for exact matches in important sections
                    score_boost = self._calculate_score_boost(content, query)
                    final_score = score * (1.0 + score_boost)
                    
                    all_results.append({
                        'content': content,
                        'score': final_score,
                        'original_score': score,
                        'distance': float(distance),
                        'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                        'index': idx,
                        'query_used': expanded_query
                    })
            
            # Remove duplicates based on content
            unique_results = []
            seen_contents = set()
            
            for result in all_results:
                content_hash = hashlib.md5(result['content'][:200].encode()).hexdigest()
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    unique_results.append(result)
            
            # Sort by score (descending)
            unique_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Take top k results
            results = unique_results[:k]
            
            # Log search results for debugging
            if results:
                logger.info(f"Search for '{query}' found {len(results)} results")
                logger.info(f"   Top score: {results[0]['score']:.4f}")
                
                # Log what type of content was found
                content_types = {}
                for result in results[:3]:
                    content_lower = result['content'].lower()
                    if 'step' in content_lower or '1.' in content_lower:
                        content_types['step'] = content_types.get('step', 0) + 1
                    if 'q:' in content_lower or 'question' in content_lower:
                        content_types['faq'] = content_types.get('faq', 0) + 1
                    if 'myloft' in content_lower:
                        content_types['myloft'] = content_types.get('myloft', 0) + 1
                    if 'past' in content_lower and 'paper' in content_lower:
                        content_types['past_papers'] = content_types.get('past_papers', 0) + 1
                
                if content_types:
                    logger.info(f"   Content types found: {content_types}")
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        query_lower = query.lower()
        expanded = [query]
        
        # Map common query patterns to library terminology
        query_mappings = {
            'past exam': ['past exam papers', 'previous papers', 'old exam papers', 'exam past papers'],
            'myloft': ['myloft app', 'e-resources app', 'mobile library app'],
            'borrow': ['borrowing', 'loan', 'checkout', 'circulation'],
            'renew': ['renewal', 'extend loan', 'extend due date'],
            'fine': ['overdue fine', 'late fee', 'penalty'],
            'e-resource': ['electronic resources', 'online resources', 'digital resources'],
            'plagiarism': ['turnitin', 'academic integrity', 'citation', 'referencing'],
            'library hour': ['opening hours', 'closing time', 'library schedule'],
            'database': ['e-journals', 'e-books', 'online databases'],
        }
        
        for pattern, expansions in query_mappings.items():
            if pattern in query_lower:
                for expansion in expansions:
                    if expansion not in expanded:
                        expanded.append(expansion)
        
        # Also add the original query with key terms emphasized
        key_terms = ['past', 'exam', 'paper', 'myloft', 'borrow', 'renew', 'fine', 
                    'e-resource', 'plagiarism', 'database', 'library']
        
        emphasized_terms = []
        for term in key_terms:
            if term in query_lower:
                emphasized_terms.append(term)
        
        if emphasized_terms:
            emphasized_query = f"{query} {' '.join(emphasized_terms)}"
            if emphasized_query not in expanded:
                expanded.append(emphasized_query)
        
        return expanded
    
    def _calculate_score_boost(self, content: str, query: str) -> float:
        """Calculate score boost based on content relevance"""
        content_lower = content.lower()
        query_lower = query.lower()
        
        boost = 0.0
        
        # Boost for exact phrase matches
        if query_lower in content_lower:
            boost += 0.5
        
        # Boost for important sections
        important_sections = ['SECTION 11:', 'MYLOFT', 'PAST EXAM PAPERS', 'STEP 1', 'STEP 2', 'STEP 3']
        for section in important_sections:
            if section.lower() in content_lower:
                boost += 0.3
                break
        
        # Boost for step-by-step content when query asks for steps
        step_keywords = ['how to', 'step by step', 'process', 'procedure']
        if any(keyword in query_lower for keyword in step_keywords):
            if 'step' in content_lower or ('1.' in content_lower and '2.' in content_lower):
                boost += 0.4
        
        # Boost for FAQ content when query is a question
        if query_lower.startswith(('how', 'what', 'where', 'when', 'why', 'can', 'do', 'does')):
            if 'q:' in content_lower or 'question' in content_lower:
                boost += 0.3
        
        return min(boost, 1.0)  # Cap at 1.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.loaded:
            return {"status": "not_loaded"}
        
        stats = {
            "status": "loaded",
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_model": self.embedding_model,
            "loaded": self.loaded,
        }
        
        # Count chunks with important keywords
        keyword_counts = {}
        important_keywords = [
            'myloft', 'past exam', 'past papers', 'borrowing', 'renewal',
            'fine', 'overdue', 'e-resources', 'plagiarism', 'turnitin',
            'apa', 'citation', 'step 1', 'step 2', 'step 3', 'q:', 'a:'
        ]
        
        for keyword in important_keywords:
            count = sum(1 for chunk in self.chunks if keyword.lower() in chunk.lower())
            if count > 0:
                keyword_counts[keyword] = count
        
        stats["keyword_counts"] = keyword_counts
        
        # Sample chunks with important content
        sample_chunks = []
        for keyword in ['myloft', 'past exam', 'step 1']:
            for i, chunk in enumerate(self.chunks):
                if keyword.lower() in chunk.lower() and len(sample_chunks) < 3:
                    preview = chunk[:100].replace('\n', ' ')
                    sample_chunks.append({
                        'index': i,
                        'keyword': keyword,
                        'preview': f"{preview}..."
                    })
                    break
        
        stats["sample_chunks"] = sample_chunks
        
        return stats

# Context formatting function (moved from utils)
def format_context(search_results: List[Dict[str, Any]], max_length: int = None) -> str:
    """Format search results into context"""
    from app.config import config
    
    if max_length is None:
        max_length = config.max_context_length
    
    if not search_results:
        return ""
    
    # Sort by score first
    sorted_results = sorted(search_results, key=lambda x: x['score'], reverse=True)
    
    # Prioritize results with step-by-step content for "how to" queries
    step_results = []
    faq_results = []
    other_results = []
    
    for result in sorted_results:
        content = result.get('content', '')
        if not isinstance(content, str):
            continue
        
        content_lower = content.lower()
        
        # Check for step-by-step content
        if 'step' in content_lower or ('1.' in content_lower and '2.' in content_lower):
            step_results.append(result)
        # Check for FAQ content
        elif 'q:' in content_lower or ('question' in content_lower and 'answer' in content_lower):
            faq_results.append(result)
        else:
            other_results.append(result)
    
    # Reorganize based on content type priority
    prioritized_results = []
    
    # If we have step results, put them first
    if step_results:
        prioritized_results.extend(step_results)
    
    # Add FAQ results
    if faq_results:
        prioritized_results.extend(faq_results)
    
    # Add other results
    prioritized_results.extend(other_results)
    
    context_parts = []
    current_length = 0
    
    # Add informative header
    header = "LIBRARY DOCUMENT INFORMATION:\n\n"
    context_parts.append(header)
    current_length += len(header)
    
    # Add each result
    for i, result in enumerate(prioritized_results):
        content = result.get('content', '')
        score = result.get('score', 0)
        
        # Skip if content is not a string or is empty
        if not isinstance(content, str) or not content.strip():
            continue
        
        # Clean content
        content = content.strip()
        
        # Format with score indication (for debugging, optional)
        formatted = f"[Relevance: {score:.2f}]\n{content}\n\n"
        
        # Check if adding this would exceed max length
        if current_length + len(formatted) > max_length:
            # Try to truncate this result instead of skipping
            space_left = max_length - current_length - 50  # Leave room for truncation note
            
            if space_left > 100:  # Only add if we have reasonable space
                truncated = content[:space_left] + "...\n[Content truncated due to length limits]\n\n"
                context_parts.append(f"[Relevance: {score:.2f}]\n{truncated}")
                current_length += len(truncated)
            break
        
        context_parts.append(formatted)
        current_length += len(formatted)
    
    # If we only have the header, try to include at least something
    if current_length <= len(header) + 10:
        # Try to include at least the first result, truncated
        if prioritized_results:
            first_result = prioritized_results[0]
            content = first_result.get('content', '')
            if content:
                # Take as much as we can fit
                max_content = min(len(content), max_length - len(header) - 50)
                if max_content > 100:
                    truncated_content = content[:max_content] + "...\n\n"
                    context_parts.append(truncated_content)
    
    context_text = ''.join(context_parts)
    
    return context_text
