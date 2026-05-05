"""Health check and metrics endpoints."""
from fastapi import APIRouter
from prometheus_client import generate_latest


router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "anthropic2openai"}

@router.get("/metrics")
async def metrics():
    return generate_latest()