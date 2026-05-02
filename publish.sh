#!/bin/bash
set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    echo "Please provide a version number (e.g. ./publish.sh 0.6.0)"
    exit 1
fi

docker build -t ewlarson/opengeometadata-api:latest -t ewlarson/opengeometadata-api:"$VERSION" .
docker push ewlarson/opengeometadata-api:latest
docker push ewlarson/opengeometadata-api:"$VERSION"

echo "Published ewlarson/opengeometadata-api:latest and ewlarson/opengeometadata-api:$VERSION"
