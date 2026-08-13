from unittest.mock import AsyncMock, patch

import pytest

import app.services.thumbnail_refresh_service as refresh


class _Cache:
    def __init__(self):
        self.invalidated = []

    async def invalidate_tags(self, tags):
        self.invalidated.append(tags)
        return len(tags)


@pytest.mark.asyncio
async def test_refresh_is_thumbnail_only_and_deduplicates_resources(monkeypatch):
    cache = _Cache()
    resource_dicts = [{"id": "map-1"}, {"id": "map-2"}]
    monkeypatch.setenv("OGM_THUMBNAIL_REFRESH_ENABLED", "true")
    monkeypatch.setenv("OGM_THUMBNAIL_REFRESH_BATCH_SIZE", "2")

    with (
        patch.object(refresh, "CacheService", return_value=cache),
        patch.object(
            refresh,
            "delete_resource_representations",
            new=AsyncMock(return_value={"durable_deleted": True, "redis_deleted": 2}),
        ),
        patch.object(refresh, "_fetch_resources", new=AsyncMock(return_value=resource_dicts)),
        patch.object(
            refresh,
            "_prime_resources",
            new=AsyncMock(return_value={"attempted": 2, "generated": 2}),
        ) as prime,
    ):
        stats = await refresh.refresh_thumbnail_cache_for_changed_resources(
            ["map-1", "map-2", "map-1"]
        )

    assert stats["resources"] == 2
    assert stats["thumbnails"] == {"attempted": 2, "generated": 2}
    assert cache.invalidated == [["resource:map-1", "resource:map-2"]]
    prime.assert_awaited_once_with(resource_dicts, concurrency=2)
