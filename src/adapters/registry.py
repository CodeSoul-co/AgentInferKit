from typing import Any, Dict

from src.adapters.base import BaseModelAdapter


# Provider name -> adapter class mapping
_PROVIDER_MAP: Dict[str, type] = {}


def _register_providers() -> None:
    """Lazily register all built-in provider adapters."""
    if _PROVIDER_MAP:
        return

    from src.adapters.deepseek import DeepSeekAdapter
    from src.adapters.openai import OpenAIAdapter
    from src.adapters.anthropic import AnthropicAdapter
    from src.adapters.qwen import QwenAdapter
    from src.adapters.huggingface import HuggingFaceAdapter
    from src.adapters.ollama import OllamaAdapter

    _PROVIDER_MAP.update(
        {
            "deepseek": DeepSeekAdapter,
            "openai": OpenAIAdapter,
            "anthropic": AnthropicAdapter,
            "qwen": QwenAdapter,
            "huggingface": HuggingFaceAdapter,
            "ollama": OllamaAdapter,
        }
    )


def load_adapter(config: Dict[str, Any]) -> BaseModelAdapter:
    """Instantiate a model adapter based on config['provider'].

    Args:
        config: A dict typically loaded from configs/models/*.yaml.
                Must contain a 'provider' key (e.g. 'deepseek', 'openai').
                Remaining keys are passed to the adapter constructor.

    Returns:
        An instance of the corresponding BaseModelAdapter subclass.

    Raises:
        ValueError: If the provider is unknown.
    """
    _register_providers()

    provider = config.get("provider", "")
    if provider not in _PROVIDER_MAP:
        available = ", ".join(sorted(_PROVIDER_MAP.keys()))
        raise ValueError(
            f"Unknown provider '{provider}'. Available: {available}"
        )

    adapter_cls = _PROVIDER_MAP[provider]
    # Remove 'provider' key; pass the rest as constructor kwargs
    adapter_kwargs = {k: v for k, v in config.items() if k != "provider"}
    return adapter_cls(**adapter_kwargs)
