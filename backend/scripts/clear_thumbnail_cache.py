#!/usr/bin/env python3
"""
Clear cached thumbnail for a resource so it can be regenerated.

Removes image:{hash}, image_type:{hash}, and pmtiles_skip_v2:{hash} (for PMTiles)
from Redis db=1. Supports all thumbnail source types: b1g_image_ss, IIIF, manifest,
COG, PMTiles, etc. Run inside the api container or with proper env.

Usage:
  python scripts/clear_thumbnail_cache.py b1g_PJxxfKgpqpUT
  python scripts/clear_thumbnail_cache.py b1g_abc123 b1g_def456  # multiple
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _compute_thumbnail_image_hash(image_service, source_url: str) -> str | None:
    """
    Compute the Redis cache key hash for any thumbnail source URL.
    Mirrors the logic in resources/thumbnail.py and worker.py.
    """
    return image_service.thumbnail_image_hash_for_source_sync(
        source_url,
        resolve_manifest=True,
    )


async def clear_thumbnail_for_resource(resource_id: str) -> bool:
    """Clear thumbnail cache for one resource. Returns True if keys were deleted."""
    import redis

    from app.api.v1.utils import sanitize_for_json
    from app.services.distribution_repository import (
        async_session_factory,
        fetch_distribution_context,
    )
    from app.services.image_service import ImageService
    from db.models import resources

    async with async_session_factory() as session:
        result = await session.execute(select(resources).where(resources.c.id == resource_id))
        row = result.fetchone()
        if not row:
            logger.warning(f"Resource not found: {resource_id}")
            return False

        resource_dict = sanitize_for_json(dict(row._mapping))

    distribution_context = await fetch_distribution_context(resource_id)
    image_service = ImageService(resource_dict, distribution_context=distribution_context)
    source_url = image_service._get_thumbnail_source_url()

    if not source_url:
        logger.warning(f"No thumbnail source for {resource_id}")
        return False

    image_hash = _compute_thumbnail_image_hash(image_service, source_url)
    if not image_hash:
        logger.warning(
            f"Could not compute cache hash for {resource_id} (manifest resolution failed)"
        )
        return False

    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        db=1,
        decode_responses=False,
    )

    keys_to_delete = [
        f"image:{image_hash}",
        f"image_type:{image_hash}",
    ]
    if image_service._is_pmtiles_url(source_url):
        keys_to_delete.append(f"pmtiles_skip_v2:{image_hash}")

    deleted = 0
    for key in keys_to_delete:
        if redis_client.delete(key):
            deleted += 1
            logger.info(f"Deleted {key}")

    if deleted:
        logger.info(f"Cleared thumbnail cache for {resource_id} (hash={image_hash[:12]}...)")
    else:
        logger.info(f"No cached keys found for {resource_id} (hash={image_hash[:12]}...)")

    return deleted > 0


async def clear_thumbnails_for_resources(resource_ids: list[str]) -> int:
    """Clear thumbnail caches for all resources within one event loop."""
    cleared = 0
    for resource_id in resource_ids:
        try:
            if await clear_thumbnail_for_resource(resource_id):
                cleared += 1
        except Exception as exc:
            logger.error(f"Failed for {resource_id}: {exc}")
            raise
    return cleared


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/clear_thumbnail_cache.py RESOURCE_ID [RESOURCE_ID ...]")
        sys.exit(1)

    resource_ids = sys.argv[1:]
    cleared = asyncio.run(clear_thumbnails_for_resources(resource_ids))

    print(f"Cleared cache for {cleared}/{len(resource_ids)} resource(s)")


if __name__ == "__main__":
    main()
