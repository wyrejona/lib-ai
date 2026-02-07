"""
System management API endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import psutil
import requests
from datetime import datetime, timezone
import logging
from pathlib import Path
import subprocess
import json
import asyncio
from fastapi.responses import StreamingResponse

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
    templates = Jinja2Templates(directory=str(config.templates_dir))
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": config.app_name,
        "app_version": config.app_version,
        "current_model": config.chat_model
    })

# Root-level routes (for frontend compatibility)
@router.get("/config")
async def get_configuration():
    """Get current configuration and available models - root endpoint for frontend"""
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
        
        # Get installed models
        installed_models = []
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 2:
                            installed_models.append(parts[0])
        except:
            installed_models = []
        
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
            "installed_models": installed_models,
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

@router.get("/system/status")
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
    """System health check - root endpoint for frontend"""
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

@router.get("/engine-status")
async def engine_status():
    """Get AI engine status for frontend"""
    try:
        # Check vector store
        vector_store_ready = False
        vector_store_path = Path(config.vector_store_path) / "vector_index.bin"
        if vector_store_path.exists():
            vector_store_ready = True
        
        # Check Ollama connection
        ollama_connected = False
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=3)
            ollama_connected = response.status_code == 200
        except:
            pass
        
        return {
            "chatModel": config.chat_model,
            "embeddingModel": config.embedding_model,
            "vectorStore": "Ready" if vector_store_ready else "Not ready",
            "ollamaStatus": "Connected" if ollama_connected else "Disconnected"
        }
        
    except Exception as e:
        logger.error(f"Error in engine-status: {e}")
        return {
            "chatModel": "Unknown",
            "embeddingModel": "Unknown",
            "vectorStore": "Error checking",
            "ollamaStatus": "Error checking"
        }

# ========== MODEL MANAGEMENT ENDPOINTS ==========

@router.get("/models/list")
async def list_all_models():
    """Get all available and recommended models"""
    # Popular models database
    all_models = {
        "chat": [
            {"name": "qwen:0.5b", "display": "Qwen 0.5B", "size": "0.3GB", "ram": "1GB", "type": "light", "desc": "Very fast, basic tasks"},
            {"name": "phi:2.7b", "display": "Phi 2.7B", "size": "1.6GB", "ram": "3GB", "type": "balanced", "desc": "Good performance, efficient"},
            {"name": "mistral:7b", "display": "Mistral 7B", "size": "4.2GB", "ram": "8GB", "type": "recommended", "desc": "Fast, great for coding"},
            {"name": "llama3:8b", "display": "Llama 3 8B", "size": "4.7GB", "ram": "10GB", "type": "recommended", "desc": "Excellent all-around"},
            {"name": "llama3:70b", "display": "Llama 3 70B", "size": "40GB", "ram": "80GB", "type": "powerful", "desc": "High quality, professional"},
            {"name": "tinyllama:1.1b", "display": "TinyLlama 1.1B", "size": "0.7GB", "ram": "1.5GB", "type": "light", "desc": "Fastest, for testing"}
        ],
        "embedding": [
            {"name": "all-minilm:latest", "display": "All-MiniLM", "size": "0.2GB", "ram": "1GB", "type": "light", "desc": "Fast, good accuracy"},
            {"name": "nomic-embed-text:latest", "display": "Nomic Embed", "size": "0.4GB", "ram": "2GB", "type": "recommended", "desc": "Best overall, long context"},
            {"name": "mxbai-embed-large:latest", "display": "MXBAI Large", "size": "0.8GB", "ram": "3GB", "type": "powerful", "desc": "High quality embeddings"}
        ]
    }
    
    # Get installed models
    installed = []
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        installed.append(parts[0])
    except:
        pass
    
    return {
        "all_models": all_models,
        "installed": installed,
        "current_chat": config.chat_model,
        "current_embedding": config.embedding_model
    }

@router.post("/models/install")
async def install_model(request: Request):
    """Install a model"""
    try:
        data = await request.json()
        model = data.get("model")
        
        if not model:
            return JSONResponse({"success": False, "error": "No model specified"})
        
        async def generate():
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", model,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                output = line.decode().strip()
                if output:
                    yield f"data: {json.dumps({'message': output})}\n\n"
            
            await process.wait()
            if process.returncode == 0:
                yield f"data: {json.dumps({'success': True, 'message': f'Model {model} installed'})}\n\n"
            else:
                yield f"data: {json.dumps({'error': f'Failed to install {model}'})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Install error: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@router.post("/models/remove")
async def remove_model(request: Request):
    """Remove a model"""
    try:
        data = await request.json()
        model = data.get("model")
        
        if not model:
            return JSONResponse({"success": False, "error": "No model specified"})
        
        result = subprocess.run(
            ["ollama", "rm", model],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return JSONResponse({"success": True, "message": f"Model {model} removed"})
        else:
            return JSONResponse({"success": False, "error": result.stderr})
            
    except Exception as e:
        logger.error(f"Remove error: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@router.get("/models/recommend")
async def recommend_models():
    """Get model recommendations based on system resources"""
    try:
        mem = psutil.virtual_memory()
        available_gb = mem.available / 1024**3
        
        recommendations = {
            "chat": [],
            "embedding": [],
            "system_ram": round(available_gb, 1)
        }
        
        # Recommend based on available RAM
        if available_gb > 50:
            recommendations["chat"] = [
                {"name": "llama3:70b", "reason": "Plenty of RAM for high-quality models"},
                {"name": "mixtral:8x7b", "reason": "Expert model for demanding tasks"}
            ]
        elif available_gb > 8:
            recommendations["chat"] = [
                {"name": "llama3:8b", "reason": "Balanced performance"},
                {"name": "mistral:7b", "reason": "Efficient and fast"}
            ]
        elif available_gb > 2:
            recommendations["chat"] = [
                {"name": "phi:2.7b", "reason": "Good for limited RAM"},
                {"name": "qwen:0.5b", "reason": "Very fast, basic tasks"}
            ]
        else:
            recommendations["chat"] = [
                {"name": "tinyllama:1.1b", "reason": "Minimal RAM usage"}
            ]
        
        # Always recommend these embeddings
        recommendations["embedding"] = [
            {"name": "nomic-embed-text:latest", "reason": "Best overall quality"},
            {"name": "all-minilm:latest", "reason": "Fast and lightweight"}
        ]
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Recommend error: {e}")
        return {"error": str(e)}
