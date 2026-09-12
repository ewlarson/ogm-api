# Upstream migration review — September 12, 2026

This document preserves the initial assessment. See the subsequent
[selected-port implementation](upstream_ports_0.9.1.md) for changes implemented
after the review. In particular, OGM's existing `app.identity` already
centralizes API version reporting, so a separate release JSON system was
not needed.

Review OGM `7ba492f` against fetched `geobtaa/api` develop
`9a4c78419e371f83642b3b1330f9fd804d3e0ff7` (0.9.1).
The local data-api checkout at `e0dd1ac` contains the same reviewed backend;
the fetched ceiling adds the release-tag merge. The previous review ceiling
was `4254aa3` (0.8.11). There are 33 non-merge backend-affecting commits in
this interval. This is a source review, not an applied migration or runtime
validation. No application code, lockfile, or import baseline was changed.

## Recommended first ports

| Priority | Upstream change | Why it applies here | Port scope and acceptance |
| --- | --- | --- | --- |
| 1 | `eb89c10` encoded facet values; `131fa98` year-range parsing | OGM still unquotes the entire query string before `parse_qs`, which turns encoded ampersands into separators. Its broad year-range parsing also accepts malformed nested keys. | Small patches in `services/search_service.py` plus upstream regression cases. Verify ampersands, plus signs, encoded brackets, valid start/end bounds, and ignored nested year-range array keys. The complete frontend chip-removal fix is outside this repository. |
| 1 | `4389011` IIIF thumbnails | OGM still hardcodes one CONTENTdm host during URL conversion, guesses image IDs from manifest IDs, and prefers a v2 resource ID over a declared image service. Catalog-page IDs and compound objects can therefore yield invalid thumbnails. | Adapt manifest parsing and URL resolution with upstream CONTENTdm/OSU tests. Preserve OGM's extra info.json handling, durable thumbnail state, source-change invalidation, and coverage pipeline. Verify v2/v3 services, list-valued services, provider hostname preservation, compound manifests, and existing OGM tests. Repair affected cached resolution/failure state after the port; code changes alone may not repair existing assets. |
| 1 | `f6e6573` derive index year from date ranges | OGM currently normalizes supplied years but does not supply this fallback. Records with only `gbl_dateRange_drsim` miss expected year-facet entries. | Add the temporal helper and use it in OGM ingestion and Elasticsearch processing; Bridge is optional. Preserve explicit years. Test canonical `[1922 TO 1962]`, malformed/empty ranges, and multiple explicit years. Reindex to repair existing search documents; persisted resource metadata requires re-ingestion or a separate backfill. This derives the first range's start year, not every covered year. |
| 1 | `4ca8e5f` static geometry interpolation; `9ee88fe` point support | OGM retains static-map v7/basemap v5 behavior, geodesic interpolation, and incomplete point/bbox viewer handling. | Port together across static maps, viewer reference parsing, and ItemViewer. Carry geometry tests for direct projected lines, zero-area point extents, WKT points, bbox-only resources, and polar fallback. Advance OGM cache variants and verify durable assets regenerate. Retain OGM global fallback branding. These fixes do not require changing tile providers. |

## Next candidates

- **Drill-down faceting (`80dcd59`):** useful API addition across GET/POST
  search, facet values, and H3 maps. Keep the existing OR default; clients
  explicitly select AND. Port the parameter allowlists, validation, query
  builders, service forwarding, links, and every affected cache key together.
  Test that the same repeated selections produce consistent hits, counts,
  and map totals, with separate AND/OR cache entries. Upstream context includes
  the previously deferred visibility work; adapt hunks rather than importing
  the whole search module.
- **Grouped Boolean search (`a0a69a2`):** replaces the current same-field OR
  heuristic with ordered positive groups. Upstream interprets `A AND B OR C`
  as `A AND (B OR C)`, with global NOT exclusions. This is an observable
  compatibility change, not conventional Boolean precedence. Adopt only with
  explicit API documentation and mixed-field, mixed-operator regression
  coverage across search, facets, and maps; invalidate changed query caches.
- **Redis response compression (`5b35609`):** a good bounded performance
  candidate for mirror nodes. Port only the codec, cache integration, tests,
  and opt-in setting. Durable rows and HTTP bodies retain their format.
  Upstream compresses sufficiently large records only when savings justify
  it and bounds decompression. Choose an OGM format marker before enabling
  writes. Deploy compatible readers before enabling compression; account for
  old readers during rollback. Measure OGM memory savings and latency rather
  than copying upstream institutional host allocations.
- **Dependency refresh (`1ebff73`, plus outstanding `9d2eb78`/`6f4b73b`):**
  open a separate OGM dependency change. Current declared aiohttp, Pillow,
  and Tornado pins are older than upstream; the MCP minimum is also lower.
  Re-resolve the OGM lockfile and run a current vulnerability audit and full
  suite. This review establishes version differences, not current advisory
  status or that upstream versions are sufficient today.
- **Central version metadata (`f3c83a9`):** useful maintenance improvement:
  one OGM-owned source for API root, OpenAPI, MCP, and package metadata.
  Include package/build tests and ensure the release JSON is shipped in the
  image/wheel. Do not copy upstream's version number or release automation.

## Changes requiring an OGM-specific decision

**Visibility remains unfinished prior work.** `7165142` was already marked
for selective porting. Resolve publication/suppression defaults and cache
isolation across public endpoints before importing broad upstream search
files. Decide whether any non-public diagnostic access belongs on the
restricted control plane rather than exposing an unrestricted public flag.

`873d9c5` removes suppression filtering from upstream relationship widgets
while retaining publication filtering. OGM's current relationship query has
neither predicate, so this is not a missing one-line fix here. Define the
desired publication/suppression contract first, then apply it consistently
to relationship responses and representation caches. The older ledger's
description of a public relationship service should not be read as proof
that these predicates are currently enforced.

`68c1f64` adds upstream institutional codes/admin tags to default full-text searches and supports
whole-day accession queries on upstream institutional fields. The shared query-builder
refactoring is reusable, but adding institutional administrative fields to
default public discovery is not an automatic OGM requirement. Likewise,
`a4006cd` adds a upstream institutional local-collection facet, not a general Aardvark collection
implementation. Defer unless corpus usage and client needs justify them.

`bf95609` changes the basemap provider, attribution, user agent, zoom limit,
and cache variants. Evaluate a configurable provider for OGM separately,
including suitability for bulk cache generation. Preserve proper attribution
and use OGM identification if adopted. Do not couple this choice to the
independently useful geometry corrections.

## Complete interval classification

These are review decisions, not claims that ports have landed.

| Commit | Decision |
| --- | --- |
| `19a869c` | Defer: Northwestern institutional access label. |
| `fc0bc0c` | Not applicable: backend release bookkeeping; named UI fixes are not backend implementations in this commit. |
| `a9f42ee` | Not applicable: backend release bookkeeping; UW viewer fix is not implemented in this backend delta. |
| `c6e00d3` | Optional small port: correct Waukesha fixture from array to object; validate local fixture ingestion. |
| `06a0cef` | Defer: Bridge cache rewarm rate limiting; retain as design input if an equivalent OGM rewarm issue is demonstrated. |
| `5a09ab2` | Not applicable: upstream institutional deployment memory settings and their tests. |
| `7d7fbdc` | Not applicable: release bookkeeping. |
| `f6e6573` | Port selectively: temporal fallback in OGM importer/indexer. |
| `a4006cd` | Defer: upstream institutional local collection facet. |
| `873d9c5` | Design decision: relationship visibility, with prior visibility work. |
| `4ca8e5f` | Port: direct projected static geometry. |
| `9ee88fe` | Port selectively: backend point and bbox viewer support; frontend work excluded. |
| `fb666ea` | Not applicable: release bookkeeping. |
| `80dcd59` | Port selectively: opt-in AND facet semantics and complete cache/endpoint propagation. |
| `a0a69a2` | Port selectively after API semantics decision: grouped Boolean queries. |
| `131fa98` | Port selectively: backend year-range parser and tests. |
| `db767c7` | Not applicable: release bookkeeping. |
| `eb89c10` | Port: parse encoded filters once. |
| `f3c83a9` | Port selectively: centralized OGM version metadata. |
| `d358141` | Not applicable: release bookkeeping. |
| `6f51ef0` | Not applicable: release metadata. |
| `9436630` | Defer: backup retention is an OGM operations decision. |
| `09411d7` | Not applicable: release metadata. |
| `bf95609` | Design decision: tile provider and attribution. |
| `e19ef34` | Not applicable: release metadata. |
| `74418ac` | Optional test port only: backend icon-gradient endpoint assertion; runtime fix is frontend. |
| `5d1dde2` | Not applicable: release metadata. |
| `5b35609` | Port selectively: opt-in response codec; exclude production memory configuration. |
| `1ebff73` | Dependency review: independently resolve and audit OGM dependencies. |
| `68c1f64` | Defer institutional search fields; shared query helper is reusable. |
| `b4ac94f` | Not applicable: release metadata. |
| `4389011` | Port selectively: IIIF resolution preserving OGM thumbnail extensions. |
| `36e25ab` | Not applicable: release metadata. |

The latest last-facet reset fix (`dff2dca`, #415) is frontend-only and is
deliberately outside the backend ledger. It would belong in a consuming
discovery client with the equivalent URL/query-state behavior.

## Suggested delivery order

1. Small filter-parser corrections.
2. Temporal normalization with an explicit existing-record repair plan.
3. IIIF resolution adapted to OGM thumbnail state.
4. Static-map and viewer geometry fixes with cache version changes.
5. Visibility contract, then broader facet/Boolean capabilities.
6. Separately: dependency refresh, optional compression, and version metadata.

Carry each port's focused upstream tests and OGM regressions, followed by
the complete backend suite before release. Keep the June full-import baseline
unchanged and record actual port SHAs in the reconciliation ledger when
implemented. The previously deferred distribution/asset work (`ab214d5`)
also remains outstanding; it was not superseded by this interval.
