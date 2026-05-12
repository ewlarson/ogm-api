#!/usr/bin/env python3
"""
Test script to search for water-related resources using the OGM API MCP service.
"""

import asyncio
import json
import websockets
from typing import Dict, Any

async def test_water_search():
    """Test searching for water-related resources via MCP WebSocket."""
    
    uri = "ws://localhost:8000/api/v1/mcp/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to OGM API MCP service")
            
            # Initialize the MCP connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "water-search-test",
                        "version": "1.0.0"
                    }
                }
            }
            
            print("📡 Initializing MCP connection...")
            await websocket.send(json.dumps(init_message))
            
            response = await websocket.recv()
            init_response = json.loads(response)
            print(f"✅ Initialization successful: {init_response['result']['serverInfo']['name']} v{init_response['result']['serverInfo']['version']}")
            
            # Search for water-related resources
            search_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_resources",
                    "arguments": {
                        "query": "water",
                        "page": 1,
                        "per_page": 5
                    }
                }
            }
            
            print("\n🔍 Searching for water-related resources...")
            await websocket.send(json.dumps(search_message))
            
            response = await websocket.recv()
            search_response = json.loads(response)
            
            if "result" in search_response:
                print("\n🌊 Water-related resources found:")
                print("=" * 50)
                content = search_response["result"]["content"][0]["text"]
                print(content)
            else:
                print(f"❌ Error: {search_response.get('error', 'Unknown error')}")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Is the Docker container running?")
        print("   Try: docker compose up -d")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_water_search())
