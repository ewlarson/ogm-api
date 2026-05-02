#!/usr/bin/env python3
"""
Test script to check what's actually being returned through the WebSocket bridge.
"""

import asyncio
import json
import websockets
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

async def test_websocket_response():
    """Test the WebSocket MCP response directly."""
    try:
        # Connect to the WebSocket MCP endpoint
        uri = "ws://localhost:8000/api/v1/mcp/ws"
        
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to WebSocket")
            
            # Initialize the MCP connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            }
            
            print("\n🔍 Sending initialize...")
            await websocket.send(json.dumps(init_message))
            response = await websocket.recv()
            print(f"✓ Initialize response: {response[:200]}...")
            
            # Call get_resource
            call_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_resource",
                    "arguments": {
                        "id": "p16022coll245:978"
                    }
                }
            }
            
            print("\n🔍 Sending get_resource call...")
            await websocket.send(json.dumps(call_message))
            response = await websocket.recv()
            
            print(f"\n📄 RAW WEBSOCKET RESPONSE:")
            print("=" * 80)
            print(response)
            print("=" * 80)
            
            # Parse the response
            response_data = json.loads(response)
            
            print(f"\n📊 RESPONSE ANALYSIS:")
            print("-" * 40)
            print(f"Response ID: {response_data.get('id')}")
            print(f"Has result: {'result' in response_data}")
            print(f"Has error: {'error' in response_data}")
            
            if 'result' in response_data:
                result = response_data['result']
                print(f"Has content: {'content' in result}")
                print(f"Content length: {len(result.get('content', []))}")
                
                if 'content' in result and result['content']:
                    content = result['content'][0]
                    print(f"Content type: {content.get('type')}")
                    text = content.get('text', '')
                    print(f"Text length: {len(text)} characters")
                    print(f"Text preview: {text[:200]}...")
                    
                    # Try to parse as JSON
                    try:
                        json_data = json.loads(text)
                        print(f"✓ Valid JSON with {len(json.dumps(json_data))} characters")
                        
                        if isinstance(json_data, dict):
                            print(f"✓ Has type: {json_data.get('type')}")
                            print(f"✓ Has attributes: {'attributes' in json_data}")
                            print(f"✓ Has meta: {'meta' in json_data}")
                            
                            if 'attributes' in json_data:
                                attrs = json_data['attributes']
                                print(f"✓ Attributes count: {len(attrs)}")
                                print(f"✓ Title: {attrs.get('dct_title_s', 'N/A')}")
                            
                            if 'meta' in json_data and 'ui' in json_data['meta']:
                                ui = json_data['meta']['ui']
                                print(f"✓ UI enhancements count: {len(ui)}")
                                print(f"✓ Downloads count: {len(ui.get('downloads', []))}")
                                print(f"✓ Has citation: {'citation' in ui}")
                                print(f"✓ Has viewer: {'viewer' in ui}")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Not valid JSON: {e}")
                        print(f"Text content: {text}")
            
            elif 'error' in response_data:
                error = response_data['error']
                print(f"❌ Error: {error.get('message')}")
            
            print("\n" + "=" * 80)
            print("✅ WEBSOCKET TEST COMPLETE")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ Error testing WebSocket: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run the WebSocket test."""
    print("Testing WebSocket MCP response...")
    await test_websocket_response()

if __name__ == "__main__":
    asyncio.run(main())
