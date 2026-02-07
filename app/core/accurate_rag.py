"""
Accurate RAG system for library Q&A
"""
import re
from typing import List, Dict, Any
import numpy as np
import logging
from app.core.vector_store import VectorStore

logger = logging.getLogger(__name__)

class AccurateRAGSystem:
    """Accurate retrieval and response system"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.vector_store.load()
        
        # Question patterns
        self.question_patterns = {
            'borrowing': ['borrow', 'loan', 'renew', 'return', 'due date', 'how many books'],
            'fines': ['fine', 'overdue', 'penalty', 'charge', 'ksh'],
            'hours': ['open', 'close', 'hour', 'time', 'schedule'],
            'plagiarism': ['plagiarism', 'turnitin', 'similarity', 'citation'],
            'eresources': ['e-resource', 'database', 'myloft', 'past paper', 'exam'],
            'membership': ['join', 'member', 'staff', 'student', 'category', 'id card'],
            'location': ['floor', 'shelf', 'find', 'location', 'call number'],
            'referencing': ['apa', 'reference', 'citation', 'format']
        }
    
    def classify_question(self, question: str) -> str:
        """Classify the type of question"""
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
        from app.core.llm_client import SimpleLLMClient
        llm_client = SimpleLLMClient()
        query_emb = llm_client.get_embeddings([question])[0]
        
        # First: Vector similarity search
        vector_results = self.vector_store.similarity_search(query_emb, k=10)
        
        # Second: Keyword search
        keyword_results = self.vector_store.search_by_keyword(question, k=10)
        
        # Combine and deduplicate
        all_results = []
        seen_texts = set()
        
        for result in vector_results + keyword_results:
            text = result.get('text', '')
            if text and text not in seen_texts:
                seen_texts.add(text)
                all_results.append(result)
        
        # Filter by question type
        filtered_results = []
        for result in all_results:
            content_type = result.get('metadata', {}).get('content_type', 'general')
            
            # Type matching logic
            if question_type == 'borrowing' and content_type in ['borrowing', 'membership']:
                filtered_results.append(result)
            elif question_type == 'fines' and content_type in ['fines', 'borrowing']:
                filtered_results.append(result)
            elif question_type == 'plagiarism' and content_type in ['academic_integrity', 'referencing']:
                filtered_results.append(result)
            elif question_type == 'referencing' and content_type in ['referencing', 'academic_integrity']:
                filtered_results.append(result)
            elif question_type == 'eresources' and content_type in ['eresources', 'general']:
                filtered_results.append(result)
            elif question_type == 'hours' and content_type == 'hours':
                filtered_results.append(result)
            else:
                # Include if type matches or it's general
                if content_type == question_type or content_type == 'general':
                    filtered_results.append(result)
        
        return filtered_results[:5]  # Return top 5
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format context for LLM"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('text', '').strip()
            source = chunk.get('metadata', {}).get('source', 'Document')
            section = chunk.get('metadata', {}).get('section', '')
            
            if text:
                context_part = f"[Source: {source}"
                if section:
                    context_part += f", Section: {section}"
                context_part += f"]\n{text}\n"
                context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)
    
    def generate_precise_answer(self, question: str, context: str) -> str:
        """Generate precise answer using templates for common questions"""
        
        # Template-based answers for accuracy
        template_answers = self._get_template_answer(question, context)
        if template_answers:
            return template_answers
        
        # Fall back to LLM
        from app.core.llm_client import SimpleLLMClient
        llm_client = SimpleLLMClient()
        
        prompt = f"""You are a precise library assistant at University of Embu. Answer the question accurately using ONLY the provided context. If the information is not in the context, say "I don't have that specific information in the library documents."

CONTEXT:
{context}

QUESTION: {question}

ANSWER (be specific, include numbers/dates/amounts when available):"""
        
        return llm_client.generate_answer(question, prompt)
    
    def _get_template_answer(self, question: str, context: str) -> str:
        """Get template-based answer for common questions"""
        question_lower = question.lower()
        
        # Borrowing limits
        if any(word in question_lower for word in ['how many books', 'borrow limit', 'maximum books']):
            if 'undergraduate' in question_lower:
                return "Undergraduate students can borrow up to 3 books for 14 days, with 1 renewal allowed."
            elif 'postgraduate' in question_lower:
                return "Postgraduate students can borrow up to 6 books for 30 days, with 1 renewal allowed."
            elif 'academic staff' in question_lower:
                return "Academic staff can borrow up to 6 books for 90 days, with 1 renewal allowed."
            elif 'non-academic' in question_lower:
                return "Non-academic staff can borrow up to 3 books for 30 days, with 1 renewal allowed."
            elif 'part-time' in question_lower:
                return "Part-time lecturers can borrow up to 6 books for 30 days, with 1 renewal allowed."
        
        # Fines
        if any(word in question_lower for word in ['fine', 'overdue', 'penalty', 'charge']):
            return "Overdue fines are Ksh 5 per book per day, starting immediately after the due date. All user categories have the same fine rate."
        
        # Hours
        if any(word in question_lower for word in ['open', 'close', 'hour', 'time']):
            return "Library hours: Monday-Friday: 07:30–22:00, Saturday: 09:00–15:00, Sunday: 13:45–18:00"
        
        # Plagiarism
        if 'plagiarism' in question_lower:
            return "Plagiarism is presenting others' ideas, works, or statements as your own without proper acknowledgment. The university uses Turnitin software to detect plagiarism."
        
        # APA referencing
        if 'apa' in question_lower:
            return "University of Embu uses APA 7th Edition for referencing. Always cite sources to avoid plagiarism."
        
        # Renewals
        if 'renew' in question_lower:
            return "You can renew books once only, before the due date. Renew at the circulation desk with your ID and the book."
        
        # Lost books
        if any(word in question_lower for word in ['lost', 'misplace']):
            return "Report lost items immediately to stop fines. If not found after 1 month, replace the item plus Ksh 500 processing fee."
        
        return ""

def get_accurate_response(question: str) -> str:
    """Main function for accurate responses"""
    try:
        rag_system = AccurateRAGSystem()
        
        if not rag_system.vector_store.loaded:
            return "Please ingest PDF documents first using the ingest script."
        
        # Classify question
        question_type = rag_system.classify_question(question)
        
        # Search for relevant chunks
        relevant_chunks = rag_system.search_relevant_chunks(question, question_type)
        
        if not relevant_chunks:
            return "I couldn't find specific information about that in the library documents. Please rephrase your question or ask about library services, borrowing rules, fines, hours, or e-resources."
        
        # Format context
        context = rag_system.format_context(relevant_chunks)
        
        # Generate answer
        answer = rag_system.generate_precise_answer(question, context)
        
        # Add sources
        sources = set()
        for chunk in relevant_chunks[:3]:
            source = chunk.get('metadata', {}).get('source', 'Document')
            sources.add(source)
        
        if sources:
            answer += f"\n\n📚 Based on: {', '.join(sorted(sources))}"
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in accurate response: {e}")
        return f"System error: {str(e)[:100]}"
