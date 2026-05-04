"""FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.logger import setup_logging, get_logger
from app.routes.health import router as health_router

settings = Settings.load_from_json()
setup_logging(settings.logging_log_dir, settings.logging_level)
logger = get_logger(__name__)

app = FastAPI(title="Anthropic to OpenAI API Proxy", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)

@app.on_event("startup")
async def startup():
    logger.info("Starting up")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down")