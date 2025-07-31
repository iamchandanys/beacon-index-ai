import structlog
import uuid

from fastapi import FastAPI, Request
from src.controllers.doc_analyser_controller import router as doc_analyser_router
from src.utils.az_logger import az_logging
from contextlib import asynccontextmanager

# This sets up Azure logging as early as possible so all logs are captured from the start.
az_logging()
logger = structlog.get_logger("app")

# Lifespan handler lets you run code when the app starts and stops, useful for setup/cleanup.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    logger.info("app.startup")  # Log when the app starts
    yield
    # shutdown logic
    logger.info("app.shutdown")  # Log when the app shuts down

# This creates the FastAPI app and sets metadata and docs URLs, also attaches the lifespan handler.
app = FastAPI(
    title="Document Portal API",
    description="API for document analysis and related operations.",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc", # ReDoc UI
    lifespan=lifespan,
)

# Middleware adds request-specific context (like request ID) to logs for better traceability.
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    structlog.contextvars.bind_contextvars(
        request_id=request.headers.get("X-Request-ID", str(uuid.uuid4())),
        path=request.url.path,
        method=request.method,
    )
    try:
        return await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()  # Clean up context after request

# This attaches the document analysis routes to the app under the /doc-analyser path.
app.include_router(
    doc_analyser_router,
    prefix="/doc-analyser",
    tags=["Document Analysis"],
)

# Defines the root ("/") endpoint, returns a welcome message and logs the call.
@app.get("/")
async def root():
    logger.info("root.called")
    return {"message": "Welcome to the Document Portal API"}