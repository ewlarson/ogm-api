#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_PATH="${1:-"$ROOT_DIR/../clients/b1g/data-api/backend"}"
DEST_PATH="${2:-"$ROOT_DIR/backend"}"

if [[ ! -d "$SOURCE_PATH" ]]; then
  echo "Backend source not found: $SOURCE_PATH" >&2
  echo "Usage: $0 [path-to-data-api-backend] [path-to-destination-backend]" >&2
  exit 1
fi

mkdir -p "$DEST_PATH"

rsync -a \
  --exclude '.DS_Store' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '.ruff_cache/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude 'coverage_html_report/' \
  --exclude 'htmlcov/' \
  --exclude '.coverage' \
  --exclude '*.pyc' \
  --exclude 'logs/' \
  --exclude 'test_logs/' \
  --exclude 'tmp/' \
  --exclude 'gazetteer_import.log' \
  --exclude 'data_api.egg-info/' \
  "$SOURCE_PATH"/ "$DEST_PATH"/

echo "Synced backend from $SOURCE_PATH to $DEST_PATH"
