"""API module - FastAPI routes and schemas.

Router imports are lazy to avoid circular-import chains when
other modules only need ``src.api.schemas``.
"""


def _load_routers():
    """Import all routers (called once at app startup)."""
    from .datasets import router as datasets_router
    from .results import router as results_router
    from .chat import router as chat_router
    from .experiments import router as experiments_router
    from .rag import router as rag_router
    from .models import router as models_router
    from .system import router as system_router
    from .custom_agent import router as agent_router
    from .settings import router as settings_router
    from .uploads import router as uploads_router

    return {
        "datasets_router": datasets_router,
        "results_router": results_router,
        "chat_router": chat_router,
        "experiments_router": experiments_router,
        "rag_router": rag_router,
        "models_router": models_router,
        "system_router": system_router,
        "agent_router": agent_router,
        "settings_router": settings_router,
        "uploads_router": uploads_router,
    }


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
    "uploads_router",
    "_load_routers",
]
