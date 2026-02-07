"""
Accurate PDF ingestor for library documents
"""
import re
from pathlib import Path
import logging
from typing import List, Dict, Any
import PyPDF2
import hashlib
import numpy as np

logger = logging.getLogger(__name__)

class AccuratePDFIngestor:
    """Specialized ingestor for library documents"""
    
    def __init__(self):
        self.library_keywords = [
            'borrow', 'return', 'renew', 'fine', 'overdue', 'loan', 
            'circulation', 'plagiarism', 'citation', 'apa', 'reference',
            'hours', 'open', 'close', 'staff', 'student', 'postgraduate',
            'undergraduate', 'academic', 'book', 'journal', 'e-resource',
            'myloft', 'turnitin', 'database', 'access', 'membership'
        ]
    
    def extract_with_sections(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract text preserving document structure"""
        try:
            sections = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                current_section = []
                current_title = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if not text.strip():
                        continue
                    
                    # Clean text
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    for line in lines:
                        # Check if this is a section header
                        if self._is_section_header(line, current_section):
                            # Save previous section
                            if current_section and len(' '.join(current_section)) > 50:
                                sections.append({
                                    'title': current_title,
                                    'content': ' '.join(current_section),
                                    'source': pdf_path.name,
                                    'page': page_num + 1
                                })
                            
                            # Start new section
                            current_title = line
                            current_section = []
                        else:
                            current_section.append(line)
                
                # Add final section
                if current_section and len(' '.join(current_section)) > 50:
                    sections.append({
                        'title': current_title,
                        'content': ' '.join(current_section),
                        'source': pdf_path.name,
                        'page': page_num + 1
                    })
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting {pdf_path.name}: {e}")
            return []
    
    def _is_section_header(self, line: str, current_section: List[str]) -> bool:
        """Determine if a line is a section header"""
        # Too long to be a header
        if len(line) > 200:
            return False
        
        # Common section indicators
        header_indicators = [
            r'^SECTION\s+\d+',
            r'^[A-Z][A-Z\s]+:$',
            r'^\d+\.\s+[A-Z]',
            r'^[IVX]+\.',
            r'^[A-Z\s]{5,30}$',  # All caps lines
            r'^Q:',
            r'^PROBLEM\s+\d+',
            r'^HOW TO\s+',
        ]
        
        for pattern in header_indicators:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        
        # Check if it starts a new topic
        if current_section and len(' '.join(current_section)) > 100:
            # Check for question patterns
            if line.lower().startswith(('what is', 'how do', 'where is', 'why is', 
                                      'when is', 'who can', 'can i')):
                return True
            
            # Check for numbered lists
            if re.match(r'^\d+[\.\)]', line):
                return True
        
        return False
    
    def create_accurate_chunks(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create meaningful chunks"""
        chunks = []
        
        for section in sections:
            content = section['content']
            title = section['title']
            
            # Split content into logical paragraphs
            paragraphs = self._split_into_paragraphs(content)
            
            for i, para in enumerate(paragraphs):
                if len(para) < 30:  # Too short
                    continue
                
                # Create metadata
                metadata = {
                    'source': section['source'],
                    'section': title,
                    'chunk_id': f"{section['source']}_{len(chunks)}",
                    'page': section.get('page', 0),
                    'content_type': self._classify_content(para)
                }
                
                chunks.append({
                    'text': para,
                    'metadata': metadata,
                    'importance': self._calculate_importance(para, title)
                })
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into logical paragraphs"""
        # Split by sentence endings followed by capital letters
        paragraphs = []
        current = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            current.append(sentence)
            
            # If we have a complete thought or reached reasonable length
            if len(' '.join(current)) > 100 or sentence.strip().endswith((':', ';')):
                paragraphs.append(' '.join(current))
                current = []
        
        if current:
            paragraphs.append(' '.join(current))
        
        return paragraphs
    
    def _classify_content(self, text: str) -> str:
        """Classify content type"""
        text_lower = text.lower()
        
        # Check for different types
        if any(word in text_lower for word in ['fine', 'overdue', 'penalty', 'charge']):
            return 'fines'
        elif any(word in text_lower for word in ['borrow', 'loan', 'renew', 'return']):
            return 'borrowing'
        elif any(word in text_lower for word in ['plagiarism', 'turnitin', 'citation']):
            return 'academic_integrity'
        elif any(word in text_lower for word in ['hour', 'open', 'close', 'schedule']):
            return 'hours'
        elif any(word in text_lower for word in ['access', 'myloft', 'e-resource', 'database']):
            return 'eresources'
        elif any(word in text_lower for word in ['staff', 'student', 'category', 'maximum']):
            return 'membership'
        elif any(word in text_lower for word in ['apa', 'reference', 'citation', 'format']):
            return 'referencing'
        else:
            return 'general'
    
    def _calculate_importance(self, text: str, title: str) -> float:
        """Calculate importance score"""
        score = 0.5  # Base score
        
        text_lower = text.lower()
        title_lower = title.lower()
        
        # Boost for library-specific content
        for keyword in self.library_keywords:
            if keyword in text_lower:
                score += 0.1
            if keyword in title_lower:
                score += 0.2
        
        # Boost for procedural information
        if any(word in text_lower for word in ['step', 'procedure', 'how to', 'guide']):
            score += 0.3
        
        # Boost for numerical information
        if re.search(r'\d+', text):
            score += 0.1
        
        # Boost for definitions
        if text_lower.startswith(('q:', 'what is', 'definition of')):
            score += 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def create_semantic_embeddings(self, chunks: List[Dict[str, Any]]) -> np.ndarray:
        """Create improved embeddings"""
        embeddings = []
        
        for chunk in chunks:
            text = chunk['text'].lower()
            importance = chunk.get('importance', 0.5)
            
            # Create embedding based on keyword presence
            emb = np.zeros(384, dtype=np.float32)
            
            # Keyword encoding
            for i, keyword in enumerate(self.library_keywords[:100]):  # Use first 100 keywords
                if keyword in text:
                    emb[i % 384] += 0.5
            
            # Content type encoding
            content_type = chunk['metadata'].get('content_type', 'general')
            type_hash = hash(content_type) % 384
            emb[type_hash:type_hash+50] += 0.3
            
            # Importance weighting
            emb *= importance
            
            # Add some randomness based on text hash for diversity
            text_hash = hashlib.md5(text.encode()).hexdigest()
            for i in range(100, 200):
                emb[i] += (ord(text_hash[i % len(text_hash)]) / 255.0) * 0.2
            
            # Normalize
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            
            embeddings.append(emb)
        
        return np.array(embeddings)
