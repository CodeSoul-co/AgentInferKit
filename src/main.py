from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.api import _load_routers
from src.utils.logger import setup_logger
from src.config import settings

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

# Register API routers with full /api/v1/{module} prefix (lazy load to avoid circular imports)
routers = _load_routers()
app.include_router(routers["system_router"], prefix="/api/v1/system", tags=["System"])
app.include_router(routers["datasets_router"], prefix="/api/v1/datasets", tags=["Datasets"])
app.include_router(routers["experiments_router"], prefix="/api/v1/experiments", tags=["Experiments"])
app.include_router(routers["results_router"], prefix="/api/v1/results", tags=["Results"])
app.include_router(routers["rag_router"], prefix="/api/v1/rag", tags=["RAG"])
app.include_router(routers["models_router"], prefix="/api/v1/models", tags=["Models"])
app.include_router(routers["chat_router"], prefix="/api/v1/chat", tags=["Chat"])
app.include_router(routers["agent_router"], prefix="/api/v1/agent", tags=["Custom Agent"])
app.include_router(routers["settings_router"], prefix="/api/v1/settings", tags=["Settings"])
app.include_router(routers["uploads_router"], prefix="/api/v1/uploads", tags=["Uploads"])
app.include_router(routers["prompts_router"], prefix="/api/v1/prompts", tags=["Prompts"])

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


@app.on_event("startup")
async def startup_event():
    """Print server URL on startup."""
    host = settings.app_host
    port = settings.app_port
    # Use localhost for display if binding to 0.0.0.0
    display_host = "localhost" if host == "0.0.0.0" else host
    print(f"\n{'='*50}")
    print(f"  AgentInferKit is running at:")
    print(f"  http://{display_host}:{port}/")
    print(f"  API docs: http://{display_host}:{port}/docs")
    print(f"{'='*50}\n")


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
