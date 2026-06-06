# OpenGeoMetadata API

This repository now runs entirely from [backend](backend/), which mirrors the current BTAA Geospatial API backend while being themed and operated for the OpenGeoMetadata community.

The old root-level API implementation has been retired into [legacy/root_api](legacy/root_api/). The repo root is now just project scaffolding for Docker, Kamal, docs, and convenience commands; the application code lives in `backend/`.

## Local Setup

Copy the environment template:

```bash
cp .env.example .env
```

The checked-in `.env.example` is host-friendly for backend-local commands. Docker services override the container-only hostnames internally, so the same `.env` also works with `docker compose`.

For local Docker development, Elasticsearch defaults `ELASTICSEARCH_DISK_THRESHOLD_ENABLED=false` so Docker Desktop disk-watermark quirks do not leave the single-node index unassigned. If you want stricter production-like allocation checks, set it back to `true` in `.env`.

If you want to run the backend directly on your host machine, install dependencies with `uv`:

```bash
uv venv
source .venv/bin/activate
cd backend
uv pip install -e ".[dev]"
```

## Run With Docker

Start the API plus its backing services:

```bash
docker compose up -d --build
```

Then initialize the app. The most reliable path is to run backend scripts inside the API container:

```bash
docker compose exec api bash -lc "cd /app/backend && python scripts/run_migrations.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/run_index.py"
```

`scripts/run_gazetteers.py` is optional for OGM-focused local work and can usually be skipped unless you specifically need the gazetteer-backed enrichment features.

Once that finishes, open:

- API docs at `http://localhost:8000/api/docs`
- OpenAPI JSON at `http://localhost:8000/api/openapi.json`
- OGM repository dashboard at `http://localhost:8000/api/v1/ogm/repos/dashboard`

This starts:

- API at `http://localhost:8000`
- Elasticsearch at `http://localhost:9200`
- ParadeDB/Postgres at `localhost:2345`
- Redis at `localhost:6380`
- Flower at `http://localhost:5555`

## Common Commands

From the repo root:

```bash
cd backend && python scripts/trigger_ogm_nightly_sync.py --dry-run
cd backend && python scripts/run_migrations.py
cd backend && python scripts/run_index.py
cd backend && python scripts/run_gazetteers.py
cd backend && python scripts/prime_generated_caches.py --limit 100
```

Or use Make targets:

```bash
make migrate
make reindex
make gazetteers
make ogm-nightly
make cache-prime ARGS="--limit 100"
make cache-prime-background ARGS="--limit 1000"
make test
```

If you prefer not to install Python dependencies locally, the same commands can be run in Docker:

```bash
docker compose exec api bash -lc "cd /app/backend && python scripts/run_migrations.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/run_index.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/prime_generated_caches.py --limit 100"
docker compose exec api bash -lc "cd /app/backend && python scripts/trigger_ogm_nightly_sync.py --dry-run"
```

## OGM Harvesting

The backend includes:

- GitHub-org discovery via `backend/scripts/populate_ogm_repos.py`
- nightly repo refresh + harvest enqueue via `backend/scripts/trigger_ogm_nightly_sync.py`
- webhook-triggered harvesting via `POST /api/v1/admin/ogm/webhook`

Set `GITHUB_TOKEN` in `.env` before running the OGM sync scripts if you want to avoid low unauthenticated GitHub API rate limits.

For near-real-time harvesting, configure an OpenGeoMetadata organization webhook:

- Payload URL: `https://ogm.geo4lib.app/api/v1/admin/ogm/webhook`
- Content type: `application/json`
- Secret: production `OGM_WEBHOOK_SECRET`
- Events: `repository`, `public`, and `push`

The webhook discovers newly created/publicized/transferred/unarchived OGM repos, enables repos
with a top-level `metadata-aardvark/` directory, and queues harvests when pushes touch
`metadata-aardvark/`. The nightly job remains the reconciliation path in case a delivery is missed.

For a first local bootstrap with real OGM data:

```bash
docker compose exec api bash -lc "cd /app/backend && python scripts/populate_ogm_repos.py"
docker compose exec api bash -lc "cd /app/backend && python - <<'PY'\nfrom app.tasks.ogm_harvest import ogm_harvest_all\nprint(ogm_harvest_all.delay(trigger='nightly').id)\nPY"
docker compose exec api bash -lc "cd /app/backend && python scripts/run_index.py"
```

The harvest populates Postgres first. Re-run `python scripts/run_index.py` from `backend/` after the harvest queue completes so Elasticsearch reflects the imported OGM records.

Production also has a dedicated monitor page at `/api/v1/ogm/repos/dashboard` and a nightly
GitHub Actions workflow for OGM repo discovery + harvest orchestration.

See [docs/backend_upstream_sync.md](docs/backend_upstream_sync.md) for the upstream-sync and repo-watching strategy.

## Generated Cache Priming

After migrations and indexing, prebuild generated artifacts with:

```bash
make cache-prime ARGS="--limit 1000"
```

For a production background run after deploy:

```bash
kamal app exec "python /app/backend/scripts/run_migrations.py"
kamal app exec "cd /app/backend && ./scripts/start_cache_prime_background.sh"
kamal app exec "tail -f /app/backend/logs/prime_generated_caches.log"
```

The combined primer warms durable generated resource representations, thumbnail
assets, and static-map/basemap assets. Full-corpus runs avoid hydrating every
image body into Redis by default; add `--hydrate-assets` only for bounded hotsets
or hosts sized for that memory profile.

See [docs/cache_priming.md](docs/cache_priming.md) for details.

## Upstream Backend Sync

This repo is maintained as the OpenGeoMetadata API product with `backend/`
imported from `geobtaa/api`.

Preview an upstream backend import:

```bash
./scripts/sync_backend_from_data_api.sh
```

Apply after review:

```bash
./scripts/sync_backend_from_data_api.sh --apply
```

The helper uses `git subtree split` to read only `geobtaa/api/backend`, protects
OpenGeoMetadata-owned files from `config/ogm-owned-paths.txt`, and records
applied import metadata in `config/geobtaa-backend-source.env`.
