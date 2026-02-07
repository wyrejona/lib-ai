# test_strict_rag.py
import sys
sys.path.insert(0, '.')

from app.core.strict_rag import get_direct_answer, get_strict_response

questions = [
    "how do I cite and reference using APA",
    "what time does the library open",
    "how many books can undergraduate students borrow",
    "what is the fine for overdue books",
    "what is plagiarism",
    "how do I access e-resources",
    "how to reference in apa format",
    "library opening hours",
    "how do I borrow a book",
    "how to renew books",
    "lost a book what to do",
    "what is turnitin",
    "where to find past exam papers",
    "how do I join the library"
]

print("🧪 TESTING STRICT RAG SYSTEM")
print("=" * 80)

for i, question in enumerate(questions, 1):
    print(f"\n{i}. ❓ QUESTION: {question}")
    print("-" * 40)
    
    # Try direct answer first
    direct = get_direct_answer(question)
    if direct:
        print(f"📝 DIRECT ANSWER: {direct[:200]}...")
    else:
        # Use strict RAG
        answer = get_strict_response(question)
        print(f"📝 STRICT RAG ANSWER: {answer[:200]}...")
    
    print("=" * 80)
