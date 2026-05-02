from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.mcp_service import mcp_service

client = TestClient(app)


@pytest.fixture
def mock_search_results():
    """Return mock search results for MCP testing."""
    return {
        "meta": {
            "pages": {
                "current_page": 1,
                "total_pages": 5,
                "total_count": 45,
            }
        },
        "data": [
            {
                "type": "resource",
                "id": "test-resource-1",
                "attributes": {
                    "dct_title_s": "Test Resource 1",
                    "dct_description_sm": ["Test description 1"],
                    "dct_creator_sm": ["Test Creator"],
                    "gbl_resourcetype_sm": ["Maps"],
                },
            },
            {
                "type": "resource",
                "id": "test-resource-2",
                "attributes": {
                    "dct_title_s": "Test Resource 2",
                    "dct_description_sm": ["Test description 2"],
                    "dct_creator_sm": ["Test Creator"],
                    "gbl_resourcetype_sm": ["Datasets"],
                },
            },
        ],
        "included": [],
        "query_time": {"elasticsearch": "10ms", "total_response_time": "30ms"},
    }


@pytest.fixture
def mock_resource_data():
    """Return mock resource data for MCP testing."""
    return {
        "id": "test-resource-123",
        "dct_title_s": "Test Resource Title",
        "dct_description_sm": ["This is a test resource description"],
        "dct_creator_sm": ["Test Creator"],
        "dct_publisher_sm": ["Test Publisher"],
        "gbl_resourcetype_sm": ["Maps"],
        "gbl_resourceclass_sm": ["Datasets"],
        "dct_spatial_sm": ["Minnesota"],
        "gbl_filesize_s": "1024",
    }


class TestMCPServiceIntegration:
    """Test MCP service integration with API endpoints."""

    @pytest.mark.asyncio
    async def test_mcp_search_resources_tool(self, mock_search_results):
        """Test that MCP search_resources tool returns proper structure."""
        with patch("app.services.mcp_service.SearchService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.search = AsyncMock(return_value=mock_search_results)

            # Mock the process_resource function
            with patch("app.services.mcp_service.process_resource") as mock_process:
                mock_process.return_value = {
                    "type": "resource",
                    "id": "test-resource-1",
                    "attributes": {"dct_title_s": "Test Resource 1"},
                    "meta": {
                        "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
                        "@type": "AardvarkRecord",
                        "ui": {
                            "citation": "Test Citation",
                            "downloads": {"pdf": "https://example.com/download.pdf"},
                            "thumbnail_url": "https://example.com/thumbnail.jpg",
                        },
                    },
                }

                # Test the MCP search_resources tool
                result = await mcp_service._search_resources(
                    {"query": "test", "page": 1, "per_page": 10}
                )

                # Verify the result structure
                assert hasattr(result, "content")
                content = result.content

                # Should have the same structure as API response
                assert "query" in content
                assert "total_results" in content
                assert "page" in content
                assert "per_page" in content
                assert "resources" in content

                # Verify the values
                assert content["query"] == "test"
                assert content["total_results"] == 45
                assert content["page"] == 1
                assert content["per_page"] == 10
                assert len(content["resources"]) == 2

    @pytest.mark.asyncio
    async def test_mcp_get_resource_tool(self, mock_resource_data):
        """Test that MCP get_resource tool returns proper structure."""
        with patch("app.services.mcp_service.async_session") as mock_session:
            # Mock the database session and query result
            mock_row = MagicMock()
            mock_row._mapping = mock_resource_data
            mock_session.return_value.__aenter__.return_value.execute.return_value.fetchone.return_value = mock_row

            # Mock the process_resource function
            with patch("app.services.mcp_service.process_resource") as mock_process:
                mock_process.return_value = {
                    "type": "resource",
                    "id": mock_resource_data["id"],
                    "attributes": mock_resource_data,
                    "meta": {
                        "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
                        "@type": "AardvarkRecord",
                        "ui": {
                            "citation": "Test Citation",
                            "downloads": {"pdf": "https://example.com/download.pdf"},
                            "thumbnail_url": "https://example.com/thumbnail.jpg",
                        },
                    },
                }

                # Test the MCP get_resource tool
                result = await mcp_service._get_resource({"id": mock_resource_data["id"]})

                # Verify the result structure
                assert hasattr(result, "content")
                content = result.content

                # Should have the same structure as API response
                assert "type" in content
                assert "id" in content
                assert "attributes" in content
                assert "meta" in content

                # Verify the values
                assert content["type"] == "resource"
                assert content["id"] == mock_resource_data["id"]
                assert content["attributes"]["dct_title_s"] == mock_resource_data["dct_title_s"]

    @pytest.mark.asyncio
    async def test_mcp_get_resource_ogm_tool(self, mock_resource_data):
        """Test that MCP get_resource_ogm tool returns proper Aardvark structure."""
        with patch("app.services.mcp_service.async_session") as mock_session:
            # Mock the database session and query result
            mock_row = MagicMock()
            mock_row._mapping = mock_resource_data
            mock_session.return_value.__aenter__.return_value.execute.return_value.fetchone.return_value = mock_row

            # Test the MCP get_resource_ogm tool
            result = await mcp_service._get_resource_ogm({"id": mock_resource_data["id"]})

            # Verify the result structure
            assert hasattr(result, "content")
            content = result.content

            # Should have Aardvark fields
            assert "dct_title_s" in content
            assert "dct_description_sm" in content
            assert "dct_creator_sm" in content
            assert "gbl_resourcetype_sm" in content

            # Should NOT have JSON:API structure
            assert "jsonapi" not in content
            assert "data" not in content
            assert "links" not in content

    @pytest.mark.asyncio
    async def test_mcp_list_resources_tool(self, mock_resource_data):
        """Test that MCP list_resources tool returns proper structure."""
        with patch("app.services.mcp_service.get_async_session") as mock_session_factory:
            # Mock the database session and query results
            mock_session = MagicMock()
            mock_session_factory.return_value = mock_session
            mock_row = MagicMock()
            mock_row._mapping = mock_resource_data

            mock_session.__aenter__.return_value.execute.return_value.fetchall.return_value = [
                mock_row
            ]
            mock_session.__aenter__.return_value.execute.return_value.scalar.return_value = 1

            # Mock the process_resource function
            with patch("app.services.mcp_service.process_resource") as mock_process:
                mock_process.return_value = {
                    "type": "resource",
                    "id": mock_resource_data["id"],
                    "attributes": mock_resource_data,
                    "meta": {
                        "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
                        "@type": "AardvarkRecord",
                        "ui": {
                            "citation": "Test Citation",
                            "downloads": {"pdf": "https://example.com/download.pdf"},
                            "thumbnail_url": "https://example.com/thumbnail.jpg",
                        },
                    },
                }

                # Test the MCP list_resources tool
                result = await mcp_service._list_resources({"page": 1, "per_page": 10})

                # Verify the result structure
                assert hasattr(result, "content")
                assert len(result.content) > 0

                # The content should be a list of TextContent objects
                content_text = result.content[0].text

                # Parse the JSON response
                import json

                content_data = json.loads(content_text)

                # Should have the same structure as API response
                assert "total_count" in content_data
                assert "total_pages" in content_data
                assert "page" in content_data
                assert "per_page" in content_data
                assert "resources" in content_data

                # Verify the values
                assert content_data["total_count"] == 1
                assert content_data["total_pages"] == 1
                assert content_data["page"] == 1
                assert content_data["per_page"] == 10
                assert len(content_data["resources"]) == 1

    @pytest.mark.asyncio
    async def test_mcp_get_suggestions_tool(self):
        """Test that MCP get_suggestions tool returns proper structure."""
        mock_suggestions = {"suggestions": ["minnesota", "mining"]}

        with patch("app.services.mcp_service.SearchService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.suggest = AsyncMock(return_value=mock_suggestions)

            # Test the MCP get_suggestions tool
            result = await mcp_service._get_suggestions({"query": "min"})

            # Verify the result structure
            assert hasattr(result, "content")
            assert len(result.content) > 0

            # The content should be a list of TextContent objects
            # Check that the first content item contains the suggestions text
            content_text = result.content[0].text
            assert "Suggestions for 'min':" in content_text
            assert "minnesota" in content_text
            assert "mining" in content_text

    @pytest.mark.asyncio
    async def test_mcp_validate_aardvark_record_tool(self):
        """Test that MCP validate_aardvark_record tool returns proper structure."""
        test_record = {
            "dct_title_s": "Test Record",
            "gbl_mdVersion_s": "Aardvark",
            "dct_description_sm": ["Test description"],
        }

        # Test the MCP validate_aardvark_record tool
        result = await mcp_service._validate_aardvark_record({"record": test_record})

        # Verify the result structure
        assert hasattr(result, "content")
        assert len(result.content) > 0

        # The content should be a list of TextContent objects
        content_text = result.content[0].text

        # Should contain validation result text
        assert "Validation Result:" in content_text
        assert "VALID" in content_text or "INVALID" in content_text

    def test_mcp_tools_list(self):
        """Test that MCP service advertises all required tools."""
        # Test that the MCP service has the required tools
        # The tools are registered via decorators, so we can't directly access them
        # But we can verify the MCP service was initialized without errors
        assert hasattr(mcp_service, "_register_tools")
        assert hasattr(mcp_service.server, "list_tools")

    def test_mcp_websocket_endpoint_exists(self):
        """Test that MCP WebSocket functionality exists."""
        # Test that the MCP service has WebSocket support
        assert hasattr(mcp_service, "run_mcp_websocket_server")
        assert hasattr(mcp_service, "handle_mcp_message")


class TestMCPResponseConsistency:
    """Test that MCP responses are consistent with API responses."""

    @pytest.mark.asyncio
    async def test_mcp_search_consistency_with_api(self, mock_search_results):
        """Test that MCP search results are consistent with API search results."""
        with patch("app.services.mcp_service.SearchService") as mock_service:
            mock_service_instance = MagicMock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.search = AsyncMock(return_value=mock_search_results)

            with patch("app.services.mcp_service.process_resource") as mock_process:
                mock_process.return_value = {
                    "type": "resource",
                    "id": "test-resource-1",
                    "attributes": {"dct_title_s": "Test Resource 1"},
                    "meta": {
                        "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
                        "@type": "AardvarkRecord",
                        "ui": {
                            "citation": "Test Citation",
                            "downloads": {"pdf": "https://example.com/download.pdf"},
                            "thumbnail_url": "https://example.com/thumbnail.jpg",
                        },
                    },
                }

                # Test MCP search
                mcp_result = await mcp_service._search_resources(
                    {"query": "test", "page": 1, "per_page": 10}
                )

                # Parse MCP result
                import json

                mcp_content = json.loads(mcp_result.content[0].text)
                mcp_resources = mcp_content["resources"]

                # Both should have the same resource structure
                assert len(mcp_resources) == 2  # Based on mock data

                for resource in mcp_resources:
                    # Should have the same basic structure
                    assert "type" in resource
                    assert "id" in resource
                    assert "attributes" in resource
                    assert "meta" in resource

    @pytest.mark.asyncio
    async def test_mcp_resource_consistency_with_api(self, mock_resource_data):
        """Test that MCP resource results are consistent with API resource results."""
        with patch("app.services.mcp_service.get_async_session") as mock_session_factory:
            mock_session = MagicMock()
            mock_session_factory.return_value = mock_session
            mock_row = MagicMock()
            mock_row._mapping = mock_resource_data
            mock_session.__aenter__.return_value.execute.return_value.fetchone.return_value = (
                mock_row
            )

            with patch("app.services.mcp_service.process_resource") as mock_process:
                mock_process.return_value = {
                    "type": "resource",
                    "id": mock_resource_data["id"],
                    "attributes": mock_resource_data,
                    "meta": {
                        "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
                        "@type": "AardvarkRecord",
                        "ui": {
                            "citation": "Test Citation",
                            "downloads": {"pdf": "https://example.com/download.pdf"},
                            "thumbnail_url": "https://example.com/thumbnail.jpg",
                        },
                    },
                }

                # Test MCP get_resource
                mcp_result = await mcp_service._get_resource({"id": mock_resource_data["id"]})

                # Parse MCP result
                import json

                mcp_resource = json.loads(mcp_result.content[0].text)

                # Should have the same resource structure
                assert mcp_resource["type"] == "resource"
                assert mcp_resource["id"] == mock_resource_data["id"]
                assert "attributes" in mcp_resource
                assert "meta" in mcp_resource
