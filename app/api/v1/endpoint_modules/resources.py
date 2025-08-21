import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.sql import select

from app.api.v1.shared import async_session
from db.models import items

from .utils import clean_dict, format_file_size, map_to_aardvark_fields

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/resources/{id}")
async def get_resource(id: str):
    """Get a specific resource by ID."""
    try:
        async with async_session() as session:
            # Query the resource
            query = select(items).where(items.c.id == id)
            result = await session.execute(query)
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Resource not found")

            # Convert to dict and clean
            resource_dict = dict(row._mapping)

            # Clean the data
            cleaned_resource = clean_dict(resource_dict)

            # Format file size if present
            if "dct_format_s" in cleaned_resource:
                cleaned_resource["formatted_file_size"] = format_file_size(
                    cleaned_resource.get("dct_format_s")
                )

            return cleaned_resource

    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without modification
        raise
    except Exception as e:
        logger.error(f"Error getting resource {id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/resources/{id}/ogm")
async def get_resource_ogm(id: str):
    """Get a resource in OpenGeoMetadata format."""
    try:
        async with async_session() as session:
            # Query the resource
            query = select(items).where(items.c.id == id)
            result = await session.execute(query)
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Resource not found")

            # Convert to dict
            resource_dict = dict(row._mapping)

            # Clean the data
            cleaned_resource = clean_dict(resource_dict)

            # Map to Aardvark field names
            aardvark_resource = map_to_aardvark_fields(cleaned_resource)

            return aardvark_resource

    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without modification
        raise
    except Exception as e:
        logger.error(f"Error getting OGM resource {id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    access_rights: Optional[str] = Query(None, description="Filter by access rights"),
):
    """List resources with pagination and filtering."""
    try:
        async with async_session() as session:
            # Build the query
            query = select(items)

            # Add filters
            if search:
                query = query.where(
                    items.c.dct_title_s.ilike(f"%{search}%")
                    | items.c.dct_description_sm.ilike(f"%{search}%")
                )

            if resource_type:
                query = query.where(items.c.gbl_resourcetype_sm.contains([resource_type]))

            if access_rights:
                query = query.where(items.c.dct_accessrights_s == access_rights)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await session.scalar(count_query)

            # Add pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)

            # Execute query
            result = await session.execute(query)
            rows = result.fetchall()

            # Convert to list of dicts
            resources = []
            for row in rows:
                resource_dict = dict(row._mapping)
                cleaned_resource = clean_dict(resource_dict)
                resources.append(cleaned_resource)

            return {
                "resources": resources,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            }

    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without modification
        raise
    except Exception as e:
        logger.error(f"Error listing resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
