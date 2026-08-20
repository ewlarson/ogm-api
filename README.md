# OpenGeoMetadata API

OpenGeoMetadata API is a deployable search, harvest, and delivery service for
public [OpenGeoMetadata](https://opengeometadata.org/) Aardvark records. It is
being prepared as the reference API node for the proposed
[OpenGeoMetadata API Mirror Network](https://github.com/OpenGeoMetadata/ogm-mirror-network).

> [!IMPORTANT]
> The mirror-network proposal is a **Draft for Community Discussion**
> (`OGM-DISCUSSION-2026-01`), not an approved OGM roadmap, production
> commitment, or technical standard. This repository implements capabilities a
> mirror node needs; it does not claim that the proposed network already exists.

## Role in the mirror network

The proposal separates the public service from any one institution:

1. Public Aardvark files in OpenGeoMetadata GitHub repositories remain the
   canonical metadata source.
2. Each mirror independently harvests that corpus into local PostgreSQL and
   Elasticsearch services and keeps its own Redis and generated caches.
3. A protected global endpoint would route public read traffic only to mirrors
   that are compatible, healthy, sufficiently current, and within capacity.
4. Institutional OGM Discovery sites would use the stable network endpoint
   rather than bind themselves to one campus origin.
5. The OGM service operator would deploy the same pinned application release
   to each mirror with Kamal, using staged upgrades and rollback.

This repository supplies the API/node software in that model. The
[technical implementation guide](https://github.com/OpenGeoMetadata/ogm-mirror-network/blob/main/proposal/opengeometadata-api-mirror-network-technical-implementation.md)
is the canonical source for the proposed network architecture and pilot
acceptance criteria.

## Current implementation status

| Capability | Status |
| --- | --- |
| Discover OpenGeoMetadata repositories and harvest `metadata-aardvark/` | Implemented |
| Nightly reconciliation with webhook-triggered acceleration | Implemented for the current production node |
| PostgreSQL record/provenance state and Elasticsearch discovery index | Implemented |
| Redis hot caches plus durable generated representations and visual assets | Implemented |
| Public search, resource, OGC, MCP, viewer, thumbnail, and static-map APIs | Implemented |
| Single-host Kamal topology with web, worker, cron, PostgreSQL, Elasticsearch, and Redis | Implemented |
| OGM repository monitoring dashboard | Implemented |
| Shared global edge, origin drain/rejoin, and weighted multi-mirror routing | Proposed pilot work |
| Network readiness contract and deterministic `corpus_generation` | Proposed pilot work |
| Shared webhook fan-out and fleet-wide release orchestration | Proposed pilot work |
| Demonstrated multi-node failover and rebuild acceptance tests | Proposed pilot work |

Administrative, webhook, harvest, reindex, and deployment operations are a
restricted control plane. A future shared endpoint is intended only for safe
public `GET` and `HEAD` routes.

## Repository layout

- `backend/` — FastAPI application, workers, migrations, scripts, and tests
- `config/` — Kamal deployment, cron, database initialization, and upstream provenance
- `docs/` — operator, development, cache, deployment, and migration documentation
- `scripts/` — repository-level upstream and registry helpers
- `legacy/root_api/` — retired pre-backend implementation; not the runtime application

The backend began from the `geobtaa/api` backend subtree and now carries an
OpenGeoMetadata-owned harvesting, branding, deployment, and cache overlay. It
is not a Git fork with mergeable history. See
[BTAA backend reconciliation](docs/upstream_reconciliation.md) for the pinned
source baseline, selective-port decisions, and accepted upstream fixes.

## Local development

Copy the environment template:

```bash
cp .env.example .env
```

Do not place production credentials in the repository. `.env` and `.kamal/`
are ignored local files; shared deployments must resolve secrets from an
approved environment or secret manager.

Start the complete local stack:

```bash
docker compose up -d --build
docker compose exec api bash -lc "cd /app/backend && python scripts/run_migrations.py"
docker compose exec api bash -lc "cd /app/backend && python scripts/run_index.py"
```

Local endpoints:

- API documentation: `http://localhost:8000/api/docs`
- OpenAPI document: `http://localhost:8000/api/openapi.json`
- OGM repository dashboard: `http://localhost:8000/api/v1/ogm/repos/dashboard`
- Elasticsearch: `http://localhost:9200`
- PostgreSQL: `localhost:2345`
- Redis: `localhost:6380`
- Flower, for optional local worker inspection: `http://localhost:5555`

For host-based Python development:

```bash
uv venv
source .venv/bin/activate
cd backend
uv pip install -e ".[dev]"
```

## Harvesting and indexing

The current node supports:

- repository discovery with `backend/scripts/populate_ogm_repos.py`;
- scheduled reconciliation with `backend/scripts/trigger_ogm_nightly_sync.py`;
- signed webhook ingestion at `POST /api/v1/admin/ogm/webhook`; and
- explicit index construction with `backend/scripts/run_index.py`.

Set `GITHUB_TOKEN` in the local environment when running GitHub discovery at a
rate that exceeds anonymous API limits. Set `OGM_WEBHOOK_SECRET` only through
the deployment secret source.

Common commands from the repository root:

```bash
make migrate
make reindex
make ogm-nightly
make cache-prime ARGS="--limit 100"
make test
make lint-check
```

The nightly reconciliation path is the correctness mechanism. Webhooks reduce
freshness latency but must not be the only way a mirror discovers changes.

## Generated caches

Resource representations, thumbnails, and static maps are generated runtime
data. They are stored in Redis and durable database-backed caches and are not
committed as source files.

After migrations and indexing, warm a bounded set:

```bash
make cache-prime ARGS="--limit 1000"
```

See [cache priming](docs/cache_priming.md) for production and background
workflows. Full-corpus runs deliberately avoid loading every image body into
Redis.

## Releases and upstream provenance

OGM product versions and BTAA backend provenance are separate:

- the product version describes this repository's API contract and release;
- `config/geobtaa-backend-source.env` records the last complete BTAA subtree
  import; and
- `docs/upstream_reconciliation.md` records selective ports made after that
  import.

Do not merge `geobtaa/api` into this repository. Preview a complete backend
import only when a deliberate rebase of the downstream product is intended:

```bash
./scripts/sync_backend_from_data_api.sh
```

The helper protects the paths in `config/ogm-owned-paths.txt`. An applied
import still requires diff review, the complete test suite, and a new
reconciliation record.

## Deployment and repository transfer

The current production node uses Kamal. Its stable operational identity is the
`ogm-api` service, existing hostname, role topology, accessory names, and host
volume paths—not the GitHub repository URL.

Repository transfer and container-registry migration are intentionally
separate changes. Preserve the running image path during the GitHub transfer,
then prove an organization-owned image with dual publication and rollback
before changing `config/deploy.yml`.

Read these before an operational change:

- [Deployment guide](docs/deployment.md)
- [Repository transfer runbook](docs/repository_transfer.md)
- [Repository transfer rehearsal](docs/repository_transfer_rehearsal.md)
- [Pre-transfer branch inventory](docs/repository_branch_inventory.md)
- [BTAA backend reconciliation](docs/upstream_reconciliation.md)
- [Backend sync design](docs/backend_upstream_sync.md)

Never change the Kamal service name, persistent volume paths, repository owner,
and image namespace in one deployment.

## Project status and participation

This codebase is being prepared for community ownership under the
OpenGeoMetadata organization. Mirror-network governance, sponsorship, service
objectives, edge ownership, and pilot authorization remain community
decisions. Discussion of the proposal belongs in the
[ogm-mirror-network issue tracker](https://github.com/OpenGeoMetadata/ogm-mirror-network/issues).

Code contributions should preserve the public API contract, keep derived state
rebuildable from canonical GitHub metadata, include focused tests, and document
any change to deployment or upstream provenance.

## License

See [LICENSE](LICENSE).
