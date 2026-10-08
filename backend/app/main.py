"""FastAPI application entry point."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, EXCEL_PATH
from app.workflow.loader import WorkflowLoader
from app.workflow.registry import WorkflowRegistry
from app.agent.agent import WorkflowAgent
from app.services.logging_service import init_db
from app.api import routes_agent, routes_workflows, routes_executions
import app.state as app_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup: load workflows and initialise services."""
    logger.info("Starting AI Workflow Automation Agent...")

    # Init execution log DB
    init_db()

    # Load workflows from Excel
    loader = WorkflowLoader(EXCEL_PATH)
    workflows = loader.load()

    # Build registry
    registry = WorkflowRegistry()
    registry.register_all(workflows)
    app_state.registry = registry
    logger.info("Workflow registry ready with %d workflows.", len(registry))

    # Build agent
    agent = WorkflowAgent(registry=registry)
    app_state.agent = agent
    logger.info("WorkflowAgent initialised.")

    yield

    logger.info("Shutting down...")


app = FastAPI(
    title="AI Workflow Automation Agent",
    description="A production-quality AI-powered business workflow automation platform.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(routes_agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(routes_workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(routes_executions.router, prefix="/api/executions", tags=["Executions"])


@app.get("/api/health", tags=["Health"])
async def health():
    registry = app_state.registry
    return {
        "status": "ok",
        "workflows_loaded": len(registry) if registry else 0,
    }
