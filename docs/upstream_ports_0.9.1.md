# Selected upstream fixes through 0.9.1

This change selectively adapts shared backend behavior from `geobtaa/api`.
It retains OGM harvesting, durable thumbnail coverage, identity, visibility
rules, deployment settings, and existing Boolean-query interpretation.

## Search and temporal behavior

Encoded filter values are decoded once, so a value such as `Maps & Atlases`
remains one value. Year-range parsing accepts only the supported `start` and
`end` keys and ignores malformed nested array keys.

Search GET/POST, facet values, and H3 maps accept `include_filter_operator`:

- `or` is the default and preserves existing repeated-value behavior.
- `and` requires every selected value within a field, including legacy `fq`
  filters. Different fields remain conjunctive. Exclusions retain their behavior.
- GET rejects invalid operators with HTTP 422; POST search rejects them with
  HTTP 400. POST also accepts uppercase AND/OR and normalizes them.

For example, a POST search body can require both spatial labels:

```json
{
  "include_filters": {"dct_spatial_sm": ["Indiana", "Indiana--Bloomington"]},
  "include_filter_operator": "and"
}
```

Clients should send the same operator to search, facet, and map requests.
Generated facet-apply links preserve it. Search and facet cache keys include
the operator, while H3 endpoint caching distinguishes query parameters.

OGM ingestion and Elasticsearch indexing derive a missing or invalid
`gbl_indexYear_im` from the start year of the first `gbl_dateRange_drsim`
value. Valid explicit years take precedence. This does not expand a range
into every covered year. A reindex repairs existing search documents;
existing database records need re-ingestion or a separately reviewed backfill
to expose the derived value in resource metadata too.

## Thumbnails, static maps, and viewers

CONTENTdm normalization preserves the source provider and treats compound
manifests as manifests rather than guessing their image IDs. IIIF v2/v3
parsing prefers declared image services, including service URLs without an
`/iiif/` path. OGM still resolves Image API `info.json` documents in the worker
to support Level 0 advertised sizes, and the thumbnail endpoint retains
ownership of job queueing.

Static lines and areas connect projected vertices directly, preventing
geodesic interpolation artifacts. Points, zero-area point extents, and
bbox-only viewer records now receive geometry support. Static-map variants
advance to `static_map_v9` and `static_basemap_v7`; old durable variants are
not reused for new requests. The current basemap provider and OGM global
fallback artwork remain in place.

Previously resolved thumbnails and recorded failures can outlive a code
change. Use the existing bounded cache-prime workflow to force regeneration
of affected resources and retry failures/placeholders as appropriate. See
[cache priming](cache_priming.md); this PR does not initiate any production
reindexing, cache invalidation, or regeneration.

## Optional Redis response compression

`CACHE_REDIS_COMPRESSION_ENABLED=false` is the default. When enabled, response
records of at least 4 KiB are compressed with zlib level 1 only if encoding
saves at least 10%. Encoding/decoding is bounded to 16 MiB of uncompressed
JSON. The format marker is `OGM-RC` followed by version byte 1.

Readers accept both legacy JSON and compressed records, even when compressed
writes are disabled. Durable database records, HTTP bodies, ETags, cache
lifetimes, and conditional responses keep their existing semantics. Invalid
Redis records use the existing durable-cache fallback or become cache misses.

Deploy compatible readers everywhere before enabling writes. Turning the
setting off stops new compressed writes but does not convert existing Redis
entries. Before rolling back to older readers, allow those entries to expire
or invalidate the affected response cache. Measure memory savings and CPU/
latency on the OGM workload before enabling it broadly.

## Provenance and scope

| Upstream SHA | Adaptation |
| --- | --- |
| `eb89c10` | Encoded facet values and regression tests. |
| `131fa98` | Year-range parsing and regression tests. |
| `f6e6573` | Temporal helper, OGM ingestion, indexing; Bridge changes excluded. |
| `4389011` | IIIF resolution; preserves OGM Level 0 and queue ownership behavior. |
| `4ca8e5f` | Direct projected static geometry and cache variants. |
| `9ee88fe` | Backend point/bbox geometry support and regression tests. |
| `80dcd59` | AND faceting across endpoints, query builders, links, caches, and tests; visibility changes excluded. |
| `5b35609` | Opt-in response compression with OGM marker; host memory settings excluded. |

The source review is in the [September review](upstream_review_2026-09-12.md).
The existing `app.identity` already centralizes API version reporting from
OGM package metadata, so upstream's separate release JSON system is not added.
Dependency refresh, grouped Boolean semantics, relationship visibility,
institutional facets, and tile-provider changes remain separate work.
