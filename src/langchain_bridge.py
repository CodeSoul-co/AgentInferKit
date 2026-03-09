"""
LangChain Bridge — wraps AgentInferKit adapters as LangChain-compatible objects.

Provides:
  - AdapterChatModel: wraps BaseModelAdapter as a LangChain BaseChatModel
  - make_langchain_llm: factory to create ChatOpenAI from our config
  - make_langchain_tools: converts toolsim tool schemas into LangChain BaseTool list
  - TokenUsageTracker: callback handler to capture token usage and latency
"""

import asyncio
import json
import time
from typing import Any, Dict, Iterator, List, Optional, Sequence

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import StructuredTool

from src.adapters.base import BaseModelAdapter
from src.api.schemas import GenerateResult, Message
from src.toolsim.executor import MockExecutor
from src.toolsim.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Callback handler for token / latency tracking
# ---------------------------------------------------------------------------

class TokenUsageTracker(BaseCallbackHandler):
    """Tracks cumulative token usage and latency across LangChain calls."""

    def __init__(self) -> None:
        super().__init__()
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_latency_ms: float = 0.0
        self._start_time: Optional[float] = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        self._start_time = time.perf_counter()

    def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any) -> None:
        self._start_time = time.perf_counter()

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        if self._start_time is not None:
            self.total_latency_ms += (time.perf_counter() - self._start_time) * 1000
            self._start_time = None
        # Try llm_output first (standard path)
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            self.prompt_tokens += usage.get("prompt_tokens", 0)
            self.completion_tokens += usage.get("completion_tokens", 0)
            return
        # Fallback: extract from generation response_metadata (AgentExecutor path)
        if hasattr(response, "generations") and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    meta = getattr(gen, "message", None)
                    if meta and hasattr(meta, "response_metadata"):
                        rm = meta.response_metadata
                        usage = rm.get("token_usage", {})
                        self.prompt_tokens += usage.get("prompt_tokens", 0)
                        self.completion_tokens += usage.get("completion_tokens", 0)
                        return

    def reset(self) -> None:
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_latency_ms = 0.0
        self._start_time = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_usage_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.total_latency_ms, 1),
        }


# ---------------------------------------------------------------------------
# Adapter -> LangChain BaseChatModel wrapper
# ---------------------------------------------------------------------------

def _msg_to_langchain(msg: Message) -> BaseMessage:
    if msg.role == "system":
        return SystemMessage(content=msg.content)
    elif msg.role == "assistant":
        return AIMessage(content=msg.content)
    return HumanMessage(content=msg.content)


def _langchain_to_msg(msg: BaseMessage) -> Message:
    if isinstance(msg, SystemMessage):
        return Message(role="system", content=msg.content)
    elif isinstance(msg, AIMessage):
        return Message(role="assistant", content=msg.content)
    return Message(role="user", content=msg.content)


class AdapterChatModel(BaseChatModel):
    """Wraps an AgentInferKit BaseModelAdapter as a LangChain BaseChatModel.

    This allows using our existing adapter infrastructure (DeepSeek, OpenAI, etc.)
    with LangChain chains and agents.
    """

    adapter: Any = None  # BaseModelAdapter instance
    model_name: str = "adapter"

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "agentinferkit-adapter"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        our_messages = [_langchain_to_msg(m) for m in messages]
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result: GenerateResult = pool.submit(
                    asyncio.run, self.adapter.generate(our_messages, **kwargs)
                ).result()
        else:
            result = asyncio.run(self.adapter.generate(our_messages, **kwargs))

        generation = ChatGeneration(
            message=AIMessage(content=result.content),
        )
        return ChatResult(
            generations=[generation],
            llm_output={
                "token_usage": {
                    "prompt_tokens": result.prompt_tokens,
                    "completion_tokens": result.completion_tokens,
                    "total_tokens": result.prompt_tokens + result.completion_tokens,
                },
                "latency_ms": result.latency_ms,
            },
        )

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}


# ---------------------------------------------------------------------------
# Factory: create ChatOpenAI from our model config
# ---------------------------------------------------------------------------

def make_langchain_llm(model_config: Dict[str, Any]) -> Any:
    """Create a LangChain ChatOpenAI from our standard model config.

    Uses ChatOpenAI for OpenAI-compatible providers (deepseek, openai, qwen).
    Falls back to AdapterChatModel wrapper for others.

    Args:
        model_config: Dict with 'provider', 'model', etc.

    Returns:
        A LangChain chat model instance.
    """
    from src.config import settings

    provider = model_config.get("provider", "deepseek")

    # OpenAI-compatible providers can use ChatOpenAI directly
    if provider in ("deepseek", "openai", "qwen"):
        from langchain_openai import ChatOpenAI

        key_map = {
            "deepseek": (settings.deepseek_api_key, settings.deepseek_base_url),
            "openai": (settings.openai_api_key, settings.openai_base_url),
            "qwen": (settings.qwen_api_key, settings.qwen_base_url),
        }
        api_key, base_url = key_map[provider]
        return ChatOpenAI(
            model=model_config.get("model", "deepseek-chat"),
            api_key=api_key,
            base_url=base_url,
            temperature=model_config.get("temperature", 0.0),
            max_tokens=model_config.get("max_tokens", 2048),
            request_timeout=model_config.get("request_timeout", 60),
        )

    # Fallback: wrap our adapter
    from src.adapters.registry import load_adapter
    adapter = load_adapter(model_config)
    return AdapterChatModel(adapter=adapter, model_name=model_config.get("model", "unknown"))


# ---------------------------------------------------------------------------
# Toolsim -> LangChain Tools
# ---------------------------------------------------------------------------

def make_langchain_tools(
    tool_schemas: List[Dict[str, Any]],
    executor: Optional[MockExecutor] = None,
) -> List[StructuredTool]:
    """Convert toolsim tool schemas into LangChain StructuredTool list.

    Each tool calls the MockExecutor when invoked, returning the mock response.

    Args:
        tool_schemas: List of tool schema dicts from ToolRegistry.get_tools_for_sample().
        executor: A MockExecutor instance. If None, creates one with the default registry.

    Returns:
        List of LangChain StructuredTool objects.
    """
    if executor is None:
        registry = ToolRegistry()
        executor = MockExecutor(registry)

    from langchain_core.tools import Tool

    tools = []
    for schema in tool_schemas:
        tool_id = schema.get("tool_id", schema.get("name", "unknown"))
        description = schema.get("description", schema.get("core_description", "No description"))
        parameters = schema.get("parameters", {})

        # Build parameter description string
        if isinstance(parameters, dict):
            props = parameters.get("properties", parameters)
            param_desc_parts = []
            for pname, pinfo in props.items():
                if isinstance(pinfo, dict):
                    param_desc_parts.append(f"{pname}: {pinfo.get('description', pinfo.get('type', ''))}")
                else:
                    param_desc_parts.append(str(pname))
            if param_desc_parts:
                description += " Parameters: " + ", ".join(param_desc_parts)

        def _make_func(tid: str, exec_ref: MockExecutor = executor):
            def tool_func(tool_input: str) -> str:
                # ReAct agent passes either a JSON string or plain text
                try:
                    params = json.loads(tool_input)
                except (json.JSONDecodeError, TypeError):
                    params = {"input": tool_input}
                if not isinstance(params, dict):
                    params = {"input": str(params)}
                result = exec_ref.execute(tid, params)
                return json.dumps(result.get("response", result), ensure_ascii=False)
            return tool_func

        func = _make_func(tool_id)

        # Use Tool (not StructuredTool) — accepts a single string input,
        # compatible with create_react_agent's text-based Action Input format.
        lc_tool = Tool(
            name=tool_id,
            func=func,
            description=description,
        )
        tools.append(lc_tool)

    return tools
