"""API module - FastAPI routes and schemas."""

from .datasets import router as datasets_router
from .results import router as results_router
from .chat import router as chat_router
from .experiments import router as experiments_router
from .rag import router as rag_router
from .models import router as models_router
from .system import router as system_router
from .custom_agent import router as agent_router
from .settings import router as settings_router

__all__ = [
    "datasets_router",
    "results_router",
    "chat_router",
    "experiments_router",
    "rag_router",
    "models_router",
    "system_router",
    "agent_router",
    "settings_router",
]
