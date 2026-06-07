# Generated Cache Priming

The API can prebuild generated artifacts so first user requests do not pay the
generation cost.

The combined primer is:

```bash
cd backend
python scripts/prime_generated_caches.py
```

It runs three stages:

- `resources`: durable JSON:API resource representations for resource detail and search result payloads
- `thumbnails`: durable thumbnail visual assets, thumbnail state, and resource-to-asset links
- `static-maps`: durable static-map and basemap visual assets plus aliases

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
