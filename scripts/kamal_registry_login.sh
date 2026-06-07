#!/usr/bin/env bash
set -euo pipefail

registry="${KAMAL_REGISTRY_SERVER:-ghcr.io}"
username="${KAMAL_REGISTRY_USERNAME:-ewlarson}"
secret_file="${KAMAL_REGISTRY_PASSWORD_FILE:-.kamal/registry-password}"

docker_bin="${DOCKER_BIN:-docker}"
if ! command -v "$docker_bin" >/dev/null 2>&1; then
  if [ -x /Applications/Docker.app/Contents/Resources/bin/docker ]; then
    docker_bin=/Applications/Docker.app/Contents/Resources/bin/docker
  else
    echo "Docker CLI not found. Start Docker Desktop or set DOCKER_BIN." >&2
    exit 1
  fi
fi

read_saved_token() {
  if [ -f "$secret_file" ]; then
    tr -d '\n' < "$secret_file"
  fi
}

prompt_for_token() {
  if [ ! -t 0 ]; then
    echo "KAMAL_REGISTRY_PASSWORD is missing or invalid, and stdin is not interactive." >&2
    exit 1
  fi

  printf "GitHub PAT classic for %s (needs write:packages): " "$registry" >&2
  IFS= read -r -s token
  printf "\n" >&2
  printf "%s" "$token"
}

store_token() {
  mkdir -p "$(dirname "$secret_file")"
  install -m 600 /dev/null "$secret_file"
  printf "%s" "$1" > "$secret_file"
  chmod 600 "$secret_file"
}

docker_login() {
  printf "%s" "$1" | "$docker_bin" login "$registry" -u "$username" --password-stdin
}

token="${KAMAL_REGISTRY_PASSWORD:-$(read_saved_token)}"
if [ -z "$token" ]; then
  token="$(prompt_for_token)"
fi

if docker_login "$token"; then
  store_token "$token"
  echo "Stored registry token in $secret_file and verified Docker login to $registry."
  exit 0
fi

echo "Existing registry token was rejected by $registry." >&2
token="$(prompt_for_token)"
docker_login "$token"
store_token "$token"
echo "Stored replacement registry token in $secret_file and verified Docker login to $registry."
