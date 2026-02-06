from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import shutil
from datetime import datetime
from typing import List
from pathlib import Path

from app.config import config
from app.utils import format_file_size

router = APIRouter()

@router.get("/status")
async def get_files_status():
    """Get file and vector store status"""
    pdfs_dir = Path(config.pdfs_dir)
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
    
    # Check vector store
    vector_store_path = Path(config.vector_store_path) / "vector_index.bin"
    vector_status = "ready" if vector_store_path.exists() else "not_ready"
    
    return {
        "files": files,
        "file_count": len(files),
        "vector_store_status": vector_status
    }

@router.post("/upload")
async def upload_files_api(files: List[UploadFile] = File(...)):
    """Upload PDF files"""
    uploaded = []
    errors = []
    pdfs_dir = Path(config.pdfs_dir)
    pdfs_dir.mkdir(exist_ok=True)
    
    for file in files:
        try:
            if not file.filename.lower().endswith('.pdf'):
                errors.append(f"{file.filename} is not a PDF file")
                continue
            
            filename = file.filename.replace(" ", "_")
            path = pdfs_dir / filename
            
            # Avoid overwriting
            if path.exists():
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                path = pdfs_dir / filename
            
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = path.stat().st_size
            uploaded.append({
                "name": filename,
                "size": file_size,
                "formatted_size": format_file_size(file_size)
            })
            
        except Exception as e:
            errors.append(f"Error uploading {file.filename}: {str(e)}")
    
    return {
        "success": True if uploaded else False,
        "uploaded": uploaded,
        "errors": errors,
        "message": f"Uploaded {len(uploaded)} files"
    }

@router.get("/")
async def list_files():
    """List all uploaded files"""
    pdfs_dir = Path(config.pdfs_dir)
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

@router.get("/download/{filename}")
async def download_file_api(filename: str):
    """Download a file"""
    path = Path(config.pdfs_dir) / filename
    if path.exists() and path.is_file():
        return FileResponse(
            path=path,
            filename=filename,
            media_type='application/pdf'
        )
    raise HTTPException(404, "File not found")

@router.delete("/{filename}")
async def delete_file_api(filename: str):
    """Delete a file"""
    path = Path(config.pdfs_dir) / filename
    if path.exists():
        os.remove(path)
        return {"success": True, "message": f"Deleted {filename}"}
    raise HTTPException(404, "File not found")

@router.delete("/")
async def clear_all_files_api():
    """Clear all files and reset vector store"""
    pdfs_dir = Path(config.pdfs_dir)
    deleted_count = 0
    
    if pdfs_dir.exists():
        for f in os.listdir(pdfs_dir):
            if f.endswith(".pdf"):
                os.remove(pdfs_dir / f)
                deleted_count += 1
    
    # Clear vector store
    vector_store_dir = Path(config.vector_store_path)
    if vector_store_dir.exists():
        shutil.rmtree(vector_store_dir)
    
    # Recreate directory
    vector_store_dir.mkdir(exist_ok=True)
    
    return {
        "success": True,
        "message": f"Cleared {deleted_count} files and reset vector store",
        "deleted_count": deleted_count
    }

@router.post("/process")
async def process_documents_api():
    """Process uploaded documents"""
    try:
        pdf_files = list(Path(config.pdfs_dir).glob("*.pdf"))
        if not pdf_files:
            raise HTTPException(400, "No PDF files found")
        
        import subprocess
        import sys
        
        base_dir = Path(__file__).parent.parent.parent
        ingest_script = base_dir / "ingest.py"
        
        if not ingest_script.exists():
            raise HTTPException(500, "Ingestion script not found")
        
        result = subprocess.run(
            [sys.executable, str(ingest_script)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Processed {len(pdf_files)} documents"
            }
        else:
            return {
                "success": False,
                "message": f"Processing failed: {result.stderr}"
            }
            
    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Processing timeout")
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")
