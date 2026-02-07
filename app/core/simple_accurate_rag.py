"""
Simple accurate RAG system
"""
import re
import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class SimpleAccurateRAG:
    """Simple but accurate RAG system"""
    
    def __init__(self):
        from app.core.vector_store import VectorStore
        from app.core.llm_client import SimpleLLMClient
        
        self.vector_store = VectorStore()
        self.llm_client = SimpleLLMClient()
        
        # Load vector store
        self.vector_store.load()
        logger.info(f"Accurate RAG loaded with {len(self.vector_store.chunks)} chunks")
        
        # Question classifiers
        self.question_patterns = {
            'borrowing': ['borrow', 'loan', 'renew', 'return', 'due date', 'how many books'],
            'fines': ['fine', 'overdue', 'penalty', 'charge', 'ksh', 'accruing'],
            'hours': ['open', 'close', 'hour', 'time', 'schedule'],
            'plagiarism': ['plagiarism', 'turnitin', 'similarity', 'citation', 'reference'],
            'eresources': ['e-resource', 'database', 'myloft', 'past paper', 'exam', 'electronic'],
            'membership': ['join', 'member', 'staff', 'student', 'category', 'id card'],
            'location': ['floor', 'shelf', 'find', 'location', 'call number', 'where is'],
            'referencing': ['apa', 'reference', 'citation', 'format', 'bibliography']
        }
    
    def classify_question(self, question: str) -> str:
        """Classify the question type"""
        question_lower = question.lower()
        
        for qtype, keywords in self.question_patterns.items():
            for keyword in keywords:
                if keyword in question_lower:
                    return qtype
        
        return 'general'
    
    def search_relevant_chunks(self, question: str, question_type: str) -> List[Dict[str, Any]]:
        """Search for relevant chunks"""
        if not self.vector_store.loaded:
            return []
        
        # Get query embedding
        query_emb = self.llm_client.get_embeddings([question])[0]
        
        # Vector search
        vector_results = self.vector_store.similarity_search(query_emb, k=10)
        
        # Keyword search
        keyword_results = self.vector_store.search_by_keyword(question, k=10)
        
        # Combine and deduplicate
        all_results = []
        seen_texts = set()
        
        for result in vector_results + keyword_results:
            text = result.get('text', '')
            if text and text not in seen_texts:
                seen_texts.add(text)
                all_results.append(result)
        
        # Filter by relevance to question type
        filtered_results = []
        for result in all_results:
            content = result.get('text', '').lower()
            metadata = result.get('metadata', {})
            content_type = metadata.get('content_type', 'general')
            
            # Check if content is relevant to question type
            if self._is_relevant(content, question_type, question):
                filtered_results.append(result)
        
        return filtered_results[:5]
    
    def _is_relevant(self, content: str, question_type: str, question: str) -> bool:
        """Check if content is relevant"""
        question_lower = question.lower()
        
        # Specific checks for different question types
        if question_type == 'borrowing':
            return any(word in content for word in ['borrow', 'loan', 'renew', 'return'])
        elif question_type == 'fines':
            return any(word in content for word in ['fine', 'overdue', 'ksh', 'charge'])
        elif question_type == 'plagiarism':
            return any(word in content for word in ['plagiarism', 'turnitin', 'citation'])
        elif question_type == 'hours':
            return any(word in content for word in ['hour', 'open', 'close', 'time'])
        elif question_type == 'eresources':
            return any(word in content for word in ['e-resource', 'database', 'myloft', 'past paper'])
        else:
            # For general questions, check for question keywords
            question_words = set(re.findall(r'\b\w+\b', question_lower))
            content_words = set(re.findall(r'\b\w+\b', content))
            common = question_words.intersection(content_words)
            return len(common) >= 2  # At least 2 common words
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format context for LLM"""
        context_parts = []
        
        for chunk in chunks:
            text = chunk.get('text', '').strip()
            source = chunk.get('metadata', {}).get('source', 'Document')
            section = chunk.get('metadata', {}).get('section', '')
            
            if text and len(text) > 30:
                context_part = f"[Source: {source}"
                if section:
                    context_part += f", Section: {section}"
                context_part += f"]\n{text}"
                context_parts.append(context_part)
        
        return "\n\n---\n\n".join(context_parts[:3])
    
    def get_template_answer(self, question: str) -> str:
        """Get template-based answer for common questions"""
        question_lower = question.lower()
        
        # Template answers for accuracy
        templates = {
            'how many books can undergraduate': "Undergraduate students can borrow up to 3 books for 14 days, with 1 renewal allowed.",
            'how many books can postgraduate': "Postgraduate students can borrow up to 6 books for 30 days, with 1 renewal allowed.",
            'how many books can academic staff': "Academic staff can borrow up to 6 books for 90 days, with 1 renewal allowed.",
            'what is the fine': "Overdue fines are Ksh 5 per book per day, starting immediately after the due date.",
            'library hours': "Library hours: Monday-Friday: 07:30–22:00, Saturday: 09:00–15:00, Sunday: 13:45–18:00",
            'what is plagiarism': "Plagiarism is presenting others' ideas, works, or statements as your own without proper acknowledgment.",
            'how do i renew': "You can renew books once only, before the due date. Renew at the circulation desk with your ID and the book.",
            'lost a book': "Report lost items immediately to stop fines. If not found after 1 month, replace the item plus Ksh 500 processing fee.",
            'apa referencing': "University of Embu uses APA 7th Edition for referencing.",
            'access past papers': "Past exam papers are available in the MyLOFT app under E-resources → Exam Past papers.",
            'how to join library': "Library serves University of Embu students, staff, and alumni only. Present valid University ID.",
            'where is': "Use the OPAC to search for books. The library uses Library of Congress Classification by floor.",
            'e-resources': "E-resources include e-journals, e-books, and databases. Access via MyLOFT or library website.",
            'turnitin': "Turnitin is anti-plagiarism software used to check assignments for originality.",
            'reference style': "University of Embu uses APA 7th Edition for referencing."
        }
        
        for pattern, answer in templates.items():
            if pattern in question_lower:
                return answer
        
        return ""
    
    def get_answer(self, question: str) -> str:
        """Get accurate answer"""
        if not question.strip():
            return "Please enter a question."
        
        # First check for template answer
        template_answer = self.get_template_answer(question)
        if template_answer:
            return template_answer
        
        # Classify question
        question_type = self.classify_question(question)
        
        # Search for relevant chunks
        relevant_chunks = self.search_relevant_chunks(question, question_type)
        
        if not relevant_chunks:
            return "I couldn't find specific information about that in the library documents. Please ask about: borrowing rules, fines, library hours, plagiarism, e-resources, or referencing."
        
        # Format context
        context = self.format_context(relevant_chunks)
        
        # Generate answer
        answer = self.llm_client.generate_accurate_answer(question, context, question_type)
        
        # Add sources
        sources = set()
        for chunk in relevant_chunks[:3]:
            source = chunk.get('metadata', {}).get('source', 'Document')
            sources.add(source)
        
        if sources:
            answer += f"\n\n📚 Based on: {', '.join(sorted(sources))}"
        
        return answer

# Global instance
_rag_instance = None

def get_accurate_response(question: str) -> str:
    """Get accurate response"""
    global _rag_instance
    try:
        if _rag_instance is None:
            _rag_instance = SimpleAccurateRAG()
        return _rag_instance.get_answer(question)
    except Exception as e:
        logger.error(f"Error in get_accurate_response: {e}")
        return f"System error: {str(e)[:100]}"
