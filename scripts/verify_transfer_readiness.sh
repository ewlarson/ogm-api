#!/usr/bin/env bash

set -euo pipefail

mode="worktree"
case "${1:-}" in
    "") ;;
    --full-history) mode="full-history" ;;
    --post-transfer) mode="post-transfer" ;;
    *)
        echo "Usage: $0 [--full-history|--post-transfer]" >&2
        exit 2
        ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd "$script_dir/.." && pwd)"
cd "$repository_root"

failures=0

pass() {
    printf 'PASS  %s\n' "$1"
}

fail() {
    printf 'FAIL  %s\n' "$1" >&2
    failures=$((failures + 1))
}

expect_exact_line() {
    local file="$1"
    local line="$2"
    local label="$3"
    if grep -Fqx -- "$line" "$file"; then
        pass "$label"
    else
        fail "$label"
    fi
}

expect_path_absent_from_index() {
    local pathspec="$1"
    local label="$2"
    if [ -z "$(git ls-files -- "$pathspec")" ]; then
        pass "$label"
    else
        fail "$label"
    fi
}

expect_path_absent_from_index '.kamal/secrets' 'Kamal secrets are not tracked'
expect_path_absent_from_index '.kamal/registry-password' 'Kamal registry password is not tracked'
expect_path_absent_from_index 'backend/static/maps/**' 'generated static maps are not tracked'

expect_exact_line .gitignore '.kamal/' 'Kamal operator files are ignored'
expect_exact_line .gitignore 'backend/static/maps/' 'generated static maps are ignored'

expected_image="${OGM_EXPECTED_IMAGE:-ewlarson/opengeometadata-api}"
expect_exact_line config/deploy.yml 'service: ogm-api' 'Kamal service identity is unchanged'
expect_exact_line config/deploy.yml "image: $expected_image" 'production image identity is unchanged'
expect_exact_line config/deploy.yml '  host: ogm.geo4lib.app' 'production proxy hostname is unchanged'
expect_exact_line config/deploy.yml '    ELASTICSEARCH_INDEX:   opengeometadata_api' 'Elasticsearch index is unchanged'
expect_exact_line config/deploy.yml '        POSTGRES_DB:   btaa_ogm_api' 'PostgreSQL database is unchanged'
expect_exact_line config/deploy.yml '      - esdata:/usr/share/elasticsearch/data' 'Elasticsearch volume is unchanged'
expect_exact_line config/deploy.yml '      - pgdata:/var/lib/postgresql/data' 'PostgreSQL volume is unchanged'
expect_exact_line config/deploy.yml '      - redisdata:/data' 'Redis volume is unchanged'

for role in web worker cron; do
    if grep -Eq "^  ${role}:$" config/deploy.yml; then
        pass "Kamal ${role} role is present"
    else
        fail "Kamal ${role} role is present"
    fi
done

if grep -Fq 'Draft for Community Discussion' README.md \
    && grep -Fq 'ogm-mirror-network' README.md; then
    pass 'README represents the proposal and its draft status'
else
    fail 'README represents the proposal and its draft status'
fi

for required_document in \
    docs/repository_transfer.md \
    docs/repository_transfer_rehearsal.md \
    docs/repository_branch_inventory.md \
    docs/upstream_reconciliation.md; do
    if [ -s "$required_document" ]; then
        pass "$required_document exists"
    else
        fail "$required_document exists"
    fi
done

floating_actions="$(grep -ERn \
    'uses:[[:space:]]+[^[:space:]#]+@(v[0-9]|main|master)([[:space:]#]|$)' \
    .github/workflows 2>/dev/null || true)"
if [ -z "$floating_actions" ]; then
    pass 'GitHub Actions dependencies are pinned to immutable commits'
else
    fail 'GitHub Actions dependencies are pinned to immutable commits'
fi

workflow_permission_failures=0
for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    [ -e "$workflow" ] || continue
    if ! grep -Fq 'permissions:' "$workflow" || ! grep -Fq '  contents: read' "$workflow"; then
        workflow_permission_failures=$((workflow_permission_failures + 1))
    fi
done
if [ "$workflow_permission_failures" -eq 0 ]; then
    pass 'GitHub workflows declare read-only repository contents permission'
else
    fail "$workflow_permission_failures GitHub workflow(s) lack explicit read-only contents permission"
fi

if grep -Eq '^UPSTREAM_API_LAST_IMPORT_COMMIT=[0-9a-f]{40}$' config/upstream-backend-source.env \
    && grep -Eq '^UPSTREAM_API_LAST_BACKEND_SPLIT_COMMIT=[0-9a-f]{40}$' config/upstream-backend-source.env; then
    pass 'Upstream subtree provenance is pinned to immutable commits'
else
    fail 'Upstream subtree provenance is pinned to immutable commits'
fi

if [ "$mode" = "full-history" ]; then
    repository_refs="$(git for-each-ref --format='%(refname)' refs/heads refs/remotes/origin)"
    if ! git remote get-url upstream >/dev/null 2>&1; then
        repository_refs="$repository_refs
$(git for-each-ref --format='%(refname)' refs/tags)"
    fi
    history_paths="$(git log --format= --name-only $repository_refs -- \
        .kamal/secrets \
        .kamal/registry-password \
        backend/static/maps \
        | awk 'NF' \
        | sort -u)"
    if [ -z "$history_paths" ]; then
        pass 'sensitive and generated paths are absent from repository-owned history'
    else
        history_sensitive_count="$(printf '%s\n' "$history_paths" | awk '
            /^\.kamal\// { count++ } END { print count + 0 }
        ')"
        history_generated_count="$(printf '%s\n' "$history_paths" | awk '
            /^backend\/static\/maps\// { count++ } END { print count + 0 }
        ')"
        fail "Git history still contains $history_sensitive_count sensitive and $history_generated_count generated path(s)"
    fi
fi

if [ "$mode" = "post-transfer" ]; then
    origin_url="$(git remote get-url origin 2>/dev/null || true)"
    case "$origin_url" in
        git@github.com:OpenGeoMetadata/ogm-api.git|https://github.com/OpenGeoMetadata/ogm-api.git)
            pass 'origin points to OpenGeoMetadata/ogm-api'
            ;;
        *) fail 'origin points to OpenGeoMetadata/ogm-api' ;;
    esac
fi

if [ "$failures" -gt 0 ]; then
    printf '\nTransfer readiness failed with %d issue(s).\n' "$failures" >&2
    exit 1
fi

printf '\nTransfer readiness checks passed (%s mode).\n' "$mode"
