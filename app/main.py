from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
from app.config import config

# Initialize FastAPI
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="University of Embu Library Support AI"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory=str(config.templates_dir))

# Mount static files
if config.static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(config.static_dir)), name="static")

# Import API routes
from app.api import chat, files, system, tasks

# Register API routes
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

# Import and register web routes
from app.api.chat import web_routes as chat_web_routes
from app.api.files import web_routes as files_web_routes
from app.api.system import web_routes as system_web_routes

app.include_router(chat_web_routes)
app.include_router(files_web_routes)
app.include_router(system_web_routes)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Library Support AI is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
