"""
Chat API using Strict RAG
"""
from fastapi import APIRouter
import logging
import time

from app.core.strict_rag import get_strict_response, get_direct_answer

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/query")
async def strict_rag_query(request: dict):
    """Strict RAG query - forces answers from context only"""
    try:
        message = request.get("message", "").strip()
        if not message:
            return {"response": "Please enter a question.", "success": False}
        
        start_time = time.time()
        
        # First try direct answer database
        direct_answer = get_direct_answer(message)
        if direct_answer:
            response = direct_answer
        else:
            # Fall back to strict RAG
            response = get_strict_response(message)
        
        time_taken = round(time.time() - start_time, 2)
        
        return {
            "response": response,
            "success": True,
            "time_taken": time_taken,
            "model": "strict_rag"
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "response": f"Error: {str(e)[:100]}",
            "success": False
        }

@router.post("/chat")
async def legacy_chat_endpoint(request: dict):
    """Legacy endpoint - redirects to strict RAG"""
    return await strict_rag_query(request)

@router.get("/status")
async def chat_status():
    """Check system status"""
    try:
        from app.core.vector_store import VectorStore
        
        vector_store = VectorStore()
        vector_store.load()
        
        return {
            "vector_store_loaded": vector_store.loaded,
            "chunks_count": len(vector_store.chunks) if vector_store.loaded else 0,
            "system": "strict_rag"
        }
    except Exception as e:
        return {"error": str(e)}

# For backward compatibility
async def chat_api(request: dict):
    """For backward compatibility"""
    return await strict_rag_query(request)

__all__ = ['router', 'chat_api']
