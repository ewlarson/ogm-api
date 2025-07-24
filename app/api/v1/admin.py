import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.security import HTTPBasic
from sqlalchemy import select

from app.api.v1.auth import verify_credentials
from app.api.v1.utils import create_response, sanitize_for_json
from app.elasticsearch.index import reindex_items
from app.services.cache_service import ENDPOINT_CACHE, CacheService, invalidate_cache_with_prefix
from app.tasks.entities import generate_geo_entities
from app.tasks.summarization import generate_item_summary
from db.database import database
from db.models import items

logger = logging.getLogger(__name__)

security = HTTPBasic()
router = APIRouter(dependencies=[Depends(verify_credentials)])


@router.post("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = Query(
        None, description="Type of cache to clear (search, item, suggest, all)"
    ),
):
    """Clear specified cache or all cache if not specified."""
    try:
        cache_service = CacheService()

        if cache_type == "search" or cache_type is None:
            await invalidate_cache_with_prefix("app.api.v1.endpoints:search")

        if cache_type == "item" or cache_type is None:
            await invalidate_cache_with_prefix("app.api.v1.endpoints:get_item")

        if cache_type == "suggest" or cache_type is None:
            await invalidate_cache_with_prefix("app.api.v1.endpoints:suggest")

        if cache_type == "all" or cache_type is None:
            await cache_service.flush_all()

        return create_response({"message": f"Cache cleared successfully: {cache_type or 'all'}"})
    except Exception as e:
        return create_response({"error": f"Failed to clear cache: {str(e)}"}, status_code=500)


@router.post("/reindex")
async def reindex(
    callback: Optional[str] = Query(None, description="JSONP callback name"),
):
    """Trigger reindexing of all items in Elasticsearch."""
    try:
        # When reindexing, invalidate all search and suggest caches
        if ENDPOINT_CACHE:
            logger.info("Invalidating search and suggest caches")
            await invalidate_cache_with_prefix("app.api.v1.endpoints:search")
            await invalidate_cache_with_prefix("app.api.v1.endpoints:suggest")

        result = await reindex_items()
        return create_response(
            {"status": "success", "message": "Reindexing completed", "details": result}, callback
        )
    except Exception as e:
        logger.error(f"Reindexing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail={"message": "Reindexing failed", "error": str(e)}
        ) from e
