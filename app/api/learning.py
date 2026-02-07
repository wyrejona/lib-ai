"""
Learning management API
"""
from fastapi import APIRouter, BackgroundTasks
import logging

from app.core.smart_continuous_learner import get_smart_learner

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/smart-learning/start")
async def start_smart_learning():
    """Start smart continuous learning"""
    try:
        learner = get_smart_learner()
        learner.start()
        
        return {
            "success": True,
            "message": "Smart continuous learning started",
            "status": learner.get_status()
        }
    except Exception as e:
        logger.error(f"Error starting smart learning: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/smart-learning/stop")
async def stop_smart_learning():
    """Stop smart continuous learning"""
    try:
        learner = get_smart_learner()
        learner.stop()
        
        return {
            "success": True,
            "message": "Smart continuous learning stopped",
            "status": learner.get_status()
        }
    except Exception as e:
        logger.error(f"Error stopping smart learning: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/smart-learning/status")
async def get_smart_learning_status():
    """Get smart learning status"""
    try:
        learner = get_smart_learner()
        
        return {
            "success": True,
            "status": learner.get_status()
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/smart-learning/check-now")
async def force_smart_check():
    """Force immediate smart check"""
    try:
        learner = get_smart_learner()
        learner.force_check()
        
        return {
            "success": True,
            "message": "Smart check initiated",
            "status": learner.get_status()
        }
    except Exception as e:
        logger.error(f"Error forcing check: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/smart-learning/rebuild")
async def rebuild_answers():
    """Rebuild answer database from all PDFs"""
    try:
        learner = get_smart_learner()
        
        # Clear existing data
        learner.direct_answers.clear()
        learner.definitions.clear()
        learner.keywords.clear()
        learner.file_hashes.clear()
        
        # Process all PDFs
        pdf_files = list(learner.pdfs_dir.glob("*.pdf"))
        for pdf_path in pdf_files:
            learner._process_pdf(pdf_path)
        
        # Build common patterns
        learner._build_common_answers()
        
        return {
            "success": True,
            "message": f"Rebuilt from {len(pdf_files)} PDFs",
            "answers": len(learner.direct_answers),
            "definitions": len(learner.definitions),
            "status": learner.get_status()
        }
    except Exception as e:
        logger.error(f"Error rebuilding: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/smart-learning/export")
async def export_to_strict_rag():
    """Export to strict_rag format"""
    try:
        learner = get_smart_learner()
        success = learner.export_to_strict_rag_format()
        
        return {
            "success": success,
            "message": "Exported to strict_rag format" if success else "Export failed",
            "answers": len(learner.direct_answers)
        }
    except Exception as e:
        logger.error(f"Error exporting: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/smart-learning/test/{question}")
async def test_smart_answer(question: str):
    """Test smart answer retrieval"""
    try:
        learner = get_smart_learner()
        answer = learner.get_direct_answer(question)
        
        return {
            "success": True,
            "question": question,
            "found": answer is not None,
            "answer": answer or "No direct answer found"
        }
    except Exception as e:
        logger.error(f"Error testing: {e}")
        return {
            "success": False,
            "error": str(e)
        }
