# Repository transfer and production continuity runbook

This runbook moves `ewlarson/ogm-api` to `OpenGeoMetadata/ogm-api` without
coupling GitHub ownership to a production deployment. The repository transfer
is a control-plane change. It must not restart containers, change the Kamal
service identity, move persistent data, or change the image pulled by
production.

GitHub normally preserves issues, pull requests, releases, webhooks, deploy
keys, secrets, and redirects when a repository is transferred. Organization
policy and package permissions still require explicit verification. Review
GitHub's current [repository transfer documentation](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository)
immediately before the change.

See `repository_transfer_rehearsal.md` for the dated, non-secret evidence from
the isolated history-rewrite and live preflight rehearsal. That evidence must
be refreshed during the actual change window.

See `repository_branch_inventory.md` for the disposition of all live personal
repository branches. Do not copy every fetched ref into the cutover mirror by
default; only GitHub-owned refs approved in that ledger belong in the transfer.

## Stop conditions

Do not transfer the repository until all of these are true:

- a secret scan of every repository-owned branch and tag is clean, and any
  credential the scan identifies has been rotated at its authority;
- a coordinated history rewrite has removed generated `backend/static/maps/`
  assets from every branch and tag (the rewrite also strips Kamal secret paths
  defensively);
- the rewritten repository passes `make transfer-readiness-full`;
- the OpenGeoMetadata owners have approved the repository name, visibility,
  teams, branch policy, Actions policy, and secret owners;
- every live branch has an approved keep/delete disposition and no open pull
  request or collaborator work depends on a branch slated for deletion;
- the currently deployed image reference and digest, Kamal version, and
  rollback version have been recorded; and
- a production database backup and a host-volume snapshot or equivalent
  recovery point have been verified.

The preparation audit found `.kamal/secrets` in commits reachable only from the
separate `geobtaa/api` upstream remote, not in branches owned by
`ewlarson/ogm-api`. It found no shared assignments between that upstream file
and the current ignored local operator file. Do not import upstream refs or
tags into the transferred repository. If a subsequent scanner finds a secret
in an OGM-owned ref, treat it as compromised: removing Git history does not
revoke a credential and is not a substitute for rotation.

## Production invariants

The following values are intentionally frozen through the repository transfer:

| Invariant | Current value |
| --- | --- |
| Kamal service | `ogm-api` |
| Production host and proxy hostname | `ogm.geo4lib.app` |
| Roles | `web`, `worker`, `cron` |
| Container image | `ewlarson/opengeometadata-api` |
| Registry and login owner | `ghcr.io`, `ewlarson` |
| Elasticsearch index | `opengeometadata_api` |
| PostgreSQL database | `btaa_ogm_api` |
| Elasticsearch volume | `/var/lib/opengeometadata-api/elasticsearch` |
| PostgreSQL volume | `/var/lib/opengeometadata-api/postgres` |
| Redis volume | `/var/lib/opengeometadata-api/redis` |

The legacy PostgreSQL database name is persistent identity, not public project
branding. Rename it only in a separate, backed-up database migration.

Run the local invariant checks before and after every preparation commit:

```bash
make transfer-readiness
```

## Phase 1: verify and externalize secrets

1. Scan every OGM-owned branch and tag without copying suspected values into an
   issue, chat, log, or pull request.
2. If the scan identifies a credential, rotate it at its authority. Relevant
   classes include registry/GitHub tokens, database/admin credentials, webhook
   signing secrets, SSH material, and third-party API credentials.
3. Replace any rotated deployment value through the approved secret source,
   verify the running application, and only then revoke the old value.
4. Confirm `.kamal/` remains ignored and that no workflow, fixture, log, or
   documentation contains a copied value.
5. Record the scan result and, when applicable, who rotated each credential,
   its authority, and completion time in the private operational system—not in
   this repository.

Do not edit the operator's ignored local `.kamal/secrets` file as part of a
repository cleanup commit; doing so can silently break the next deployment.

## Phase 2: rewrite contaminated and generated history

The current repository-owned branch history contains more than a thousand
generated static-map paths. Schedule a push freeze and announce that every
existing clone will need to be re-cloned. Record the last pre-rewrite commit in
the private change record; do not create a public pre-rewrite tag, because that
would keep the removed objects reachable. Perform the rewrite in a fresh
temporary mirror of `origin`, never in an operator's deployment checkout:

```bash
git clone --mirror git@github.com:ewlarson/ogm-api.git ogm-api-sanitized.git
cd ogm-api-sanitized.git
git filter-repo --force \
  --path .kamal/secrets \
  --path .kamal/registry-password \
  --path backend/static/maps \
  --invert-paths
```

Inspect every rewritten ref, run a secret scanner approved by the
OpenGeoMetadata organization, and run the equivalent of:

```bash
git rev-list --objects --all | grep -E '(^|/)(\.kamal/(secrets|registry-password)|backend/static/maps/)'
```

The command must return no paths. Only after verification should the release
operator force-push all rewritten branches and tags. Remove cached forks or
temporary mirrors that could reintroduce the old objects, preserve the private
audit record, and require collaborators to re-clone.

## Phase 3: record the running deployment

From the operator workstation, record these outputs in the private change
record:

```bash
git rev-parse HEAD
kamal version
kamal details
kamal app images
```

Also record the active container image including its immutable digest, the
previous known-good image, accessory health, free disk space, last successful
nightly reconciliation, database backup identifier, and a small production
smoke-test result. Do not run `kamal deploy` during the GitHub transfer.

The transfer operator must separately confirm that the personal GHCR image is
still readable by the production host. GitHub repository transfer does not
make a personal container package organization-owned. Package linkage and
access are managed separately; review GitHub's current
[package/repository connection documentation](https://docs.github.com/en/packages/learn-github-packages/connecting-a-repository-to-a-package).

## Phase 4: transfer the repository

1. Freeze pushes and scheduled/manual deployment activity.
2. Run `make transfer-readiness-full` against the exact commit being moved.
3. In GitHub, transfer the repository to `OpenGeoMetadata` using the unchanged
   repository name `ogm-api`.
4. Do not create a replacement `ewlarson/ogm-api`; that would interfere with
   GitHub's redirect from the old URL.
5. Update the local Git remote after the transfer:

   ```bash
   git remote set-url origin git@github.com:OpenGeoMetadata/ogm-api.git
   git remote -v
   ```

6. Run `./scripts/verify_transfer_readiness.sh --post-transfer`.

No production containers should change during these steps.

## Phase 5: verify GitHub controls and automation

Immediately verify:

- repository visibility, default branch (`develop`), tags, releases, issues,
  pull requests, discussions, and redirect behavior;
- OpenGeoMetadata owner/admin access and least-privilege team access;
- branch protection or rulesets, required checks, Actions permissions, and
  environment approval rules;
- webhooks, deploy keys, GitHub Apps, security settings, vulnerability alerts,
  and code-scanning configuration;
- Actions secrets `OGM_KAMAL_SSH_PRIVATE_KEY`, `OGM_KAMAL_SSH_HOST`,
  `OGM_KAMAL_SSH_PORT`, and `OGM_KAMAL_SSH_USER`; and
- that the nightly workflow can locate a running container labeled
  `service=ogm-api` and complete one manually dispatched reconciliation.

Verify the public API, OpenAPI document, a representative search, a resource
response, sitemap/robots behavior, and the harvest dashboard. Then unfreeze
normal repository activity. A successful repository transfer does not require
or authorize a production deployment.

## Phase 6: migrate the image namespace later

Move from the personal package to an organization-owned GHCR package only in a
separate release:

1. create `ghcr.io/opengeometadata/opengeometadata-api` with explicit package
   access for the repository and deployment principals;
2. publish the same immutable release to both personal and organization image
   names;
3. verify matching image digests and pull the organization image from the
   production host before editing Kamal configuration;
4. change only the Kamal image/registry settings, keeping the service, host,
   roles, index, database, accessory names, and volume paths fixed;
5. deploy during a separate window, verify health and data continuity, and
   keep the personal image available for rollback; and
6. retire the personal package only after a complete rollback window and an
   independent cold-start/pull test.

## Rollback

If GitHub ownership or policy is wrong, freeze writes and transfer the
repository back while the original owner and name are still available. The
running application is unaffected because its image and host were not changed.

If the nightly workflow fails, disable its schedule or leave it frozen, run the
existing production reconciliation through the recorded operator path, and fix
organization secrets/permissions before re-enabling it.

If the later image migration fails, restore
`ewlarson/opengeometadata-api` and the recorded immutable tag/digest, then use
the normal Kamal rollback procedure. Never remove or recreate PostgreSQL,
Elasticsearch, or Redis accessories as part of an image rollback.

## Completion evidence

The migration is complete only when the organization repository is the
documented canonical source, the old URL redirects, all organization controls
and scheduled workflows are verified, the full-history and secret scans are
clean (with any actual exposure recorded as rotated), and production continues
to serve the same data from the same persistent volumes. Organization-owned
image publication may remain a documented follow-up if the personal image is
still deliberately pinned and supported.
