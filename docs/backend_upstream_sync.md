# Backend Upstream Sync

This repository is the OpenGeoMetadata API product. The application code in
`backend/` tracks the backend subtree from `geobtaa/api`, while the repo keeps
OpenGeoMetadata branding, deployment, cache priming, and OGM harvesting as a
downstream overlay.

## Model

- `geobtaa/api` remains the source for shared backend bug fixes and enhancements.
- `backend/` is the import boundary.
- `config/ogm-owned-paths.txt` lists files this repo owns downstream.
- `config/upstream-backend-source.env` records the canonical upstream branch and
  the last applied import metadata.

Do not routinely merge the full `geobtaa/api` repository into this repo. The
upstream project contains more than the backend, and this repo has its own
product scaffolding.

## Sync Command

The sync helper uses `git subtree split` to create a backend-only source branch
from `geobtaa/api`, then imports that tree into `./backend` with `rsync`.

Dry run first:

```bash
./scripts/sync_backend_from_data_api.sh
```

Apply after reviewing the dry run:

```bash
./scripts/sync_backend_from_data_api.sh --apply
```

Useful options:

```bash
./scripts/sync_backend_from_data_api.sh --branch develop
./scripts/sync_backend_from_data_api.sh --source-path /path/to/geobtaa-api/backend
./scripts/sync_backend_from_data_api.sh --print-owned
```

Applied imports refuse a dirty worktree by default. Commit or stash local work
first, or pass `--allow-dirty` when you intentionally want to inspect the import
mixed with existing local edits.

## OGM-Owned Overlay

The import protects backend paths listed in `config/ogm-owned-paths.txt`, including:

- `backend/scripts/trigger_ogm_nightly_sync.py`
- `backend/scripts/prime_generated_caches.py`
- `backend/scripts/start_cache_prime_background.sh`
- `backend/db/migrations/backfill_resources_from_legacy_items.py`
- `backend/tests/db/migrations/`
- `backend/tests/db/migrations/test_backfill_resources_from_legacy_items.py`
- `backend/tests/api/v1/test_ogm_webhook.py`
- `backend/tests/services/test_ogm_harvest_repository.py`
- `backend/tests/tasks/test_ogm_harvest_tasks.py`
- `backend/static/brand.css`
- `backend/static/opengeometadata-*.svg`
- `backend/templates/docs.html`
- `backend/templates/ogm_repo_dashboard.html`

The manifest also documents root-level overlay files such as `README.md`,
`docs/`, `Dockerfile`, `docker-compose.yml`, and `.github/workflows/ogm-nightly-sync.yml`.

## Import Commit Pattern

Keep imports reviewable:

```bash
git switch develop
git switch -c feature/sync-geobtaa-api-YYYY-MM-DD
./scripts/sync_backend_from_data_api.sh
./scripts/sync_backend_from_data_api.sh --apply
git diff --stat
make test
git add backend config/upstream-backend-source.env
git commit -m "Import geobtaa/api backend <sha>"
```

If the import requires local reconciliation, make a second commit:

```bash
git add backend config README.md docs
git commit -m "Reapply OpenGeoMetadata overlay"
```

That two-layer history keeps upstream backend movement separate from OGM product
choices, which makes the next sync much easier to reason about.

## OGM Repo Watching

The imported backend supports:

- `POST /api/v1/admin/ogm/webhook` for GitHub push webhooks
- `backend/scripts/populate_ogm_repos.py` for GitHub-org repo discovery
- `ogm_harvest_all` and `ogm_harvest_repo` Celery tasks for ingestion

This repo owns `backend/scripts/trigger_ogm_nightly_sync.py`, which:

1. refreshes the `ogm_repos` table from the `OpenGeoMetadata` GitHub org
2. enqueues `ogm_harvest_all(trigger="nightly")`

Run it manually:

```bash
cd backend
python scripts/trigger_ogm_nightly_sync.py
```

Production also includes `.github/workflows/ogm-nightly-sync.yml`, which SSHes to
the production host nightly and runs the same in-container script.

Kamal cron support is also downstream-owned here: `config/deploy.yml` defines a
`cron` role, `config/crontab` is copied into the production image, and
`backend/scripts/start_cron.sh` loads it. The OGM nightly cron entry is gated by
`OGM_NIGHTLY_CRON_ENABLED=false` by default so the GitHub Actions workflow remains
the only active nightly scheduler unless production intentionally switches over.

For near-real-time harvesting, configure an OpenGeoMetadata organization webhook:

- Payload URL: `https://ogm.geo4lib.app/api/v1/admin/ogm/webhook`
- Content type: `application/json`
- Secret: production `OGM_WEBHOOK_SECRET`
- Events: `repository`, `public`, and `push`

The webhook handler enables repositories with a top-level `metadata-aardvark/`
directory and queues harvests when pushes touch `metadata-aardvark/`.
