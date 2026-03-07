import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AppSettings(BaseSettings):
    """Application-level settings loaded from environment variables."""

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_env: str = "development"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # Anthropic
    anthropic_api_key: str = ""

    # Qwen (DashScope)
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # Embedding
    embedding_model: str = "BAAI/bge-m3"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton settings instance
settings = AppSettings()

# Standard directory paths
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_MAPPINGS_DIR = DATA_DIR / "mappings"
DATA_SCHEMAS_DIR = DATA_DIR / "schemas"
DATA_INDEXES_DIR = DATA_DIR / "indexes"

OUTPUTS_PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"
OUTPUTS_METRICS_DIR = OUTPUTS_DIR / "metrics"
OUTPUTS_LOGS_DIR = OUTPUTS_DIR / "logs"
OUTPUTS_FIGURES_DIR = OUTPUTS_DIR / "figures"

TOOL_SCHEMAS_DIR = DATA_SCHEMAS_DIR / "tool_schemas"
