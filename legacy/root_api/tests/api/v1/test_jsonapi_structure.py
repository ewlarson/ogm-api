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
def client(override_get_async_session):
    """Create a test client with isolated database session."""
    return TestClient(app)


class TestJSONAPIStructure:
    """Test JSON:API structure compliance for various endpoints."""

    def test_resources_endpoint_jsonapi_structure(self, client):
        """Test that /resources/{id} endpoint returns proper JSON:API structure."""
        # Use a real item ID that should exist in the test data
        item_id = "stanford-cg357zz0321"  # From the test data

        response = client.get(f"/api/v1/resources/{item_id}")

        assert response.status_code == 200
        data = response.json()

        # Test JSON:API structure
        assert "jsonapi" in data
        assert data["jsonapi"]["version"] == "1.1"
        assert "profile" in data["jsonapi"]
        assert "https://opengeometadata.org/profile/aardvark" in data["jsonapi"]["profile"]
        assert "https://opengeometadata.org/profile/ui-hints" in data["jsonapi"]["profile"]
        assert "https://opengeometadata.org/profile/mcp/search" in data["jsonapi"]["profile"]

        # Test links structure
        assert "links" in data
        assert "self" in data["links"]
        assert f"/api/v1/resources/{item_id}" in data["links"]["self"]

        # Test data structure
        assert "data" in data
        assert data["data"]["type"] == "resource"
        assert data["data"]["id"] == item_id
        assert "attributes" in data["data"]
        # Meta should be inside the data object
        assert "meta" in data["data"]

    def test_resources_list_endpoint_jsonapi_structure(self, client):
        """Test that /resources/ endpoint returns proper JSON:API structure with pagination."""
        response = client.get("/api/v1/resources/?per_page=10")

        assert response.status_code == 200
        data = response.json()

        # Test JSON:API structure
        assert "jsonapi" in data
        assert data["jsonapi"]["version"] == "1.1"
        assert "profile" in data["jsonapi"]

        # Test links structure with pagination
        assert "links" in data
        assert "self" in data["links"]
        assert "first" in data["links"]
        assert "last" in data["links"]

        # Test meta structure with pagination
        assert "meta" in data
        assert "totalCount" in data["meta"]
        assert "totalPages" in data["meta"]
        assert "currentPage" in data["meta"]
        assert "perPage" in data["meta"]

        # Test data structure
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0  # Should have items from test data
        assert data["data"][0]["type"] == "resource"

    def test_resources_ogm_endpoint_structure(self, client):
        """Test that /resources/{id}/ogm endpoint returns Aardvark structure (not JSON:API)."""
        # Use a real item ID that should exist in the test data
        item_id = "stanford-cg357zz0321"  # From the test data

        response = client.get(f"/api/v1/resources/{item_id}/ogm")

        assert response.status_code == 200
        data = response.json()

        # Test that it returns Aardvark fields (not JSON:API structure)
        assert "dct_title_s" in data
        assert "dct_description_sm" in data
        assert "dct_creator_sm" in data
        assert "gbl_mdVersion_s" in data or "gbl_mdversion_s" in data

        # Should NOT have JSON:API structure
        assert "jsonapi" not in data
        assert "data" not in data
        assert "links" not in data


class TestJSONAPICompliance:
    """Test JSON:API compliance for resource objects."""

    def test_resource_object_structure(self, client):
        """Test that resource objects have proper JSON:API structure."""
        # Use a real item ID that should exist in the test data
        item_id = "stanford-cg357zz0321"  # From the test data

        response = client.get(f"/api/v1/resources/{item_id}")

        assert response.status_code == 200
        data = response.json()

        # Test that data exists and has proper structure
        assert "data" in data
        resource = data["data"]

        # Test required JSON:API fields
        assert "type" in resource
        assert "id" in resource
        assert resource["type"] == "resource"
        assert resource["id"] == item_id

        # Test attributes
        assert "attributes" in resource
        attributes = resource["attributes"]
        assert isinstance(attributes, dict)

        # Test meta inside the data object
        assert "meta" in resource
        meta = resource["meta"]
        assert isinstance(meta, dict)


class TestRefactoringRegression:
    """Test that refactoring didn't break existing functionality."""

    def test_endpoint_urls_still_work(self, client):
        """Test that all endpoint URLs still work after refactoring."""
        # Test resources list endpoint
        response = client.get("/api/v1/resources/")
        assert response.status_code == 200

        # Test resources detail endpoint with real data
        item_id = "stanford-cg357zz0321"  # From the test data
        response = client.get(f"/api/v1/resources/{item_id}")
        assert response.status_code == 200

        # Test OGM endpoint
        response = client.get(f"/api/v1/resources/{item_id}/ogm")
        assert response.status_code == 200

    def test_response_structure_consistency(self, client):
        """Test that response structures are consistent across endpoints."""
        # Use a real item ID that should exist in the test data
        item_id = "stanford-cg357zz0321"  # From the test data

        # Test JSON:API endpoint
        response = client.get(f"/api/v1/resources/{item_id}")
        assert response.status_code == 200
        jsonapi_data = response.json()

        # Test OGM endpoint
        response = client.get(f"/api/v1/resources/{item_id}/ogm")
        assert response.status_code == 200
        ogm_data = response.json()

        # Both should have the same basic resource data
        jsonapi_attributes = jsonapi_data["data"]["attributes"]
        assert jsonapi_attributes["dct_title_s"] == ogm_data["dct_title_s"]
        assert jsonapi_attributes["id"] == ogm_data["id"]
