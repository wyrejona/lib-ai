#!/usr/bin/env python3
import requests
import sys

def check_ollama():
    try:
        print("Checking Ollama connection...")
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is running!")
            print(f"📊 Available models: {len(models)}")
            for model in models:
                print(f"  - {model.get('name')}")
            return True
        else:
            print(f"❌ Ollama responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Is it running?")
        print("   Try: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if check_ollama():
        sys.exit(0)
    else:
        sys.exit(1)
