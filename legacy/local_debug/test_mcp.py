#!/usr/bin/env python3
"""
Test script for the OGM API MCP service.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

async def test_mcp_service():
    """Test the MCP service by running it as a subprocess and sending test messages."""
    
    # Start the MCP service as a subprocess
    process = subprocess.Popen(
        [sys.executable, "-m", "app.services.mcp_service"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
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
        
        # Send initialization
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print(f"Init response: {response}")
        
        # Test list tools
        list_tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(list_tools_message) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"List tools response: {response}")
        
        # Test calling a tool
        call_tool_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_resources",
                "arguments": {
                    "query": "test",
                    "page": 1,
                    "per_page": 5
                }
            }
        }
        
        process.stdin.write(json.dumps(call_tool_message) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print(f"Call tool response: {response}")
        
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_service())
