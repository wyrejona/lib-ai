# test_questions.py
from app.core.strict_rag import get_strict_response

questions = [
    "how many books can I borrow?",
    "borrowing limits for students",
    "what are the library hours?",
    "how to cite in APA",
    "plagiarism software",
    "turnitin",
    "how do I access past exam papers?",
    "lost a book procedure",
    "how to renew books",
    "library membership",
]

for q in questions:
    print(f"\n{'='*80}")
    print(f"Q: {q}")
    print(f"A: {get_strict_response(q)[:300]}...")
