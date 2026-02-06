"""
File management API endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
import os
import shutil
from datetime import datetime
from typing import List

from app.config import config
from app.utils import format_file_size

router = APIRouter()

# Web routes
web_routes = APIRouter()

@web_routes.get("/files", response_class=HTMLResponse)
async def manage_files(request: Request):
    """File management page"""
    pdfs_dir = config.pdfs_dir
    files = []
    
    if pdfs_dir.exists():
        for f in os.listdir(pdfs_dir):
            if f.endswith(".pdf"):
                file_path = pdfs_dir / f
                files.append({
                    "name": f,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)),
                    "formatted_size": format_file_size(os.path.getsize(file_path))
                })
    
    files.sort(key=lambda x: x["modified"], reverse=True)
    total_size = format_file_size(sum(f["size"] for f in files) if files else 0)
    
    # Check vector store status (simplified)
    vector_status = "Not processed"
    vector_store_path = config.vector_store_path / "vector_index.bin"
    if vector_store_path.exists():
        vector_status = "Ready"
    
    return config.templates.TemplateResponse("files.html", {
        "request": request,
        "files": files,
        "total_files": len(files),
        "total_size": total_size,
        "vector_status": vector_status,
        "current_model": config.chat_model,
        "embedding_model": config.embedding_model
    })

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload PDF files"""
    uploaded = []
    pdfs_dir = config.pdfs_dir
    
    for file in files:
        if file.filename.lower().endswith('.pdf'):
            path = pdfs_dir / file.filename
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded.append({"name": file.filename})
    
    return {"status": "success", "uploaded": uploaded}

@router.get("/")
async def list_files():
    """List all uploaded files"""
    pdfs_dir = config.pdfs_dir
    files = []
    
    if pdfs_dir.exists():
        for f in os.listdir(pdfs_dir):
            if f.endswith(".pdf"):
                file_path = pdfs_dir / f
                files.append({
                    "name": f,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "formatted_size": format_file_size(os.path.getsize(file_path))
                })
    
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": files, "count": len(files)}

@router.delete("/{filename}")
async def delete_file(filename: str):
    """Delete a file"""
    path = config.pdfs_dir / filename
    if path.exists():
        os.remove(path)
        return {"status": "deleted"}
    raise HTTPException(404, "File not found")

@router.delete("/")
async def clear_all_files():
    """Clear all files and reset vector store"""
    try:
        # Clear PDFs
        pdfs_dir = config.pdfs_dir
        if pdfs_dir.exists():
            for f in os.listdir(pdfs_dir):
                os.remove(pdfs_dir / f)
        
        # Clear vector store
        if config.vector_store_path.exists():
            shutil.rmtree(config.vector_store_path)
            os.makedirs(config.vector_store_path, exist_ok=True)
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))
