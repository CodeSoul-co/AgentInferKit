from fastapi import FastAPI

from src.api.system import router as system_router
from src.utils.logger import setup_logger

setup_logger()

app = FastAPI(
    title="AgentInferKit",
    description="LLM Inference Benchmark Platform",
    version="1.0.0",
)

# Register routers
app.include_router(system_router)
