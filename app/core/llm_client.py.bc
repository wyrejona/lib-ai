"""
Ollama LLM client for chat functionality
"""
import requests
import json
import re
import logging
import time

from app.config import config

# Configure logging
logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model: str = None):
        # Use passed model or config model
        self.model = model or config.chat_model
        self.base_url = config.ollama_base_url
        
        # Use config timeout
        self.timeout = config.ollama_timeout
        
        self.system_prompt = """You are the University of Embu Library AI.
STRICT INSTRUCTIONS:
1. Answer using ONLY the provided Context.
2. If the Context contains a list or steps (like "MyLOFT", "past exam papers", "accessing exam papers"), list ALL steps exactly as they appear in the Context.
3. For step-by-step instructions, present them clearly with numbering or bullet points.
4. Be concise but complete.
5. If the answer is not in the context, say "I cannot find that information in the library documents."
6. When providing steps, make sure to include ALL steps from the context without cutting off.
"""

    def test_connection(self) -> tuple[bool, str]:
        """Test if Ollama is accessible and get available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return True, f"Connected. Available models: {', '.join(model_names[:5])}"
            else:
                return False, f"Ollama API returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama. Make sure Ollama is running on http://localhost:11434"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def is_model_available(self) -> tuple[bool, str]:
        """Check if the current model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [m.get("name", "") for m in models]
                
                if self.model in available_models:
                    return True, f"Model '{self.model}' is available"
                else:
                    # Suggest similar models
                    similar = [m for m in available_models if self.model.split(':')[0] in m]
                    suggestion = ""
                    if similar:
                        suggestion = f" Similar available models: {', '.join(similar[:3])}"
                    return False, f"Model '{self.model}' not found.{suggestion}"
            return False, "Could not retrieve model list"
        except Exception as e:
            return False, f"Error checking model: {str(e)}"

    def generate_response(self, prompt: str, context: str = "") -> str:
        # First check if Ollama is running
        try:
            health_response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if health_response.status_code != 200:
                return "Error: Ollama is not running or not accessible. Please make sure Ollama is running."
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Please:\n1. Make sure Ollama is running ('ollama serve')\n2. Check if port 11434 is accessible"
        except Exception as e:
            return f"Error checking Ollama: {str(e)}"
        
        # Check if model is available
        model_available, model_msg = self.is_model_available()
        if not model_available:
            return f"Error: {model_msg}\n\nPlease install the model using: ollama pull {self.model}"
        
        if not context:
            return "I cannot find relevant information in the library documents."

        # Truncate context if it's too long
        max_context_length = 3000
        if len(context) > max_context_length:
            context = context[:max_context_length] + "... [truncated]"
        
        user_message = f"CONTEXT:\n{context}\n\nQUESTION:\n{prompt}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]

        try:
            logger.info(f"Sending request to Ollama ({self.model})...")
            
            # Optimized parameters for speed
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": config.ollama_temperature,
                    "num_ctx": 2048,  # Reduced from 4096
                    "num_predict": 512,  # Reduced from 1024
                    "top_k": 20,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "stop": ["\n\n", "Question:", "Context:", "Answer:"]
                }
            }
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Ollama response received in {elapsed_time:.2f} seconds")
            
            if response.status_code == 200:
                content = response.json().get("message", {}).get("content", "")
                if not content:
                    return "I received an empty response. Please try again or try a different model."
                
                cleaned = self._clean_response(content)
                
                # If response is suspiciously short
                if len(cleaned) < 20:
                    return f"Response seems incomplete. Model used: {self.model}. Try a simpler question."
                
                return cleaned
            elif response.status_code == 404:
                return f"Error: Model '{self.model}' not found. Please install it using: ollama pull {self.model}"
            elif response.status_code == 503:
                return "Error: Model is still loading. Please wait a moment and try again."
            else:
                logger.error(f"Ollama API Error {response.status_code}: {response.text[:200]}")
                return f"Error: AI Service returned {response.status_code}. Please try again."

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s.")
            return f"""The model '{self.model}' is taking too long to respond. 

Quick fixes:
1. Switch to a smaller model in Dashboard (like qwen:0.5b, phi:latest)
2. Install faster model: ollama pull qwen:0.5b
3. Check system memory and restart Ollama"""
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to {self.base_url}")
            return "Error: Cannot connect to Ollama. Please:\n1. Make sure Ollama is running ('ollama serve')\n2. Check if port 11434 is accessible\n3. Try restarting Ollama"
            
        except Exception as e:
            logger.error(f"Unexpected error in OllamaClient: {e}")
            return f"Error: {str(e)[:200]}"

    def _clean_response(self, text: str) -> str:
        text = text.strip()
        patterns = [
            r"^Based on the provided context,?",
            r"^According to the documents?,?",
            r"^From the context provided,?",
            r"^The context (?:states|says|indicates) that,?",
            r"^Based on (?:the )?information (?:provided|available),?"
        ]
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
