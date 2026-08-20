# Pre-transfer branch inventory

This inventory records the branch state of `ewlarson/ogm-api` on 2026-08-19.
It exists so the history rewrite and organization transfer use an intentional
ref set. Branch deletion is not performed by repository preparation scripts.

At audit time the repository had 18 live branches, no tags, and no open pull
requests. All ten historical pull requests were closed and merged.

## Fully merged branches

These branch tips are ancestors of `develop` and contain zero commits ahead of
it. Their pull-request or commit history remains in `develop`; retaining the
branch name adds no source history.

| Branch | Commits behind `develop` | Recommended disposition |
| --- | ---: | --- |
| `agent/fix-unr-iiif-thumbnails` | 5 | Delete before transfer |
| `feature/admin-endpoints` | 118 | Delete before transfer |
| `feature/ai-summaries` | 138 | Delete before transfer |
| `feature/downloads` | 169 | Delete before transfer |
| `feature/gazetteer` | 158 | Delete before transfer |
| `feature/item_allmaps` | 99 | Delete before transfer |
| `feature/ogm-studio-api-dashboard` | 17 | Delete before transfer |
| `feature/queue-and-cache` | 172 | Delete before transfer |
| `feature/reference-visuals-from-dct-references` | 10 | Delete before transfer |
| `feature/relations` | 164 | Delete before transfer |
| `feature/restore-ogm-repo-dashboard` | 7 | Delete before transfer |
| `feature/swagger-json-response-highlighting` | 18 | Delete before transfer |
| `feature/sync-geobtaa-api-2026-06-06` | 18 | Delete before transfer |
| `main` | 217 | Delete after confirming `develop` remains the default branch |

## Unmerged historical branches

These branches have no pull requests and have been inactive since 2025. Their
patches are not byte-for-byte present in `develop`, so deletion needs an owner
decision even though their intended capabilities have been superseded.

| Branch | Behind/ahead | Unique commits | Assessment | Recommended disposition |
| --- | ---: | --- | --- | --- |
| `feature/duckdb-shapefiles` | 97 / 1 | `f3870d0` | Early shapefile endpoint plus a committed 3.4 MB DuckDB file and large lockfile change. Current `develop` has a maintained shapefile service and endpoint test coverage. | Delete after owner confirmation |
| `feature/geosearch` | 97 / 2 | `2277261`, `efce8eb` | Initial bbox search. Current `develop` has normalized bbox filters, scoring, containment behavior, and extensive tests. The same branch also remains in the BTAA upstream remote. | Delete after owner confirmation |
| `feature/test-suite` | 174 / 1 | `e2f8305` | Initial test harness with a committed SQLite test database. Current `develop` has 158 backend test modules and a passing 1,831-test suite. | Delete after owner confirmation |

If any historical branch must be retained for archaeology, preserve it outside
the transferred repository with an access-controlled `git bundle` and record
its full commit SHA in the private migration record. Do not create archive tags
inside this repository: tags keep the same objects reachable and defeat ref
cleanup.

## Cutover procedure

1. Freeze pushes and repeat the live branch inventory.
2. Confirm that no pull request is open and no collaborator has unpublished
   work based on a branch slated for deletion.
3. Obtain explicit owner approval for the three unmerged branches.
4. Delete approved remote branches while the repository is still under the
   personal owner.
5. Fetch with pruning into the cutover workstation and verify that local
   `origin/*` refs exactly match GitHub.
6. Populate the fresh rewrite mirror only from the approved live heads and
   tags. Never include `upstream/*` refs or locally fetched BTAA tags.
7. Record the final ref names and pre-rewrite SHAs in the private change record.

The tested rewrite can preserve all 18 branches, so branch pruning is a
governance and cleanliness decision rather than a technical prerequisite. The
recommended community-facing end state is a single `develop` branch unless an
OpenGeoMetadata maintainer asks to retain another ref.
