import structlog
import uuid
import jwt
import os

from fastapi import FastAPI, Request, Header, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from src.controllers.doc_analyser_controller import router as doc_analyser_router
from src.controllers.doc_chat_controller import router as doc_chat_router
# from src.controllers.doc_extractor_controller import router as doc_extractor_router
from src.controllers.user_registration_controller import router as user_registration_router
from src.core.app_settings import get_settings, refresh_settings
from src.utils.az_logger import az_logging
from contextlib import asynccontextmanager

# This sets up Azure logging as early as possible so all logs are captured from the start.
az_logging()
logger = structlog.get_logger("app")

# Lifespan handler lets you run code when the app starts and stops, useful for setup/cleanup.
# This feature requires FastAPI version 0.95 or higher.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    _ = get_settings()  # Ensure settings are loaded at startup
    logger.info("App setting configurations loaded and application startup complete")
    yield
    # shutdown logic
    logger.info("Application shutdown initiated")

def verify_token(token: str) -> dict:
    return jwt.decode(token, os.getenv("JWT_SECRET_KEY", None), algorithms=["HS256"], options={"require": ["exp", "iat", "nbf"]})

def auth_dependency(authorization: str = Header(...)):
    # Expect "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError
        return verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

bearer_scheme = HTTPBearer()

def auth_bearer_dependency(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    try:
        return verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# This creates the FastAPI app and sets metadata and docs URLs, also attaches the lifespan handler.
app = FastAPI(
    title="Document Portal API",
    description="API for document analysis and related operations.",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc", # ReDoc UI
    lifespan=lifespan,
)

# To enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Include the routers with appropriate prefixes and tags.
routers = [
    (doc_analyser_router, "/doc-analyser", ["Document Analysis"]),
    (doc_chat_router, "/doc-chat", ["Document Chat"]),
    # (doc_extractor_router, "/doc-extractor", ["Document Extractor"]),
    (user_registration_router, "/user", ["User Registration"]),
]

# Loop through each router and register it with the app.
# Each router has a prefix and tags for better organization in the API docs.
# Secure all routers except user_registration_router
for router, prefix, tags in routers:
    if router is user_registration_router:
        app.include_router(router, prefix=prefix, tags=tags)
    else:
        app.include_router(
            router,
            prefix=prefix,
            tags=tags,
            # dependencies=[Security(auth_bearer_dependency)]
        )

# Defines the root ("/") endpoint, returns a welcome message and logs the call.
@app.get("/")
async def root():
    logger.info("root.called")
    return {"message": "Welcome to Beacon API"}

# Admin endpoint to refresh app settings configurations
@app.post("/refresh-config")
def admin_refresh():
    _ = refresh_settings()
    return {"status": "ok"}