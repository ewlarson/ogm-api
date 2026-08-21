#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

matches="$({
  rg --hidden -n -i \
    -g '!LICENSE' \
    -g '!.git/**' \
    -g '!scripts/verify_identity_cleanup.sh' \
    -g '!backend/data/fixtures/gbl_fixtures_data/**' \
    -g '!backend/data/fixtures/ogm_featured_resources/**' \
    -g '!backend/data/fixtures/ogm_fixtures_data/**' \
    -g '!backend/data/ogm_api_legacy_dump.txt' \
    -g '!legacy/root_api/ogm/**' \
    -g '!legacy/root_api/*.txt' \
    '(btaa|big ten|geobtaa)' . || true
})"

# These values identify external resources or persistent production data. They
# are compatibility/provenance literals, not OGM product branding.
unexpected="$({
  printf '%s\n' "$matches" | rg -v \
    '(github\.com/(repos/)?geobtaa|raw\.githubusercontent\.com/geobtaa|geobtaa/api|geobtaa-api|geobtaa-assets-prod|btaa_ogm_api|gin\.btaa\.org|BTAA-GIN Staff|btaa-api-key-hash-v2|gazetteer_btaa|btaa_(primary|secondary|member_primary|member_affiliated))' || true
})"

if [[ -n "$unexpected" ]]; then
  printf '%s\n' 'Unexpected legacy identity references:'
  printf '%s\n' "$unexpected"
  exit 1
fi

printf '%s\n' 'Identity check passed: remaining legacy strings are approved compatibility or provenance literals.'
