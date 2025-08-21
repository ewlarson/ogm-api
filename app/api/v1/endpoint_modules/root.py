import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def api_root():
    """API root endpoint with available endpoints."""
    return {
        "name": "OpenGeoMetadata API",
        "version": "1.0.0",
        "description": "API for accessing OpenGeoMetadata resources",
        "endpoints": [
            "/resources/{id}",
            "/resources/{id}/ogm",
            "/resources/{id}/viewer",
            "/resources/",
            "/search",
            "/suggest",
            "/thumbnails/{image_hash}",
            "/mcp",
            "/validate",
        ],
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
    }
