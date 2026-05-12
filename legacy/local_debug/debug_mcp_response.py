#!/usr/bin/env python3
"""
Debug script to see what's actually happening in the MCP service.
"""

import asyncio
import json
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

async def debug_mcp_response():
    """Debug the MCP response to see what's happening."""
    try:
        from app.services.mcp_service import OGMMCPService
        from unittest.mock import AsyncMock, MagicMock, patch
        
        print("=" * 80)
        print("DEBUGGING MCP RESPONSE")
        print("=" * 80)
        
        # Create MCP service instance
        mcp_service = OGMMCPService()
        print("✓ MCP service created")
        
        # Mock resource data that should exist
        mock_resource_data = {
            "id": "p16022coll245:978",
            "dct_title_s": "Minneapolis.",
            "dct_description_sm": ["35 x 48 centimeters", "Minneapolis and St. Paul Maps and Atlases"],
            "dct_creator_sm": ["Cram, George Franklin, 1841-1928"],
            "dct_publisher_sm": ["Geo. F. Cram, (Chicago), 1906"],
            "dct_format_s": "JPEG",
            "dct_accessrights_s": "Public",
            "dct_issued_s": "1906",
            "gbl_indexyear_im": [1906],
            "dct_references_s": json.dumps({
                "http://iiif.io/api/image": "https://cdm16022.contentdm.oclc.org/digital/iiif/p16022coll245/978/info.json",
                "http://schema.org/url": "https://umedia.lib.umn.edu/item/p16022coll245:978",
                "http://iiif.io/api/presentation#manifest": "https://cdm16022.contentdm.oclc.org/iiif/info/p16022coll245/978/manifest.json"
            }),
            "locn_geometry": "POLYGON((-93.329 45.051, -93.194 45.051, -93.194 44.890, -93.329 44.890, -93.329 45.051))",
            "dcat_bbox": "ENVELOPE(-93.329,-93.194,45.051,44.890)",
            "dcat_centroid": "44.9705,-93.2615",
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
                    "id": "p16022coll245:978",
                    "attributes": {
                        "id": "p16022coll245:978",
                        "dct_title_s": "Minneapolis.",
                        "dct_description_sm": ["35 x 48 centimeters", "Minneapolis and St. Paul Maps and Atlases"],
                        "dct_creator_sm": ["Cram, George Franklin, 1841-1928"],
                        "dct_publisher_sm": ["Geo. F. Cram, (Chicago), 1906"],
                        "dct_format_s": "JPEG",
                        "dct_accessRights_s": "Public",
                        "dct_issued_s": "1906",
                        "gbl_indexYear_im": [1906],
                        "locn_geometry": "POLYGON((-93.329 45.051, -93.194 45.051, -93.194 44.890, -93.329 44.890, -93.329 45.051))",
                        "dcat_bbox": "ENVELOPE(-93.329,-93.194,45.051,44.890)",
                        "dcat_centroid": "44.9705,-93.2615",
                        "gbl_mdVersion_s": "Aardvark"
                    },
                    "meta": {
                        "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
                        "@type": "AardvarkRecord",
                        "ui": {
                            "citation": "Cram, George Franklin, 1841-1928. (1906). Minneapolis.. Geo. F. Cram, (Chicago), 1906. https://umedia.lib.umn.edu/item/p16022coll245:978",
                            "downloads": [
                                {
                                    "label": "Thumb Image",
                                    "url": "https://cdm16022.contentdm.oclc.org/digital/iiif/p16022coll245/978/full/150,150/0/default.jpg",
                                    "type": "image/jpeg"
                                },
                                {
                                    "label": "Full Resolution Image",
                                    "url": "https://cdm16022.contentdm.oclc.org/digital/iiif/p16022coll245/978/full/full/0/default.jpg",
                                    "type": "image/jpeg"
                                }
                            ],
                            "thumbnail_url": "https://cdm16022.contentdm.oclc.org/iiif/2/p16022coll245:978/full/400,/0/default.jpg",
                            "viewer": {
                                "protocol": "iiif_manifest",
                                "endpoint": "https://cdm16022.contentdm.oclc.org/iiif/info/p16022coll245/978/manifest.json",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [[[-93.329, 45.051], [-93.194, 45.051], [-93.194, 44.89], [-93.329, 44.89], [-93.329, 45.051]]]
                                }
                            }
                        }
                    }
                }
                
                print("\n🔍 CALLING MCP _get_resource...")
                result = await mcp_service._get_resource({"id": "p16022coll245:978"})
                
                print(f"✓ Result isError: {result.isError}")
                print(f"✓ Number of content items: {len(result.content)}")
                
                for i, content_item in enumerate(result.content):
                    print(f"✓ Content {i} type: {content_item.type}")
                    print(f"✓ Content {i} text length: {len(content_item.text)}")
                    print(f"✓ Content {i} preview: {content_item.text[:200]}...")
                
                # Test the WebSocket handler
                print("\n🔍 TESTING WEBSOCKET HANDLER...")
                from app.services.mcp_service import handle_mcp_message
                
                # Create a mock MCP message
                mcp_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_resource",
                        "arguments": {
                            "id": "p16022coll245:978"
                        }
                    }
                }
                
                # Mock the mcp_service for the WebSocket handler
                with patch('app.services.mcp_service.mcp_service', mcp_service):
                    response = await handle_mcp_message(mcp_message)
                
                print(f"✓ WebSocket response ID: {response.get('id')}")
                print(f"✓ Has result: {'result' in response}")
                print(f"✓ Has error: {'error' in response}")
                
                if 'result' in response:
                    result_data = response['result']
                    print(f"✓ Has content: {'content' in result_data}")
                    print(f"✓ Content length: {len(result_data.get('content', []))}")
                    
                    if 'content' in result_data and result_data['content']:
                        content = result_data['content'][0]
                        print(f"✓ Content type: {content.get('type')}")
                        text = content.get('text', '')
                        print(f"✓ Text length: {len(text)} characters")
                        print(f"✓ Text preview: {text[:200]}...")
                        
                        # Try to parse as JSON
                        try:
                            json_data = json.loads(text)
                            print(f"✓ Valid JSON with {len(json.dumps(json_data))} characters")
                            print(f"✓ Has type: {json_data.get('type')}")
                            print(f"✓ Has attributes: {'attributes' in json_data}")
                            print(f"✓ Has meta: {'meta' in json_data}")
                        except json.JSONDecodeError as e:
                            print(f"❌ Not valid JSON: {e}")
                            print(f"Text content: {text}")
                
                elif 'error' in response:
                    error = response['error']
                    print(f"❌ Error: {error.get('message')}")
                
                print("\n" + "=" * 80)
                print("✅ DEBUG COMPLETE")
                print("=" * 80)
                
    except Exception as e:
        print(f"❌ Error debugging MCP response: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run the debug."""
    await debug_mcp_response()

if __name__ == "__main__":
    asyncio.run(main())
