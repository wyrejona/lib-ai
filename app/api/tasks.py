"""
Background task management API endpoints
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
import threading
import time
import subprocess
import requests
from datetime import datetime, timezone
import logging

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
        
        # Simulate processing (in production, replace with actual ingestion)
        for i, pdf_file in enumerate(pdf_files):
            progress = int((i / total_files) * 100)
            update_task_progress(task_id, progress, f"Processing {pdf_file.name} ({i+1}/{total_files})")
            
            # Simulate processing time
            time.sleep(2)  # Simulate processing time
            
            # TODO: Add actual PDF processing here
            
        update_task_progress(task_id, 100, f"Successfully reindexed {total_files} files", "completed")
        
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        update_task_progress(task_id, 0, f"Reindexing failed: {str(e)}", "failed")

def install_model_task(task_id: str, model_name: str):
    """Background task for installing models"""
    try:
        update_task_progress(task_id, 0, f"Starting installation of {model_name}")
        
        # Check if Ollama is available
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                update_task_progress(task_id, 0, "Ollama is not running or not accessible", "failed")
                return
        except:
            update_task_progress(task_id, 0, "Ollama is not running or not accessible", "failed")
            return
        
        # Run ollama pull command
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output and update progress
        line_count = 0
        max_lines = 50  # Estimated max lines for a pull operation
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                line_count += 1
                progress = min(95, int((line_count / max_lines) * 100))
                
                # Parse progress from ollama output
                line_lower = line.lower()
                if "pulling" in line_lower or "downloading" in line_lower:
                    update_task_progress(task_id, progress, f"Downloading {model_name}: {line.strip()}")
                elif "verifying" in line_lower:
                    update_task_progress(task_id, progress, f"Verifying {model_name}: {line.strip()}")
                elif "success" in line_lower or "complete" in line_lower or "pulled" in line_lower:
                    update_task_progress(task_id, 95, f"Finalizing {model_name}: {line.strip()}")
                else:
                    update_task_progress(task_id, progress, f"Installing {model_name}: {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            update_task_progress(task_id, 100, f"Successfully installed {model_name}", "completed")
        else:
            update_task_progress(task_id, 0, f"Failed to install {model_name} (exit code: {process.returncode})", "failed")
            
    except Exception as e:
        logger.error(f"Model installation failed: {e}")
        update_task_progress(task_id, 0, f"Installation failed: {str(e)}", "failed")

@router.post("/install-model")
async def install_model(request: Request, background_tasks: BackgroundTasks):
    """Install a model via Ollama"""
    try:
        data = await request.json()
        model = data.get("model")
        
        if not model:
            raise HTTPException(status_code=400, detail="Model name required")
        
        # Generate task ID
        task_id = f"install_{model.replace(':', '_')}_{int(time.time())}"
        
        # Start installation in background
        background_tasks.add_task(install_model_task, task_id, model)
        
        return {
            "task_id": task_id,
            "message": f"Started installation of {model}",
            "status": "started",
            "monitor_url": f"/api/tasks/progress/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting model installation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start installation: {str(e)}")

@router.post("/start/{task_type}")
async def start_task(task_type: str, request: Request, background_tasks: BackgroundTasks):
    """Start a long-running task"""
    try:
        data = await request.json() if await request.body() else {}
        
        # Generate task ID
        timestamp = int(time.time())
        task_id = f"{task_type}_{timestamp}"
        
        if task_type == "reindex":
            # Start reindexing task
            background_tasks.add_task(reindex_task, task_id)
            
            return {
                "task_id": task_id,
                "message": "Started reindexing documents",
                "status": "started",
                "monitor_url": f"/api/tasks/progress/{task_id}"
            }
        else:
            raise HTTPException(400, f"Unknown task type: {task_type}")
            
    except Exception as e:
        logger.error(f"Error starting task: {e}")
        raise HTTPException(500, f"Failed to start task: {str(e)}")

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
