#!/usr/bin/env python3
"""
Show the raw response that Claude Desktop is receiving.
"""

import asyncio
import json
import websockets

async def show_raw_response():
    uri = "ws://localhost:8000/api/v1/mcp/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Call get_resource
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
        
        # Parse the response
        data = json.loads(response)
        content = data['result']['content'][0]['text']
        
        print("\n" + "=" * 80)
        print("RAW JSON RESPONSE THAT CLAUDE DESKTOP RECEIVES:")
        print("=" * 80)
        print(content)
        print("=" * 80)
        
        # Parse the content to show structure
        resource_data = json.loads(content)
        
        print(f"\n📊 RESPONSE STRUCTURE:")
        print("-" * 40)
        print(f"Resource ID: {resource_data['id']}")
        print(f"Title: {resource_data['attributes']['dct_title_s']}")
        print(f"Creators: {resource_data['attributes']['dct_creator_s']}")
        
        # Show UI enhancements
        ui = resource_data['meta']['ui']
        print(f"\n🎨 UI ENHANCEMENTS:")
        print("-" * 40)
        print(f"Citation: {ui['citation']}")
        print(f"Downloads: {len(ui['downloads'])} items")
        print(f"Thumbnail: {ui['thumbnail_url']}")
        print(f"Viewer protocol: {ui['viewer']['protocol']}")
        
        print(f"\n✅ This is the COMPLETE response that Claude Desktop receives!")
        print("Claude is interpreting this JSON and showing you a summary.")

if __name__ == "__main__":
    asyncio.run(show_raw_response())
