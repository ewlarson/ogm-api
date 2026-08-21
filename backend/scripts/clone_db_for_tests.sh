#!/bin/bash
# Clone opengeometadata_api database to opengeometadata_api_test for testing

set -e

echo "Cloning opengeometadata_api to opengeometadata_api_test..."

# Drop test DB if it exists
docker compose exec -T paradedb bash -lc 'PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -c "DROP DATABASE IF EXISTS opengeometadata_api_test;"'

# Create test DB as a clone
docker compose exec -T paradedb bash -lc 'PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -c "CREATE DATABASE opengeometadata_api_test WITH TEMPLATE opengeometadata_api OWNER postgres;"'

echo "✓ Database cloned successfully!"
echo ""
echo "To verify:"
echo "  docker compose exec -T paradedb psql -U postgres -d opengeometadata_api_test -c 'SELECT COUNT(*) FROM resources;'"

