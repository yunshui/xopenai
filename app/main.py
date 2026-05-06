"""FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import Settings
from app.logger import setup_logging, get_logger
from app.routes.health import router as health_router
from app.routes.v1 import router as v1_router, set_services, set_limiter
from app.services.messages import AnthropicMessagesService
from app.services.models import AnthropicModelsService
import uuid
import os

settings = Settings.load_from_json()
setup_logging(settings.logging_log_dir, settings.logging_level)
logger = get_logger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Services
messages_service = AnthropicMessagesService(settings)
models_service = AnthropicModelsService(settings)

app = FastAPI(title="Anthropic to OpenAI API Proxy", version="0.1.0")

# Set limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set services for v1 routes
set_limiter(limiter)
set_services(messages_service, models_service, settings)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request ID and security headers
@app.middleware("http")
async def middleware(request: Request, call_next):
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Get client IP
    client_ip = request.client.host if request.client else "-"

    # Request size validation
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.proxy_max_request_size_mb * 1024 * 1024:
            logger.warning(f"Request too large", extra={"client_ip": client_ip, "request_id": request_id, "path": request.url.path})
            return JSONResponse(status_code=413, content={
                "error": {"type": "request_too_large", "message": "Request too large"}
            })
    # API key validation (optional)
    if settings.security_require_authentication:
        api_key = request.headers.get(settings.security_api_key_header)
        valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
        if not api_key or api_key not in valid_keys:
            logger.warning(f"Authentication failed", extra={"client_ip": client_ip, "request_id": request_id, "path": request.url.path})
            return JSONResponse(status_code=401, content={
                "error": {"type": "authentication_error", "message": "Invalid API key"}
            })

    # Log incoming request
    logger.info(f"{request.method} {request.url.path}", extra={"client_ip": client_ip, "request_id": request_id})

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Log response status
    logger.info(f"{request.method} {request.url.path} - {response.status_code}", extra={"client_ip": client_ip, "request_id": request_id})

    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    client_ip = request.client.host if request.client else "-"
    request_id = getattr(request.state, 'request_id', '-')
    logger.error(f"Unhandled: {exc}", extra={"client_ip": client_ip, "request_id": request_id, "path": request.url.path})
    return JSONResponse(status_code=500, content={"error": {"type": "internal_error", "message": str(exc)}})

# Routes
app.include_router(health_router)
app.include_router(v1_router)

@app.on_event("startup")
async def startup():
    logger.info("Starting up")

@app.on_event("shutdown")
async def shutdown():
    await messages_service.close()
    await models_service.close()
    logger.info("Shutting down")