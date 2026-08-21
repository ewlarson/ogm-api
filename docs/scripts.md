# Scripts Documentation

The application code lives in `backend/`, and operational scripts live in
`backend/scripts/`.

The repo-root `scripts/` directory is intentionally minimal. It contains
project-scaffolding helpers such as `sync_backend_from_data_api.sh`, which
imports the backend subtree from `geobtaa/api`, and `kamal_registry_login.sh`,
which stores and verifies the GHCR token used by Kamal deploys.

## Where To Run Scripts

From the repo root:

```bash
cd backend
python scripts/run_migrations.py
python scripts/run_index.py
python scripts/prime_generated_caches.py --limit 100
python scripts/trigger_ogm_nightly_sync.py --dry-run
```

If you prefer Docker:

```bash
docker compose exec api bash -lc "cd /app/backend && python scripts/run_migrations.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/run_index.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/prime_generated_caches.py --limit 100"
docker compose exec api bash -lc "cd /app/backend && python scripts/trigger_ogm_nightly_sync.py --dry-run"
```

## Core Backend Scripts

### `scripts/run_migrations.py`

Runs the standard OpenGeoMetadata database migrations for the mirrored backend,
including durable generated resource and visual asset cache tables.

### `scripts/run_index.py`

Builds or refreshes the Elasticsearch index from Postgres-backed resource data.

### `scripts/run_gazetteers.py`

Loads gazetteer support data. This is optional for many OGM-focused workflows.

### `scripts/populate_ogm_repos.py`

Discovers OpenGeoMetadata repositories and updates the local `ogm_repos` table.

### `scripts/trigger_ogm_nightly_sync.py`

Refreshes repo discovery and enqueues the nightly OGM harvest workflow.

### `scripts/ogm_harvester.py`

Provides the standalone OGM repository harvesting utility used for cloning,
pulling, and iterating over Aardvark records.

### `scripts/run_migration.py`

Runs one targeted migration by name when you need a single fix or backfill rather
than the full migration bundle.

### `scripts/clear_cache.py`

Clears Redis-backed API caches using the configured `REDIS_HOST` and `REDIS_PORT`.

### `scripts/prime_generated_caches.py`

Runs the generated cache warmers in sequence:

- generated JSON:API resource representations
- thumbnail visual assets and thumbnail state
- static-map and basemap visual assets

The default full-corpus mode writes durable database-backed cache rows and avoids
hydrating every image body into Redis. Add `--hydrate-assets` only for bounded
hotsets or hosts sized for a full Redis image-body cache.

Examples:

```bash
cd backend
python scripts/prime_generated_caches.py --limit 1000
python scripts/prime_generated_caches.py --stage resources --stage static-maps
python scripts/prime_generated_caches.py --hydrate-assets --limit 250
```

### `scripts/start_cache_prime_background.sh`

Starts `prime_generated_caches.py` in the background and writes:

- log: `backend/logs/prime_generated_caches.log`
- pid: `backend/tmp/prime_generated_caches.pid`

## Upstream Sync Helper

At the repo root:

### `scripts/sync_backend_from_data_api.sh`

Imports `geobtaa/api/backend` into this repo's `backend/` directory. It uses
`git subtree split` to create a backend-only source branch, protects
OpenGeoMetadata-owned backend files listed in `config/ogm-owned-paths.txt`, and
records applied import metadata in `config/upstream-backend-source.env`.

Dry run:

```bash
./scripts/sync_backend_from_data_api.sh
```

Apply:

```bash
./scripts/sync_backend_from_data_api.sh --apply
```

### `scripts/kamal_registry_login.sh`

Stores the GitHub Container Registry token in `.kamal/registry-password` and
verifies Docker login for Kamal deploys.

```bash
make kamal-registry-login
```
