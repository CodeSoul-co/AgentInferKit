"""
Settings API routes.

Implements: model configuration CRUD, API key management, .env editing.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .schemas import ResponseEnvelope

router = APIRouter(tags=["settings"])

# Paths
MODELS_CONFIG_DIR = Path("configs/models")
ENV_FILE = Path(".env")
ENV_EXAMPLE_FILE = Path(".env.example")

SUPPORTED_PROVIDERS = ["deepseek", "openai", "anthropic", "qwen", "ollama", "huggingface"]

# Provider -> env var mapping
PROVIDER_ENV_KEYS = {
    "deepseek": {"api_key": "DEEPSEEK_API_KEY", "base_url": "DEEPSEEK_BASE_URL"},
    "openai": {"api_key": "OPENAI_API_KEY", "base_url": "OPENAI_BASE_URL"},
    "anthropic": {"api_key": "ANTHROPIC_API_KEY"},
    "qwen": {"api_key": "QWEN_API_KEY", "base_url": "QWEN_BASE_URL"},
    "ollama": {},
    "huggingface": {"api_key": "HF_TOKEN"},
}


# =========================================================================
# Schemas
# =========================================================================

class ModelConfigFull(BaseModel):
    """Full model configuration matching YAML format."""
    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model ID")
    base_url: Optional[str] = Field(default=None, description="API base URL (can use ${ENV_VAR})")
    api_key: Optional[str] = Field(default=None, description="API key (can use ${ENV_VAR})")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1, le=128000)
    seed: Optional[int] = Field(default=None)
    system_prompt: Optional[str] = Field(default="You are a helpful assistant.")
    batch_size: int = Field(default=10, ge=1, le=100)
    request_timeout_s: int = Field(default=60, ge=5, le=600)


class ModelConfigListResponse(BaseModel):
    configs: List[Dict[str, Any]] = Field(default_factory=list)


class EnvVarItem(BaseModel):
    key: str
    value: str = ""
    masked: bool = True


class EnvConfigResponse(BaseModel):
    variables: List[EnvVarItem] = Field(default_factory=list)


class EnvUpdateRequest(BaseModel):
    variables: Dict[str, str] = Field(..., description="Key-value pairs to update in .env")


# =========================================================================
# Helpers
# =========================================================================

def _read_env_file() -> Dict[str, str]:
    """Read .env file into a dict."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def _write_env_file(updates: Dict[str, str]):
    """Update .env file, preserving comments and structure."""
    lines = []
    existing_keys = set()

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in updates:
                    lines.append(f"{key}={updates[key]}")
                    existing_keys.add(key)
                else:
                    lines.append(line)
            else:
                lines.append(line)

    # Append new keys
    for key, value in updates.items():
        if key not in existing_keys:
            lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Also update os.environ so changes take effect immediately
    for key, value in updates.items():
        os.environ[key] = value


def _mask_value(value: str) -> str:
    """Mask sensitive values, showing only last 4 chars."""
    if not value or value.startswith("${"):
        return value
    if len(value) <= 8:
        return "****"
    return "****" + value[-4:]


def _load_model_yaml(provider: str) -> Optional[Dict[str, Any]]:
    """Load a single model YAML config."""
    config_file = MODELS_CONFIG_DIR / f"{provider}.yaml"
    if not config_file.exists():
        return None
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _save_model_yaml(provider: str, config: Dict[str, Any]):
    """Save model config to YAML."""
    MODELS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file = MODELS_CONFIG_DIR / f"{provider}.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


# =========================================================================
# Model Config Endpoints
# =========================================================================

@router.get(
    "/models",
    response_model=ResponseEnvelope[ModelConfigListResponse],
    summary="List all model configurations with full parameters",
)
async def list_model_configs():
    """Return full YAML config for each provider."""
    configs = []
    for provider in SUPPORTED_PROVIDERS:
        data = _load_model_yaml(provider)
        if data:
            data["_provider_file"] = provider
            # Check if API key is configured
            env_keys = PROVIDER_ENV_KEYS.get(provider, {})
            api_key_env = env_keys.get("api_key")
            data["_api_key_configured"] = bool(
                api_key_env and os.environ.get(api_key_env)
            ) if api_key_env else True
            configs.append(data)

    return ResponseEnvelope(data=ModelConfigListResponse(configs=configs))


@router.get(
    "/models/{provider}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Get model config for a provider",
)
async def get_model_config(provider: str):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    data = _load_model_yaml(provider)
    if not data:
        raise HTTPException(status_code=404, detail=f"No config for provider: {provider}")
    return ResponseEnvelope(data=data)


@router.put(
    "/models/{provider}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Update model config for a provider",
)
async def update_model_config(provider: str, config: Dict[str, Any]):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    # Remove internal fields
    config.pop("_provider_file", None)
    config.pop("_api_key_configured", None)

    _save_model_yaml(provider, config)
    return ResponseEnvelope(data={"provider": provider, "status": "saved"})


@router.post(
    "/models/{provider}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Create a new model config for a provider",
)
async def create_model_config(provider: str, config: Dict[str, Any]):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    existing = _load_model_yaml(provider)
    if existing:
        raise HTTPException(status_code=409, detail=f"Config for {provider} already exists. Use PUT to update.")

    config.pop("_provider_file", None)
    config.pop("_api_key_configured", None)

    _save_model_yaml(provider, config)
    return ResponseEnvelope(data={"provider": provider, "status": "created"})


@router.delete(
    "/models/{provider}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Delete model config for a provider",
)
async def delete_model_config(provider: str):
    config_file = MODELS_CONFIG_DIR / f"{provider}.yaml"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail=f"No config for provider: {provider}")
    config_file.unlink()
    return ResponseEnvelope(data={"provider": provider, "status": "deleted"})


# =========================================================================
# Environment / API Key Endpoints
# =========================================================================

@router.get(
    "/env",
    response_model=ResponseEnvelope[EnvConfigResponse],
    summary="List environment variables (API keys masked)",
)
async def list_env_vars():
    """Return all .env variables with sensitive values masked."""
    env = _read_env_file()

    # Also include expected keys from .env.example that might not be set
    if ENV_EXAMPLE_FILE.exists():
        for line in ENV_EXAMPLE_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key = line.split("=", 1)[0].strip()
                if key not in env:
                    env[key] = ""

    items = []
    for key, value in sorted(env.items()):
        is_sensitive = any(kw in key.upper() for kw in ["KEY", "TOKEN", "SECRET", "PASSWORD"])
        items.append(EnvVarItem(
            key=key,
            value=_mask_value(value) if is_sensitive and value else value,
            masked=is_sensitive and bool(value),
        ))

    return ResponseEnvelope(data=EnvConfigResponse(variables=items))


@router.put(
    "/env",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Update environment variables",
)
async def update_env_vars(req: EnvUpdateRequest):
    """Update .env file and os.environ."""
    _write_env_file(req.variables)
    return ResponseEnvelope(data={"updated": list(req.variables.keys()), "status": "saved"})
