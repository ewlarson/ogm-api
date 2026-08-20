from __future__ import annotations

import asyncio
import os
from collections import Counter
from typing import Any, Iterable

from sqlalchemy import select

from app.api.v1.utils import sanitize_for_json
from app.services.cache_service import CacheService
from app.services.distribution_repository import async_session_factory
from app.services.resource_representation_cache import delete_resource_representations
from db.models import resources


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def _positive_env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _enabled() -> bool:
    return os.getenv("OGM_THUMBNAIL_REFRESH_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


async def _fetch_resources(resource_ids: list[str]) -> list[dict[str, Any]]:
    async with async_session_factory() as session:
        result = await session.execute(select(resources).where(resources.c.id.in_(resource_ids)))
        return [sanitize_for_json(dict(row._mapping)) for row in result.fetchall()]


async def _prime_resources(
    resource_dicts: list[dict[str, Any]],
    *,
    concurrency: int,
) -> dict[str, int]:
    from scripts.prime_thumbnail_cache import (
        FALLBACK_ICON_DETAIL,
        _prime_thumbnail_with_fallback_for_resource,
    )

    counters: Counter[str] = Counter()
    semaphore = asyncio.Semaphore(concurrency)

    async def run_one(resource_dict: dict[str, Any]) -> tuple[str, str, str]:
        async with semaphore:
            return await _prime_thumbnail_with_fallback_for_resource(
                resource_dict,
                force=True,
                retry_failures=True,
                retry_placeheld=True,
            )

    tasks = [asyncio.create_task(run_one(resource_dict)) for resource_dict in resource_dicts]
    for task in asyncio.as_completed(tasks):
        status, _resource_id, detail = await task
        counters[status] += 1
        if FALLBACK_ICON_DETAIL in detail:
            counters["fallback-icon"] += 1
    return {"attempted": len(resource_dicts), **dict(counters)}


async def refresh_thumbnail_cache_for_changed_resources(
    resource_ids: Iterable[str],
) -> dict[str, Any]:
    """Prime OGM-owned thumbnails and invalidate representations that embedded old URLs."""
    ids = _dedupe(resource_ids)
    if not ids:
        return {"enabled": True, "resources": 0, "thumbnails": {"attempted": 0}}
    if not _enabled():
        return {"enabled": False, "resources": len(ids)}

    cache = CacheService()
    batch_size = _positive_env_int("OGM_THUMBNAIL_REFRESH_BATCH_SIZE", 500)
    concurrency = _positive_env_int("OGM_THUMBNAIL_REFRESH_CONCURRENCY", 2)
    thumbnail_totals: Counter[str] = Counter()
    redis_representations_deleted = 0
    durable_representations_deleted = True
    api_responses_deleted = 0

    for start in range(0, len(ids), batch_size):
        resource_id_batch = ids[start : start + batch_size]
        delete_stats = await delete_resource_representations(
            resource_id_batch,
            cache_service=cache,
        )
        redis_representations_deleted += int(delete_stats.get("redis_deleted") or 0)
        durable_representations_deleted = durable_representations_deleted and bool(
            delete_stats.get("durable_deleted", True)
        )
        api_responses_deleted += await cache.invalidate_tags(
            [f"resource:{resource_id}" for resource_id in resource_id_batch]
        )
        resource_dicts = await _fetch_resources(resource_id_batch)
        thumbnail_totals.update(await _prime_resources(resource_dicts, concurrency=concurrency))

    return {
        "enabled": True,
        "resources": len(ids),
        "representations_deleted": {
            "durable_deleted": durable_representations_deleted,
            "redis_deleted": redis_representations_deleted,
        },
        "api_responses_deleted": api_responses_deleted,
        "thumbnails": dict(thumbnail_totals),
    }
