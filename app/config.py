"""
Centralized configuration for the Library Support AI system
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """Central configuration manager"""
    
    # Class-level constants (from the code you want to add)
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    PDFS_DIR = BASE_DIR / "pdfs"
    VECTOR_STORE_PATH = DATA_DIR / "vector_store"
    
    # Create directories at import time
    PDFS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    VECTOR_STORE_PATH.mkdir(exist_ok=True)
    
    # Ollama settings from environment variables
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen:0.5b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-minilm:latest")
    
    # API settings from environment variables
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # RAG settings
    SIMILARITY_TOP_K = 5
    MAX_CONTEXT_LENGTH = 2000
    
    # Default JSON config (from your existing file)
    _defaults = {
        # Ollama settings
        "ollama": {
            "base_url": "http://localhost:11434",
            "chat_model": "qwen:0.5b",
            "embedding_model": "all-minilm:latest",
            "timeout": 300,
            "temperature": 0.1
        },
        
        # Vector store settings
        "vector_store": {
            "path": "vector_store",
            "chunk_size": 800,
            "chunk_overlap": 100,
            "batch_size": 5
        },
        
        # File paths
        "paths": {
            "pdfs_dir": "pdfs",
            "data_dir": "data",
            "templates_dir": "templates",
            "static_dir": "static",
            "project_root": "."
        },
        
        # Server settings
        "server": {
            "host": "0.0.0.0",
            "port": 8000
        },
        
        # Search settings
        "search": {
            "default_k": 5,
            "max_context_length": 3000
        },
        
        # Application settings
        "app": {
            "name": "Library Support AI",
            "version": "1.0.0",
            "debug": False
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self._config_file = Path(config_file) if config_file else Path("config.json")
        self.config = self._load_config()
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r') as f:
                    user_config = json.load(f)
                return self._deep_merge(self._defaults, user_config)
            except Exception as e:
                logger.error(f"Failed to load config, using defaults: {e}")
                return self._defaults.copy()
        else:
            self._save_config(self._defaults)
            return self._defaults.copy()
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self, config: Dict[str, Any]):
        try:
            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _ensure_directories(self):
        for path_key in self.config["paths"]:
            Path(self.config["paths"][path_key]).mkdir(parents=True, exist_ok=True)
        Path(self.config["vector_store"]["path"]).mkdir(parents=True, exist_ok=True)
    
    # Property getters (from your existing file)
    @property
    def ollama_base_url(self) -> str: return self.config["ollama"]["base_url"]
    @property
    def chat_model(self) -> str: return self.config["ollama"]["chat_model"]
    @property
    def embedding_model(self) -> str: return self.config["ollama"]["embedding_model"]
    @property
    def ollama_timeout(self) -> int: return self.config["ollama"]["timeout"]
    @property
    def ollama_temperature(self) -> float: return self.config["ollama"]["temperature"]
    @property
    def pdfs_dir(self) -> Path: return Path(self.config["paths"]["pdfs_dir"])
    @property
    def data_dir(self) -> Path: return Path(self.config["paths"]["data_dir"])
    @property
    def templates_dir(self) -> Path: return Path(self.config["paths"]["templates_dir"])
    @property
    def static_dir(self) -> Path: return Path(self.config["paths"]["static_dir"])
    @property
    def vector_store_path(self) -> Path: return Path(self.config["vector_store"]["path"])
    @property
    def chunk_size(self) -> int: return self.config["vector_store"]["chunk_size"]
    @property
    def chunk_overlap(self) -> int: return self.config["vector_store"]["chunk_overlap"]
    @property
    def batch_size(self) -> int: return self.config["vector_store"]["batch_size"]
    @property
    def search_default_k(self) -> int: return self.config["search"]["default_k"]
    @property
    def max_context_length(self) -> int: return self.config["search"]["max_context_length"]
    @property
    def server_host(self) -> str: return self.config["server"]["host"]
    @property
    def server_port(self) -> int: return self.config["server"]["port"]
    @property
    def app_name(self) -> str: return self.config["app"]["name"]
    @property
    def app_version(self) -> str: return self.config["app"]["version"]
    @property
    def debug(self) -> bool: return self.config["app"]["debug"]
    
    # Class methods from the code you want to add
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        # Check PDF directory
        if not cls.PDFS_DIR.exists():
            errors.append(f"PDFs directory not found: {cls.PDFS_DIR}")
        
        # Check if PDFs exist
        pdf_files = list(cls.PDFS_DIR.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {cls.PDFS_DIR}")
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        
        logger.info("✅ Configuration validated successfully")
        return True
    
    @classmethod
    def print_summary(cls):
        """Print configuration summary"""
        pdf_files = list(cls.PDFS_DIR.glob("*.pdf"))
        
        print("\n" + "="*60)
        print("📋 CONFIGURATION SUMMARY")
        print("="*60)
        print(f"Base Directory: {cls.BASE_DIR}")
        print(f"Data Directory: {cls.DATA_DIR}")
        print(f"PDFs Directory: {cls.PDFS_DIR} ({len(pdf_files)} PDFs)")
        print(f"Vector Store: {cls.VECTOR_STORE_PATH}")
        print(f"Ollama URL: {cls.OLLAMA_BASE_URL}")
        print(f"Chat Model: {cls.CHAT_MODEL}")
        print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"API: {cls.API_HOST}:{cls.API_PORT}")
        print(f"Debug: {cls.DEBUG}")
        print(f"Similarity Top K: {cls.SIMILARITY_TOP_K}")
        print(f"Max Context Length: {cls.MAX_CONTEXT_LENGTH}")
        print("="*60)

    def update_config(self, section: str, key: str, value: Any) -> bool:
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            self._save_config(self.config)
            return True
        return False

    def reload(self):
        self.config = self._load_config()

# Global configuration instance
config = Config()
