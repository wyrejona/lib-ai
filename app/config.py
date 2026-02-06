import os
from pathlib import Path
from typing import Optional
import configparser

class Config:
    def __init__(self):
        # Default paths
        self.app_dir = Path(__file__).parent
        self.project_root = self.app_dir.parent
        
        # Default directories
        self.pdfs_dir = self.project_root / "pdfs"
        self.data_dir = self.project_root / "data"
        self.vector_store_path = self.data_dir / "vector_store"
        self.templates_dir = self.project_root / "templates"
        self.knowledge_base_path = self.data_dir / "knowledge_base.json"
        
        # Create directories
        for dir_path in [self.pdfs_dir, self.data_dir, self.vector_store_path, self.templates_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # App info
        self.app_name = "University of Embu Library Support AI"
        self.app_version = "1.0.0"
        
        # Default configuration
        self.default_config = {
            'ollama': {
                'base_url': 'http://localhost:11434',
                'chat_model': 'qwen:0.5b',
                'embedding_model': 'nomic-embed-text:latest',
                'timeout': 30
            },
            'search': {
                'default_k': 5,
                'max_context_length': 3000,
                'similarity_threshold': 0.3
            },
            'system': {
                'batch_size': 10,
                'max_file_size_mb': 50,
                'log_level': 'INFO'
            }
        }
        
        # Config file path
        self.config_file = self.project_root / "config.ini"
        self.config = configparser.ConfigParser()
        
        # Load or create config
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            self.config.read(self.config_file)
        else:
            self.config.read_dict(self.default_config)
            self._save_config()
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback=None):
        """Get configuration value"""
        try:
            return self.config.get(section, key)
        except:
            return self.default_config.get(section, {}).get(key, fallback)
    
    def set(self, section: str, key: str, value: str):
        """Set configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self._save_config()

    # Add to Config class

def get_available_models(self) -> Dict[str, List[str]]:
    """Get available models from Ollama"""
    import requests
    try:
        response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_models = response.json().get("models", [])
            
            # Separate chat and embedding models
            chat_models = []
            embedding_models = []
            
            embedding_keywords = [
                "embed", "bge", "nomic", "mxbai", "e5", "minilm", 
                "multilingual", "instructor", "sentence"
            ]
            
            for model in ollama_models:
                model_name = model.get("name", "")
                is_embedding = any(keyword in model_name.lower() 
                                 for keyword in embedding_keywords)
                
                if is_embedding:
                    embedding_models.append(model_name)
                else:
                    chat_models.append(model_name)
            
            return {
                "chat_models": chat_models,
                "embedding_models": embedding_models
            }
    except:
        pass
    
    # Return empty lists if can't connect
    return {"chat_models": [], "embedding_models": []}

def is_model_available(self, model_name: str) -> bool:
    """Check if a specific model is available"""
    models = self.get_available_models()
    all_models = models["chat_models"] + models["embedding_models"]
    return model_name in all_models
    
    # Property accessors for common settings
    @property
    def ollama_base_url(self):
        return self.get('ollama', 'base_url')
    
    @property
    def chat_model(self):
        return self.get('ollama', 'chat_model')
    
    @property
    def embedding_model(self):
        return self.get('ollama', 'embedding_model')
    
    @property
    def ollama_timeout(self):
        return int(self.get('ollama', 'timeout', 30))
    
    @property
    def search_default_k(self):
        return int(self.get('search', 'default_k', 5))
    
    @property
    def max_context_length(self):
        return int(self.get('search', 'max_context_length', 3000))
    
    @property
    def batch_size(self):
        return int(self.get('system', 'batch_size', 10))

# Global config instance
config = Config()