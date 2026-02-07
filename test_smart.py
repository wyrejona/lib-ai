#!/usr/bin/env python3
"""
Test the SMART RAG system
"""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.smart_rag import get_smart_response

def test_questions():
    """Test with various questions"""
    print("🧠 TESTING SMART RAG SYSTEM")
    print("=" * 70)
    
    test_cases = [
        {
            "question": "What time does the library open?",
            "type": "simple"
        },
        {
            "question": "How do I borrow a book from the library?",
            "type": "procedural"
        },
        {
            "question": "What is plagiarism according to university guidelines?",
            "type": "definition"
        },
        {
            "question": "Explain the APA referencing style",
            "type": "complex"
        },
        {
            "question": "What are the library rules for students?",
            "type": "general"
        }
    ]
    
    for test in test_cases:
        print(f"\n🔍 [{test['type'].upper()}] QUESTION: {test['question']}")
        print("-" * 70)
        
        try:
            answer = get_smart_response(test['question'])
            print(f"📝 ANSWER:\n{answer}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("=" * 70)

if __name__ == "__main__":
    test_questions()
