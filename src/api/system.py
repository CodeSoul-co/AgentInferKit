from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "status": "healthy",
            "milvus": "not_checked",
            "version": "1.0.0",
        },
    }


@router.get("/config")
async def get_system_config():
    """Return a summary of loaded models, strategies, datasets, etc."""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "models": [],
            "strategies": [],
            "datasets_count": 0,
            "kbs_count": 0,
            "tools_count": 0,
        },
    }
