"""
System management API endpoints
"""
from fastapi import APIRouter, HTTPException
import psutil
import requests
from datetime import datetime, timezone
import logging

from app.config import config
from app.core.vector_store import VectorStore
from app.core.llm_client import OllamaClient

router = APIRouter()
logger = logging.getLogger(__name__)

# Web routes
web_routes = APIRouter()

@web_routes.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home/dashboard page"""
    return config.templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": config.app_name,
        "app_version": config.app_version,
        "current_model": config.chat_model
    })

@router.get("/status")
async def system_status():
    """Get detailed system status"""
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # Process info
        process = psutil.Process()
        process_mem = process.memory_info()
        
        # Check Ollama status
        ollama_connected = False
        ollama_models = []
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_connected = True
                ollama_models = response.json().get("models", [])
        except:
            ollama_connected = False
        
        # Check vector store
        vector_store = VectorStore()
        vector_store.load()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            },
            "memory": {
                "total_gb": round(mem.total / 1024**3, 2),
                "available_gb": round(mem.available / 1024**3, 2),
                "used_gb": round(mem.used / 1024**3, 2),
                "percent": mem.percent,
                "swap_total_gb": round(psutil.swap_memory().total / 1024**3, 2),
                "swap_used_gb": round(psutil.swap_memory().used / 1024**3, 2)
            },
            "disk": {
                "total_gb": round(disk.total / 1024**3, 2),
                "used_gb": round(disk.used / 1024**3, 2),
                "free_gb": round(disk.free / 1024**3, 2),
                "percent": disk.percent
            },
            "process": {
                "memory_mb": round(process_mem.rss / 1024**2, 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads()
            },
            "system": {
                "ollama_connected": ollama_connected,
                "ollama_models_count": len(ollama_models),
                "vector_store_ready": vector_store.loaded,
                "vector_store_chunks": len(vector_store.chunks) if vector_store.loaded else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(500, str(e))

@router.get("/health")
async def health_check():
    """System health check"""
    ollama_ok = False
    ollama_models = []
    try:
        response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            ollama_ok = True
            ollama_models = response.json().get("models", [])
    except Exception as e:
        logger.warning(f"Ollama connection failed: {e}")
    
    # Get memory info
    mem = psutil.virtual_memory()
    
    # Check vector store
    vector_store = VectorStore()
    vector_store.load()
    vector_store_ready = vector_store.loaded
    vector_store_chunks = len(vector_store.chunks) if vector_store.loaded else 0
    
    return {
        "status": "healthy" if ollama_ok and vector_store_ready else "degraded",
        "vector_store_ready": vector_store_ready,
        "vector_store_chunks": vector_store_chunks,
        "ollama_connected": ollama_ok,
        "ollama_models_count": len(ollama_models),
        "current_model": config.chat_model,
        "embedding_model": config.embedding_model,
        "memory_usage": f"{mem.percent}% ({round(mem.available / 1024**3, 1)}GB available)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/config")
async def get_configuration():
    """Get current configuration and available models"""
    try:
        # Try to get models from Ollama
        chat_models = []
        embedding_models = []
        
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_models = response.json().get("models", [])
                
                # Common embedding model patterns
                embedding_patterns = [
                    "embed", "bge", "nomic", "mxbai", "e5", "minilm", "multilingual",
                    "instructor", "text-embedding", "sentence", "all-mpnet"
                ]
                
                for model in ollama_models:
                    model_name = model.get("name", "")
                    
                    # Check if it's an embedding model
                    is_embedding = any(pattern in model_name.lower() for pattern in embedding_patterns)
                    
                    if is_embedding:
                        embedding_models.append(model_name)
                    else:
                        chat_models.append(model_name)
        except Exception as e:
            logger.warning(f"Could not fetch Ollama models: {e}")
            # Fallback to default models
            chat_models = ["llama2:7b", "mistral:7b", "qwen:0.5b"]
            embedding_models = ["nomic-embed-text:latest", "all-minilm:latest"]
        
        return {
            "current": {
                "chat_model": config.chat_model,
                "embedding_model": config.embedding_model,
                "ollama_base_url": config.ollama_base_url
            },
            "available_models": {
                "chat_models": chat_models,
                "embedding_models": embedding_models
            },
            "system": {
                "pdfs_dir": str(config.pdfs_dir),
                "vector_store_path": str(config.vector_store_path),
                "max_context_length": config.max_context_length,
                "search_default_k": config.search_default_k
            }
        }
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(500, f"Failed to get configuration: {str(e)}")

@router.put("/config/model")
async def update_model(data: dict):
    """Update model configuration"""
    try:
        success = True
        changes = {}
        
        if "chat_model" in data:
            changes["chat_model"] = data["chat_model"]
            success &= config.update_config("ollama", "chat_model", data["chat_model"])
        
        if "embedding_model" in data:
            changes["embedding_model"] = data["embedding_model"]
            success &= config.update_config("ollama", "embedding_model", data["embedding_model"])
        
        if success:
            return {
                "success": True,
                "message": "Models updated successfully. Changes will take effect immediately.",
                "updated": changes
            }
        else:
            return {
                "success": False,
                "error": "Failed to update configuration file"
            }
            
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        raise HTTPException(500, f"Failed to update model: {str(e)}")
