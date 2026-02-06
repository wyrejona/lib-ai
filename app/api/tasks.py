"""
Background task management API endpoints
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
import threading
import time
import subprocess
import requests
from datetime import datetime, timezone
import logging
from pathlib import Path  # ADD THIS IMPORT - it's missing

from app.config import config

router = APIRouter()
logger = logging.getLogger(__name__)

# Global variables for task tracking
progress_data = {}
task_lock = threading.Lock()

def update_task_progress(task_id: str, progress: int, message: str, status: str = "running"):
    """Update task progress in a thread-safe way"""
    with task_lock:
        if task_id not in progress_data:
            progress_data[task_id] = {
                "task_id": task_id,
                "progress": 0,
                "message": "",
                "status": "pending",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "logs": []
            }
        
        progress_data[task_id]["progress"] = progress
        progress_data[task_id]["message"] = message
        progress_data[task_id]["status"] = status
        
        if status in ["completed", "failed", "cancelled"]:
            progress_data[task_id]["end_time"] = datetime.now(timezone.utc).isoformat()
            progress_data[task_id]["duration"] = (
                datetime.now(timezone.utc) - 
                datetime.fromisoformat(progress_data[task_id]["start_time"].replace('Z', '+00:00'))
            ).total_seconds()
        
        # Keep log of last 100 messages
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        progress_data[task_id]["logs"].append(log_entry)
        if len(progress_data[task_id]["logs"]) > 100:
            progress_data[task_id]["logs"] = progress_data[task_id]["logs"][-100:]

async def start_reindex_task(background_tasks: BackgroundTasks):
    """Start reindexing task"""
    try:
        # Check if PDFs exist
        pdf_files = list(config.pdfs_dir.glob("*.pdf"))
        if not pdf_files:
            raise HTTPException(400, "No PDF files found. Please upload PDFs first.")
        
        # Generate task ID
        timestamp = int(time.time())
        task_id = f"reindex_{timestamp}"
        
        # Start reindexing task
        background_tasks.add_task(reindex_task, task_id)
        
        return {
            "task_id": task_id,
            "message": f"Started reindexing {len(pdf_files)} documents",
            "status": "started",
            "monitor_url": f"/api/tasks/progress/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting reindex task: {e}")
        raise HTTPException(500, f"Failed to start reindexing: {str(e)}")

@router.post("/start/reindex")
async def start_reindex_api(background_tasks: BackgroundTasks):
    """API endpoint to start reindexing"""
    return await start_reindex_task(background_tasks)

def reindex_task(task_id: str):
    """Background task for reindexing documents"""
    try:
        update_task_progress(task_id, 0, "Starting reindexing process...")
        
        # Check if there are PDFs to process
        pdf_files = list(config.pdfs_dir.glob("*.pdf"))
        if not pdf_files:
            update_task_progress(task_id, 100, "No PDF files found to process", "completed")
            return
        
        total_files = len(pdf_files)
        
        # Run actual ingestion
        update_task_progress(task_id, 10, f"Found {total_files} PDF files")
        
        # Run the ingest.py script
        ingest_script = "ingest.py"
        if not Path(ingest_script).exists():  # This line needs Path imported
            update_task_progress(task_id, 0, f"Ingestion script {ingest_script} not found", "failed")
            return
        
        update_task_progress(task_id, 20, "Running ingestion script...")
        
        process = subprocess.Popen(
            ["python3", "-u", ingest_script],
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
            progress = 20 + min(70, len(lines) // 2)
            update_task_progress(task_id, progress, f"Processing... line {len(lines)}")
        
        process.wait()
        
        if process.returncode == 0:
            update_task_progress(task_id, 95, "Ingestion complete, loading vector store...")
            
            # Load vector store
            from app.core.vector_store import VectorStore
            vector_store = VectorStore()
            vector_store.load()
            
            if vector_store.loaded:
                update_task_progress(task_id, 100, 
                    f"Reindexing complete! {len(vector_store.chunks)} chunks loaded.", 
                    "completed")
            else:
                update_task_progress(task_id, 100, 
                    "Reindexing completed but vector store not loaded.", 
                    "completed")
        else:
            update_task_progress(task_id, 0, 
                f"Reindexing failed (exit code: {process.returncode})", 
                "failed")
                
    except Exception as e:
        logger.error(f"Reindexing task failed: {e}")
        update_task_progress(task_id, 0, f"Reindexing failed: {str(e)}", "failed")

@router.get("/progress/{task_id}")
async def get_task_progress(task_id: str):
    """Get progress of a long-running task"""
    with task_lock:
        if task_id in progress_data:
            task_info = progress_data[task_id].copy()
            
            # Calculate estimated time remaining if still running
            if task_info["status"] == "running":
                start_time = datetime.fromisoformat(task_info["start_time"].replace('Z', '+00:00'))
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                if task_info["progress"] > 0:
                    estimated_total = elapsed / (task_info["progress"] / 100)
                    remaining = estimated_total - elapsed
                    task_info["estimated_remaining_seconds"] = max(0, int(remaining))
                    task_info["elapsed_seconds"] = int(elapsed)
            
            return task_info
        else:
            raise HTTPException(404, f"Task {task_id} not found")

@router.get("/active")
async def get_active_tasks():
    """Get list of active tasks"""
    with task_lock:
        active_tasks = [
            {
                "task_id": task_id,
                "type": task_id.split('_')[0],
                "progress": info["progress"],
                "message": info["message"],
                "status": info["status"],
                "start_time": info["start_time"]
            }
            for task_id, info in progress_data.items()
            if info["status"] == "running"
        ]
        
        completed_tasks = [
            {
                "task_id": task_id,
                "type": task_id.split('_')[0],
                "progress": info["progress"],
                "status": info["status"],
                "start_time": info["start_time"],
                "end_time": info.get("end_time"),
                "duration": info.get("duration")
            }
            for task_id, info in progress_data.items()
            if info["status"] in ["completed", "failed", "cancelled"]
        ][-10:]  # Last 10 completed tasks
        
        return {
            "active": active_tasks,
            "recent": completed_tasks,
            "total_tasks": len(progress_data)
        }

@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task"""
    with task_lock:
        if task_id in progress_data:
            if progress_data[task_id]["status"] == "running":
                progress_data[task_id]["status"] = "cancelled"
                progress_data[task_id]["message"] = "Task cancelled by user"
                progress_data[task_id]["end_time"] = datetime.now(timezone.utc).isoformat()
                return {"status": "cancelled", "task_id": task_id}
            else:
                return {"status": "not_running", "task_id": task_id}
        else:
            raise HTTPException(404, f"Task {task_id} not found")
