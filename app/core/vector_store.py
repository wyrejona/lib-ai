import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """Simplified vector store using numpy arrays"""
    
    def __init__(self):
        self.embeddings = None
        self.chunks = []
        self.metadata = []
        self.loaded = False
        
    def create(self, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict] = None):
        """Create a simple vector store"""
        self.chunks = chunks
        self.embeddings = np.array(embeddings, dtype='float32')
        self.metadata = metadata if metadata else [{} for _ in chunks]
        self.loaded = True
        
        # Save to disk
        self._save()
        logger.info(f"Created vector store with {len(chunks)} chunks")
    
    def _save(self):
        """Save to disk"""
        from app.config import config
        
        # Save embeddings as numpy array
        if self.embeddings is not None:
            np.save(config.vector_store_path / "embeddings.npy", self.embeddings)
        
        # Save chunks and metadata
        data = {
            'chunks': self.chunks,
            'metadata': self.metadata
        }
        
        with open(config.vector_store_path / "data.pkl", 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Saved vector store to {config.vector_store_path}")
    
    def load(self):
        """Load from disk"""
        from app.config import config
        
        embeddings_path = config.vector_store_path / "embeddings.npy"
        data_path = config.vector_store_path / "data.pkl"
        
        if not embeddings_path.exists() or not data_path.exists():
            logger.warning("Vector store files not found")
            return
        
        try:
            # Load embeddings
            self.embeddings = np.load(embeddings_path)
            
            # Load data
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                self.chunks = data['chunks']
                self.metadata = data['metadata']
            
            self.loaded = True
            logger.info(f"Loaded vector store with {len(self.chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            self.loaded = False
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Simple search using cosine similarity"""
        if not self.loaded or self.embeddings is None:
            return []
        
        # Convert query embedding to numpy
        query_vec = np.array([query_embedding], dtype='float32')
        
        # Calculate cosine similarity
        # Normalize vectors
        query_norm = query_vec / np.linalg.norm(query_vec)
        embeddings_norm = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        
        # Calculate similarities
        similarities = np.dot(embeddings_norm, query_norm.T).flatten()
        
        # Get top k indices
        if k > len(similarities):
            k = len(similarities)
        
        top_indices = np.argsort(similarities)[::-1][:k]
        
        # Build results
        results = []
        for idx in top_indices:
            if similarities[idx] < 0.1:  # Low similarity threshold
                continue
                
            results.append({
                'content': self.chunks[idx],
                'score': float(similarities[idx]),
                'metadata': self.metadata[idx] if idx < len(self.metadata) else {},
                'index': int(idx)
            })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        if not self.loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "total_chunks": len(self.chunks),
            "loaded": self.loaded
        }