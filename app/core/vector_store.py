"""
Optimized vector store for limited resources - FIXED VERSION
"""
import pickle
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
import hashlib
import json

logger = logging.getLogger(__name__)

class FixedVectorStore:
    """Lightweight vector store with NaN handling"""
    
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.loaded = False
        
        # Use config for path
        from app.config import config
        self.store_path = Path(config.vector_store_path)
        self.store_path.mkdir(exist_ok=True)
        
        # Cache for faster searches
        self._search_cache = {}
        self.cache_size = 50
    
    def save(self):
        """Save vector store efficiently"""
        try:
            # Save chunks as JSON
            chunks_data = {
                "chunks": self.chunks,
                "count": len(self.chunks),
                "version": "2.1"
            }
            
            chunks_file = self.store_path / "chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
            
            # Save embeddings as numpy array
            if self.embeddings is not None:
                # Clean NaN values before saving
                embeddings_clean = np.nan_to_num(self.embeddings, nan=0.0)
                embeddings_file = self.store_path / "embeddings.npy"
                np.save(str(embeddings_file), embeddings_clean)
                logger.info(f"✅ Saved embeddings shape: {embeddings_clean.shape}")
            
            logger.info(f"✅ Saved {len(self.chunks)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save vector store: {e}")
            return False
    
    def load(self):
        """Load vector store"""
        try:
            chunks_file = self.store_path / "chunks.json"
            embeddings_file = self.store_path / "embeddings.npy"
            
            # Load JSON chunks
            if chunks_file.exists():
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.chunks = data.get("chunks", [])
                self.loaded = len(self.chunks) > 0
                
                # Load embeddings if they exist
                if embeddings_file.exists():
                    try:
                        self.embeddings = np.load(str(embeddings_file))
                        # Clean NaN values
                        self.embeddings = np.nan_to_num(self.embeddings, nan=0.0)
                        logger.info(f"✅ Loaded embeddings: {self.embeddings.shape}")
                    except Exception as e:
                        logger.warning(f"Could not load embeddings: {e}")
                        self.embeddings = None
                
                logger.info(f"✅ Loaded {len(self.chunks)} chunks from vector store")
                
                # If no embeddings, create them from chunks
                if self.loaded and self.embeddings is None:
                    logger.warning("No embeddings found, creating simple ones...")
                    self._create_simple_embeddings()
                
                return True
            
            # No data found
            self.chunks = []
            self.embeddings = None
            self.loaded = False
            logger.info("No vector store data found")
            return True
            
        except Exception as e:
            logger.error(f"❌ Load error: {e}")
            self.chunks = []
            self.embeddings = None
            self.loaded = False
            return False
    
    def _create_simple_embeddings(self):
        """Create simple embeddings from chunks"""
        if not self.chunks:
            return
        
        import hashlib
        embeddings_list = []
        
        for chunk in self.chunks:
            text = chunk.get("text", "")
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            # Create 384-dim embedding from hash
            emb = np.zeros(384, dtype=np.float32)
            
            for i in range(384):
                char_idx = i % len(text_hash)
                emb[i] = (ord(text_hash[char_idx]) / 255.0) - 0.5
            
            # Normalize
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            
            embeddings_list.append(emb)
        
        self.embeddings = np.array(embeddings_list)
        logger.info(f"Created simple embeddings: {self.embeddings.shape}")
    
    def clear(self):
        """Clear vector store"""
        self.chunks = []
        self.embeddings = None
        self._search_cache.clear()
        self.loaded = False
        
        # Delete files
        for file in self.store_path.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
            except:
                pass
        
        logger.info("✅ Vector store cleared")
    
    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: Optional[np.ndarray] = None):
        """Add chunks to store"""
        self.chunks.extend(chunks)
        
        if embeddings is not None:
            # Clean NaN values
            embeddings = np.nan_to_num(embeddings, nan=0.0)
            
            if self.embeddings is None:
                self.embeddings = embeddings
            else:
                self.embeddings = np.vstack([self.embeddings, embeddings])
        
        self.loaded = True
        self._search_cache.clear()
    
    def similarity_search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Fast similarity search with NaN handling"""
        if not self.loaded or not self.chunks or self.embeddings is None:
            return []
        
        # Clean query embedding
        query_embedding = np.nan_to_num(query_embedding, nan=0.0)
        
        # Check cache
        query_hash = hashlib.md5(query_embedding.tobytes()).hexdigest()
        cache_key = f"{query_hash}_{k}"
        
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]
        
        try:
            # Ensure 2D and clean
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            query_embedding = np.nan_to_num(query_embedding, nan=0.0)
            
            # Normalize query
            query_norm = query_embedding.copy()
            query_magnitude = np.linalg.norm(query_norm, axis=1, keepdims=True)
            query_magnitude[query_magnitude == 0] = 1.0  # Avoid division by zero
            query_norm = query_norm / query_magnitude
            
            # Normalize database embeddings
            db_norm = self.embeddings.copy()
            db_magnitude = np.linalg.norm(db_norm, axis=1, keepdims=True)
            db_magnitude[db_magnitude == 0] = 1.0  # Avoid division by zero
            db_norm = db_norm / db_magnitude
            
            # Compute similarities
            similarities = np.dot(db_norm, query_norm.T).flatten()
            
            # Get top-k
            if k > len(similarities):
                k = len(similarities)
            
            # Filter out NaN similarities
            valid_indices = ~np.isnan(similarities)
            if not np.any(valid_indices):
                return []
            
            valid_similarities = similarities[valid_indices]
            valid_chunks = [self.chunks[i] for i in range(len(self.chunks)) if valid_indices[i]]
            
            if len(valid_similarities) == 0:
                return []
            
            # Get top-k indices
            top_indices = np.argpartition(valid_similarities, -min(k, len(valid_similarities)))[-min(k, len(valid_similarities)):]
            top_indices = top_indices[np.argsort(valid_similarities[top_indices])[::-1]]
            
            # Get results
            results = []
            for idx in top_indices:
                if idx < len(valid_chunks):
                    chunk = valid_chunks[idx].copy()
                    chunk["similarity"] = float(valid_similarities[idx])
                    results.append(chunk)
            
            # Cache results
            if len(self._search_cache) >= self.cache_size:
                self._search_cache.pop(next(iter(self._search_cache)))
            self._search_cache[cache_key] = results
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def search_by_keyword(self, keyword: str, k: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword search"""
        if not self.loaded:
            return []
        
        keyword_lower = keyword.lower()
        scored_chunks = []
        
        for chunk in self.chunks:
            text = chunk.get("text", "").lower()
            source = chunk.get("metadata", {}).get("source", "").lower()
            
            score = 0
            if keyword_lower in text:
                # Higher score for exact matches
                score += text.count(keyword_lower) * 3
            if keyword_lower in source:
                score += 2
            
            if score > 0:
                scored_chunks.append((score, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:k]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        if not self.loaded:
            return {"total_chunks": 0, "loaded": False}
        
        sources = {}
        chunk_types = {}
        
        for chunk in self.chunks:
            source = chunk.get("metadata", {}).get("source", "unknown")
            chunk_type = chunk.get("metadata", {}).get("chunk_type", "paragraph")
            
            sources[source] = sources.get(source, 0) + 1
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        # Check embeddings for NaN
        has_nan = False
        if self.embeddings is not None:
            has_nan = np.any(np.isnan(self.embeddings))
        
        return {
            "total_chunks": len(self.chunks),
            "sources": sources,
            "chunk_types": chunk_types,
            "loaded": True,
            "embeddings_shape": str(self.embeddings.shape) if self.embeddings is not None else "None",
            "has_nan": has_nan
        }

# Alias for backward compatibility
VectorStore = FixedVectorStore
