# app/api/__init__.py
from .chat import router as chat_router
from .files import router as files_router
from .system import router as system_router
from .tasks import router as tasks_router

__all__ = ["chat_router", "files_router", "system_router", "tasks_router"]
