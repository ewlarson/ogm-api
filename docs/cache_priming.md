# Generated Cache Priming

The API can prebuild generated artifacts so first user requests do not pay the
generation cost.

The combined primer is:

```bash
cd backend
python scripts/prime_generated_caches.py
```

It runs three stages, in this order:

- `thumbnails`: durable thumbnail visual assets, thumbnail state, and resource-to-asset links
- `static-maps`: durable static-map and basemap visual assets plus aliases
- `resources`: durable JSON:API resource representations for resource detail and search result payloads

The ordering is intentional: representations are generated after visual assets,
so gallery payloads contain immutable OGM API asset URLs. External IIIF, image,
service, COG, PMTiles, download-image, and PDF URLs are source inputs only. The
API never asks a browser to load those source URLs as thumbnails. When a preview
cannot be materialized, the primer generates and stores an OGM resource-class icon.

By default, full-corpus runs persist durable database-backed rows and avoid
loading every image body into Redis. Runtime requests can rehydrate Redis from
durable storage as needed.

## Local Examples

Prime a small sample:

```bash
make cache-prime ARGS="--limit 100"
```

Prime only resource representations:

```bash
make cache-prime ARGS="--stage resources"
```

Prime the exact Maps resource-class cohort, with no provider filter:

```bash
make cache-prime ARGS="--stage thumbnails --stage resources --resource-class Maps"
```

Do not add `--provider` for the cross-provider Maps coverage run. The option is
available only for diagnosing an individual provider.

Hydrate Redis image bodies for a bounded hotset:

```bash
make cache-prime ARGS="--hydrate-assets --limit 250"
```

Run in the background:

```bash
make cache-prime-background ARGS="--limit 1000"
tail -f backend/logs/prime_generated_caches.log
```

## Production After Deploy

Run migrations first so durable cache tables exist:

```bash
kamal app exec "python /app/backend/scripts/run_migrations.py"
```

Start a background cache prime inside the deployed app container:

```bash
kamal app exec "cd /app/backend && ./scripts/start_cache_prime_background.sh"
```

For a bounded warmup:

```bash
kamal app exec "cd /app/backend && ./scripts/start_cache_prime_background.sh --limit 5000"
```

Watch progress:

```bash
kamal app exec "tail -f /app/backend/logs/prime_generated_caches.log"
```

## Failure Policy

Thumbnail and static-map generation depend on external providers and tile
services. The primer logs failures and continues by default. Add
`--strict-failures` for CI or smoke runs where any failed resource should return
a nonzero exit code.

Use these options for retries:

```bash
python scripts/prime_generated_caches.py --retry-thumbnail-failures
python scripts/prime_generated_caches.py --retry-thumbnail-placeheld
```

## Maps Coverage Report

Measure the same cohort as the gallery's
`include_filters[gbl_resourceClass_sm][]=Maps` query:

```bash
cd backend
python scripts/report_thumbnail_completeness.py --scope maps --format table
python scripts/report_thumbnail_completeness.py --scope maps --format json
```

The report deliberately has no default provider filter. It separates two metrics:

- `success_pct`: eligible records with a real, durable preview derived and stored by OGM.
- `gallery_ready_pct`: eligible records with either a durable preview or a durable
  OGM-generated resource-class icon. Restricted records are excluded from this
  denominator and are never fetched.

Use `--show-missing 50` to sample real-preview gaps and `--source-bucket` to work
one source family at a time. A durable asset means image bytes exist in OGM's
visual-asset store; a source URL alone does not count.

## Production Backfill Sequence

After deploying the image containing Poppler (`pdftoppm`), capture a baseline,
prime locally owned visual assets, rebuild gallery representations, and verify:

```bash
kamal app exec "cd /app/backend && python scripts/report_thumbnail_completeness.py --scope maps --format json"
kamal app exec "cd /app/backend && ./scripts/start_cache_prime_background.sh --stage thumbnails --stage resources --resource-class Maps --retry-thumbnail-failures --retry-thumbnail-placeheld"
kamal app exec "tail -f /app/backend/logs/prime_generated_caches.log"
kamal app exec "cd /app/backend && python scripts/report_thumbnail_completeness.py --scope maps --format json"
```

Start with a bounded canary by adding `--limit 500`, inspect failures, then run
the full cohort. Do not use `--hydrate-assets` for the unbounded run unless Redis
is sized for all image bodies; durable database assets remain gallery-ready and
can be rehydrated on demand.

## Ongoing Refresh

OGM harvests compare fields that can change thumbnail selection. Only changed or
new records are re-primed, and their generated API representations are invalidated.
Controls:

- `OGM_THUMBNAIL_REFRESH_ENABLED` (default `true`)
- `OGM_THUMBNAIL_REFRESH_BATCH_SIZE` (default `500`)
- `OGM_THUMBNAIL_REFRESH_CONCURRENCY` (default `2`)
- `PDF_THUMBNAIL_MAX_BYTES` (default `33554432`)
- `REMOTE_THUMBNAIL_MAX_BYTES` (default `20971520`)

Set `OGM_THUMBNAIL_REFRESH_ENABLED=false` to stop post-harvest refresh without
disabling harvest. Existing immutable OGM assets continue to serve during a
rollback.
