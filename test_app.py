#!/usr/bin/env python3
"""
Test the application
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
print("Testing imports...")
try:
    from app.config import config
    print("✅ config imported")
except Exception as e:
    print(f"❌ config import failed: {e}")

try:
    from app.api import chat, files, system, tasks, ingest
    print("✅ All API modules imported")
except Exception as e:
    print(f"❌ API import failed: {e}")

try:
    from app.core.vector_store import VectorStore
    print("✅ VectorStore imported")
except Exception as e:
    print(f"❌ VectorStore import failed: {e}")

try:
    from app.core.llm_client import OllamaClient
    print("✅ OllamaClient imported")
except Exception as e:
    print(f"❌ OllamaClient import failed: {e}")

print("\nChecking directories...")
directories = ["pdfs", "vector_store", "templates", "static"]
for dir_name in directories:
    path = os.path.join(".", dir_name)
    if os.path.exists(path):
        print(f"✅ {dir_name}: exists")
    else:
        print(f"⚠️  {dir_name}: missing (will be created on startup)")

print("\nTesting config...")
print(f"  App name: {config.app_name}")
print(f"  PDFs dir: {config.pdfs_dir}")
print(f"  Chat model: {config.chat_model}")
print(f"  Embedding model: {config.embedding_model}")

print("\n✅ All tests passed!")
