#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$ROOT_DIR/config/upstream-backend-source.env"
OGM_OWNED_PATHS_FILE="$ROOT_DIR/config/ogm-owned-paths.txt"

if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
fi

REMOTE_NAME="${UPSTREAM_API_REMOTE_NAME:-upstream}"
REMOTE_URL="${UPSTREAM_API_REMOTE_URL:-https://github.com/geobtaa/api.git}"
UPSTREAM_BRANCH="${UPSTREAM_API_BRANCH:-develop}"
BACKEND_PREFIX="${UPSTREAM_API_BACKEND_PREFIX:-backend}"
SPLIT_BRANCH="${UPSTREAM_API_BACKEND_SPLIT_BRANCH:-vendor/upstream-api-backend}"
DEST_PATH="$ROOT_DIR/$BACKEND_PREFIX"

APPLY=0
ALLOW_DIRTY=0
ALLOW_OVERWRITE_OGM=0
NO_FETCH=0
SOURCE_PATH=""
PRINT_OWNED=0

usage() {
  cat <<EOF
Usage: $0 [options]

Refresh ./$BACKEND_PREFIX from geobtaa/api:$UPSTREAM_BRANCH's backend subtree.

Default mode is a dry run. Pass --apply to update files.

Options:
  --apply                  Apply the import. Without this, rsync runs dry.
  --allow-dirty            Allow an applied import with uncommitted changes.
  --allow-overwrite-ogm    Do not protect backend paths in config/ogm-owned-paths.txt.
  --branch BRANCH          Upstream branch to read. Default: $UPSTREAM_BRANCH.
  --remote NAME            Git remote name. Default: $REMOTE_NAME.
  --remote-url URL         Canonical upstream URL. Default: $REMOTE_URL.
  --source-path PATH       Import from an existing backend directory instead of Git.
  --no-fetch               Do not fetch the upstream remote before splitting.
  --print-owned            Print protected backend paths and exit.
  -h, --help               Show this help.

Examples:
  $0
  $0 --apply
  $0 --apply --source-path ../clients/b1g/data-api/backend
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY=1
      shift
      ;;
    --allow-dirty)
      ALLOW_DIRTY=1
      shift
      ;;
    --allow-overwrite-ogm)
      ALLOW_OVERWRITE_OGM=1
      shift
      ;;
    --branch)
      UPSTREAM_BRANCH="${2:?--branch requires a value}"
      shift 2
      ;;
    --remote)
      REMOTE_NAME="${2:?--remote requires a value}"
      shift 2
      ;;
    --remote-url)
      REMOTE_URL="${2:?--remote-url requires a value}"
      shift 2
      ;;
    --source-path)
      SOURCE_PATH="${2:?--source-path requires a value}"
      shift 2
      ;;
    --no-fetch)
      NO_FETCH=1
      shift
      ;;
    --print-owned)
      PRINT_OWNED=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_clean_worktree() {
  if [[ "$ALLOW_DIRTY" -eq 1 ]]; then
    return
  fi

  if ! git -C "$ROOT_DIR" diff --quiet || \
     ! git -C "$ROOT_DIR" diff --cached --quiet || \
     [[ -n "$(git -C "$ROOT_DIR" ls-files --others --exclude-standard)" ]]; then
    cat >&2 <<EOF
Refusing to apply an upstream backend import with uncommitted changes.
Commit or stash first, or rerun with --allow-dirty if you intentionally want
to review the import in the current working tree.
EOF
    exit 1
  fi
}

print_protected_backend_paths() {
  if [[ ! -f "$OGM_OWNED_PATHS_FILE" ]]; then
    return
  fi

  while IFS= read -r raw_path || [[ -n "$raw_path" ]]; do
    path="${raw_path%%#*}"
    path="${path#"${path%%[![:space:]]*}"}"
    path="${path%"${path##*[![:space:]]}"}"
    [[ -z "$path" ]] && continue
    case "$path" in
      "$BACKEND_PREFIX"/*)
        printf '%s\n' "${path#"$BACKEND_PREFIX"/}"
        ;;
    esac
  done < "$OGM_OWNED_PATHS_FILE"
}

if [[ "$PRINT_OWNED" -eq 1 ]]; then
  print_protected_backend_paths
  exit 0
fi

if [[ "$APPLY" -eq 1 ]]; then
  require_clean_worktree
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required for backend imports." >&2
  exit 1
fi

SOURCE_LABEL=""
UPSTREAM_COMMIT=""
SPLIT_COMMIT=""
TMP_DIR=""

cleanup() {
  if [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

if [[ -n "$SOURCE_PATH" ]]; then
  if [[ ! -d "$SOURCE_PATH" ]]; then
    echo "Backend source not found: $SOURCE_PATH" >&2
    exit 1
  fi
  SOURCE_LABEL="$SOURCE_PATH"
  if git -C "$SOURCE_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    UPSTREAM_COMMIT="$(git -C "$SOURCE_PATH" rev-parse HEAD)"
  else
    UPSTREAM_COMMIT="local-path"
  fi
else
  if ! git -C "$ROOT_DIR" remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
    git -C "$ROOT_DIR" remote add "$REMOTE_NAME" "$REMOTE_URL"
  else
    current_url="$(git -C "$ROOT_DIR" remote get-url "$REMOTE_NAME")"
    if [[ "$current_url" != "$REMOTE_URL" ]]; then
      git -C "$ROOT_DIR" remote set-url "$REMOTE_NAME" "$REMOTE_URL"
    fi
  fi

  if [[ "$NO_FETCH" -eq 0 ]]; then
    git -C "$ROOT_DIR" fetch "$REMOTE_NAME" "$UPSTREAM_BRANCH"
  fi

  UPSTREAM_COMMIT="$(git -C "$ROOT_DIR" rev-parse "$REMOTE_NAME/$UPSTREAM_BRANCH")"
  echo "Splitting $REMOTE_NAME/$UPSTREAM_BRANCH:$BACKEND_PREFIX ..."
  SPLIT_COMMIT="$(
    git -C "$ROOT_DIR" subtree split -q \
      --prefix="$BACKEND_PREFIX" \
      "$REMOTE_NAME/$UPSTREAM_BRANCH"
  )"
  git -C "$ROOT_DIR" update-ref "refs/heads/$SPLIT_BRANCH" "$SPLIT_COMMIT"

  TMP_DIR="$(mktemp -d)"
  git -C "$ROOT_DIR" archive "$SPLIT_COMMIT" | tar -x -C "$TMP_DIR"
  SOURCE_PATH="$TMP_DIR"
  SOURCE_LABEL="$REMOTE_NAME/$UPSTREAM_BRANCH:$BACKEND_PREFIX"
fi

mkdir -p "$DEST_PATH"
EXCLUDE_FILE="$(mktemp)"
TMP_DIR="${TMP_DIR:-}"
trap 'cleanup; rm -f "$EXCLUDE_FILE"' EXIT

cat > "$EXCLUDE_FILE" <<'EOF'
.DS_Store
__pycache__/
.pytest_cache/
.ruff_cache/
.venv/
venv/
coverage_html_report/
htmlcov/
.coverage
*.pyc
logs/
test_logs/
tmp/
gazetteer_import.log
data_api.egg-info/
data/duckdb/
data/elasticsearch/
data/gazetteers/
data/harvest_dumps/
data/opengeometadata/
data/postgres/
data/postgres_test/
data/redis/
static/maps/
EOF

if [[ "$ALLOW_OVERWRITE_OGM" -eq 0 ]]; then
  print_protected_backend_paths >> "$EXCLUDE_FILE"
fi

RSYNC_FLAGS=(-a --delete --exclude-from "$EXCLUDE_FILE")
if [[ "$APPLY" -eq 0 ]]; then
  RSYNC_FLAGS+=(--dry-run --itemize-changes)
fi

echo "Importing backend from $SOURCE_LABEL"
echo "Destination: $DEST_PATH"
if [[ "$ALLOW_OVERWRITE_OGM" -eq 0 ]]; then
  echo "Protecting OGM-owned backend paths from $OGM_OWNED_PATHS_FILE"
fi

rsync "${RSYNC_FLAGS[@]}" "$SOURCE_PATH"/ "$DEST_PATH"/

if [[ "$APPLY" -eq 0 ]]; then
  cat <<EOF

Dry run complete. Re-run with --apply to update $BACKEND_PREFIX/.
EOF
  exit 0
fi

imported_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
cat > "$CONFIG_FILE" <<EOF
# Canonical upstream source for the mirrored backend tree.
#
# scripts/sync_backend_from_data_api.sh reads these defaults. The import metadata
# at the bottom is updated by the script after a successful --apply run.

UPSTREAM_API_REMOTE_NAME=$REMOTE_NAME
UPSTREAM_API_REMOTE_URL=$REMOTE_URL
UPSTREAM_API_BRANCH=$UPSTREAM_BRANCH
UPSTREAM_API_BACKEND_PREFIX=$BACKEND_PREFIX
UPSTREAM_API_BACKEND_SPLIT_BRANCH=$SPLIT_BRANCH

# Updated after an applied import.
UPSTREAM_API_LAST_IMPORT_COMMIT=$UPSTREAM_COMMIT
UPSTREAM_API_LAST_BACKEND_SPLIT_COMMIT=$SPLIT_COMMIT
UPSTREAM_API_LAST_IMPORT_AT=$imported_at
EOF

cat <<EOF
Applied backend import from $SOURCE_LABEL.
Upstream commit: $UPSTREAM_COMMIT
Backend split commit: ${SPLIT_COMMIT:-n/a}
Updated $CONFIG_FILE

Recommended next steps:
  git diff --stat
  make test
  git add $BACKEND_PREFIX $CONFIG_FILE
  git commit -m "Import geobtaa/api backend $UPSTREAM_COMMIT"
EOF
