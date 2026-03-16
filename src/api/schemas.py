"""
Pydantic schemas for API request/response models.

This module defines all data models used by the FastAPI routes,
following the unified ResponseEnvelope pattern.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, Field


# =============================================================================
# Core Data Structures (used by adapters, strategies, runners)
# =============================================================================

class Message(BaseModel):
    """Chat message used throughout the inference pipeline."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    image_url: Optional[str] = Field(default=None, description="Optional image URL for vision models")


class GenerateResult(BaseModel):
    """Result from a model adapter generate() call."""
    content: str = Field(default="", description="Generated text content")
    prompt_tokens: Optional[int] = Field(default=0, description="Number of prompt tokens")
    completion_tokens: Optional[int] = Field(default=0, description="Number of completion tokens")
    latency_ms: Optional[float] = Field(default=0.0, description="Latency in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if generation failed")


# =============================================================================
# Generic Response Envelope
# =============================================================================

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Unified API response wrapper.
    
    All endpoints return this structure:
    - code: 0 for success, non-zero for errors
    - message: "ok" on success, error description on failure
    - data: The actual response payload
    """
    code: int = Field(default=0, description="Response code. 0=success, 400=param error, 404=not found, 409=conflict, 500=server error")
    message: str = Field(default="ok", description="Response message")
    data: T = Field(description="Response payload")


# =============================================================================
# Nested Configuration Models
# =============================================================================

class RAGConfig(BaseModel):
    """RAG (Retrieval-Augmented Generation) configuration."""
    enabled: bool = Field(default=False, description="Whether to enable RAG")
    mode: Literal["closed", "oracle", "retrieved"] = Field(
        default="retrieved",
        description="RAG mode: closed (no context), oracle (ground truth chunks), retrieved (auto retrieval)"
    )
    kb_name: Optional[str] = Field(default=None, description="Knowledge base name for retrieval")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of chunks to retrieve")
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score for retrieved chunks (0 = no filtering)")


class RunnerConfig(BaseModel):
    """Task runner configuration."""
    concurrency: int = Field(default=5, ge=1, le=50, description="Number of concurrent inference requests")
    retry_times: int = Field(default=3, ge=0, le=10, description="Number of retries on failure")
    resume: bool = Field(default=True, description="Whether to resume from checkpoint on restart")


class EvalConfig(BaseModel):
    """Evaluation configuration."""
    metrics: List[str] = Field(
        default=[],
        description="List of metrics to compute, e.g., ['exact_match', 'f1_score', 'choice_accuracy']"
    )
    group_by: List[str] = Field(
        default=[],
        description="Dimensions to group results by, e.g., ['difficulty', 'topic']"
    )


# =============================================================================
# Experiment Module
# =============================================================================

class ExperimentCreateRequest(BaseModel):
    """Request body for creating a new experiment."""
    name: str = Field(..., min_length=1, max_length=200, description="Experiment name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Optional experiment description")
    dataset_id: str = Field(..., description="Target dataset ID")
    split: Literal["train", "dev", "test"] = Field(default="test", description="Dataset split to use")
    max_samples: Optional[int] = Field(default=None, ge=1, description="Maximum number of samples to process")
    
    model_id: str = Field(..., description="Model ID to use for inference")
    strategy: Literal["direct", "cot", "long_cot", "tot", "self_refine", "self_consistency", "react"] = Field(
        default="direct",
        description="Inference strategy"
    )
    strategy_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific parameters (e.g. temperature, reasoning_depth for cot, search_method for tot)"
    )
    
    rag: RAGConfig = Field(default_factory=RAGConfig, description="RAG configuration")
    runner: RunnerConfig = Field(default_factory=RunnerConfig, description="Runner configuration")
    eval: EvalConfig = Field(default_factory=EvalConfig, description="Evaluation configuration")
    
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed for reproducibility")


class ExperimentCreateResponse(BaseModel):
    """Response data for experiment creation."""
    experiment_id: str = Field(..., description="Generated experiment ID")
    status: Literal["created", "running", "finished", "failed", "stopped"] = Field(
        default="created",
        description="Current experiment status"
    )
    config_snapshot_path: str = Field(..., description="Path to saved configuration snapshot")


class ExperimentInfo(BaseModel):
    """Experiment summary information."""
    experiment_id: str = Field(..., description="Experiment ID")
    name: str = Field(..., description="Experiment name")
    status: Literal["created", "running", "finished", "failed", "stopped"] = Field(..., description="Current status")
    dataset_id: str = Field(..., description="Associated dataset ID")
    model_id: str = Field(..., description="Model used")
    strategy: str = Field(..., description="Inference strategy used")
    total_samples: int = Field(..., ge=0, description="Total number of samples")
    completed: int = Field(default=0, ge=0, description="Number of completed samples")
    created_at: datetime = Field(..., description="Creation timestamp")
    finished_at: Optional[datetime] = Field(default=None, description="Completion timestamp")


class ExperimentListResponse(BaseModel):
    """Response data for listing experiments."""
    experiments: List[ExperimentInfo] = Field(default_factory=list, description="List of experiments")


class ExperimentRunResponse(BaseModel):
    """Response data for starting an experiment run."""
    experiment_id: str = Field(..., description="Experiment ID")
    status: str = Field(..., description="New status after starting")
    stream_url: str = Field(..., description="SSE endpoint URL for progress updates")


class ExperimentStopResponse(BaseModel):
    """Response data for stopping an experiment."""
    status: str = Field(..., description="New status after stopping")
    completed: int = Field(..., ge=0, description="Number of samples completed before stop")


# =============================================================================
# Dataset Module
# =============================================================================

class DatasetInfo(BaseModel):
    """Dataset summary information."""
    dataset_id: str = Field(..., description="Dataset ID")
    task_type: Literal["qa", "text_qa", "text_exam", "image_mcq", "api_calling"] = Field(..., description="Task type")
    total_samples: int = Field(..., ge=0, description="Total number of samples")
    version: str = Field(default="1.0.0", description="Dataset version")
    created_at: datetime = Field(..., description="Creation timestamp")


class DatasetListResponse(BaseModel):
    """Response data for listing datasets."""
    datasets: List[DatasetInfo] = Field(default_factory=list, description="List of datasets")


class DatasetUploadResponse(BaseModel):
    """Response data for dataset upload."""
    dataset_id: str = Field(..., description="Assigned dataset ID")
    file_path: str = Field(..., description="Path where file was saved")
    total_samples: int = Field(..., ge=0, description="Number of samples in dataset")
    validated: bool = Field(..., description="Whether validation passed")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class DatasetStatsResponse(BaseModel):
    """Response data for dataset statistics."""
    dataset_id: str = Field(..., description="Dataset ID")
    task_type: str = Field(..., description="Task type")
    total: int = Field(..., ge=0, description="Total sample count")
    by_split: Dict[str, int] = Field(default_factory=dict, description="Sample count by split")
    by_difficulty: Dict[str, int] = Field(default_factory=dict, description="Sample count by difficulty")
    by_topic: Dict[str, int] = Field(default_factory=dict, description="Sample count by topic")
    missing_fields: Dict[str, int] = Field(default_factory=dict, description="Count of samples missing each field")


class SamplePreviewResponse(BaseModel):
    """Response data for dataset sample preview."""
    total: int = Field(..., ge=0, description="Total samples in dataset")
    offset: int = Field(..., ge=0, description="Current offset")
    limit: int = Field(..., ge=1, description="Number of samples returned")
    samples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of sample objects (structure varies by task type)"
    )


# =============================================================================
# Evaluation / Results Module
# =============================================================================

class UsageInfo(BaseModel):
    """Token usage and latency information."""
    total_tokens: int = Field(default=0, ge=0, description="Total tokens consumed")
    latency_ms: int = Field(default=0, ge=0, description="Request latency in milliseconds")


class RAGTraceChunk(BaseModel):
    """Single retrieved chunk in the RAG trace."""
    chunk_id: Optional[str] = None
    text: Optional[str] = None
    score: Optional[float] = None
    topic: Optional[str] = None
    source_qa_ids: Optional[List[str]] = None


class RAGTrace(BaseModel):
    """RAG context trace attached to a prediction."""
    mode: Optional[str] = Field(default=None, description="RAG mode: retrieved, oracle, or None")
    query_text: Optional[str] = Field(default=None, description="Query sent to retriever")
    retrieval_latency_ms: Optional[float] = Field(default=None, description="Retrieval latency")
    retrieved_chunks: List[RAGTraceChunk] = Field(default_factory=list, description="Retrieved evidence chunks")
    source_qa_ids: Optional[List[str]] = Field(default=None, description="Oracle source QA IDs")
    topic: Optional[str] = Field(default=None, description="Topic label")


class PredictionItem(BaseModel):
    """Single prediction result."""
    sample_id: str = Field(..., description="Sample ID")
    question: Optional[str] = Field(default=None, description="Original question text")
    options: Optional[Dict[str, str]] = Field(default=None, description="Answer options (for MCQ tasks)")
    ground_truth: Optional[str] = Field(default=None, description="Ground truth answer")
    parsed_answer: Optional[str] = Field(default=None, description="Model's parsed answer")
    raw_output: Optional[str] = Field(default=None, description="Raw model output before parsing")
    correct: Optional[bool] = Field(default=None, description="Whether the answer is correct")
    reasoning_trace: Optional[Any] = Field(default=None, description="Model's reasoning process (string or structured)")
    rag_context: Optional[RAGTrace] = Field(default=None, description="RAG retrieval trace")
    model: Optional[str] = Field(default=None, description="Model used")
    strategy: Optional[str] = Field(default=None, description="Inference strategy used")
    usage: UsageInfo = Field(default_factory=UsageInfo, description="Token usage and latency")


class PredictionListResponse(BaseModel):
    """Response data for listing predictions."""
    total: int = Field(..., ge=0, description="Total predictions available")
    offset: int = Field(..., ge=0, description="Current offset")
    limit: int = Field(..., ge=1, description="Number of items returned")
    items: List[PredictionItem] = Field(default_factory=list, description="List of prediction items")


class GroupMetrics(BaseModel):
    """Metrics for a specific group."""
    group_name: str = Field(..., description="Group identifier")
    accuracy: float = Field(..., ge=0, le=1, description="Accuracy score")
    total: int = Field(..., ge=0, description="Number of samples in group")
    correct: int = Field(..., ge=0, description="Number of correct predictions")


class MetricsResponse(BaseModel):
    """Response data for experiment metrics."""
    experiment_id: str = Field(..., description="Experiment ID")
    model: Optional[str] = Field(default=None, description="Model used")
    strategy: Optional[str] = Field(default=None, description="Strategy used")
    dataset: Optional[str] = Field(default=None, description="Dataset path")
    total_samples: Optional[int] = Field(default=None, description="Total samples")
    valid_samples: Optional[int] = Field(default=None, description="Valid samples")
    evaluated_at: Optional[str] = Field(default=None, description="Evaluation timestamp")
    overall: Dict[str, Any] = Field(
        default_factory=dict,
        description="Overall metrics (accuracy, avg_latency_ms, avg_tokens, etc.)"
    )
    by_difficulty: Optional[Any] = Field(
        default=None,
        description="Metrics grouped by difficulty"
    )
    by_topic: Optional[Any] = Field(
        default=None,
        description="Metrics grouped by topic"
    )
    by_category: Optional[Any] = Field(default=None, description="Metrics grouped by category")
    by_call_type: Optional[Any] = Field(default=None, description="Metrics grouped by call type")
    by_question_type: Optional[Any] = Field(default=None, description="Metrics grouped by question type")
    latency_stats: Optional[Dict[str, Any]] = Field(default=None, description="Latency statistics")
    token_stats: Optional[Dict[str, Any]] = Field(default=None, description="Token statistics")
    cost_estimate: Optional[Dict[str, Any]] = Field(default=None, description="Cost estimate")
    option_bias: Optional[Dict[str, Any]] = Field(default=None, description="Option bias distribution")
    exact_match: Optional[Dict[str, Any]] = Field(default=None, description="Exact match details")
    f1_score: Optional[Dict[str, Any]] = Field(default=None, description="F1 score details")
    bleu: Optional[Dict[str, Any]] = Field(default=None, description="BLEU details")
    rouge_l: Optional[Dict[str, Any]] = Field(default=None, description="ROUGE-L details")


class CompareRequest(BaseModel):
    """Request body for comparing multiple experiments."""
    experiment_ids: List[str] = Field(..., min_length=1, description="List of experiment IDs to compare")
    metrics: List[str] = Field(
        default=["exact_match", "f1_score"],
        description="Metrics to include in comparison"
    )
    group_by: Optional[str] = Field(default=None, description="Optional grouping dimension")


class CompareResponse(BaseModel):
    """Response data for experiment comparison."""
    columns: List[str] = Field(..., description="Column names for the comparison table")
    rows: List[List[Any]] = Field(..., description="Comparison data rows")
    by_group: Optional[Dict[str, List[List[Any]]]] = Field(
        default=None,
        description="Grouped comparison data"
    )


# =============================================================================
# Model Module
# =============================================================================

class ModelInfo(BaseModel):
    """Model configuration information."""
    model_id: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Model provider (deepseek, openai, anthropic, qwen)")
    config_file: str = Field(..., description="Path to model configuration file")
    available: bool = Field(..., description="Whether API key is configured")


class ModelListResponse(BaseModel):
    """Response data for listing models."""
    models: List[ModelInfo] = Field(default_factory=list, description="List of available models")


class ModelPingResponse(BaseModel):
    """Response data for model connectivity test."""
    model_id: str = Field(..., description="Model ID tested")
    reachable: bool = Field(..., description="Whether the model API is reachable")
    latency_ms: Optional[int] = Field(default=None, ge=0, description="Response latency in milliseconds")


# =============================================================================
# RAG Module
# =============================================================================

class RAGBuildRequest(BaseModel):
    """Request parameters for RAG index building (form data, not JSON)."""
    kb_name: str = Field(..., description="Knowledge base name")
    chunk_strategy: Literal["by_topic", "by_sentence", "by_token", "by_paragraph"] = Field(
        default="by_topic",
        description="Chunking strategy"
    )
    chunk_size: int = Field(default=256, ge=64, le=2048, description="Chunk size in tokens (for by_token strategy)")
    chunk_overlap: int = Field(default=0, ge=0, le=512, description="Overlap between consecutive chunks (chars or tokens)")
    embedder: str = Field(default="BAAI/bge-m3", description="Embedding model name")


class KnowledgeBaseInfo(BaseModel):
    """Knowledge base information."""
    kb_name: str = Field(..., description="Knowledge base name")
    total_chunks: int = Field(..., ge=0, description="Total number of chunks")
    collection: str = Field(..., description="Milvus collection name")
    embedder: str = Field(..., description="Embedding model used")
    created_at: datetime = Field(..., description="Creation timestamp")


class KnowledgeBaseListResponse(BaseModel):
    """Response data for listing knowledge bases."""
    kbs: List[KnowledgeBaseInfo] = Field(default_factory=list, description="List of knowledge bases")


class RAGSearchRequest(BaseModel):
    """Request body for RAG search."""
    kb_name: str = Field(..., description="Knowledge base to search")
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")


class ChunkResult(BaseModel):
    """Single chunk retrieval result."""
    chunk_id: str = Field(..., description="Chunk identifier")
    score: float = Field(..., ge=0, le=1, description="Relevance score")
    text: str = Field(..., description="Chunk text content")
    topic: Optional[str] = Field(default=None, description="Associated topic")
    source_qa_ids: List[str] = Field(default_factory=list, description="Source QA sample IDs")


class RAGSearchResponse(BaseModel):
    """Response data for RAG search."""
    results: List[ChunkResult] = Field(default_factory=list, description="Retrieved chunks")


# =============================================================================
# Chat Module
# =============================================================================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class ChatRAGConfig(BaseModel):
    """RAG configuration for chat."""
    enabled: bool = Field(default=False, description="Whether to enable RAG")
    kb_name: Optional[str] = Field(default=None, description="Knowledge base name")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of chunks to retrieve")


class ChatCompleteRequest(BaseModel):
    """Request body for chat completion."""
    model_id: str = Field(..., description="Model to use")
    strategy: Literal["direct", "cot", "long_cot", "tot", "self_refine", "self_consistency", "react"] = Field(
        default="direct",
        description="Inference strategy"
    )
    messages: List[ChatMessage] = Field(..., min_length=1, description="Conversation messages")
    rag: ChatRAGConfig = Field(default_factory=ChatRAGConfig, description="RAG configuration")
    sample_id: Optional[str] = Field(default=None, description="Optional sample ID to load context from")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt for debugging")


class ChatRAGContext(BaseModel):
    """RAG context included in chat response."""
    retrieved_chunks: List[ChunkResult] = Field(default_factory=list, description="Retrieved chunks used")


class ChatCompleteResponse(BaseModel):
    """Response data for chat completion."""
    reply: str = Field(..., description="Model's reply")
    reasoning_trace: Optional[str] = Field(default=None, description="Reasoning process (if applicable)")
    rag_context: Optional[ChatRAGContext] = Field(default=None, description="RAG context if enabled")
    usage: UsageInfo = Field(default_factory=UsageInfo, description="Token usage and latency")


# =============================================================================
# System Module
# =============================================================================

class HealthResponse(BaseModel):
    """Response data for health check."""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="System health status")
    milvus: Literal["connected", "disconnected"] = Field(..., description="Milvus connection status")
    version: str = Field(..., description="API version")


class SystemConfigResponse(BaseModel):
    """Response data for system configuration overview."""
    models: List[str] = Field(default_factory=list, description="Available model IDs")
    strategies: List[str] = Field(default_factory=list, description="Available strategy names")
    dataset_count: int = Field(default=0, ge=0, description="Number of loaded datasets")
    kb_count: int = Field(default=0, ge=0, description="Number of knowledge bases")
