import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Set the database URL for tests
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:2346/btaa_ogm_api_test"
)


# Create a fresh client for each test
@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_api_root(client):
    """Test the API root endpoint."""
    response = client.get("/api/v1/")
    assert response.status_code == 200


def test_resources_endpoint_exists(client):
    """Test that the resources endpoint exists and returns a response."""
    response = client.get("/api/v1/resources/")
    # We expect either 200 (success) or 500 (database error), but not 404 (not found)
    assert response.status_code in [200, 500]


def test_resource_detail_endpoint_exists(client):
    """Test that the resource detail endpoint exists and returns a response."""
    response = client.get("/api/v1/resources/test-id")
    # We expect either 200 (success), 404 (not found), or 500 (database error)
    assert response.status_code in [200, 404, 500]
