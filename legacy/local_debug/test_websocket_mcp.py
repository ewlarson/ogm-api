#!/usr/bin/env python3
"""
Test script for the OGM API MCP WebSocket service.
"""

import asyncio
import json
import websockets
from typing import Dict, Any

async def test_mcp_websocket():
    """Test the MCP WebSocket service."""
    
    uri = "ws://localhost:8000/api/v1/mcp/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to MCP WebSocket service")
            
            # Test initialization
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            print(f"Sending initialization: {json.dumps(init_message, indent=2)}")
            await websocket.send(json.dumps(init_message))
            
            # Read response
            response = await websocket.recv()
            print(f"Init response: {json.dumps(json.loads(response), indent=2)}")
            
            # Test list tools
            list_tools_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            print(f"\nSending list tools: {json.dumps(list_tools_message, indent=2)}")
            await websocket.send(json.dumps(list_tools_message))
            
            response = await websocket.recv()
            print(f"List tools response: {json.dumps(json.loads(response), indent=2)}")
            
            # Test calling a tool
            call_tool_message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "list_resources",
                    "arguments": {
                        "page": 1,
                        "per_page": 3
                    }
                }
            }
            
            print(f"\nSending tool call: {json.dumps(call_tool_message, indent=2)}")
            await websocket.send(json.dumps(call_tool_message))
            
            response = await websocket.recv()
            print(f"Call tool response: {json.dumps(json.loads(response), indent=2)}")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_websocket())
