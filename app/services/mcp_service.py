import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    ServerCapabilities,
    ToolsCapability,
)

from app.services.search_service import SearchService
from app.services.citation_service import CitationService
from app.services.download_service import DownloadService
from app.services.viewer_service import ViewerService
from app.services.image_service import ImageService
from app.services.relationship_service import RelationshipService
from app.services.allmaps_service import AllmapsService
from db.config import DATABASE_URL
from db.models import items
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Lazy initialization of database engine and session
_engine = None
_async_session = None

def get_async_session():
    """Get the async session factory, creating it if necessary."""
    global _engine, _async_session
    if _engine is None:
        _engine = create_async_engine(DATABASE_URL)
        _async_session = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session

class OGMMCPService:
    """MCP service for OpenGeoMetadata API endpoints."""
    
    def __init__(self):
        self.server = Server("ogm-api")
        self._register_tools()
    
    def _register_tools(self):
        """Register all API endpoints as MCP tools."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List all available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="search_resources",
                        description="Search for geospatial resources using text queries, filters, and sorting options",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query string"
                                },
                                "page": {
                                    "type": "integer",
                                    "description": "Page number (default: 1)",
                                    "default": 1
                                },
                                "per_page": {
                                    "type": "integer",
                                    "description": "Resources per page (max 100, default: 10)",
                                    "default": 10
                                },
                                "sort": {
                                    "type": "string",
                                    "description": "Sort option (relevance, year_desc, year_asc, title_asc, title_desc)",
                                    "enum": ["relevance", "year_desc", "year_asc", "title_asc", "title_desc"]
                                }
                            }
                        }
                    ),
                    Tool(
                        name="get_resource",
                        description="Get a single geospatial resource by ID with full metadata and UI enhancements",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Resource ID"
                                }
                            },
                            "required": ["id"]
                        }
                    ),
                    Tool(
                        name="get_resource_ogm",
                        description="Get just the OpenGeoMetadata Aardvark record for a resource by ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Resource ID"
                                }
                            },
                            "required": ["id"]
                        }
                    ),
                    Tool(
                        name="list_resources",
                        description="List all geospatial resources with pagination",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "page": {
                                    "type": "integer",
                                    "description": "Page number (default: 1)",
                                    "default": 1
                                },
                                "per_page": {
                                    "type": "integer",
                                    "description": "Resources per page (max 100, default: 10)",
                                    "default": 10
                                }
                            }
                        }
                    ),
                    Tool(
                        name="get_suggestions",
                        description="Get search suggestions for autocomplete",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query for suggestions"
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="get_resource_viewer",
                        description="Get an HTML page with the embedded OGM viewer for a specific resource",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Resource ID"
                                },
                                "embed": {
                                    "type": "boolean",
                                    "description": "Embedded mode for iframe usage",
                                    "default": False
                                }
                            },
                            "required": ["id"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "search_resources":
                    return await self._search_resources(arguments)
                elif name == "get_resource":
                    return await self._get_resource(arguments)
                elif name == "get_resource_ogm":
                    return await self._get_resource_ogm(arguments)
                elif name == "list_resources":
                    return await self._list_resources(arguments)
                elif name == "get_suggestions":
                    return await self._get_suggestions(arguments)
                elif name == "get_resource_viewer":
                    return await self._get_resource_viewer(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: {str(e)}"
                        )
                    ],
                    isError=True
                )
    
    async def _search_resources(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search for resources."""
        query = arguments.get("query")
        page = arguments.get("page", 1)
        per_page = arguments.get("per_page", 10)
        sort = arguments.get("sort")
        
        search_service = SearchService()
        results = await search_service.search(
            q=query,
            page=page,
            limit=per_page,
            sort=sort,
            request_query_params="",
            callback=None,
        )
        
        # Format the results for MCP
        content = [
            TextContent(
                type="text",
                text=f"Found {len(results.get('data', []))} resources matching '{query}'"
            )
        ]
        
        # Add resource details
        for item in results.get("data", [])[:5]:  # Limit to first 5 for display
            attrs = item.get("attributes", {})
            title = attrs.get("dct_title_s", "Untitled")
            content.append(
                TextContent(
                    type="text",
                    text=f"- {title} (ID: {item.get('id')})"
                )
            )
        
        if len(results.get("data", [])) > 5:
            content.append(
                TextContent(
                    type="text",
                    text=f"... and {len(results.get('data', [])) - 5} more results"
                )
            )
        
        return CallToolResult(content=content)
    
    async def _get_resource(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get a single resource."""
        resource_id = arguments["id"]
        
        async with get_async_session()() as session:
            query = select(items).where(items.c.id == resource_id)
            result = await session.execute(query)
            row = result.fetchone()
            
            if not row:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Resource not found: {resource_id}"
                        )
                    ],
                    isError=True
                )
            
            # Convert to dict
            resource_dict = dict(row._mapping)
            
            # Get basic info
            title = resource_dict.get("dct_title_s", "Untitled")
            description = resource_dict.get("dct_description_s", "No description available")
            
            content = [
                TextContent(
                    type="text",
                    text=f"Resource: {title}\n\nDescription: {description}\n\nID: {resource_id}"
                )
            ]
            
            # Add citation if available
            try:
                citation_service = CitationService(resource_dict)
                citation = citation_service.get_citation()
                if citation:
                    content.append(
                        TextContent(
                            type="text",
                            text=f"\nCitation:\n{citation}"
                        )
                    )
            except Exception as e:
                logger.warning(f"Could not generate citation: {e}")
            
            return CallToolResult(content=content)
    
    async def _get_resource_ogm(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get Aardvark record for a resource."""
        resource_id = arguments["id"]
        
        async with get_async_session()() as session:
            query = select(items).where(items.c.id == resource_id)
            result = await session.execute(query)
            row = result.fetchone()
            
            if not row:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Resource not found: {resource_id}"
                        )
                    ],
                    isError=True
                )
            
            # Convert to dict and return as JSON
            resource_dict = dict(row._mapping)
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Aardvark record for resource {resource_id}:\n{str(resource_dict)}"
                    )
                ]
            )
    
    async def _list_resources(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List resources with pagination."""
        page = arguments.get("page", 1)
        per_page = arguments.get("per_page", 10)
        
        skip = (page - 1) * per_page
        limit = per_page
        
        async with get_async_session()() as session:
            query = select(items).offset(skip).limit(limit)
            result = await session.execute(query)
            results = result.fetchall()
            
            # Get total count
            count_query = select(func.count(items.c.id))
            count_result = await session.execute(count_query)
            total_count = count_result.scalar()
            
            content = [
                TextContent(
                    type="text",
                    text=f"Showing {len(results)} of {total_count} total resources (page {page})"
                )
            ]
            
            # Add resource details
            for row in results:
                resource_dict = dict(row._mapping)
                title = resource_dict.get("dct_title_s", "Untitled")
                content.append(
                    TextContent(
                        type="text",
                        text=f"- {title} (ID: {resource_dict.get('id')})"
                    )
                )
            
            return CallToolResult(content=content)
    
    async def _get_suggestions(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get search suggestions."""
        query = arguments["query"]
        
        search_service = SearchService()
        suggestions = await search_service.suggest(query)
        
        content = [
            TextContent(
                type="text",
                text=f"Suggestions for '{query}':"
            )
        ]
        
        for suggestion in suggestions.get("suggestions", []):
            content.append(
                TextContent(
                    type="text",
                    text=f"- {suggestion}"
                )
            )
        
        return CallToolResult(content=content)
    
    async def _get_resource_viewer(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get viewer HTML for a resource."""
        resource_id = arguments["id"]
        embed = arguments.get("embed", False)
        
        # Build the record URL for the viewer
        base_url = "http://localhost:8000"
        record_url = f"{base_url}/api/v1/resources/{resource_id}/ogm"
        
        # Create the HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OGM Viewer - Resource {resource_id}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .viewer-container {{
            width: 100vw;
            height: 100vh;
        }}
        {f'.viewer-container {{ height: 600px; }}' if embed else ''}
    </style>
</head>
<body>
    <div class="viewer-container">
        <ogm-viewer 
            record-url="{record_url}"
            >
        </ogm-viewer>
    </div>
    
    <!-- Load the OGM Viewer web component -->
    <script type="module" src="https://unpkg.com/ogm-viewer"></script>
</body>
</html>
"""
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Viewer HTML for resource {resource_id}:\n\n{html_content}"
                )
            ]
        )

# Create global service instance
mcp_service = OGMMCPService()

async def run_mcp_server():
    """Run the MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_service.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ogm-api",
                server_version="0.1.0",
                capabilities=ServerCapabilities(
                    tools=ToolsCapability()
                ),
            ),
        )

async def run_mcp_websocket_server(websocket):
    """Run the MCP server via WebSocket."""
    try:
        # Handle MCP protocol over WebSocket
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                response = await handle_mcp_message(data)
                await websocket.send_text(json.dumps(response))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }))
    except Exception as e:
        logging.error(f"WebSocket error: {e}")

async def handle_mcp_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP protocol messages."""
    method = data.get("method")
    msg_id = data.get("id")
    params = data.get("params", {})
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "ogm-api",
                    "version": "0.1.0"
                }
            }
        }
    
    elif method == "tools/list":
        tools = [
            {
                "name": "search_resources",
                "description": "Search for geospatial resources using text queries, filters, and sorting options",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query string"},
                        "page": {"type": "integer", "description": "Page number (default: 1)", "default": 1},
                        "per_page": {"type": "integer", "description": "Resources per page (max 100, default: 10)", "default": 10},
                        "sort": {"type": "string", "description": "Sort option", "enum": ["relevance", "year_desc", "year_asc", "title_asc", "title_desc"]}
                    }
                }
            },
            {
                "name": "get_resource",
                "description": "Get a single geospatial resource by ID with full metadata and UI enhancements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Resource ID"}
                    },
                    "required": ["id"]
                }
            },
            {
                "name": "list_resources",
                "description": "List all geospatial resources with pagination",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "description": "Page number (default: 1)", "default": 1},
                        "per_page": {"type": "integer", "description": "Resources per page (max 100, default: 10)", "default": 10}
                    }
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": tools
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "search_resources":
                result = await mcp_service._search_resources(arguments)
            elif tool_name == "get_resource":
                result = await mcp_service._get_resource(arguments)
            elif tool_name == "list_resources":
                result = await mcp_service._list_resources(arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                }
            
            # Convert CallToolResult to JSON-RPC response
            content_text = ""
            for content_item in result.content:
                if hasattr(content_item, 'text'):
                    content_text += content_item.text + "\n"
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text.strip()
                        }
                    ],
                    "isError": result.isError if hasattr(result, 'isError') else False
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

if __name__ == "__main__":
    asyncio.run(run_mcp_server())
