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
    
    # Property getters
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
