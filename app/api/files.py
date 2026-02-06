from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import shutil
import os
from pathlib import Path
import logging
from app.config import config
from app.utils import format_file_size

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def list_files():
    """List uploaded PDF files"""
    files = []
    
    if config.pdfs_dir.exists():
        for f in os.listdir(config.pdfs_dir):
            if f.lower().endswith('.pdf'):
                file_path = config.pdfs_dir / f
                files.append({
                    "name": f,
                    "size": os.path.getsize(file_path),
                    "formatted_size": format_file_size(os.path.getsize(file_path))
                })
    
    return {"files": files, "count": len(files)}

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload PDF files"""
    uploaded = []
    
    for file in files:
        if file.filename.lower().endswith('.pdf'):
            # Secure filename
            safe_name = file.filename.replace(" ", "_")
            path = config.pdfs_dir / safe_name
            
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded.append({"name": safe_name})
    
    return {"uploaded": uploaded, "count": len(uploaded)}

@router.delete("/{filename}")
async def delete_file(filename: str):
    """Delete a file"""
    path = config.pdfs_dir / filename
    
    if not path.exists():
        raise HTTPException(404, "File not found")
    
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files can be deleted")
    
    os.remove(path)
    return {"deleted": filename}