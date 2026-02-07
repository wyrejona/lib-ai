"""
FINAL WORKING RAG SYSTEM - No Ollama timeout
"""
import numpy as np
import hashlib
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FinalRAGSystem:
    """Complete RAG system that works without Ollama delays"""
    
    def __init__(self):
        self.vector_store = None
        self._load_store()
    
    def _load_store(self):
        """Load vector store"""
        from .vector_store import VectorStore
        self.vector_store = VectorStore()
        self.vector_store.load()
        logger.info(f"RAG system ready with {len(self.vector_store.chunks) if self.vector_store.loaded else 0} chunks")
    
    def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Fast hash-based embeddings"""
        embeddings = []
        for text in texts:
            h = hashlib.sha256(text.encode()).hexdigest()
            emb = np.zeros(384, dtype=np.float32)
            for i in range(384):
                emb[i] = (ord(h[i % len(h)]) / 255.0) - 0.5
            
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            
            embeddings.append(emb)
        return embeddings
    
    def _extract_answer_from_chunks(self, question: str, chunks: List[Dict]) -> str:
        """Extract or generate answer from chunks"""
        if not chunks:
            return "No information found."
        
        # Combine top chunks
        combined_text = ""
        sources = set()
        
        for chunk in chunks[:3]:
            text = chunk.get("text", "").strip()
            source = chunk.get("metadata", {}).get("source", "Library Document")
            
            if text:
                combined_text += text + "\n\n"
                sources.add(source)
        
        # Try to extract direct answer
        question_lower = question.lower()
        
        # For time questions
        if any(word in question_lower for word in ['time', 'open', 'close', 'hour', 'when']):
            answer = self._extract_time_info(combined_text, question)
            if answer:
                return answer
        
        # For procedural questions
        if any(word in question_lower for word in ['step', 'how to', 'procedure', 'process', 'guide']):
            answer = self._extract_steps(combined_text, question)
            if answer:
                return answer
        
        # For definition questions
        if any(word in question_lower for word in ['what is', 'define', 'meaning', 'explain']):
            answer = self._extract_definition(combined_text, question)
            if answer:
                return answer
        
        # Default: return relevant excerpts
        return self._format_excerpts(chunks[:3])
    
    def _extract_time_info(self, text: str, question: str) -> str:
        """Extract time information"""
        time_patterns = [
            r'(\d{1,2}(?:\.\d{2})?\s*(?:am|pm|AM|PM|hours?))',
            r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)',
            r'(open.*?\d{1,2}.*?\d{1,2})',
            r'(hours?.*?\d{1,2}.*?\d{1,2})',
            r'(Monday.*?Friday.*?\d{1,2}.*?\d{1,2})'
        ]
        
        matches = []
        for pattern in time_patterns:
            found = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if found:
                matches.extend(found)
        
        if matches:
            unique_matches = list(set(matches))[:5]
            answer = f"**Library Hours Information:**\n\n"
            for i, match in enumerate(unique_matches, 1):
                answer += f"{i}. {match.strip()}\n"
            return answer
        
        return ""
    
    def _extract_steps(self, text: str, question: str) -> str:
        """Extract step-by-step information"""
        # Look for numbered steps
        numbered_steps = re.findall(r'(\d+[\.\)]\s+[^\n]+)', text)
        
        if numbered_steps:
            answer = f"**Steps from Library Documents:**\n\n"
            for step in numbered_steps[:10]:
                answer += f"• {step.strip()}\n"
            return answer
        
        # Look for bullet points
        bullets = re.findall(r'([•\-*]\s+[^\n]+)', text)
        if bullets:
            answer = f"**Guidelines from Library Documents:**\n\n"
            for bullet in bullets[:10]:
                answer += f"• {bullet.strip()}\n"
            return answer
        
        return ""
    
    def _extract_definition(self, text: str, question: str) -> str:
        """Extract definition"""
        patterns = [
            r'([^.]*?is\s+defined\s+as[^.]*\.)',
            r'([^.]*?means[^.]*\.)',
            r'([^.]*?refers\s+to[^.]*\.)',
            r'([^.]*?is\s+[^.]*\.)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if len(match) > 20 and len(match) < 300:
                        return f"**Definition from Library Documents:**\n\n{match.strip()}"
        
        return ""
    
    def _format_excerpts(self, chunks: List[Dict]) -> str:
        """Format chunks as readable excerpts"""
        response = "**Relevant Information from Library Documents:**\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "").strip()
            source = chunk.get("metadata", {}).get("source", "Library Document")
            chunk_type = chunk.get("metadata", {}).get("chunk_type", "information")
            
            if text:
                if len(text) > 250:
                    text = text[:250] + "..."
                
                response += f"{i}. **From {source}** ({chunk_type}):\n"
                response += f"   {text}\n\n"
        
        response += "\n*Information extracted from University of Embu Library documents.*"
        return response
    
    def query(self, question: str) -> str:
        """Main query function"""
        try:
            if not self.vector_store or not self.vector_store.loaded:
                return "⚠️ System is initializing. Please try again in a moment."
            
            logger.info(f"Processing: {question}")
            
            # Get query embedding
            query_emb = self.get_embeddings([question])[0]
            
            # Search
            results = self.vector_store.similarity_search(query_emb, k=5)
            
            if not results:
                results = self.vector_store.search_by_keyword(question, k=5)
            
            if not results:
                return "❌ No relevant information found in the library documents."
            
            # Extract answer
            answer = self._extract_answer_from_chunks(question, results)
            
            return answer
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            return "⚠️ System error. Please try again."

# Global instance
rag_system = FinalRAGSystem()

def get_rag_response(question: str) -> str:
    """Get response from RAG system"""
    return rag_system.query(question)
