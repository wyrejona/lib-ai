#!/usr/bin/env python3
"""
Simple embedding system that doesn't need Ollama
"""
import numpy as np
import hashlib

class SimpleEmbedder:
    def get_embedding(self, text: str) -> np.ndarray:
        """Create a simple embedding from text"""
        # Create deterministic embedding from text hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Convert hash to 384 numbers
        embedding = np.zeros(384, dtype=np.float32)
        
        for i in range(384):
            # Use hash bytes to create numbers
            byte_idx = i % 64
            char_val = ord(text_hash[byte_idx % len(text_hash)])
            embedding[i] = (char_val / 255.0) - 0.5
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def get_embeddings(self, texts: list) -> list:
        return [self.get_embedding(text) for text in texts]

# Test
if __name__ == "__main__":
    embedder = SimpleEmbedder()
    emb = embedder.get_embedding("Library procedure steps")
    print(f"Embedding shape: {emb.shape}")
    print(f"Sample: {emb[:5]}")
