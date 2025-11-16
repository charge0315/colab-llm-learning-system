"""
Health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Web Music Analyzer"
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Could add database connectivity check here
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }
