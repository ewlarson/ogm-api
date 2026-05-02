from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_endpoint_structure():
    """Test the search endpoint JSON:API structure."""
    # Call endpoint with basic query
    response = client.get("/api/v1/search?q=test&page=1&per_page=5")

    # Verify the response
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

    # Test meta structure
    assert "meta" in data
    assert "totalCount" in data["meta"]
    assert "currentPage" in data["meta"]
    assert "perPage" in data["meta"]
    assert "query" in data["meta"]
    assert data["meta"]["query"] == "test"

    # Test data structure
    assert "data" in data
    assert isinstance(data["data"], list)

    # Test that each resource has the correct structure (if any results)
    for resource in data["data"]:
        assert "type" in resource
        assert resource["type"] == "resource"
        assert "id" in resource
        assert "attributes" in resource
        assert "meta" in resource


def test_search_with_sort():
    """Test the search endpoint with sorting."""
    # Call endpoint with sort parameter
    response = client.get("/api/v1/search?q=test&sort=year_desc&per_page=3")

    # Verify the response
    assert response.status_code == 200
    data = response.json()

    # Test JSON:API structure
    assert "jsonapi" in data
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["sort"] == "year_desc"


def test_search_with_filters():
    """Test the search endpoint with filters."""
    # Call endpoint with filter parameters
    response = client.get("/api/v1/search?q=test&fq[dct_spatial_sm][]=Minnesota&per_page=3")

    # Verify the response
    assert response.status_code == 200
    data = response.json()

    # Test JSON:API structure
    assert "jsonapi" in data
    assert "data" in data
    assert "meta" in data


def test_suggest_endpoint():
    """Test the suggest endpoint structure."""
    # Call endpoint
    response = client.get("/api/v1/suggest?q=min")

    # Verify the response
    assert response.status_code == 200
    data = response.json()

    # Test JSON:API structure
    assert "data" in data
    assert isinstance(data["data"], list)

    # Test that each suggestion has the correct structure (if any results)
    for suggestion in data["data"]:
        assert "type" in suggestion
        assert suggestion["type"] == "suggestion"
        assert "id" in suggestion
        assert "attributes" in suggestion
        assert "text" in suggestion["attributes"]


def test_suggest_with_resource_class():
    """Test the suggest endpoint with resource class filter."""
    # Call endpoint with resource class
    response = client.get("/api/v1/suggest?q=min&resource_class=Maps")

    # Verify the response
    assert response.status_code == 200
    data = response.json()

    # Test JSON:API structure
    assert "data" in data
    assert isinstance(data["data"], list)
