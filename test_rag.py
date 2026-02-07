#!/usr/bin/env python3
"""
Test the RAG system with procedural questions
"""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.llm_client import OllamaClient
from app.core.vector_store import VectorStore

def test_questions():
    """Test with procedural questions"""
    questions = [
        "What are the steps to borrow a book from the library?",
        "How do I access e-resources?",
        "Explain the procedure for library registration",
        "What are the steps to avoid plagiarism?",
        "How do I reference using APA format?",
        "What is the process for library circulation?"
    ]
    
    print("🧪 TESTING RAG SYSTEM WITH PROCEDURAL QUESTIONS")
    print("=" * 60)
    
    # Initialize
    llm = OllamaClient()
    vector_store = VectorStore()
    vector_store.load()
    
    print(f"✅ Vector store loaded: {vector_store.loaded}")
    print(f"✅ Chunks: {len(vector_store.chunks) if vector_store.loaded else 0}")
    print(f"✅ Ollama connected: {llm.check_connection()}")
    print(f"✅ Chat model: {llm.chat_model}")
    print(f"✅ Embedding model: {llm.embedding_model}")
    print("=" * 60)
    
    # Test each question
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. ❓ QUESTION: {question}")
        print("-" * 40)
        
        try:
            answer = llm.quick_rag_response(question)
            print(f"📝 ANSWER:\n{answer}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("=" * 60)

if __name__ == "__main__":
    test_questions()
