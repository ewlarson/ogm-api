# BTAA backend reconciliation

This repository does not share Git ancestry with `geobtaa/api`. The local
`develop` branch and `upstream/develop` have no merge base, so Git ahead/behind
counts are not an integration plan. The supported unit of comparison is the
BTAA `backend/` subtree recorded in `config/geobtaa-backend-source.env`.

## Baseline and target

| Item | Value |
| --- | --- |
| Last imported BTAA commit | `0c9d80b3b36e833fce0a17551da893bf0aa68928` |
| BTAA tag containing that commit | `v0.7.16` |
| Recorded backend split | `1cf222b377be4ba1d8468fa864724542e866eb3e` |
| Review ceiling | BTAA `0.8.11` (`4254aa3`) |
| OGM product version | Independent; currently `0.7.0` |

The review ceiling is not a promise that this product becomes BTAA `0.8.11`.
OGM releases and BTAA source provenance are separate concepts.

## Reconciliation policy

1. Review only non-merge commits that affect `backend/` between the recorded
   baseline and the selected review ceiling.
2. Classify each change as `ported`, `port selectively`, `dependency review`,
   `defer`, or `not applicable`.
3. Port shared behavior with its tests and record the upstream SHA. Do not
   cherry-pick whole commits across the unrelated histories.
4. Never overwrite the downstream paths listed in
   `config/ogm-owned-paths.txt` without an explicit OGM design decision.
5. Run focused tests for every port, followed by the complete backend suite
   before release.
6. Update `config/geobtaa-backend-source.env` only for a complete applied
   subtree import. Selective ports remain documented here instead.

## Decision ledger: `v0.7.16` through `0.8.11`

| Upstream commit | Decision | OGM rationale or follow-up |
| --- | --- | --- |
| `e95178a` Prepare GTM for production cutover | Not applicable | BTAA frontend analytics and production configuration are outside the OGM mirror API contract. |
| `1433322` Bump API version to 0.8.0 | Not applicable | OGM product versioning is independent. |
| `a529b3b` Prepare v0.8.1 release | Not applicable | BTAA release bookkeeping is not imported. |
| `a17b83e` Fix production feedback delivery default | Not applicable | Recipient and mail defaults are operator-specific. |
| `a51a018` Fix production sitemap canonical URL | **Ported** | Prevents a mirror from serving sitemap documents generated for a different origin. Ported with OGM hostname coverage. |
| `97c80d2` Add Turnstile bot exemptions and update Kithe bridge | Defer | Mixed BTAA edge policy and Kithe control-plane behavior. Revisit only if those components enter the supported OGM deployment profile. |
| `7becdd8` Version bump for v0.8.4 | Not applicable | BTAA release bookkeeping is not imported. |
| `caf71d7` Fix similar items missing Elasticsearch docs | **Ported** | Uses `exists` instead of a traced `GET` 404 for retired or intentionally unindexed records. |
| `e6674b4` Bump version to 0.8.5 | Not applicable | BTAA release bookkeeping is not imported. |
| `7165142` Improve telemetry and Elasticsearch visibility controls | Port selectively | Public/suppressed filtering, mapping checks, and cache-key isolation support the mirror public-read contract. AppSignal and BTAA fallback values do not. Requires a dedicated cross-endpoint PR. |
| `1ea6609` Bump version to 0.8.6 | Not applicable | BTAA release bookkeeping is not imported. |
| `d60a24a` Fix bridge relationship sync and indexing refresh | Defer | Primarily Kithe Bridge reconciliation. OGM mirrors use GitHub Aardvark harvests as their correctness path. |
| `15c1200` Fix AppSignal frontend telemetry isolation | Not applicable | Frontend telemetry and BTAA observability configuration are not part of this backend product. |
| `a477847` Fix Kithe Bridge deletion reconciliation | Defer | Kithe-specific deletion workflow; evaluate against OGM repository removal and tombstone policy separately. |
| `9d2eb78` Bump `aiohttp` | Dependency review | Re-resolve against the OGM lockfile and run security/compatibility tests instead of copying one lockfile delta. |
| `fb4bbbf` Drop Flower from Kamal deployments | Already satisfied | OGM Kamal roles are `web`, `worker`, and `cron`; Flower remains only an optional local Compose service. |
| `a545109` Handle Bridge tombstone deletes | Defer | Useful design input for deletion semantics, but the implementation is coupled to Kithe Bridge. |
| `b8098a0` Bump version to 0.8.7 | Not applicable | BTAA release bookkeeping is not imported. |
| `6f4b73b` Refresh project dependencies | Dependency review | Produce a fresh OGM dependency PR with lockfile, license, vulnerability, and runtime verification. |
| `721ea3b` Adjust response handling and file checks | Port selectively | Generic error sanitization and file checks are candidates; Slack, admin, and BTAA response labels require endpoint-by-endpoint review. |
| `93f73d6` Use local Postgres backups in production | Design reference | Mirror backup/rebuild behavior belongs in the OGM operating runbook and secret model, not as a blind BTAA script import. |
| `0a24422` Bump version to 0.8.8 | Not applicable | BTAA release bookkeeping is not imported. |
| `d991db3` Bump version to 0.8.9 | Not applicable | BTAA release bookkeeping is not imported. |
| `ab214d5` Fix GEOMG distribution and asset syncing | Port selectively | Aardvark distribution, reference, asset, and relationship correctness is relevant, but the commit is broad and Bridge-heavy. Split it into contract-focused ports after fixture comparison. |
| `2d5444f` Fix location filtering for contained resources | **Ported** | Uses document containment for bbox eligibility so a large query retains small fully contained resources. |
| `bfbd4db` Bump version to 0.8.10 | Not applicable | BTAA release bookkeeping is not imported. |
| `ac1b700` Fix relationship cache priming visibility | **Ported** | Routes priming through the public relationship service, connects the legacy database pool for in-process warming, and advances the representation cache version. |
| `78466a2` Fix source relationship direction | **Ported** | Emits canonical `dct:isSourceOf`, removes the legacy inverse during sync, canonicalizes old rows, and deduplicates responses. |
| `f1f4092` Release v0.8.11 | Not applicable | Backend changes are release-version updates; the named PMTiles rendering fix is in the BTAA frontend, which this repository does not ship. |

## Port verification

The accepted ports are covered by focused tests in:

- `tests/elasticsearch/test_search.py`
- `tests/services/test_relationship_service.py`
- `tests/services/test_relationship_sync.py`
- `tests/services/test_sitemap_service.py`
- `tests/scripts/test_prime_resource_representation_cache.py`
- `tests/scripts/test_refresh_resource_caches.py`

Before the next upstream review, fetch `upstream`, choose a new immutable review
ceiling, append every backend-affecting commit to this ledger, and keep earlier
decisions intact for auditability.
