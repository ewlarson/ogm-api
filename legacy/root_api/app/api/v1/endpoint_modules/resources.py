import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.sql import select

from app.api.v1.shared import async_session
from app.api.v1.utils import create_response, process_resource, sanitize_for_json
from db.models import items

from .utils import clean_dict, map_to_aardvark_fields


def build_pagination_links(
    base_url: str, current_page: int, total_pages: int, params: dict = None
) -> dict:
    """Build JSON:API pagination links."""
    # Build query string from params
    query_parts = []
    if params:
        for key, value in params.items():
            if value is not None and value != "":
                query_parts.append(f"{key}={value}")

    query_string = "&".join(query_parts)
    url_with_params = f"{base_url}?{query_string}" if query_string else base_url

    links = {
        "self": f"{url_with_params}&page={current_page}",
        "first": f"{url_with_params}&page=1",
        "last": f"{url_with_params}&page={total_pages}"
        if total_pages > 0
        else f"{url_with_params}&page=1",
    }

    # Add prev link if not on first page
    if current_page > 1:
        links["prev"] = f"{url_with_params}&page={current_page - 1}"

    # Add next link if not on last page
    if current_page < total_pages:
        links["next"] = f"{url_with_params}&page={current_page + 1}"

    return links


def build_jsonapi_response(data: list, links: dict, meta: dict, included: list = None) -> dict:
    """Build a complete JSON:API response."""
    response = {
        "jsonapi": {
            "version": "1.1",
            "profile": [
                "https://opengeometadata.org/profile/aardvark",
                "https://opengeometadata.org/profile/ui-hints",
                "https://opengeometadata.org/profile/mcp/search",
            ],
        },
        "links": links,
        "meta": meta,
        "data": data,
    }

    if included:
        response["included"] = included

    return response


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/resources/{id}")
async def get_resource(
    id: str,
    callback: Optional[str] = Query(None, description="JSONP callback name"),
):
    """Get a single resource by ID (direct SQL version)."""
    try:
        async with async_session() as session:
            query = select(items).where(items.c.id == id)
            result = await session.execute(query)
            row = result.fetchone()
            if not row:
                return JSONResponse(content={"error": "Resource not found"}, status_code=404)

            # Convert to dict and sanitize datetime objects
            resource_dict = sanitize_for_json(dict(row._mapping))

            # Process the resource using shared logic
            resource_object = await process_resource(resource_dict, session)

            # Build the response in JSON:API format
            response = {
                "jsonapi": {
                    "version": "1.1",
                    "profile": [
                        "https://opengeometadata.org/profile/aardvark",
                        "https://opengeometadata.org/profile/ui-hints",
                        "https://opengeometadata.org/profile/mcp/search",
                    ],
                },
                "links": {"self": f"https://ogm.geo4lib.app/api/v1/resources/{id}"},
                "data": resource_object,
            }

            return create_response(response, callback)
    except HTTPException:
        # Re-raise HTTP exceptions to maintain their status code
        raise
    except Exception as e:
        logger.error(f"Error getting resource {id}: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/resources/{id}/ogm")
async def get_resource_ogm(
    id: str,
    callback: Optional[str] = Query(None, description="JSONP callback name"),
):
    """Get just the OpenGeoMetadata Aardvark record for a resource by ID."""
    try:
        async with async_session() as session:
            query = select(items).where(items.c.id == id)
            result = await session.execute(query)
            row = result.fetchone()
            if not row:
                return JSONResponse(content={"error": "Resource not found"}, status_code=404)

            # Convert to dict and sanitize datetime objects
            resource_dict = sanitize_for_json(dict(row._mapping))

            # Map database column names to official Aardvark field names
            aardvark_attributes = map_to_aardvark_fields(resource_dict)

            # Return just the cleaned attributes (the Aardvark record)
            aardvark_record = clean_dict(aardvark_attributes)

            return create_response(aardvark_record, callback)
    except HTTPException:
        # Re-raise HTTP exceptions to maintain their status code
        raise
    except Exception as e:
        logger.error(f"Error getting Aardvark record for resource {id}: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/resources/{id}/viewer")
async def get_resource_viewer(
    id: str,
    embed: bool = Query(False, description="Embedded mode for iframe usage"),
):
    """Get an HTML page with the embedded OGM viewer for a specific resource."""
    try:
        # First check if the resource exists
        async with async_session() as session:
            query = select(items).where(items.c.id == id)
            result = await session.execute(query)
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Resource not found")

        # Build the record URL for the viewer
        base_url = os.getenv("APPLICATION_URL", "http://localhost:8000")
        record_url = f"{base_url}/api/v1/resources/{id}/ogm"

        # Create the HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OGM Viewer - Resource {id}</title>
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
        {".viewer-container { height: 600px; }" if embed else ""}
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

        return HTMLResponse(content=html_content)
    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without modification
        raise
    except Exception as e:
        logger.error(f"Error creating viewer page for resource {id}: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/resources/")
async def list_resources(
    page: int = Query(1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Resources per page (max 100)"),
    callback: Optional[str] = Query(None, description="JSONP callback name"),
):
    try:
        # Convert page/per_page to skip/limit for database query
        skip = (page - 1) * per_page
        limit = per_page

        async with async_session() as session:
            query = select(items).offset(skip).limit(limit)
            logger.info(f"Executing query: {query}")
            result = await session.execute(query)
            results = result.fetchall()  # Get full rows instead of scalars
            logger.info(f"Found {len(results)} resources")

            processed_resources = []
            for row in results:
                try:
                    logger.info(f"Processing resource: {row}")
                    # Convert to dict and sanitize datetime objects
                    resource_dict = sanitize_for_json(dict(row._mapping))
                    logger.info(f"Resource dict: {resource_dict}")

                    # Process the resource using shared logic
                    resource_object = await process_resource(resource_dict, session)

                    processed_resources.append(resource_object)
                    logger.info(f"Successfully processed resource {resource_dict['id']}")
                except Exception as e:
                    logger.error(f"Error processing resource: {str(e)}", exc_info=True)
                    continue

            # Get total count for pagination
            count_query = select(func.count(items.c.id))
            count_result = await session.execute(count_query)
            total_count = count_result.scalar()
            total_pages = (total_count + per_page - 1) // per_page  # Ceiling division

            # Build pagination links
            base_url = "https://ogm.geo4lib.app/api/v1/resources/"
            params = {"page": page, "per_page": per_page}
            links = build_pagination_links(base_url, page, total_pages, params)

            # Build meta information
            meta = {
                "totalCount": total_count,
                "totalPages": total_pages,
                "currentPage": page,
                "perPage": per_page,
            }

            # Build the full JSON:API response
            response = build_jsonapi_response(processed_resources, links, meta)

            logger.info(f"Returning {len(processed_resources)} processed resources")
            return create_response(response, callback)
    except Exception as e:
        logger.error(f"Error in list_resources: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
