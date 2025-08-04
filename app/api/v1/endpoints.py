import logging
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select


def format_file_size(size_str: Optional[str]) -> Optional[str]:
    """Convert file size string to human-readable format."""
    if not size_str:
        return None
    
    try:
        # Try to parse as bytes
        size_bytes = int(size_str)
    except (ValueError, TypeError):
        return size_str
    
    # Convert to human readable format
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def clean_dict(data: dict) -> dict:
    """Remove null and empty entries from a dictionary recursively."""
    if not isinstance(data, dict):
        return data
    
    cleaned = {}
    for key, value in data.items():
        if value is None:
            continue
        elif isinstance(value, dict):
            cleaned_value = clean_dict(value)
            if cleaned_value:  # Only include if not empty after cleaning
                cleaned[key] = cleaned_value
        elif isinstance(value, list):
            if value:  # Only include non-empty lists
                cleaned[key] = value
        elif isinstance(value, str):
            if value.strip():  # Only include non-empty strings
                cleaned[key] = value
        else:
            # Include all other non-None values
            cleaned[key] = value
    
    return cleaned


async def process_resource(resource_dict: dict, session: AsyncSession) -> dict:
    """Process a single resource and return the JSON:API formatted object."""
    # Add citation
    from app.services.citation_service import CitationService
    citation_service = CitationService(resource_dict)
    citation = citation_service.get_citation()

    # Add download options
    download_service = DownloadService(resource_dict)
    downloads = download_service.get_download_options()

    # Add viewer attributes
    viewer_service = ViewerService(resource_dict)
    viewer_attributes = viewer_service.get_viewer_attributes()

    # Add relationships
    from app.services.relationship_service import RelationshipService
    relationship_service = RelationshipService()
    relationships = await relationship_service.get_resource_relationships(resource_dict["id"])

    # Add summaries
    summaries_query = text("""
        SELECT * FROM item_ai_enrichments 
        WHERE item_id = :resource_id 
        ORDER BY created_at DESC
    """)
    summaries_result = await session.execute(summaries_query, {"resource_id": resource_dict["id"]})
    summaries = summaries_result.fetchall()
    summaries = [sanitize_for_json(dict(summary)) for summary in summaries]

    # Add Allmaps data
    logger.info(f"Processing resource data: {resource_dict}")
    allmaps_service = AllmapsService({"id": resource_dict["id"], "attributes": resource_dict})
    allmaps_attributes = await allmaps_service.get_allmaps_attributes(session)
    logger.info(f"Got Allmaps attributes: {allmaps_attributes}")

    # Build the resource object in JSON:API format
    resource_object = {
        "type": "resource",
        "id": str(resource_dict["id"]),
        "attributes": clean_dict(resource_dict),
        "meta": clean_dict({
            "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
            "@type": "AardvarkRecord",
            "geometry": {
                "locn_geometry": resource_dict.get("locn_geometry"),
                "dcat_bbox": resource_dict.get("dcat_bbox"),
                "dcat_centroid": resource_dict.get("dcat_centroid")
            },
            "human_readable": {
                "file_size": format_file_size(resource_dict.get("gbl_filesize_s"))
            },
            "ui": {
                "allmaps": allmaps_attributes,
                "citation": citation,
                "downloads": downloads,
                "relationships": relationships,
                "summaries": summaries,
                "viewer": {
                    "protocol": viewer_attributes.get("protocol"),
                    "endpoint": viewer_attributes.get("endpoint"),
                    "geometry": viewer_attributes.get("geometry")
                }
            }
        })
    }
    
    return resource_object

from app.api.v1.utils import (
    add_thumbnail_url,
    create_response,
    sanitize_for_json,
)
from app.services.allmaps_service import AllmapsService
from app.services.cache_service import (
    cached_endpoint,
)
from app.services.download_service import DownloadService
from app.services.image_service import ImageService
from app.services.search_service import SearchService
from app.services.viewer_service import ViewerService
from db.config import DATABASE_URL
from db.models import items

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

logger = logging.getLogger(__name__)

# Create async engine and session
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

base_url = os.getenv("APPLICATION_URL", "http://localhost:8000/api/v1/")

# Cache TTL configuration in seconds
ITEM_CACHE_TTL = int(os.getenv("ITEM_CACHE_TTL", 86400))  # 24 hours
SEARCH_CACHE_TTL = int(os.getenv("SEARCH_CACHE_TTL", 3600))  # 1 hour
SUGGEST_CACHE_TTL = int(os.getenv("SUGGEST_CACHE_TTL", 7200))  # 2 hours
LIST_CACHE_TTL = int(os.getenv("LIST_CACHE_TTL", 43200))  # 12 hours


@router.get("")
async def api_root():
    """Return JSON-LD service document."""
    return JSONResponse(
        content={
            "@context": "https://opengeometadata.org/ns/service-context.jsonld",
            "id": "https://ogm.geo4lib.app/api/v1/service",
            "api": "OpenGeoMetadata API",
            "version": "0.1.0",
            "description": "A REST API for accessing geospatial metadata from the OpenGeoMetadata community.",
            "type": "Service",
            "label": "OGM API Service Document",
            "endpoints": {
                "resources": "/resources/{id}",
                "search": "/search{?q,page,per_page,sort,callback}",
                "suggestions": "/suggest{?q,callback}",
                "validate": "/validate"
            }
        }
    )


@router.get("/resources/{id}")
@cached_endpoint(ttl=ITEM_CACHE_TTL)
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
                        "https://opengeometadata.org/profile/mcp/search"
                    ]
                },
                "links": {
                    "self": f"https://ogm.geo4lib.app/api/v1/resources/{id}"
                },
                "data": resource_object
            }

            return create_response(response, callback)
    except HTTPException:
        # Re-raise HTTP exceptions to maintain their status code
        raise
    except Exception as e:
        logger.error(f"Error getting resource {id}: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/resources/")
@cached_endpoint(ttl=LIST_CACHE_TTL)
async def list_resources(
    skip: int = 0,
    limit: int = 10,
    callback: Optional[str] = Query(None, description="JSONP callback name"),
):
    try:
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

            # Build the full JSON:API response
            response = {
                "jsonapi": {
                    "version": "1.1",
                    "profile": [
                        "https://opengeometadata.org/profile/aardvark",
                        "https://opengeometadata.org/profile/ui-hints",
                        "https://opengeometadata.org/profile/mcp/search"
                    ]
                },
                "links": {
                    "self": f"https://ogm.geo4lib.app/api/v1/resources/?skip={skip}&limit={limit}"
                },
                "data": processed_resources
            }

            logger.info(f"Returning {len(processed_resources)} processed resources")
            return create_response(response, callback)
    except Exception as e:
        logger.error(f"Error in list_resources: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/search")
@cached_endpoint(ttl=SEARCH_CACHE_TTL)
async def search(
    request: Request,
    q: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, description="Page number"),
    per_page: int = Query(10, description="Resources per page"),
    sort: Optional[str] = Query(
        None, description="Sort option (relevance, year_desc, year_asc, title_asc, title_desc)"
    ),
    callback: Optional[str] = Query(None, description="JSONP callback name"),
):
    """Search resources."""
    try:
        search_service = SearchService()
        results = await search_service.search(
            q=q,
            page=page,
            limit=per_page,
            sort=sort,
            request_query_params=str(request.query_params),
            callback=callback,
        )

        # Sanitize the results for JSON serialization
        results = sanitize_for_json(results)

        # Create the response
        response = create_response(results, callback)

        # Return the response
        return response
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/suggest")
@cached_endpoint(ttl=SUGGEST_CACHE_TTL)
async def suggest(
    q: str = Query(..., description="Search query for suggestions"),
    callback: Optional[str] = Query(None, description="JSONP callback name"),
):
    """Get search suggestions."""
    try:
        search_service = SearchService()
        suggestions = await search_service.suggest(q)
        return create_response(suggestions, callback)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/thumbnails/{image_hash}")
async def get_thumbnail(image_hash: str):
    """Serve a cached thumbnail image."""
    try:
        # Create service without resource (we only need cache access)
        image_service = ImageService({})
        image_data = await image_service.get_cached_image(image_hash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not image_data:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(
        content=image_data,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000"},  # Cache for 1 year
    )
    