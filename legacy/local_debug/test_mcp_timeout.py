#!/usr/bin/env python3
"""
Test script to test MCP service with timeout to simulate broken pipe scenario.
"""

import asyncio
import logging
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_mcp_timeout():
    """Test MCP service with timeout."""
    try:
        from app.services.mcp_service import run_mcp_server
        
        print("Testing MCP service with timeout...")
        print("This will start the MCP server and wait for 10 seconds")
        print("Then it will timeout to simulate a client disconnection")
        
        # Run the MCP server with a timeout
        try:
            await asyncio.wait_for(run_mcp_server(), timeout=10.0)
        except asyncio.TimeoutError:
            print("✓ MCP server timed out as expected")
            return True
        
    except Exception as e:
        print(f"✗ Error in MCP timeout test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Run the MCP timeout test."""
    print("MCP Timeout Test")
    print("=" * 50)
    
    success = await test_mcp_timeout()
    
    print("=" * 50)
    if success:
        print("✓ MCP timeout test completed successfully!")
    else:
        print("✗ MCP timeout test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
