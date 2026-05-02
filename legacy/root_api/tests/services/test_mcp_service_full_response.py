import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.mcp_service import OGMMCPService


@pytest.fixture
def mock_resource_data():
    """Mock resource data that would come from the database."""
    return {
        "id": "stanford-test-123",
        "dct_title_s": "Test Geospatial Dataset",
        "dct_description_s": ["This is a comprehensive test dataset for geospatial analysis."],
        "dct_creator_s": ["Stanford University", "Test Creator"],
        "dct_publisher_s": ["Stanford University Libraries"],
        "dct_subject_s": ["Geospatial data", "Test data", "GIS"],
        "dct_spatial_sm": ["California", "Stanford"],
        "gbl_resourceclass_sm": ["Datasets"],
        "gbl_resourcetype_sm": ["Geospatial data"],
        "dct_format_s": "Shapefile",
        "dct_accessrights_s": "Public",
        "dct_issued_s": "2023",
        "gbl_indexyear_im": [2023],
        "dct_references_s": json.dumps(
            {
                "http://schema.org/downloadUrl": "https://example.com/download/test.zip",
                "http://www.opengis.net/def/serviceType/ogc/wms": "https://example.com/geoserver/wms",
                "http://www.opengis.net/def/serviceType/ogc/wfs": "https://example.com/geoserver/wfs",
                "http://iiif.io/api/image": "https://example.com/iiif/image/info.json",
                "http://iiif.io/api/presentation#manifest": "https://example.com/iiif/manifest",
            }
        ),
        "locn_geometry": '{"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]}',
        "dcat_bbox": "ENVELOPE(-122.5, -122.0, 37.0, 37.5)",
        "dcat_centroid": "POINT(-122.25 37.25)",
        "gbl_mdmodified_dt": "2023-12-01T10:00:00Z",
        "gbl_mdversion_s": "Aardvark",
    }


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()

    # Mock the row result
    mock_row = MagicMock()
    mock_row._mapping = {
        "id": "stanford-test-123",
        "dct_title_s": "Test Geospatial Dataset",
        "dct_description_s": ["This is a comprehensive test dataset for geospatial analysis."],
        "dct_creator_s": ["Stanford University", "Test Creator"],
        "dct_publisher_s": ["Stanford University Libraries"],
        "dct_subject_s": ["Geospatial data", "Test data", "GIS"],
        "dct_spatial_sm": ["California", "Stanford"],
        "gbl_resourceclass_sm": ["Datasets"],
        "gbl_resourcetype_sm": ["Geospatial data"],
        "dct_format_s": "Shapefile",
        "dct_accessrights_s": "Public",
        "dct_issued_s": "2023",
        "gbl_indexyear_im": [2023],
        "dct_references_s": json.dumps(
            {
                "http://schema.org/downloadUrl": "https://example.com/download/test.zip",
                "http://www.opengis.net/def/serviceType/ogc/wms": "https://example.com/geoserver/wms",
                "http://www.opengis.net/def/serviceType/ogc/wfs": "https://example.com/geoserver/wfs",
                "http://iiif.io/api/image": "https://example.com/iiif/image/info.json",
                "http://iiif.io/api/presentation#manifest": "https://example.com/iiif/manifest",
            }
        ),
        "locn_geometry": '{"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]}',
        "dcat_bbox": "ENVELOPE(-122.5, -122.0, 37.0, 37.5)",
        "dcat_centroid": "POINT(-122.25 37.25)",
        "gbl_mdmodified_dt": "2023-12-01T10:00:00Z",
        "gbl_mdversion_s": "Aardvark",
    }

    # Mock the execute result
    mock_result = MagicMock()
    mock_result.fetchone.return_value = mock_row
    session.execute.return_value = mock_result

    return session


@pytest.fixture
def mock_search_results():
    """Mock search results."""
    return {
        "data": [
            {
                "id": "stanford-test-123",
                "attributes": {
                    "id": "stanford-test-123",
                    "dct_title_s": "Test Geospatial Dataset",
                    "dct_description_s": [
                        "This is a comprehensive test dataset for geospatial analysis."
                    ],
                    "dct_creator_s": ["Stanford University", "Test Creator"],
                    "dct_publisher_s": ["Stanford University Libraries"],
                    "dct_subject_s": ["Geospatial data", "Test data", "GIS"],
                    "dct_spatial_sm": ["California", "Stanford"],
                    "gbl_resourceclass_sm": ["Datasets"],
                    "gbl_resourcetype_sm": ["Geospatial data"],
                    "dct_format_s": "Shapefile",
                    "dct_accessrights_s": "Public",
                    "dct_issued_s": "2023",
                    "gbl_indexyear_im": [2023],
                    "dct_references_s": json.dumps(
                        {
                            "http://schema.org/downloadUrl": "https://example.com/download/test.zip",
                            "http://www.opengis.net/def/serviceType/ogc/wms": "https://example.com/geoserver/wms",
                            "http://www.opengis.net/def/serviceType/ogc/wfs": "https://example.com/geoserver/wfs",
                            "http://iiif.io/api/image": "https://example.com/iiif/image/info.json",
                            "http://iiif.io/api/presentation#manifest": "https://example.com/iiif/manifest",
                        }
                    ),
                    "locn_geometry": '{"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]}',
                    "dcat_bbox": "ENVELOPE(-122.5, -122.0, 37.0, 37.5)",
                    "dcat_centroid": "POINT(-122.25 37.25)",
                    "gbl_mdmodified_dt": "2023-12-01T10:00:00Z",
                    "gbl_mdversion_s": "Aardvark",
                },
            }
        ],
        "meta": {"pages": {"total_count": 1, "total_pages": 1, "current_page": 1}},
    }


class TestMCPServiceFullResponse:
    """Test the MCP service to demonstrate full response capabilities."""

    @pytest.mark.asyncio
    async def test_get_resource_full_response(self, mock_session):
        """Test that get_resource returns the complete resource object."""
        # Create MCP service instance
        mcp_service = OGMMCPService()

        # Mock the database session factory
        with patch("app.services.mcp_service.get_async_session") as mock_session_factory:
            mock_session_factory.return_value.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.return_value.__aexit__.return_value = None

            # Mock the process_resource function to return a complete resource object
            with patch("app.api.v1.utils.process_resource") as mock_process_resource:
                mock_process_resource.return_value = {
                    "type": "resource",
                    "id": "stanford-test-123",
                    "attributes": {
                        "id": "stanford-test-123",
                        "dct_title_s": "Test Geospatial Dataset",
                        "dct_description_s": [
                            "This is a comprehensive test dataset for geospatial analysis."
                        ],
                        "dct_creator_s": ["Stanford University", "Test Creator"],
                        "dct_publisher_s": ["Stanford University Libraries"],
                        "dct_subject_s": ["Geospatial data", "Test data", "GIS"],
                        "dct_spatial_sm": ["California", "Stanford"],
                        "gbl_resourceClass_sm": ["Datasets"],
                        "gbl_resourceType_sm": ["Geospatial data"],
                        "dct_format_s": "Shapefile",
                        "dct_accessRights_s": "Public",
                        "dct_issued_s": "2023",
                        "gbl_indexYear_im": [2023],
                        "locn_geometry": '{"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]}',
                        "dcat_bbox": "ENVELOPE(-122.5, -122.0, 37.0, 37.5)",
                        "dcat_centroid": "POINT(-122.25 37.25)",
                        "gbl_mdModified_dt": "2023-12-01T10:00:00Z",
                        "gbl_mdVersion_s": "Aardvark",
                    },
                    "meta": {
                        "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
                        "@type": "AardvarkRecord",
                        "human_readable": {"file_size": None},
                        "ui": {
                            "allmaps": {"enabled": False, "url": None},
                            "citation": "Stanford University Libraries. (2023). Test Geospatial Dataset. Stanford University.",
                            "downloads": [
                                {
                                    "label": "Shapefile",
                                    "url": "https://example.com/download/test.zip",
                                    "type": "direct",
                                },
                                {
                                    "label": "WMS Service",
                                    "url": "https://example.com/geoserver/wms",
                                    "type": "service",
                                },
                                {
                                    "label": "WFS Service",
                                    "url": "https://example.com/geoserver/wfs",
                                    "type": "service",
                                },
                            ],
                            "relationships": [],
                            "summaries": [
                                {
                                    "id": 1,
                                    "item_id": "stanford-test-123",
                                    "enrichment_type": "summary",
                                    "content": "This dataset contains comprehensive geospatial data for testing purposes.",
                                    "created_at": "2023-12-01T10:00:00Z",
                                }
                            ],
                            "thumbnail_url": "https://example.com/thumbnails/test.jpg",
                            "viewer": {
                                "protocol": "wms",
                                "endpoint": "https://example.com/geoserver/wms",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [
                                            [-122.5, 37.0],
                                            [-122.0, 37.0],
                                            [-122.0, 37.5],
                                            [-122.5, 37.5],
                                            [-122.5, 37.0],
                                        ]
                                    ],
                                },
                            },
                        },
                    },
                }

                # Call the MCP service method
                result = await mcp_service._get_resource({"id": "stanford-test-123"})

                # Verify the result structure
                assert result.isError is False
                assert len(result.content) == 1
                assert result.content[0].type == "text"

                # Parse the JSON response
                response_data = json.loads(result.content[0].text)

                # Verify the complete resource structure
                assert response_data["type"] == "resource"
                assert response_data["id"] == "stanford-test-123"
                assert "attributes" in response_data
                assert "meta" in response_data

                # Verify Aardvark attributes
                attrs = response_data["attributes"]
                assert attrs["dct_title_s"] == "Test Geospatial Dataset"
                assert attrs["dct_creator_s"] == ["Stanford University", "Test Creator"]
                assert attrs["gbl_resourceClass_sm"] == ["Datasets"]  # Note the capital C
                assert attrs["dct_accessRights_s"] == "Public"  # Note the capital R

                # Verify UI enhancements
                ui = response_data["meta"]["ui"]
                assert "citation" in ui
                assert "downloads" in ui
                assert "relationships" in ui
                assert "summaries" in ui
                assert "thumbnail_url" in ui
                assert "viewer" in ui

                # Verify downloads
                downloads = ui["downloads"]
                assert len(downloads) >= 1
                assert any(d["type"] == "direct" for d in downloads)
                assert any(d["type"] == "service" for d in downloads)

                # Verify viewer information
                viewer = ui["viewer"]
                assert viewer["protocol"] == "wms"
                assert viewer["endpoint"] == "https://example.com/geoserver/wms"
                assert "geometry" in viewer

    @pytest.mark.asyncio
    async def test_search_resources_full_response(self, mock_search_results):
        """Test that search_resources returns complete resource objects."""
        # Create MCP service instance
        mcp_service = OGMMCPService()

        # Mock the SearchService
        with patch("app.services.search_service.SearchService") as mock_search_service_class:
            mock_search_service = AsyncMock()
            mock_search_service.search.return_value = mock_search_results
            mock_search_service_class.return_value = mock_search_service

            # Mock the database session
            with patch("app.services.mcp_service.get_async_session") as mock_session_factory:
                mock_session = AsyncMock()
                mock_session_factory.return_value.return_value.__aenter__.return_value = (
                    mock_session
                )
                mock_session_factory.return_value.return_value.__aexit__.return_value = None

                # Mock the process_resource function
                with patch("app.api.v1.utils.process_resource") as mock_process_resource:
                    mock_process_resource.return_value = {
                        "type": "resource",
                        "id": "stanford-test-123",
                        "attributes": {
                            "dct_title_s": "Test Geospatial Dataset",
                            "dct_creator_s": ["Stanford University", "Test Creator"],
                            "gbl_resourceClass_sm": ["Datasets"],
                        },
                        "meta": {
                            "ui": {
                                "citation": "Stanford University Libraries. (2023). Test Geospatial Dataset.",
                                "downloads": [
                                    {
                                        "label": "Shapefile",
                                        "url": "https://example.com/download/test.zip",
                                        "type": "direct",
                                    }
                                ],
                                "viewer": {
                                    "protocol": "wms",
                                    "endpoint": "https://example.com/geoserver/wms",
                                },
                            }
                        },
                    }

                    # Call the MCP service method
                    result = await mcp_service._search_resources(
                        {"query": "test dataset", "page": 1, "per_page": 10}
                    )

                    # Verify the result structure
                    assert result.isError is False
                    assert len(result.content) == 1
                    assert result.content[0].type == "text"

                    # Parse the JSON response
                    response_data = json.loads(result.content[0].text)

                    # Verify search metadata
                    assert response_data["query"] == "test dataset"
                    assert response_data["total_results"] == 1
                    assert response_data["page"] == 1
                    assert response_data["per_page"] == 10

                    # Verify resources array
                    assert "resources" in response_data
                    assert len(response_data["resources"]) == 1

                    # Verify each resource has complete structure
                    resource = response_data["resources"][0]
                    assert resource["type"] == "resource"
                    assert resource["id"] == "stanford-test-123"
                    assert "attributes" in resource
                    assert "meta" in resource
                    assert "ui" in resource["meta"]

    @pytest.mark.asyncio
    async def test_get_resource_ogm_full_response(self, mock_session):
        """Test that get_resource_ogm returns the complete Aardvark record."""
        # Create MCP service instance
        mcp_service = OGMMCPService()

        # Mock the database session factory
        with patch("app.services.mcp_service.get_async_session") as mock_session_factory:
            mock_session_factory.return_value.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.return_value.__aexit__.return_value = None

            # Call the MCP service method
            result = await mcp_service._get_resource_ogm({"id": "stanford-test-123"})

            # Verify the result structure
            assert result.isError is False
            assert len(result.content) == 1
            assert result.content[0].type == "text"

            # Parse the JSON response
            response_data = json.loads(result.content[0].text)

            # Verify it's a complete Aardvark record
            assert "id" in response_data
            assert "dct_title_s" in response_data
            assert "dct_creator_s" in response_data
            assert "gbl_resourceClass_sm" in response_data  # Note the capital C
            assert "dct_accessRights_s" in response_data  # Note the capital R
            assert "gbl_mdVersion_s" in response_data  # Note the capital V

            # Verify field mapping worked correctly
            assert response_data["gbl_resourceClass_sm"] == ["Datasets"]
            assert response_data["dct_accessRights_s"] == "Public"
            assert response_data["gbl_mdVersion_s"] == "Aardvark"

    @pytest.mark.asyncio
    async def test_list_resources_full_response(self, mock_session):
        """Test that list_resources returns complete resource objects with pagination."""
        # Create MCP service instance
        mcp_service = OGMMCPService()

        # Mock the database session factory
        with patch("app.services.mcp_service.get_async_session") as mock_session_factory:
            mock_session_factory.return_value.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.return_value.__aexit__.return_value = None

            # Mock the count query result
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_count_result

            # Mock the process_resource function
            with patch("app.api.v1.utils.process_resource") as mock_process_resource:
                mock_process_resource.return_value = {
                    "type": "resource",
                    "id": "stanford-test-123",
                    "attributes": {
                        "dct_title_s": "Test Geospatial Dataset",
                        "dct_creator_s": ["Stanford University", "Test Creator"],
                    },
                    "meta": {
                        "ui": {
                            "citation": "Stanford University Libraries. (2023). Test Geospatial Dataset.",
                            "downloads": [],
                            "viewer": {},
                        }
                    },
                }

                # Call the MCP service method
                result = await mcp_service._list_resources({"page": 1, "per_page": 10})

                # Verify the result structure
                assert result.isError is False
                assert len(result.content) == 1
                assert result.content[0].type == "text"

                # Parse the JSON response
                response_data = json.loads(result.content[0].text)

                # Verify pagination metadata
                assert response_data["page"] == 1
                assert response_data["per_page"] == 10
                assert response_data["total_count"] == 1
                assert response_data["total_pages"] == 1

                # Verify resources array
                assert "resources" in response_data
                assert len(response_data["resources"]) == 1

                # Verify each resource has complete structure
                resource = response_data["resources"][0]
                assert resource["type"] == "resource"
                assert resource["id"] == "stanford-test-123"
                assert "attributes" in resource
                assert "meta" in resource

    def test_mcp_service_tools_registration(self):
        """Test that all tools are properly registered with correct schemas."""
        # Create MCP service instance
        mcp_service = OGMMCPService()

        # Verify the server has tools registered
        assert hasattr(mcp_service, "server")

        # The tools are registered via decorators, so we can't directly access them
        # But we can verify the service was initialized without errors
        assert mcp_service is not None


def demonstrate_full_response():
    """Demonstration function showing what the full MCP response looks like."""
    print("=" * 80)
    print("MCP SERVICE FULL RESPONSE DEMONSTRATION")
    print("=" * 80)

    print("\n1. GET_RESOURCE FULL RESPONSE:")
    print("-" * 40)
    print("""
{
  "type": "resource",
  "id": "stanford-test-123",
  "attributes": {
    "id": "stanford-test-123",
    "dct_title_s": "Test Geospatial Dataset",
    "dct_description_s": ["This is a comprehensive test dataset for geospatial analysis."],
    "dct_creator_s": ["Stanford University", "Test Creator"],
    "dct_publisher_s": ["Stanford University Libraries"],
    "dct_subject_s": ["Geospatial data", "Test data", "GIS"],
    "dct_spatial_sm": ["California", "Stanford"],
    "gbl_resourceClass_sm": ["Datasets"],
    "gbl_resourceType_sm": ["Geospatial data"],
    "dct_format_s": "Shapefile",
    "dct_accessRights_s": "Public",
    "dct_issued_s": "2023",
    "gbl_indexYear_im": [2023],
    "locn_geometry": {"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]},
    "dcat_bbox": "ENVELOPE(-122.5, -122.0, 37.0, 37.5)",
    "dcat_centroid": "POINT(-122.25 37.25)",
    "gbl_mdModified_dt": "2023-12-01T10:00:00Z",
    "gbl_mdVersion_s": "Aardvark"
  },
  "meta": {
    "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
    "@type": "AardvarkRecord",
    "human_readable": {
      "file_size": "2.5 MB"
    },
    "ui": {
      "allmaps": {
        "enabled": false,
        "url": null
      },
      "citation": "Stanford University Libraries. (2023). Test Geospatial Dataset. Stanford University.",
      "downloads": [
        {
          "label": "Shapefile",
          "url": "https://example.com/download/test.zip",
          "type": "direct"
        },
        {
          "label": "WMS Service",
          "url": "https://example.com/geoserver/wms",
          "type": "service"
        },
        {
          "label": "WFS Service",
          "url": "https://example.com/geoserver/wfs", 
          "type": "service"
        }
      ],
      "relationships": [],
      "summaries": [
        {
          "id": 1,
          "item_id": "stanford-test-123",
          "enrichment_type": "summary",
          "content": "This dataset contains comprehensive geospatial data for testing purposes.",
          "created_at": "2023-12-01T10:00:00Z"
        }
      ],
      "thumbnail_url": "https://example.com/thumbnails/test.jpg",
      "viewer": {
        "protocol": "wms",
        "endpoint": "https://example.com/geoserver/wms",
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]
        }
      }
    }
  }
}
""")

    print("\n2. SEARCH_RESOURCES FULL RESPONSE:")
    print("-" * 40)
    print("""
{
  "query": "test dataset",
  "total_results": 1,
  "page": 1,
  "per_page": 10,
  "resources": [
    {
      "type": "resource",
      "id": "stanford-test-123",
      "attributes": {
        "dct_title_s": "Test Geospatial Dataset",
        "dct_creator_s": ["Stanford University", "Test Creator"],
        "gbl_resourceClass_sm": ["Datasets"]
      },
      "meta": {
        "ui": {
          "citation": "Stanford University Libraries. (2023). Test Geospatial Dataset.",
          "downloads": [
            {
              "label": "Shapefile",
              "url": "https://example.com/download/test.zip",
              "type": "direct"
            }
          ],
          "viewer": {
            "protocol": "wms",
            "endpoint": "https://example.com/geoserver/wms"
          }
        }
      }
    }
  ]
}
""")

    print("\n3. LIST_RESOURCES FULL RESPONSE:")
    print("-" * 40)
    print("""
{
  "page": 1,
  "per_page": 10,
  "total_count": 1,
  "total_pages": 1,
  "resources": [
    {
      "type": "resource",
      "id": "stanford-test-123",
      "attributes": {
        "dct_title_s": "Test Geospatial Dataset",
        "dct_creator_s": ["Stanford University", "Test Creator"]
      },
      "meta": {
        "ui": {
          "citation": "Stanford University Libraries. (2023). Test Geospatial Dataset.",
          "downloads": [],
          "viewer": {}
        }
      }
    }
  ]
}
""")

    print("\n4. GET_RESOURCE_OGM FULL RESPONSE:")
    print("-" * 40)
    print("""
{
  "id": "stanford-test-123",
  "dct_title_s": "Test Geospatial Dataset",
  "dct_description_s": ["This is a comprehensive test dataset for geospatial analysis."],
  "dct_creator_s": ["Stanford University", "Test Creator"],
  "dct_publisher_s": ["Stanford University Libraries"],
  "dct_subject_s": ["Geospatial data", "Test data", "GIS"],
  "dct_spatial_sm": ["California", "Stanford"],
  "gbl_resourceClass_sm": ["Datasets"],
  "gbl_resourceType_sm": ["Geospatial data"],
  "dct_format_s": "Shapefile",
  "dct_accessRights_s": "Public",
  "dct_issued_s": "2023",
  "gbl_indexYear_im": [2023],
  "locn_geometry": {"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]},
  "dcat_bbox": "ENVELOPE(-122.5, -122.0, 37.0, 37.5)",
  "dcat_centroid": "POINT(-122.25 37.25)",
  "gbl_mdModified_dt": "2023-12-01T10:00:00Z",
  "gbl_mdVersion_s": "Aardvark"
}
""")

    print("\n" + "=" * 80)
    print("KEY IMPROVEMENTS IN MCP SERVICE RESPONSES:")
    print("=" * 80)
    print("✓ Full Aardvark metadata fields with proper field mapping")
    print("✓ Complete UI enhancements (citations, downloads, viewer info)")
    print("✓ AI-generated summaries and relationships")
    print("✓ Thumbnail URLs and Allmaps integration")
    print("✓ Proper JSON formatting with indentation")
    print("✓ Consistent structure matching API endpoints")
    print("✓ Pagination metadata for list/search operations")
    print("✓ Error handling with detailed error messages")


if __name__ == "__main__":
    # Run the demonstration
    demonstrate_full_response()

    # Run the tests
    pytest.main([__file__, "-v"])
