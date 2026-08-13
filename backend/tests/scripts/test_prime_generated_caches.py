from argparse import Namespace
from collections import Counter
from unittest.mock import patch

import pytest

from scripts import prime_generated_caches


def _args() -> Namespace:
    return Namespace(
        resource_ids=[],
        limit=None,
        resource_batch_size=500,
        resource_concurrency=16,
        visual_batch_size=100,
        thumbnail_concurrency=4,
        static_map_concurrency=2,
        force=False,
        retry_thumbnail_failures=False,
        retry_thumbnail_placeheld=False,
        strict_failures=False,
        hydrate_assets=False,
        allow_full_hydration=False,
        resource_class="Maps",
        provider=None,
        stage=["all"],
    )


@pytest.mark.asyncio
async def test_all_stages_prime_visuals_before_resource_representations():
    calls: list[str] = []

    async def thumbnails(args):
        calls.append("thumbnails")
        assert args.resource_class == "Maps"
        assert args.provider is None
        return 0

    async def static_maps(args):
        calls.append("static-maps")
        assert args.resource_class == "Maps"
        assert args.provider is None
        return 0

    async def resources(**kwargs):
        calls.append("resources")
        assert kwargs["resource_class"] == "Maps"
        assert kwargs["provider"] is None
        return Counter()

    with (
        patch("scripts.prime_thumbnail_cache._run", side_effect=thumbnails),
        patch("scripts.prime_static_map_cache._run", side_effect=static_maps),
        patch(
            "scripts.prime_resource_representation_cache.prime_resource_representation_cache",
            side_effect=resources,
        ),
    ):
        result = await prime_generated_caches._run(_args())

    assert result == 0
    assert calls == ["thumbnails", "static-maps", "resources"]


def test_default_stage_order_places_resources_last():
    assert prime_generated_caches._normalize_stages(None) == [
        "thumbnails",
        "static-maps",
        "resources",
    ]
