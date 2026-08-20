#!/usr/bin/env bash

set -euo pipefail

version="${1:-}"
if [ -z "$version" ]; then
    echo "Usage: OGM_IMAGE_REPOSITORIES='ghcr.io/owner/image [ghcr.io/owner/image]' $0 VERSION" >&2
    exit 1
fi

read -r -a image_repositories <<< "${OGM_IMAGE_REPOSITORIES:-ghcr.io/ewlarson/opengeometadata-api}"
if [ "${#image_repositories[@]}" -eq 0 ]; then
    echo "OGM_IMAGE_REPOSITORIES must contain at least one image repository." >&2
    exit 1
fi

build_tags=()
for image_repository in "${image_repositories[@]}"; do
    build_tags+=(--tag "$image_repository:$version" --tag "$image_repository:latest")
done

docker build "${build_tags[@]}" .

for image_repository in "${image_repositories[@]}"; do
    docker push "$image_repository:$version"
    docker push "$image_repository:latest"
    echo "Published $image_repository:$version and $image_repository:latest"
done
