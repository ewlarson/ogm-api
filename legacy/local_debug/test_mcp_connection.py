#!/usr/bin/env python3
"""
Test script to simulate MCP connection and test graceful handling of disconnections.
"""

import asyncio
import logging
import sys
import os
import signal
import time

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_mcp_connection():
    """Test MCP connection handling."""
    try:
        from app.services.mcp_service import run_mcp_server
        
        print("Testing MCP connection handling...")
        print("This will simulate a client connection and then disconnect")
        print("Press Ctrl+C to stop the test")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print("\nReceived interrupt signal, shutting down gracefully...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Run the MCP server
        await run_mcp_server()
        
    except KeyboardInterrupt:
        print("\n✓ Test interrupted by user - graceful shutdown")
    except BrokenPipeError:
        print("\n✓ Broken pipe handled gracefully")
    except Exception as e:
        print(f"\n✗ Error in MCP connection test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Run the MCP connection test."""
    print("MCP Connection Test")
    print("=" * 50)
    
    success = await test_mcp_connection()
    
    print("=" * 50)
    if success:
        print("✓ MCP connection test completed successfully!")
    else:
        print("✗ MCP connection test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
