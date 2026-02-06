from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from app.core.llm_client import SimpleLLMClient
from app.core.vector_store import SimpleVectorStore
from app.config import config
from app.utils import format_context

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize components
llm_client = SimpleLLMClient()
vector_store = SimpleVectorStore()

@router.post("/chat")
async def chat_endpoint(request: Dict[str, Any]):
    """Simple chat endpoint"""
    try:
        query = request.get("message", "").strip()
        if not query:
            return {"response": "Please enter a question."}
        
        # Load vector store
        vector_store.load()
        
        # TODO: Get embeddings for query (simplified for now)
        # For now, we'll use a placeholder
        if vector_store.loaded:
            # This is simplified - in real implementation, you'd generate embeddings
            results = vector_store.search([0.1] * 384, k=config.search_default_k)  # Placeholder
            context = format_context(results)
        else:
            context = ""
        
        # Generate response
        response = llm_client.generate(query, context)
        
        return {
            "response": response,
            "context_used": bool(context)
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": "Sorry, I encountered an error."}

@router.get("/test")
async def test_chat():
    """Test endpoint"""
    return {"status": "ok", "message": "Chat API is working"}