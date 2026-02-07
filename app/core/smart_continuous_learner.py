"""
Smart Continuous Learner - Builds direct answer database from PDFs
"""
import os
import time
import logging
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any
import hashlib
import re

logger = logging.getLogger(__name__)

class SmartContinuousLearner:
    """Builds direct answer database automatically from PDFs"""
    
    def __init__(self, check_interval: int = 300):
        from app.config import config
        
        self.pdfs_dir = Path(config.PDFS_DIR)
        self.data_dir = Path(config.DATA_DIR)
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        
        # Direct answer database files
        self.direct_answers_file = self.data_dir / "direct_answers.json"
        self.definitions_file = self.data_dir / "definitions.json"
        self.keywords_file = self.data_dir / "keywords.json"
        
        # File tracking
        self.tracker_file = self.data_dir / "smart_tracker.json"
        self.file_hashes = self._load_tracker()
        
        # Load existing databases
        self.direct_answers = self._load_direct_answers()
        self.definitions = self._load_definitions()
        self.keywords = self._load_keywords()
        
        # Stats
        self.stats = {
            "last_check": None,
            "total_answers": len(self.direct_answers),
            "total_definitions": len(self.definitions),
            "last_updated": None,
            "errors": 0
        }
        
        logger.info(f"Smart continuous learner initialized")
        logger.info(f"📚 Direct answers: {len(self.direct_answers)}")
        logger.info(f"📖 Definitions: {len(self.definitions)}")
        logger.info(f"📁 Monitoring: {self.pdfs_dir}")
    
    def _load_tracker(self) -> Dict[str, str]:
        """Load file tracking data"""
        try:
            if self.tracker_file.exists():
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tracker: {e}")
        return {}
    
    def _save_tracker(self):
        """Save file tracking data"""
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(self.file_hashes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tracker: {e}")
    
    def _load_direct_answers(self) -> Dict[str, str]:
        """Load direct answer database"""
        try:
            if self.direct_answers_file.exists():
                with open(self.direct_answers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading direct answers: {e}")
        return {}
    
    def _save_direct_answers(self):
        """Save direct answer database"""
        try:
            with open(self.direct_answers_file, 'w', encoding='utf-8') as f:
                json.dump(self.direct_answers, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved {len(self.direct_answers)} direct answers")
        except Exception as e:
            logger.error(f"Error saving direct answers: {e}")
    
    def _load_definitions(self) -> Dict[str, str]:
        """Load definitions database"""
        try:
            if self.definitions_file.exists():
                with open(self.definitions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading definitions: {e}")
        return {}
    
    def _save_definitions(self):
        """Save definitions database"""
        try:
            with open(self.definitions_file, 'w', encoding='utf-8') as f:
                json.dump(self.definitions, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved {len(self.definitions)} definitions")
        except Exception as e:
            logger.error(f"Error saving definitions: {e}")
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """Load keyword mapping"""
        try:
            if self.keywords_file.exists():
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading keywords: {e}")
        return {}
    
    def _save_keywords(self):
        """Save keyword mapping"""
        try:
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved keyword mapping for {len(self.keywords)} terms")
        except Exception as e:
            logger.error(f"Error saving keywords: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash"""
        try:
            return hashlib.md5(file_path.read_bytes()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            return ""
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"Page {page_num + 1}:\n{page_text}\n\n"
                    except Exception as e:
                        logger.warning(f"Error reading page {page_num + 1} of {pdf_path.name}: {e}")
                        continue
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting from {pdf_path.name}: {e}")
            return ""
    
    def _parse_qa_from_text(self, text: str, source: str) -> Dict[str, Any]:
        """Parse Q&A pairs from text"""
        questions = []
        definitions = []
        keyword_map = {}
        
        if not text.strip():
            return {"questions": [], "definitions": [], "keywords": {}}
        
        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        current_question = ""
        current_answer = []
        in_answer = False
        in_definition = False
        
        for i, line in enumerate(lines):
            # Look for FAQ patterns (Q:, Question:, etc.)
            if re.match(r'^(Q:|QUESTION:|Q\d+\.|Q\s*\d+[:\.]|\d+\.\s+[A-Z])', line, re.IGNORECASE):
                if current_question and current_answer:
                    questions.append({
                        "question": current_question.lower().strip(),
                        "answer": ' '.join(current_answer).strip(),
                        "source": source
                    })
                
                # Extract question
                question = re.sub(r'^(Q:|QUESTION:|Q\d+\.|Q\s*\d+[:\.]\s*|\d+\.\s+)', '', line, flags=re.IGNORECASE)
                current_question = question
                current_answer = []
                in_answer = True
                in_definition = False
            
            # Look for definition patterns
            elif re.match(r'^(What is|Define|Definition of|.*means|.*refers to|.*is defined as)', line, re.IGNORECASE):
                in_definition = True
                # Try to extract term and definition
                if ':' in line:
                    parts = line.split(':', 1)
                    term = parts[0].lower().replace('what is', '').replace('define', '').replace('definition of', '').strip()
                    definition = parts[1].strip()
                    if term and definition:
                        definitions.append({
                            "term": term,
                            "definition": definition,
                            "source": source
                        })
                elif len(line) < 200:  # Short line might be a definition
                    definitions.append({
                        "term": line.lower().strip('.:'),
                        "definition": "See document for full definition",
                        "source": source
                    })
            
            # Look for section headers (potential questions)
            elif re.match(r'^[A-Z][A-Za-z\s]+\?$', line) and len(line) < 150:
                if current_question and current_answer:
                    questions.append({
                        "question": current_question.lower().strip(),
                        "answer": ' '.join(current_answer).strip(),
                        "source": source
                    })
                
                current_question = line.lower().strip('?').strip()
                current_answer = []
                in_answer = True
                in_definition = False
            
            # Answer content (for Q&A)
            elif in_answer and line and not re.match(r'^(Q:|A:|QUESTION:|ANSWER:|Page \d+:)', line, re.IGNORECASE):
                current_answer.append(line)
            
            # Definition content
            elif in_definition and line and len(line) > 20:
                if definitions:
                    definitions[-1]["definition"] += " " + line
            
            # End of section
            elif line.startswith(('---', '===', '***', 'SECTION', 'CHAPTER', '###')):
                if current_question and current_answer:
                    questions.append({
                        "question": current_question.lower().strip(),
                        "answer": ' '.join(current_answer).strip(),
                        "source": source
                    })
                current_question = ""
                current_answer = []
                in_answer = False
                in_definition = False
        
        # Add last Q&A pair
        if current_question and current_answer:
            questions.append({
                "question": current_question.lower().strip(),
                "answer": ' '.join(current_answer).strip(),
                "source": source
            })
        
        # Extract keywords from questions
        for qa in questions:
            if qa["question"]:
                keywords = self._extract_keywords(qa["question"])
                for keyword in keywords:
                    if keyword not in keyword_map:
                        keyword_map[keyword] = []
                    if qa["question"] not in keyword_map[keyword]:
                        keyword_map[keyword].append(qa["question"])
        
        # Also extract keywords from definitions
        for definition in definitions:
            if definition["term"]:
                keywords = self._extract_keywords(definition["term"])
                for keyword in keywords:
                    if keyword not in keyword_map:
                        keyword_map[keyword] = []
                    term_question = f"what is {definition['term']}"
                    if term_question not in keyword_map[keyword]:
                        keyword_map[keyword].append(term_question)
        
        return {
            "questions": questions,
            "definitions": definitions,
            "keywords": keyword_map
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Remove common words
        stop_words = {'what', 'how', 'when', 'where', 'why', 'which', 'who', 
                     'is', 'are', 'do', 'does', 'can', 'could', 'will', 'would',
                     'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'from',
                     'to', 'in', 'on', 'at', 'by', 'about', 'as', 'like', 'this',
                     'that', 'these', 'those', 'have', 'has', 'had', 'been'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = []
        
        for word in words:
            if word not in stop_words and not word.isdigit():
                keywords.append(word)
        
        return list(set(keywords))
    
    def _process_pdf(self, pdf_path: Path):
        """Process a PDF and extract Q&A"""
        file_str = str(pdf_path)
        file_hash = self._get_file_hash(pdf_path)
        
        logger.info(f"📄 Processing {pdf_path.name}...")
        
        # Extract text
        text = self._extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"⚠️ No text extracted from {pdf_path.name}")
            return
        
        # Parse Q&A from text
        extracted = self._parse_qa_from_text(text, pdf_path.name)
        
        # Add to databases
        added_questions = 0
        added_definitions = 0
        
        # Add questions to direct answers
        for qa in extracted["questions"]:
            if qa["question"] and qa["answer"] and len(qa["answer"]) > 10:
                # Create multiple question variations
                variations = self._create_question_variations(qa["question"])
                
                for variation in variations:
                    if variation not in self.direct_answers:
                        self.direct_answers[variation] = qa["answer"]
                        added_questions += 1
        
        # Add definitions
        for definition in extracted["definitions"]:
            if definition["term"] and definition["definition"]:
                term = definition["term"].lower().strip()
                if term and term not in self.definitions:
                    self.definitions[term] = definition["definition"]
                    added_definitions += 1
        
        # Update keyword mapping
        for keyword, questions in extracted["keywords"].items():
            if keyword not in self.keywords:
                self.keywords[keyword] = []
            
            for question in questions:
                if question not in self.keywords[keyword]:
                    self.keywords[keyword].append(question)
        
        # Update tracker
        self.file_hashes[file_str] = {
            "hash": file_hash,
            "processed": datetime.now().isoformat(),
            "questions": added_questions,
            "definitions": added_definitions,
            "source": pdf_path.name
        }
        
        # Save databases
        self._save_direct_answers()
        self._save_definitions()
        self._save_keywords()
        self._save_tracker()
        
        # Update stats
        self.stats["total_answers"] = len(self.direct_answers)
        self.stats["total_definitions"] = len(self.definitions)
        self.stats["last_updated"] = datetime.now().isoformat()
        
        logger.info(f"✅ Added {added_questions} questions, {added_definitions} definitions from {pdf_path.name}")
    
    def _create_question_variations(self, question: str) -> List[str]:
        """Create multiple variations of a question"""
        variations = [question]
        
        # Remove question mark if present
        no_qmark = question.rstrip('?').strip()
        if no_qmark != question:
            variations.append(no_qmark)
        
        # Common variations
        if 'how many' in question:
            variations.append(question.replace('how many', 'what is the number of'))
            variations.append(question.replace('how many', 'number of'))
        
        if 'how do i' in question:
            variations.append(question.replace('how do i', 'how to'))
            variations.append(question.replace('how do i', 'what is the procedure for'))
        
        if 'how do you' in question:
            variations.append(question.replace('how do you', 'how to'))
        
        if 'what is' in question:
            variations.append(question.replace('what is', 'define'))
            variations.append('definition of ' + question.replace('what is', ''))
        
        if 'when does' in question:
            variations.append(question.replace('when does', 'what time does'))
        
        if 'where is' in question:
            variations.append(question.replace('where is', 'location of'))
        
        # Add "the" variations
        words = question.split()
        if 'the' not in words and len(words) > 2:
            # Try adding "the" in different positions
            for i in range(1, min(3, len(words))):
                new_words = words[:i] + ['the'] + words[i:]
                variations.append(' '.join(new_words))
        
        return list(set([v for v in variations if v]))
    
    def _build_common_answers(self):
        """Build common Q&A patterns from existing data"""
        logger.info("🔨 Building common answer patterns...")
        
        # Group questions by topic
        topic_groups = {
            "borrowing": ["borrow", "loan", "check out", "take out", "return", "renew"],
            "fines": ["fine", "overdue", "penalty", "charge", "ksh"],
            "hours": ["open", "close", "hour", "time", "when", "schedule"],
            "plagiarism": ["plagiarism", "turnitin", "cheating", "academic dishonesty"],
            "referencing": ["apa", "reference", "cite", "citation", "bibliography"],
            "eresources": ["e-resource", "database", "online", "electronic", "myloft"],
            "membership": ["join", "member", "id card", "register", "student card"],
        }
        
        # Build comprehensive answers for each topic
        for topic, keywords in topic_groups.items():
            topic_questions = []
            topic_answers = []
            
            for question, answer in self.direct_answers.items():
                if any(keyword in question for keyword in keywords):
                    topic_questions.append(question)
                    topic_answers.append(answer)
            
            if topic_questions and topic_answers:
                # Find the most comprehensive answer
                if topic_answers:
                    best_answer = max(topic_answers, key=len)
                    
                    # Add topic-based questions
                    self.direct_answers[topic] = best_answer
                    self.direct_answers[f"about {topic}"] = best_answer
                    self.direct_answers[f"information about {topic}"] = best_answer
        
        self._save_direct_answers()
        logger.info(f"✅ Built common patterns. Total answers: {len(self.direct_answers)}")
    
    def check_for_new_files(self):
        """Check for new or modified PDF files"""
        try:
            self.stats["last_check"] = datetime.now().isoformat()
            
            # Find all PDF files
            pdf_files = list(self.pdfs_dir.glob("*.pdf"))
            
            if not pdf_files:
                logger.info("📭 No PDF files found in directory")
                return
            
            new_or_modified = []
            
            for pdf_path in pdf_files:
                file_str = str(pdf_path)
                current_hash = self._get_file_hash(pdf_path)
                
                if file_str not in self.file_hashes:
                    # New file
                    logger.info(f"🆕 New file detected: {pdf_path.name}")
                    new_or_modified.append(pdf_path)
                else:
                    # Check if modified
                    old_hash = self.file_hashes[file_str].get("hash", "")
                    if current_hash != old_hash:
                        logger.info(f"📝 Modified file detected: {pdf_path.name}")
                        new_or_modified.append(pdf_path)
            
            if new_or_modified:
                logger.info(f"🔍 Found {len(new_or_modified)} new/modified files to process")
                
                for pdf_path in new_or_modified:
                    try:
                        self._process_pdf(pdf_path)
                    except Exception as e:
                        logger.error(f"❌ Failed to process {pdf_path.name}: {e}")
                        self.stats["errors"] += 1
                
                # Rebuild common patterns
                self._build_common_answers()
                
                logger.info(f"✅ Processing complete. Total answers: {len(self.direct_answers)}")
            else:
                logger.debug("📊 No new or modified files found")
                
        except Exception as e:
            logger.error(f"❌ Error checking for new files: {e}")
            self.stats["errors"] += 1
    
    def run_continuous(self):
        """Run continuous learning in background"""
        self.running = True
        logger.info("🚀 Starting smart continuous learning service")
        
        while self.running:
            try:
                self.check_for_new_files()
                
                # Sleep for check interval
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Received interrupt, shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in continuous learning loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        logger.info("🛑 Smart continuous learning service stopped")
    
    def start(self):
        """Start the smart continuous learning service"""
        if self.thread and self.thread.is_alive():
            logger.warning("⚠️ Smart continuous learner already running")
            return
        
        self.thread = threading.Thread(target=self.run_continuous, daemon=True)
        self.thread.start()
        logger.info("✅ Smart continuous learning started in background")
    
    def stop(self):
        """Stop the smart continuous learning service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("✅ Smart continuous learning stopped")
    
    def force_check(self):
        """Force immediate check"""
        logger.info("🔄 Forcing immediate file check")
        self.check_for_new_files()
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            "running": self.running,
            "pdfs_directory": str(self.pdfs_dir),
            "tracked_files": len(self.file_hashes),
            "direct_answers": len(self.direct_answers),
            "definitions": len(self.definitions),
            "keywords_mapped": len(self.keywords),
            "stats": self.stats,
            "check_interval": self.check_interval,
            "sample_questions": list(self.direct_answers.keys())[:5] if self.direct_answers else []
        }
    
    def get_direct_answer(self, question: str) -> str:
        """Get direct answer from database (for integration with strict_rag)"""
        question_lower = question.lower().strip()
        
        # Direct match
        if question_lower in self.direct_answers:
            return self.direct_answers[question_lower]
        
        # Check for definition
        if question_lower.startswith('what is') or question_lower.startswith('define'):
            term = question_lower.replace('what is', '').replace('define', '').strip()
            if term in self.definitions:
                return self.definitions[term]
        
        # Keyword match
        for keyword, questions in self.keywords.items():
            if keyword in question_lower:
                # Find the most relevant question
                for q in questions:
                    if q in self.direct_answers:
                        return self.direct_answers[q]
        
        return None
    
    def export_to_strict_rag_format(self):
        """Export databases to strict_rag.py format"""
        try:
            output_file = self.data_dir / "strict_rag_auto.py"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('"""\nAUTO-GENERATED DIRECT ANSWERS FOR STRICT_RAG\nGenerated on: ' + datetime.now().isoformat() + '\n"""\n\n')
                f.write('# Auto-generated answers from PDFs\n')
                f.write('AUTO_GENERATED_ANSWERS = {\n')
                
                for question, answer in sorted(self.direct_answers.items()):
                    # Escape special characters
                    safe_answer = answer.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                    safe_question = question.replace('\\', '\\\\').replace('"', '\\"')
                    f.write(f'    "{safe_question}": "{safe_answer}",\n')
                
                f.write('}\n')
            
            logger.info(f"✅ Exported {len(self.direct_answers)} answers to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting to strict_rag format: {e}")
            return False
    
    def process_all_pdfs(self):
        """Process all PDFs in the directory (initial setup)"""
        pdf_files = list(self.pdfs_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("⚠️ No PDF files found to process")
            return False
        
        logger.info(f"📚 Processing {len(pdf_files)} PDF files...")
        
        for pdf_path in pdf_files:
            try:
                self._process_pdf(pdf_path)
            except Exception as e:
                logger.error(f"❌ Error processing {pdf_path.name}: {e}")
        
        self._build_common_answers()
        logger.info(f"✅ Initial processing complete. Total answers: {len(self.direct_answers)}")
        return True

# Global instance
_smart_learner = None

def get_smart_learner() -> SmartContinuousLearner:
    """Get or create smart learner instance"""
    global _smart_learner
    if _smart_learner is None:
        _smart_learner = SmartContinuousLearner()
    return _smart_learner

def initialize_smart_learning():
    """Initialize and optionally process all PDFs"""
    learner = get_smart_learner()
    
    # Check if we should process all PDFs on startup
    if not learner.direct_answers and list(learner.pdfs_dir.glob("*.pdf")):
        logger.info("🔄 No existing answers found. Processing all PDFs...")
        learner.process_all_pdfs()
    
    return learner
