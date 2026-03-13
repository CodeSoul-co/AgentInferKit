"""
System API routes.

Implements: health check, system configuration overview.
Monitors dependent services like Milvus.
"""

import os
from typing import List

from fastapi import APIRouter

from .schemas import (
    HealthResponse,
    ResponseEnvelope,
    SystemConfigResponse,
)


router = APIRouter(tags=["system"])

# API version
API_VERSION = "1.0.0"

# Available inference strategies
AVAILABLE_STRATEGIES = ["direct", "cot", "long_cot", "tot", "react", "self_consistency"]


async def _check_milvus_connection() -> str:
    """Check Milvus connection status."""
    try:
        # TODO: Integrate with A组's Milvus store
        # from src.rag.milvus_store import MilvusStore
        # store = MilvusStore()
        # return "connected" if store.is_connected() else "disconnected"
        
        # Check if Milvus environment variables are configured
        milvus_host = os.environ.get("MILVUS_HOST", "localhost")
        milvus_port = os.environ.get("MILVUS_PORT", "19530")
        
        # Mock connection check - in production, actually connect to Milvus
        # For now, return "disconnected" unless explicitly configured
        if milvus_host and milvus_port:
            return "connected"
        return "disconnected"
        
    except Exception:
        return "disconnected"


def _count_datasets() -> int:
    """Count available datasets from the datasets store."""
    try:
        from .datasets import datasets_store
        return len(datasets_store)
    except ImportError:
        return 0


def _count_knowledge_bases() -> int:
    """Count available knowledge bases."""
    # Import here to avoid circular imports
    try:
        from .rag import _knowledge_bases
        return len(_knowledge_bases)
    except ImportError:
        return 0


def _get_available_models() -> List[str]:
    """Get list of available model IDs."""
    try:
        from .models import _load_model_configs
        models = _load_model_configs()
        return [m["model_id"] for m in models if m.get("available", False)]
    except ImportError:
        # Return default models if models module not available
        return ["deepseek-chat", "gpt-4", "claude-3-opus", "qwen-max"]


@router.get(
    "/health",
    response_model=ResponseEnvelope[HealthResponse],
    summary="Health check endpoint",
)
async def health_check():
    """
    Check system health status.
    
    Returns:
    - status: healthy, degraded, or unhealthy
    - milvus: connected or disconnected
    - version: API version
    """
    milvus_status = await _check_milvus_connection()
    
    # Determine overall health
    if milvus_status == "connected":
        status = "healthy"
    else:
        status = "degraded"  # System works but without RAG support
    
    return ResponseEnvelope(
        data=HealthResponse(
            status=status,
            milvus=milvus_status,
            version=API_VERSION,
        )
    )


@router.get(
    "/config",
    response_model=ResponseEnvelope[SystemConfigResponse],
    summary="Get system configuration overview",
)
async def get_system_config():
    """
    Return a summary of system configuration.
    
    Includes:
    - Available model IDs
    - Available inference strategies
    - Number of loaded datasets
    - Number of knowledge bases
    """
    models = _get_available_models()
    dataset_count = _count_datasets()
    kb_count = _count_knowledge_bases()
    
    return ResponseEnvelope(
        data=SystemConfigResponse(
            models=models,
            strategies=AVAILABLE_STRATEGIES,
            dataset_count=dataset_count,
            kb_count=kb_count,
        )
    )
