# MCP Integration

This document describes the Model Context Protocol (MCP) integration for the OpenGeoMetadata API.

## Overview

The OGM API now includes an MCP service that exposes all API endpoints as MCP tools. This allows AI assistants and other MCP clients to interact with the geospatial metadata API programmatically.

## MCP Endpoint

The MCP service is advertised at `/api/v1/mcp` and provides information about the available tools and how to connect to the service.

### Service Information

```json
{
  "name": "ogm-api",
  "version": "0.1.0",
  "description": "OpenGeoMetadata API MCP Service",
  "protocol": "mcp",
  "transport": "stdio",
  "capabilities": {
    "tools": [
      "search_resources",
      "get_resource", 
      "get_resource_ogm",
      "list_resources",
      "get_suggestions",
      "get_resource_viewer"
    ]
  },
  "connection": {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "app.services.mcp_service"]
  }
}
```

## Available Tools

### search_resources

Search for geospatial resources using text queries, filters, and sorting options.

**Parameters:**
- `query` (string): Search query string
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Resources per page (max 100, default: 10)
- `sort` (string, optional): Sort option (relevance, year_desc, year_asc, title_asc, title_desc)

**Example:**
```json
{
  "name": "search_resources",
  "arguments": {
    "query": "Indiana maps",
    "page": 1,
    "per_page": 10,
    "sort": "relevance"
  }
}
```

### get_resource

Get a single geospatial resource by ID with full metadata and UI enhancements.

**Parameters:**
- `id` (string, required): Resource ID

**Example:**
```json
{
  "name": "get_resource",
  "arguments": {
    "id": "stanford-abc123"
  }
}
```

### get_resource_ogm

Get just the OpenGeoMetadata Aardvark record for a resource by ID.

**Parameters:**
- `id` (string, required): Resource ID

**Example:**
```json
{
  "name": "get_resource_ogm",
  "arguments": {
    "id": "stanford-abc123"
  }
}
```

### list_resources

List all geospatial resources with pagination.

**Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Resources per page (max 100, default: 10)

**Example:**
```json
{
  "name": "list_resources",
  "arguments": {
    "page": 1,
    "per_page": 20
  }
}
```

### get_suggestions

Get search suggestions for autocomplete.

**Parameters:**
- `query` (string, required): Search query for suggestions

**Example:**
```json
{
  "name": "get_suggestions",
  "arguments": {
    "query": "Indiana"
  }
}
```

### get_resource_viewer

Get an HTML page with the embedded OGM viewer for a specific resource.

**Parameters:**
- `id` (string, required): Resource ID
- `embed` (boolean, optional): Embedded mode for iframe usage (default: false)

**Example:**
```json
{
  "name": "get_resource_viewer",
  "arguments": {
    "id": "stanford-abc123",
    "embed": true
  }
}
```

## Usage

### Running the MCP Service

The MCP service can be run as a standalone process:

```bash
cd backend
python -m app.services.mcp_service
```

### Integration with MCP Clients

To integrate with an MCP client, configure it to use the OGM API MCP service:

```json
{
  "mcpServers": {
    "ogm-api": {
      "command": "python",
      "args": ["-m", "app.services.mcp_service"],
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/opengeometadata_api",
        "ELASTICSEARCH_URL": "http://localhost:9200",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6380"
      }
    }
  }
}
```

### Testing

A backend test suite is provided to verify the MCP service functionality:

```bash
cd backend
pytest tests/api/v1/test_mcp_endpoints.py tests/services/test_mcp_service.py
```

## Implementation Details

The MCP service is implemented in `app/services/mcp_service.py` and uses the main Python MCP SDK. It:

1. Creates an MCP server instance
2. Registers all API endpoints as tools
3. Handles tool calls by delegating to the appropriate service methods
4. Returns formatted results as MCP content

The service reuses existing service classes (SearchService, CitationService, etc.) to maintain consistency with the REST API implementation.

## Dependencies

The MCP integration requires:
- `mcp>=1.12.2` - The main Python MCP SDK
- All existing OGM API dependencies

The `fastapi-mcp` dependency has been removed in favor of the main MCP SDK for better control and transparency.
