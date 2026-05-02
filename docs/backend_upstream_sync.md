# Backend Sync Strategy

This repository now carries a `backend/` directory that mirrors the current backend from `geobtaa/api`.

## Why not a Git submodule?

Git submodules work at the repository level, not the subdirectory level. The upstream backend we want to track lives inside the larger `geobtaa/api` repository, so a submodule would pull the whole upstream repo rather than only the backend tree.

For this layout, the better fit is one of:

- a repeatable sync script that mirrors `geobtaa/api/backend` into `./backend`
- a future `git subtree` workflow if we want Git history for upstream backend imports inside this repository

## Current approach

Use the helper script to refresh the mirrored backend tree from a local `data-api` checkout:

```bash
./scripts/sync_backend_from_data_api.sh
```

By default it syncs from:

```text
../clients/b1g/data-api/backend
```

You can also pass an explicit source path:

```bash
./scripts/sync_backend_from_data_api.sh /path/to/geobtaa-api/backend
```

## OGM repo watching strategy

The imported backend already supports:

- `POST /api/v1/admin/ogm/webhook` for GitHub push webhooks
- `scripts/populate_ogm_repos.py` for GitHub-org repo discovery
- `ogm_harvest_all` and `ogm_harvest_repo` Celery tasks for ingestion

This repo adds `backend/scripts/trigger_ogm_nightly_sync.py`, which:

1. refreshes the `ogm_repos` table from the `OpenGeoMetadata` GitHub org
2. enqueues `ogm_harvest_all(trigger="weekly")`

Example nightly command:

```bash
cd backend
python scripts/trigger_ogm_nightly_sync.py
```

## Recommended scheduler setup

- Nightly: run `backend/scripts/trigger_ogm_nightly_sync.py`
- Event-driven: configure a GitHub webhook that targets `/api/v1/admin/ogm/webhook`

This gives us both:

- discovery of newly created OpenGeoMetadata repositories
- near-real-time harvesting when records change in watched repos

GitHub’s current docs indicate that:

- organization webhooks can subscribe to events across all repositories in an organization
- the `push` event is available to organization webhooks

References:

- [Types of webhooks](https://docs.github.com/webhooks/about-webhooks-for-repositories)
- [Webhook events and payloads: `push`](https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=reintroduced)
