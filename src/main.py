from fastapi import FastAPI

from src.api.system import router as system_router
from src.api.chat import router as chat_router
from src.api.datasets import router as datasets_router
from src.api.results import router as results_router
from src.utils.logger import setup_logger

setup_logger()

app = FastAPI(
    title="AgentInferKit",
    description="LLM Inference Benchmark Platform",
    version="1.0.0",
)

# Register routers
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(datasets_router)
app.include_router(results_router)
