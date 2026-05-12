#!/usr/bin/env python3
"""
Quick test to check WebSocket response for a specific resource.
"""

import asyncio
import json
import websockets

async def quick_test():
    uri = "ws://localhost:8000/api/v1/mcp/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Call get_resource directly
        call_message = {
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
        
        print("Sending get_resource call...")
        await websocket.send(json.dumps(call_message))
        response = await websocket.recv()
        
        print(f"\nResponse length: {len(response)} characters")
        print(f"Response preview: {response[:500]}...")
        
        # Parse and check
        try:
            data = json.loads(response)
            if 'result' in data and 'content' in data['result']:
                content = data['result']['content'][0]['text']
                print(f"\nContent length: {len(content)} characters")
                print(f"Content preview: {content[:500]}...")
                
                # Try to parse the content as JSON
                try:
                    json_content = json.loads(content)
                    print(f"\n✓ Content is valid JSON with {len(json.dumps(json_content))} characters")
                    print(f"✓ Resource type: {json_content.get('type')}")
                    print(f"✓ Has attributes: {'attributes' in json_content}")
                    print(f"✓ Has meta: {'meta' in json_content}")
                    
                    if 'meta' in json_content and 'ui' in json_content['meta']:
                        ui = json_content['meta']['ui']
                        print(f"✓ UI enhancements: {list(ui.keys())}")
                        print(f"✓ Downloads count: {len(ui.get('downloads', []))}")
                        print(f"✓ Has citation: {'citation' in ui}")
                        print(f"✓ Has viewer: {'viewer' in ui}")
                        
                except json.JSONDecodeError:
                    print("❌ Content is not valid JSON")
                    print(f"Content: {content}")
            else:
                print("❌ No content in response")
                print(f"Response: {data}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(quick_test())
