from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import subprocess
import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any
from app.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory task store
tasks_db = {}

async def run_ingestion(ingest_script: Path, task_id: str):
    """Run ingestion with progress tracking"""
    tasks_db[task_id] = {
        "id": task_id,
        "type": "ingestion",
        "status": "running",
        "progress": 0,
        "logs": [],
        "start_time": time.time()
    }
    
    try:
        process = await asyncio.create_subprocess_exec(
            "python3", str(ingest_script),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Read output line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            output = line.decode().strip()
            tasks_db[task_id]["logs"].append(output)
            
            # Update progress based on output
            if "Processing" in output:
                tasks_db[task_id]["progress"] = min(90, tasks_db[task_id].get("progress", 0) + 10)
            elif "complete" in output.lower():
                tasks_db[task_id]["progress"] = 100
        
        await process.wait()
        
        if process.returncode == 0:
            tasks_db[task_id]["status"] = "completed"
            tasks_db[task_id]["progress"] = 100
        else:
            tasks_db[task_id]["status"] = "failed"
            error = await process.stderr.read()
            tasks_db[task_id]["error"] = error.decode()
            
    except Exception as e:
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)
    finally:
        tasks_db[task_id]["end_time"] = time.time()

@router.post("/ingest")
async def start_ingestion(background_tasks: BackgroundTasks):
    """Start ingestion process"""
    ingest_script = config.project_root / "ingest.py"
    
    if not ingest_script.exists():
        raise HTTPException(404, "ingest.py not found")
    
    task_id = f"ingest_{int(time.time())}"
    
    # Start in background
    background_tasks.add_task(run_ingestion, ingest_script, task_id)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Ingestion started",
        "monitor_url": f"/api/tasks/{task_id}"
    }

@router.get("/ingest/stream")
async def stream_ingestion():
    """Stream ingestion logs in real-time"""
    ingest_script = config.project_root / "ingest.py"
    
    async def event_generator():
        if not ingest_script.exists():
            yield "data: ❌ Error: ingest.py not found\n\n"
            return
        
        # Run the ingestion process
        process = await asyncio.create_subprocess_exec(
            "python3", "-u", str(ingest_script),  # -u for unbuffered
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        yield "data: 🚀 Starting ingestion process...\n\n"
        
        # Stream output
        while True:
            line = await process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                output = line.decode().strip()
                yield f"data: {output}\n\n"
        
        # Final status
        if process.returncode == 0:
            yield "data: ✅ Ingestion completed successfully!\n\n"
        else:
            yield f"data: ❌ Process failed with exit code {process.returncode}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering for nginx
        }
    )

@router.get("tasks/active")
async def get_active_tasks():
    """Get active tasks"""
    active_tasks = {}
    for task_id, task in tasks_db.items():
        if task.get("status") in ["running", "pending"]:
            active_tasks[task_id] = task
    
    return {
        "tasks": active_tasks,
        "count": len(active_tasks)
    }

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    
    return task

@router.get("/")
async def list_tasks():
    """List all tasks"""
    return {
        "tasks": list(tasks_db.values()),
        "count": len(tasks_db)
    }

@router.post("/reindex")
async def reindex():
    """Reindex documents"""
    # This would trigger a re-ingestion
    ingest_script = config.project_root / "ingest.py"
    
    if not ingest_script.exists():
        raise HTTPException(404, "ingest.py not found")
    
    task_id = f"reindex_{int(time.time())}"
    
    # Start in background
    asyncio.create_task(run_ingestion(ingest_script, task_id))
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Reindexing started",
        "monitor_url": f"/api/tasks/{task_id}"
    }
