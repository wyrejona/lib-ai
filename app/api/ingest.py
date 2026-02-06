"""
Ingestion API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import subprocess
from pathlib import Path
import logging
from datetime import datetime

from app.config import config
from app.core.vector_store import VectorStore

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stream")
async def stream_ingestion():
    """Stream ingestion process logs"""
    async def log_generator():
        ingest_script = Path.cwd() / "ingest.py"
        
        if not ingest_script.exists():
            yield "❌ Error: ingest.py not found\n"
            yield f"Looked for: {ingest_script}\n"
            return
        
        # Check if PDFs exist
        pdf_files = list(config.pdfs_dir.glob("*.pdf"))
        if not pdf_files:
            yield "❌ No PDF files found in pdfs/ directory\n"
            yield "Please upload PDF files first using the /files page\n"
            return
        
        yield f"🚀 Starting ingestion of {len(pdf_files)} PDF files...\n"
        yield "=" * 50 + "\n"
        
        # Run python script unbuffered
        process = subprocess.Popen(
            ["python3", "-u", str(ingest_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output line by line
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                yield line

        # Final status
        if process.returncode == 0:
            yield "\n" + "=" * 50 + "\n"
            yield "✅ Ingestion Completed Successfully!\n"
            
            # Reload vector store
            try:
                vector_store = VectorStore()
                vector_store.load()
                if vector_store.loaded:
                    yield f"✅ Vector store loaded with {len(vector_store.chunks)} chunks\n"
                else:
                    yield "⚠️ Vector store could not be loaded\n"
            except Exception as e:
                yield f"⚠️ Warning: Could not reload vector store: {e}\n"
        else:
            yield f"\n❌ Process failed with exit code {process.returncode}\n"

    return StreamingResponse(log_generator(), media_type="text/plain")

@router.post("/start")
async def start_ingestion(background_tasks: BackgroundTasks):
    """Start ingestion in background"""
    try:
        # Check if PDFs exist
        pdf_files = list(config.pdfs_dir.glob("*.pdf"))
        if not pdf_files:
            raise HTTPException(400, "No PDF files found. Please upload PDFs first.")
        
        # Generate task ID
        task_id = f"ingest_{int(datetime.now().timestamp())}"
        
        # Start background task
        background_tasks.add_task(run_ingestion_background, task_id)
        
        return {
            "task_id": task_id,
            "message": f"Started ingestion of {len(pdf_files)} PDF files",
            "status": "started",
            "monitor_url": f"/api/tasks/progress/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start ingestion: {e}")
        raise HTTPException(500, f"Failed to start ingestion: {str(e)}")

def run_ingestion_background(task_id: str):
    """Background ingestion task"""
    from app.api.tasks import update_task_progress
    
    try:
        update_task_progress(task_id, 0, "Starting ingestion...")
        
        ingest_script = Path.cwd() / "ingest.py"
        if not ingest_script.exists():
            update_task_progress(task_id, 0, "Ingestion script not found", "failed")
            return
        
        # Run ingestion
        process = subprocess.Popen(
            ["python3", "-u", str(ingest_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output
        lines = []
        for line in process.stdout:
            lines.append(line)
            # Update progress based on lines
            progress = min(90, len(lines) // 2)
            update_task_progress(task_id, progress, f"Processing... ({len(lines)} lines)")
        
        process.wait()
        
        if process.returncode == 0:
            # Load vector store
            vector_store = VectorStore()
            vector_store.load()
            
            if vector_store.loaded:
                update_task_progress(task_id, 100, 
                    f"Ingestion complete! {len(vector_store.chunks)} chunks loaded.", 
                    "completed")
            else:
                update_task_progress(task_id, 100, 
                    "Ingestion completed but vector store not loaded.", 
                    "completed")
        else:
            update_task_progress(task_id, 0, 
                f"Ingestion failed (exit code: {process.returncode})", 
                "failed")
                
    except Exception as e:
        logger.error(f"Ingestion task failed: {e}")
        update_task_progress(task_id, 0, f"Ingestion failed: {str(e)}", "failed")

@router.get("/reload")
async def reload_vector_store():
    """Manually reload the vector store"""
    try:
        vector_store = VectorStore()
        vector_store.load()
        
        return {
            "success": True,
            "loaded": vector_store.loaded,
            "chunks_count": len(vector_store.chunks) if vector_store.loaded else 0,
            "embedding_model": vector_store.embedding_model,
            "message": "Vector store reloaded" if vector_store.loaded else "Vector store not loaded"
        }
    except Exception as e:
        logger.error(f"Failed to reload vector store: {e}")
        raise HTTPException(500, f"Failed to reload vector store: {str(e)}")

@router.get("/status")
async def get_ingestion_status():
    """Get ingestion and vector store status"""
    try:
        # Check PDFs
        pdf_files = list(config.pdfs_dir.glob("*.pdf"))
        
        # Check vector store
        vector_store = VectorStore()
        vector_store.load()
        
        return {
            "pdfs": {
                "count": len(pdf_files),
                "directory": str(config.pdfs_dir),
                "exists": config.pdfs_dir.exists()
            },
            "vector_store": {
                "loaded": vector_store.loaded,
                "chunks": len(vector_store.chunks) if vector_store.loaded else 0,
                "path": str(config.vector_store_path),
                "index_exists": (config.vector_store_path / "vector_index.bin").exists(),
                "metadata_exists": (config.vector_store_path / "metadata.pkl").exists()
            },
            "ready_for_chat": vector_store.loaded and len(pdf_files) > 0,
            "message": "Ready for chat" if vector_store.loaded else "Run ingestion first"
        }
    except Exception as e:
        logger.error(f"Failed to get ingestion status: {e}")
        raise HTTPException(500, f"Failed to get ingestion status: {str(e)}")
