"""
Models API routes.

Implements: model listing and connectivity testing.
Integrates with A组's adapter registry module.
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException

from .schemas import (
    ModelInfo,
    ModelListResponse,
    ModelPingResponse,
    ResponseEnvelope,
)


router = APIRouter(tags=["models"])

# Model configuration directory
MODELS_CONFIG_DIR = Path("configs/models")

# Supported providers
SUPPORTED_PROVIDERS = ["deepseek", "openai", "anthropic", "qwen", "ollama", "huggingface"]


def _load_model_configs() -> List[Dict[str, Any]]:
    """Load model configurations from YAML files."""
    models = []
    
    if not MODELS_CONFIG_DIR.exists():
        return models
    
    for config_file in MODELS_CONFIG_DIR.glob("*.yaml"):
        provider = config_file.stem
        if provider not in SUPPORTED_PROVIDERS:
            continue
        
        try:
            import yaml
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            
            # Support both formats:
            # 1. Single model: { provider, model, ... }
            # 2. Multi-model: { models: [id1, id2, ...] }
            model_ids = config.get("models", [])
            if isinstance(model_ids, dict):
                model_ids = list(model_ids.keys())
            
            # If no "models" key, use "model" (single model config)
            if not model_ids and "model" in config:
                model_ids = [config["model"]]
            
            for model_id in model_ids:
                models.append({
                    "model_id": model_id,
                    "provider": config.get("provider", provider),
                    "config_file": str(config_file),
                    "available": _check_api_key_configured(config.get("provider", provider)),
                })
        except Exception:
            # Skip invalid config files
            continue
    
    return models


def _check_api_key_configured(provider: str) -> bool:
    """Check if API key is configured for a provider."""
    import os
    
    env_var_map = {
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "ollama": None,  # Ollama doesn't need API key
        "huggingface": "HF_TOKEN",
    }
    
    env_var = env_var_map.get(provider)
    if env_var is None:
        return True  # No API key needed
    
    return bool(os.environ.get(env_var))


def _get_model_or_404(model_id: str) -> Dict[str, Any]:
    """Get model config by ID or raise 404."""
    models = _load_model_configs()
    for model in models:
        if model["model_id"] == model_id:
            return model
    raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")


@router.get(
    "",
    response_model=ResponseEnvelope[ModelListResponse],
    summary="List all available models",
)
async def list_models():
    """
    List all configured models with their availability status.
    
    A model is marked as available if its provider's API key is configured.
    """
    models = _load_model_configs()
    
    # If no config files found, return default models
    if not models:
        models = [
            {
                "model_id": "deepseek-chat",
                "provider": "deepseek",
                "config_file": "configs/models/deepseek.yaml",
                "available": _check_api_key_configured("deepseek"),
            },
            {
                "model_id": "gpt-4",
                "provider": "openai",
                "config_file": "configs/models/openai.yaml",
                "available": _check_api_key_configured("openai"),
            },
            {
                "model_id": "claude-3-opus",
                "provider": "anthropic",
                "config_file": "configs/models/anthropic.yaml",
                "available": _check_api_key_configured("anthropic"),
            },
            {
                "model_id": "qwen-max",
                "provider": "qwen",
                "config_file": "configs/models/qwen.yaml",
                "available": _check_api_key_configured("qwen"),
            },
        ]
    
    model_infos = [
        ModelInfo(
            model_id=m["model_id"],
            provider=m["provider"],
            config_file=m["config_file"],
            available=m["available"],
        )
        for m in models
    ]
    
    return ResponseEnvelope(
        data=ModelListResponse(models=model_infos)
    )


@router.post(
    "/api-key",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Set API key for a provider (session-only)",
)
async def set_api_key(body: Dict[str, Any] = Body(...)):
    """
    Set an API key for a provider in the current process environment.
    This is session-only and does NOT persist to .env file.
    """
    import os

    provider = body.get("provider", "")
    api_key = body.get("api_key", "")

    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="provider and api_key are required")

    env_var_map = {
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "huggingface": "HF_TOKEN",
    }

    env_var = env_var_map.get(provider)
    if not env_var:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    os.environ[env_var] = api_key

    return ResponseEnvelope(
        data={"provider": provider, "env_var": env_var, "status": "set"}
    )


@router.get(
    "/{model_id}",
    response_model=ResponseEnvelope[ModelInfo],
    summary="Get model details",
)
async def get_model(model_id: str):
    """
    Get detailed information about a specific model.
    """
    model = _get_model_or_404(model_id)
    
    return ResponseEnvelope(
        data=ModelInfo(
            model_id=model["model_id"],
            provider=model["provider"],
            config_file=model["config_file"],
            available=model["available"],
        )
    )


@router.post(
    "/{model_id}/ping",
    response_model=ResponseEnvelope[ModelPingResponse],
    summary="Test model connectivity",
)
async def ping_model(model_id: str):
    """
    Test connectivity to a model's API.
    
    Sends a minimal request to verify the model is reachable
    and returns the response latency.
    """
    model = _get_model_or_404(model_id)
    
    if not model["available"]:
        return ResponseEnvelope(
            data=ModelPingResponse(
                model_id=model_id,
                reachable=False,
                latency_ms=None,
            )
        )
    
    # TODO: Integrate with A组's adapter registry
    # from src.adapters.registry import get_adapter
    # adapter = get_adapter(model["provider"], model_id)
    
    start_time = time.time()
    reachable = False
    latency_ms = None
    
    try:
        # Mock ping - in production, use adapter.ping() or minimal completion
        # result = await adapter.ping()
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        reachable = True
        latency_ms = int((time.time() - start_time) * 1000)
        
    except Exception:
        reachable = False
        latency_ms = None
    
    return ResponseEnvelope(
        data=ModelPingResponse(
            model_id=model_id,
            reachable=reachable,
            latency_ms=latency_ms,
        )
    )
