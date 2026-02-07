"""
Fixed LLM client - SIMPLE VERSION
"""
import requests
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import time
import hashlib
import re

from app.config import config

logger = logging.getLogger(__name__)


class SimpleLLMClient:
    """Simple client that works"""

    def __init__(self):
        self.base_url = config.ollama_base_url.rstrip('/')
        self.chat_model = config.chat_model
        self.embedding_model = config.embedding_model
        self.timeout = 60

    def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Create simple hash-based embeddings"""
        embeddings = []

        for text in texts:
            # Create deterministic embedding
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            emb = np.zeros(384, dtype=np.float32)

            for i in range(384):
                char_idx = i % len(text_hash)
                emb[i] = (ord(text_hash[char_idx]) / 255.0) - 0.5

            # Normalize
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm

            embeddings.append(emb)

        return embeddings

    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using Ollama"""
        try:
            # Simple prompt
            prompt = f"""Based on these library documents, answer the question.

LIBRARY DOCUMENTS:
{context}

QUESTION: {query}

ANSWER:"""

            data = {
                "model": self.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 800
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()

                # Clean up answer
                if answer.startswith("ANSWER:"):
                    answer = answer[7:].strip()

                return answer if answer else "No answer generated."

            return f"Error: HTTP {response.status_code}"

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error: {str(e)}"

    def generate_accurate_answer(
            self,
            query: str,
            context: str,
            question_type: str) -> str:
        """Generate accurate answer with specialized prompting"""
        try:
            # Specialized prompts based on question type
            if question_type == 'borrowing':
                prompt = f"""You are a library assistant. Answer this borrowing question accurately using ONLY the information below.

LIBRARY RULES:
{context}

QUESTION: {query}

ANSWER (be specific with numbers/days/amounts):"""

            elif question_type == 'fines':
                prompt = f"""You are a library assistant. Answer this fines question accurately using ONLY the information below.

FINES INFORMATION:
{context}

QUESTION: {query}

ANSWER (include exact fine amounts and conditions):"""

            elif question_type == 'plagiarism':
                prompt = f"""You are an academic integrity advisor. Answer this plagiarism question using ONLY the information below.

ACADEMIC INTEGRITY INFORMATION:
{context}

QUESTION: {query}

ANSWER (be clear about consequences and procedures):"""

            else:
                prompt = f"""Based on these library documents, answer the question accurately. Use ONLY the provided information.

LIBRARY INFORMATION:
{context}

QUESTION: {query}

ACCURATE ANSWER:"""

            data = {
                "model": self.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for accuracy
                    "num_predict": 500,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()

                # Clean up
                answer = re.sub(
                    r'^(ANSWER|RESPONSE|ACCURATE ANSWER)[:\s]*',
                    '',
                    answer,
                    flags=re.IGNORECASE)

                return answer if answer else "I couldn't find a specific answer in the documents."

            return "Error retrieving answer."

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"System error: {str(e)[:100]}"

    def generate_context_only_answer(self, query: str, context: str) -> str:
        """Generate answer using ONLY context"""
        try:
            prompt = f"""You are a library assistant at University of Embu. Answer the question using ONLY the information provided below. DO NOT use any outside knowledge. If the answer is not in the provided information, say "The documents do not contain specific information about this."

INFORMATION FROM LIBRARY DOCUMENTS:
{context}

QUESTION: {query}

RULES:
1. Answer ONLY from the information above
2. Do not add information not found above
3. If unsure, say "The documents do not contain specific information about this"
4. Be specific and accurate
5. Quote numbers and details exactly as they appear

ANSWER BASED ONLY ON THE INFORMATION ABOVE:"""

            data = {
                "model": self.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Very low temperature for accuracy
                    "num_predict": 500,
                    "top_p": 0.8,
                    "repeat_penalty": 1.2,
                    "stop": ["\n\n", "Note:", "However:", "Additionally:"]
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()

                # Clean up
                answer = re.sub(
                    r'^(ANSWER|RESPONSE|BASED ON)[:\s]*',
                    '',
                    answer,
                    flags=re.IGNORECASE)

                # Check if answer is valid
                if not answer or len(answer) < 10:
                    return "The documents do not contain specific information about this."

                return answer

            return "Error retrieving answer from documents."

        except Exception as e:
            logger.error(f"Context-only generation error: {e}")
            return "System error"

    def quick_rag_response(self, query: str) -> str:
        """Simple RAG response"""
        try:
            logger.info(f"Query: {query}")

            # Get query embedding
            query_emb = self.get_embeddings([query])[0]

            # Search vector store
            from app.core.vector_store import VectorStore
            vector_store = VectorStore()
            vector_store.load()

            if not vector_store.loaded:
                return "No documents loaded. Please ingest PDFs first."

            # Search
            results = vector_store.similarity_search(query_emb, k=5)

            if not results:
                # Try keyword search
                results = vector_store.search_by_keyword(query, k=5)

            if not results:
                return "I couldn't find relevant information in the documents."

            # Build context
            context_parts = []
            sources = set()

            for result in results:
                text = result.get("text", "").strip()
                source = result.get("metadata", {}).get("source", "Document")

                if text and len(text) > 20:
                    context_parts.append(f"[From {source}]\n{text}")
                    sources.add(source)

            if not context_parts:
                return "No useful content found."

            context = "\n\n---\n\n".join(context_parts[:3])  # Use top 3

            # Generate answer
            answer = self.generate_answer(query, context)

            # Add sources
            if sources:
                answer += f"\n\n📚 Sources: {', '.join(sorted(sources))}"

            return answer

        except Exception as e:
            logger.error(f"RAG error: {e}")
            return f"System error: {str(e)[:100]}"

    def check_connection(self) -> bool:
        """Check Ollama connection"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except BaseException:
            return False


# Alias
OllamaClient = SimpleLLMClient
