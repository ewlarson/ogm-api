# Scripts Documentation

The application code lives in `backend/`, and the operational scripts live in `backend/scripts/`.

The repo-root `scripts/` directory is intentionally minimal now. It only contains project-scaffolding helpers such as `sync_backend_from_data_api.sh`, which refreshes the mirrored backend from the upstream BTAA `data-api` checkout.

## Where To Run Scripts

From the repo root:

```bash
cd backend
python scripts/run_migrations.py
python scripts/run_index.py
python scripts/trigger_ogm_nightly_sync.py --dry-run
```

If you prefer Docker:

```bash
docker compose exec api bash -lc "cd /app/backend && python scripts/run_migrations.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/run_index.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/trigger_ogm_nightly_sync.py --dry-run"
```

## Core Backend Scripts

### `scripts/run_migrations.py`

Runs the standard OpenGeoMetadata database migrations for the mirrored backend.

### `scripts/run_index.py`

Builds or refreshes the Elasticsearch index from Postgres-backed resource data.

### `scripts/run_gazetteers.py`

Loads gazetteer support data. This is optional for many OGM-focused workflows.

### `scripts/populate_ogm_repos.py`

Discovers OpenGeoMetadata repositories and updates the local `ogm_repos` table.

### `scripts/trigger_ogm_nightly_sync.py`

Refreshes repo discovery and enqueues the nightly OGM harvest workflow.

### `scripts/ogm_harvester.py`

Provides the standalone OGM repository harvesting utility used for cloning, pulling, and iterating over Aardvark records.

### `scripts/run_migration.py`

Runs one targeted migration by name when you need a single fix or backfill rather than the full migration bundle.

### `scripts/clear_cache.py`

Clears Redis-backed API caches using the configured `REDIS_HOST` and `REDIS_PORT`.

## Upstream Sync Helper

At the repo root, this script remains useful:

### `scripts/sync_backend_from_data_api.sh`

Copies `backend/` forward from a local BTAA `data-api` checkout while excluding local runtime data and other generated artifacts.
