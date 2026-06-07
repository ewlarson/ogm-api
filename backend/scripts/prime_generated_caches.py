#!/usr/bin/env python3
"""
Prime generated cache artifacts for OpenGeoMetadata API resources.

This orchestrates the durable cache warmers for:
- generated JSON:API resource representations
- thumbnail visual assets and thumbnail state
- static-map and basemap visual assets

The default full-corpus run stores durable database-backed assets and aliases
without hydrating every image body into Redis. Use --hydrate-assets only for
bounded hotsets or hosts sized for a full Redis DB 1 image-body cache.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from collections import Counter
from typing import Iterable

from dotenv import load_dotenv

# Add backend to path when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logger = logging.getLogger(__name__)

STAGES = ("resources", "thumbnails", "static-maps")


def configure_logging(*, verbose: bool = False) -> None:
    """Keep bulk priming output readable unless verbose diagnostics are requested."""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", force=True)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)


def _normalize_stages(stage_values: Iterable[str] | None) -> list[str]:
    values = list(stage_values or ["all"])
    if "all" in values:
        return list(STAGES)
    return [stage for stage in STAGES if stage in values]


def _print_resource_summary(counters: Counter[str]) -> None:
    print(
        "Resource representation priming complete: "
        f"primed={counters['primed']} "
        f"cached={counters['cached']} "
        f"missing={counters['missing']} "
        f"failed={counters['failed']}"
    )


async def _run(args: argparse.Namespace) -> int:
    from scripts.prime_resource_representation_cache import (  # noqa: PLC0415
        prime_resource_representation_cache,
    )
    from scripts.prime_static_map_cache import _run as prime_static_maps  # noqa: PLC0415
    from scripts.prime_thumbnail_cache import _run as prime_thumbnails  # noqa: PLC0415

    stages = _normalize_stages(args.stage)
    exit_code = 0

    if "resources" in stages:
        logger.info("Priming generated resource representations...")
        counters = await prime_resource_representation_cache(
            resource_ids=args.resource_ids,
            limit=args.limit,
            batch_size=max(1, args.resource_batch_size),
            concurrency=max(1, args.resource_concurrency),
            force=args.force,
        )
        _print_resource_summary(counters)
        if counters["failed"] and args.strict_failures:
            exit_code = max(exit_code, 1)

    if "thumbnails" in stages:
        logger.info("Priming thumbnail generated visual assets...")
        thumbnail_code = await prime_thumbnails(
            argparse.Namespace(
                resource_ids=args.resource_ids,
                limit=args.limit,
                batch_size=max(1, args.visual_batch_size),
                concurrency=max(1, args.thumbnail_concurrency),
                force=args.force,
                retry_failures=args.retry_thumbnail_failures,
                retry_placeheld=args.retry_thumbnail_placeheld,
                strict_failures=args.strict_failures,
                hydrate_assets=args.hydrate_assets,
                allow_full_hydration=args.allow_full_hydration,
            )
        )
        exit_code = max(exit_code, thumbnail_code)

    if "static-maps" in stages:
        logger.info("Priming static-map generated visual assets...")
        static_map_code = await prime_static_maps(
            argparse.Namespace(
                resource_ids=args.resource_ids,
                limit=args.limit,
                batch_size=max(1, args.visual_batch_size),
                concurrency=max(1, args.static_map_concurrency),
                force=args.force,
                hydrate_assets=args.hydrate_assets,
                allow_full_hydration=args.allow_full_hydration,
                strict_failures=args.strict_failures,
            )
        )
        exit_code = max(exit_code, static_map_code)

    print(f"Generated cache priming finished for stages: {', '.join(stages)}")
    return exit_code


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prime generated resource, thumbnail, and static-map caches."
    )
    parser.add_argument("resource_ids", nargs="*", help="Optional explicit resource IDs to prime")
    parser.add_argument(
        "--stage",
        action="append",
        choices=("all", *STAGES),
        help="Stage to run. Repeat for multiple stages. Default: all",
    )
    parser.add_argument("--limit", type=int, help="Maximum number of resources per stage")
    parser.add_argument(
        "--resource-batch-size",
        type=int,
        default=500,
        help="Database batch size for resource representation priming",
    )
    parser.add_argument(
        "--visual-batch-size",
        type=int,
        default=100,
        help="Database batch size for thumbnail and static-map priming",
    )
    parser.add_argument(
        "--resource-concurrency",
        type=int,
        default=16,
        help="Concurrent generated resource builders",
    )
    parser.add_argument(
        "--thumbnail-concurrency",
        type=int,
        default=4,
        help="Concurrent thumbnail generators",
    )
    parser.add_argument(
        "--static-map-concurrency",
        type=int,
        default=2,
        help="Concurrent static-map generators",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate existing cache entries")
    parser.add_argument(
        "--retry-thumbnail-failures",
        action="store_true",
        help="Retry thumbnails previously recorded as failed",
    )
    parser.add_argument(
        "--retry-thumbnail-placeheld",
        action="store_true",
        help="Retry thumbnails previously recorded as placeholder-only",
    )
    parser.add_argument(
        "--hydrate-assets",
        action="store_true",
        help=(
            "Also load generated image bodies into Redis DB 1. Default stores durable "
            "visual assets, links, aliases, and states without full Redis hydration."
        ),
    )
    parser.add_argument(
        "--allow-full-hydration",
        action="store_true",
        help=(
            "Allow --hydrate-assets without --limit or explicit resource IDs. Use only "
            "on hosts sized for full Redis image-body hydration."
        ),
    )
    parser.add_argument(
        "--strict-failures",
        action="store_true",
        help="Exit nonzero if any stage records failed resources",
    )
    parser.add_argument("--verbose", action="store_true", help="Show INFO logs from services")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    configure_logging(verbose=args.verbose)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
