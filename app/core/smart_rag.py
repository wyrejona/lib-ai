"""
SMART HYBRID RAG SYSTEM - Fast with accurate answers
"""
import numpy as np
import hashlib
import re
import json
import time
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SmartRAGSystem:
    """Smart RAG that uses Ollama only when needed"""
    
    def __init__(self):
        self.vector_store = None
        self.cache_file = Path("rag_cache.json")
        self.answer_cache = self._load_cache()
        self.ollama_client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize components"""
        from .vector_store import VectorStore
        self.vector_store = VectorStore()
        self.vector_store.load()
        logger.info(f"Smart RAG loaded with {len(self.vector_store.chunks) if self.vector_store.loaded else 0} chunks")
    
    def _load_cache(self) -> Dict:
        """Load answer cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self):
        """Save answer cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.answer_cache, f, indent=2)
        except:
            pass
    
    def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Fast embeddings"""
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
    
    def _get_ollama_client(self):
        """Lazy load Ollama client"""
        if self.ollama_client is None:
            from .llm_client import OllamaClient
            self.ollama_client = OllamaClient()
        return self.ollama_client
    
    def _check_cache(self, question: str) -> Optional[str]:
        """Check if answer is in cache"""
        question_key = hashlib.md5(question.lower().encode()).hexdigest()
        if question_key in self.answer_cache:
            cached = self.answer_cache[question_key]
            # Check if cache is recent (last 24 hours)
            if time.time() - cached.get("timestamp", 0) < 86400:
                logger.info(f"Using cached answer for: {question[:50]}...")
                return cached.get("answer")
        return None
    
    def _save_to_cache(self, question: str, answer: str):
        """Save answer to cache"""
        question_key = hashlib.md5(question.lower().encode()).hexdigest()
        self.answer_cache[question_key] = {
            "question": question,
            "answer": answer,
            "timestamp": time.time()
        }
        # Keep cache size manageable
        if len(self.answer_cache) > 100:
            # Remove oldest entries
            sorted_items = sorted(self.answer_cache.items(), key=lambda x: x[1].get("timestamp", 0))
            for key, _ in sorted_items[:20]:
                del self.answer_cache[key]
        self._save_cache()
    
    def _extract_direct_answer(self, question: str, chunks: List[Dict]) -> Optional[str]:
        """Try to extract direct answer from chunks without Ollama"""
        combined_text = "\n\n".join([c.get("text", "") for c in chunks[:3]])
        question_lower = question.lower()
        
        # For library hours
        if any(word in question_lower for word in ['time', 'open', 'close', 'hour']):
            return self._extract_library_hours(combined_text)
        
        # For definitions
        if any(word in question_lower for word in ['what is', 'define', 'meaning of']):
            term = question.replace('what is', '').replace('define', '').replace('meaning of', '').strip()
            if term:
                return self._extract_definition(combined_text, term)
        
        # For steps/procedures
        if any(word in question_lower for word in ['step', 'how to', 'procedure', 'process']):
            return self._extract_procedure(combined_text)
        
        return None
    
    def _extract_library_hours(self, text: str) -> str:
        """Extract library hours accurately"""
        # Look for common library hour patterns
        patterns = [
            r'Library\s+hours?[:\s]+([^\n]+)',
            r'Open[:\s]+([^\n]+)',
            r'Opening\s+hours?[:\s]+([^\n]+)',
            r'Monday.*?Friday[:\s]+([^\n]+)',
            r'(\d{1,2}(?:\.\d{2})?\s*(?:am|pm|AM|PM)\s*to\s*\d{1,2}(?:\.\d{2})?\s*(?:am|pm|AM|PM))',
            r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)\s*-\s*\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))'
        ]
        
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                matches.extend([m.strip() for m in found if len(m.strip()) > 5])
        
        if matches:
            unique_matches = list(dict.fromkeys(matches))[:3]
            response = "**Library Hours Information:**\n\n"
            for match in unique_matches:
                response += f"• {match}\n"
            return response
        
        return ""
    
    def _extract_definition(self, text: str, term: str) -> str:
        """Extract definition of a term"""
        # Look for the term followed by definition
        term_pattern = rf'{re.escape(term)}[^.]*?\.'
        matches = re.findall(term_pattern, text, re.IGNORECASE)
        
        if matches:
            # Get the most relevant sentence
            for match in matches:
                if len(match) > len(term) + 10 and len(match) < 300:
                    return f"**Definition of {term.title()}:**\n\n{match.strip()}"
        
        return ""
    
    def _extract_procedure(self, text: str) -> str:
        """Extract step-by-step procedure"""
        # Look for numbered steps
        steps = re.findall(r'(\d+[\.\)]\s+[^\n]+(?:\n(?!\d+[\.\)])[^\n]*)*)', text, re.MULTILINE)
        
        if steps:
            response = "**Step-by-Step Procedure:**\n\n"
            for step in steps[:10]:
                step = step.strip()
                if step:
                    response += f"• {step}\n"
            return response
        
        # Look for bullet points
        bullets = re.findall(r'([•\-*]\s+[^\n]+(?:\n(?!\s*[•\-*])[^\n]*)*)', text, re.MULTILINE)
        if bullets:
            response = "**Procedure Guidelines:**\n\n"
            for bullet in bullets[:10]:
                bullet = bullet.strip()
                if bullet:
                    response += f"• {bullet}\n"
            return response
        
        return ""
    
    def _generate_smart_answer(self, question: str, chunks: List[Dict]) -> str:
        """Generate answer using Ollama with relevant context"""
        try:
            # Prepare context
            context_parts = []
            sources = set()
            
            for chunk in chunks[:5]:  # Use top 5 chunks
                text = chunk.get("text", "").strip()
                source = chunk.get("metadata", {}).get("source", "Library Document")
                
                if text and len(text) > 20:
                    context_parts.append(f"[From {source}]\n{text}")
                    sources.add(source)
            
            if not context_parts:
                return "I couldn't find relevant information in the library documents."
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Use Ollama to generate answer
            client = self._get_ollama_client()
            
            # Simple prompt for accuracy
            prompt = f"""You are a University of Embu Library assistant. Answer the question based ONLY on the provided library documents.

LIBRARY DOCUMENTS:
{context}

QUESTION: {question}

IMPORTANT: 
1. Answer based ONLY on the documents above
2. If the documents don't contain the information, say so
3. Be precise and factual
4. Use bullet points for steps if applicable

ANSWER:"""
            
            # Generate with timeout
            import requests
            data = {
                "model": client.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 500
                }
            }
            
            response = requests.post(
                f"{client.base_url}/api/generate",
                json=data,
                timeout=10  # Short timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                if answer:
                    # Add sources
                    if sources and len(answer) < 800:
                        answer += f"\n\n📚 **Sources:** {', '.join(sorted(sources))}"
                    
                    return answer
            
            # Fallback to extracted answer
            direct_answer = self._extract_direct_answer(question, chunks)
            if direct_answer:
                return direct_answer
            
            return "I found some information but couldn't generate a clear answer. Please try rephrasing your question."
            
        except requests.exceptions.Timeout:
            # Ollama too slow, use extracted answer
            direct_answer = self._extract_direct_answer(question, chunks)
            if direct_answer:
                return direct_answer + "\n\n⚠️ *Note: Answer extracted directly from documents*"
            
            return "The system is taking too long to respond. Please try a simpler question."
        except Exception as e:
            logger.error(f"Generation error: {e}")
            # Fallback to extracted answer
            direct_answer = self._extract_direct_answer(question, chunks)
            if direct_answer:
                return direct_answer
            
            return "System error. Please try again."
    
    def query(self, question: str, use_cache: bool = True) -> str:
        """Main query function - SMART version"""
        try:
            if not self.vector_store or not self.vector_store.loaded:
                return "⚠️ Library documents are being loaded. Please wait a moment."
            
            logger.info(f"Smart query: {question}")
            
            # Check cache first
            if use_cache:
                cached = self._check_cache(question)
                if cached:
                    return cached
            
            # Get query embedding
            query_emb = self.get_embeddings([question])[0]
            
            # Search for relevant chunks
            results = self.vector_store.similarity_search(query_emb, k=7)
            
            if not results or len(results) < 2:
                # Try keyword search
                results = self.vector_store.search_by_keyword(question, k=7)
            
            if not results:
                return "❌ I couldn't find any information about this in the library documents."
            
            # Check if we should use Ollama or direct extraction
            question_lower = question.lower()
            
            # Use Ollama for complex questions, direct extraction for simple ones
            simple_questions = [
                'time', 'open', 'close', 'hour', 'when',
                'what is', 'define', 'meaning',
                'step', 'how to', 'procedure'
            ]
            
            is_simple = any(word in question_lower for word in simple_questions)
            
            if is_simple:
                # Try direct extraction first
                direct_answer = self._extract_direct_answer(question, results)
                if direct_answer and len(direct_answer) > 50:
                    self._save_to_cache(question, direct_answer)
                    return direct_answer
            
            # Use Ollama for better answers
            answer = self._generate_smart_answer(question, results)
            
            # Cache the answer
            if answer and len(answer) > 30:
                self._save_to_cache(question, answer)
            
            return answer
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            return "⚠️ System error. Please try again or contact support."

# Global instance
smart_rag = SmartRAGSystem()

def get_smart_response(question: str) -> str:
    """Get smart response from RAG system"""
    return smart_rag.query(question)
