"""FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import Settings
from app.logger import setup_logging, get_logger
from app.routes.health import router as health_router
from app.routes.v1 import router as v1_router, set_services
from app.services.messages import AnthropicMessagesService
from app.services.models import AnthropicModelsService
import uuid

settings = Settings.load_from_json()
setup_logging(settings.logging_log_dir, settings.logging_level)
logger = get_logger(__name__)

# Services
messages_service = AnthropicMessagesService(settings)
models_service = AnthropicModelsService(settings)

app = FastAPI(title="Anthropic to OpenAI API Proxy", version="0.1.0")

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
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {exc}", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"error": {"type": "internal_error", "message": str(exc)}})

# Set services for v1 routes
set_services(messages_service, models_service, settings)

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