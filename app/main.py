from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path
import os
import math

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
from app.config import config

# Import API routes
from app.api import chat, files, system, tasks

# Initialize FastAPI
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="University of Embu Library Support AI"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files directory - ADD THIS
static_dir = config.project_root / "static"
static_dir.mkdir(parents=True, exist_ok=True)  # Create if doesn't exist
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(config.templates_dir))

# Add custom template filters - ADD THIS
def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 Bytes"
    
    size_names = ("Bytes", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def format_timestamp(timestamp):
    """Format timestamp"""
    from datetime import datetime
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return str(timestamp)

# Register filters with Jinja2 - ADD THIS
templates.env.filters["format_file_size"] = format_file_size
templates.env.filters["format_timestamp"] = format_timestamp

# Include API routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

# Simple homepage
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": config.app_name,
        "app_version": config.app_version
    })

# Chat page
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

# Files page
@app.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    return templates.TemplateResponse("files.html", {"request": request})

@app.get("/models", response_class=HTMLResponse)
async def models_page(request: Request):
    return templates.TemplateResponse("models.html", {
        "request": request,
        "app_name": config.app_name,
        "app_version": config.app_version
    })

@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"routes": routes}

@app.get("/debug/api-routes")
async def debug_api_routes():
    """Debug only API routes"""
    api_routes = []
    for route in app.routes:
        if hasattr(route, "path") and route.path.startswith("/api"):
            api_routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"api_routes": api_routes}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": config.app_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
