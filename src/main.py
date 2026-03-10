from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.api import (
    datasets_router,
    results_router,
    chat_router,
    experiments_router,
    rag_router,
    models_router,
    system_router,
    agent_router,
)
from src.utils.logger import setup_logger

setup_logger()

app = FastAPI(
    title="AgentInferKit",
    description="LLM Inference Benchmark Platform",
    version="1.0.0",
)

# CORS middleware for WebUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with full /api/v1/{module} prefix
app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
app.include_router(datasets_router, prefix="/api/v1/datasets", tags=["Datasets"])
app.include_router(experiments_router, prefix="/api/v1/experiments", tags=["Experiments"])
app.include_router(results_router, prefix="/api/v1/results", tags=["Results"])
app.include_router(rag_router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(models_router, prefix="/api/v1/models", tags=["Models"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["Custom Agent"])

# WebUI paths
WEBUI_DIR = Path("webui")
WEBUI_STATIC = WEBUI_DIR / "static"
WEBUI_TEMPLATES = WEBUI_DIR / "templates"

# Initialize Jinja2 templates
templates = None
if WEBUI_TEMPLATES.exists():
    templates = Jinja2Templates(directory=str(WEBUI_TEMPLATES))

# Mount static files for WebUI (if directory exists)
if WEBUI_STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(WEBUI_STATIC)), name="static")


@app.get("/")
async def root(request: Request):
    """Root endpoint - render index.html using Jinja2 templates."""
    if templates:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "active_tab": "dashboard",
        })
    return {
        "message": "AgentInferKit API",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/ui")
@app.get("/ui/{path:path}")
async def serve_ui(request: Request, path: str = ""):
    """
    Serve WebUI using Jinja2 templates.
    This enables client-side routing (SPA).
    """
    if templates:
        # Determine active tab from path
        active_tab = path.split("/")[0] if path else "dashboard"
        return templates.TemplateResponse("index.html", {
            "request": request,
            "active_tab": active_tab,
        })
    return RedirectResponse(url="/docs")
