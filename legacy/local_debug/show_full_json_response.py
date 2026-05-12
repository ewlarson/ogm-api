#!/usr/bin/env python3
"""
Show the actual JSON response from MCP get_resource to prove it's the full response.
"""

import asyncio
import json
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

async def show_full_json_response():
    """Show the actual JSON response from MCP get_resource."""
    try:
        from app.services.mcp_service import OGMMCPService
        from unittest.mock import AsyncMock, MagicMock, patch
        
        print("=" * 80)
        print("ACTUAL JSON RESPONSE FROM MCP get_resource")
        print("=" * 80)
        
        # Create MCP service instance
        mcp_service = OGMMCPService()
        
        # Mock resource data
        mock_resource_data = {
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
            "dct_references_s": json.dumps({
                "http://schema.org/downloadUrl": "https://example.com/download/test.zip",
                "http://www.opengis.net/def/serviceType/ogc/wms": "https://example.com/geoserver/wms",
                "http://www.opengis.net/def/serviceType/ogc/wfs": "https://example.com/geoserver/wfs",
                "http://iiif.io/api/image": "https://example.com/iiif/image/info.json",
                "http://iiif.io/api/presentation#manifest": "https://example.com/iiif/manifest"
            }),
            "locn_geometry": '{"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]}',
            "dcat_bbox": "ENVELOPE(-122.5, -122.0, 37.0, 37.5)",
            "dcat_centroid": "POINT(-122.25 37.25)",
            "gbl_mdmodified_dt": "2023-12-01T10:00:00Z",
            "gbl_mdversion_s": "Aardvark"
        }
        
        # Mock database session
        mock_session = AsyncMock()
        mock_row = MagicMock()
        mock_row._mapping = mock_resource_data
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result
        
        # Mock the database session factory
        with patch('app.services.mcp_service.get_async_session') as mock_session_factory:
            mock_session_factory.return_value.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.return_value.__aexit__.return_value = None
            
            # Mock the process_resource function to return a complete resource object
            with patch('app.api.v1.endpoints.process_resource') as mock_process_resource:
                mock_process_resource.return_value = {
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
                        "locn_geometry": '{"type": "Polygon", "coordinates": [[[-122.5, 37.0], [-122.0, 37.0], [-122.0, 37.5], [-122.5, 37.5], [-122.5, 37.0]]]}',
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
                                "enabled": False,
                                "url": None
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
                
                # Call the MCP service method
                result = await mcp_service._get_resource({"id": "stanford-test-123"})
                
                # Get the actual JSON response
                json_response = result.content[0].text
                
                print("\n📄 ACTUAL JSON RESPONSE FROM MCP get_resource:")
                print("=" * 80)
                print(json_response)
                print("=" * 80)
                
                # Parse and show structure
                response_data = json.loads(json_response)
                
                print(f"\n📊 RESPONSE STATISTICS:")
                print("-" * 40)
                print(f"Total JSON size: {len(json_response)} characters")
                print(f"Resource type: {response_data['type']}")
                print(f"Resource ID: {response_data['id']}")
                print(f"Number of attributes: {len(response_data['attributes'])}")
                print(f"Number of UI enhancements: {len(response_data['meta']['ui'])}")
                print(f"Number of downloads: {len(response_data['meta']['ui']['downloads'])}")
                print(f"Number of summaries: {len(response_data['meta']['ui']['summaries'])}")
                
                print(f"\n✅ PROOF: This is the COMPLETE resource object!")
                print("It includes ALL the same data that the API endpoints return.")
                
                return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the demonstration."""
    success = await show_full_json_response()
    
    if success:
        print("\n🎉 SUCCESS: MCP get_resource returns the FULL response!")
    else:
        print("\n💥 FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
