import requests
import json
import logging
from typing import Optional, Dict, Any, List  # Added List here
from app.config import config

logger = logging.getLogger(__name__)

class SimpleLLMClient:
    """Simple LLM client for Ollama with timeout handling"""
    
    def __init__(self, model: Optional[str] = None):
        self.base_url = config.ollama_base_url
        self.model = model or config.chat_model
        self.timeout = config.ollama_timeout
        
    def generate(self, prompt: str, context: str = "", system_prompt: str = None) -> str:
        """Generate response from LLM"""
        if not context:
            full_prompt = prompt
        else:
            full_prompt = f"""Context from library documents:
{context}

User question: {prompt}

Please answer based on the context provided. If the context doesn't contain relevant information, say so politely."""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": full_prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 500
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return "I'm having trouble connecting to the AI model. Please try again."
                
        except requests.exceptions.Timeout:
            logger.error("LLM request timed out")
            return "The request took too long. Please try a simpler question or check your Ollama setup."
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama")
            return "Cannot connect to Ollama. Please make sure Ollama is running."
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "An error occurred while processing your request."
    
    def check_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model.get('name', '') for model in models]
        except:
            pass
        return []
