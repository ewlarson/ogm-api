# Repository transfer rehearsal evidence

This file records non-secret evidence gathered on 2026-08-19 while preparing
`ewlarson/ogm-api` for transfer to `OpenGeoMetadata/ogm-api`. It is a snapshot,
not authorization to transfer. Repeat every live check during the scheduled
change window and store sensitive operational evidence in the private change
record described by `repository_transfer.md`.

## Requirement evidence

| Requirement | Evidence | Result |
| --- | --- | --- |
| Source repository identity | GitHub reported public, active `ewlarson/ogm-api`, default branch `develop` | Pass |
| Destination authority | GitHub reported active `admin` membership in `OpenGeoMetadata` | Pass |
| Destination name | Authenticated request for `OpenGeoMetadata/ogm-api` returned HTTP 404 | Available at check time |
| Rehearsal source fidelity | All 18 locally fetched `origin/*` branch names and tips matched the live GitHub branch list | Pass |
| Historical secret paths | Repository-owned history contained zero `.kamal/secrets` or `.kamal/registry-password` paths | Pass |
| Generated history | Repository-owned history contained 2,108 `backend/static/maps/` paths | Rewrite required |
| Current worktree | Generated maps are deleted from the index and `backend/static/maps/` is ignored | Pass |
| Actions secrets | Four expected nightly SSH secret names exist; values were not read | Pass |
| Other GitHub attachments | Zero webhooks, deploy keys, rulesets, environments, and Actions variables | Pass |
| Branch disposition | 14 non-default branches are fully merged; three inactive 2025 branches contain superseded unique patches; no pull request is open | Owner decision required for three branches |
| Source Actions policy | Actions enabled; repository default was write, while each prepared workflow now declares `contents: read` | Pass after prepared changes are published |
| Destination Actions policy | Token could not read organization policy because it lacks `admin:org` | Manual preflight required |
| Personal GHCR package metadata | Token could not read package metadata because it lacks `read:packages` | Manual preflight required |
| Production registry access | Production host successfully inspected the deployed personal GHCR manifest using its existing credentials | Pass |
| Production topology | Kamal 2.7.0 reported healthy proxy, `web`, `worker`, `cron`, PostgreSQL, Elasticsearch, and Redis containers | Pass |
| Production API | API root returned version `0.7.0`; representative search returned results | Pass |

## Isolated rewrite rehearsal

The rehearsal populated a new bare repository only from the locally fetched
`refs/remotes/origin/*` branches after those refs were compared to live GitHub.
BTAA remote refs and locally fetched BTAA tags were excluded. The temporary
mirror was rewritten with:

```bash
git filter-repo --force \
  --path .kamal/secrets \
  --path .kamal/registry-password \
  --path backend/static/maps \
  --invert-paths
```

Results:

- all 18 branch names remained present;
- all 232 source commits received a mapping and none were dropped;
- sensitive-path count remained zero;
- generated-map path count fell from 2,108 to zero;
- `git fsck --full --strict` completed successfully;
- packed object storage fell from approximately 329 MiB to 122 MiB; and
- the rewritten `develop` tree retained the `ogm-api` service, personal image
  path, production hostname, and all three persistent host directory mappings.

The rehearsal mirror was local and disposable. Nothing was force-pushed, no
repository was transferred, no image was published, and no production state
was changed.

The sanitized mirror was then cloned into a disposable candidate checkout.
Every modified, deleted, and untracked path from the prepared shared worktree
was overlaid onto that checkout. A path-by-path comparison covered 799 source
paths with zero mismatches. After a temporary candidate-only commit:

- `./scripts/verify_transfer_readiness.sh --full-history` passed every check;
- `git fsck --full --strict` passed; and
- the complete backend suite passed with 1,831 tests passed, 99 skipped, and
  one expected-pass after the existing ignored local test configuration was
  linked into the disposable checkout; and
- the candidate worktree was clean.

The temporary rehearsal commit was not created in the shared checkout and was
not pushed anywhere.

## Change-window evidence still required

Before the actual transfer:

1. commit and review the prepared worktree;
2. approve `repository_branch_inventory.md`, prune approved branches, freeze
   pushes, and repeat the live branch-tip comparison;
3. verify the OpenGeoMetadata Actions policy with an organization-authorized
   token or in the organization settings UI;
4. verify personal GHCR package ownership/access with `read:packages`, while
   keeping production pinned to the personal image path;
5. create and verify the database backup and host snapshot identified in the
   private change record;
6. rewrite a fresh mirror of the frozen GitHub repository and require
   `make transfer-readiness-full` to pass in a checkout of the result; and
7. follow the transfer and rollback sequence in `repository_transfer.md`.
