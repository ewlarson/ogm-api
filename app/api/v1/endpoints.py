import logging
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, text
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


def map_to_aardvark_fields(resource_dict: dict) -> dict:
    """Map database column names to official Aardvark field names."""
    # Mapping from database column names to official Aardvark field names
    field_mapping = {
        # Most fields already match, but some need mapping
        "dct_accessrights_s": "dct_accessRights_s",  # Note the capital R
        "pcdm_memberof_sm": "pcdm_memberOf_sm",  # Note the capital O
        "gbl_displaynote_sm": "gbl_displayNote_sm",  # Note the capital N
        "gbl_resourceclass_sm": "gbl_resourceClass_sm",  # Note the capital C
        "gbl_resourcetype_sm": "gbl_resourceType_sm",  # Note the capital T
        "gbl_indexyear_im": "gbl_indexYear_im",  # Note the capital Y
        "gbl_daterange_drsim": "gbl_dateRange_drsim",  # Note the capital R
        "dct_ispartof_sm": "dct_isPartOf_sm",  # Note the capital P
        "dct_isversionof_sm": "dct_isVersionOf_sm",  # Note the capital V
        "dct_isreplacedby_sm": "dct_isReplacedBy_sm",  # Note the capital R
        "dct_rightsholder_sm": "dct_rightsHolder_sm",  # Note the capital H
        "gbl_mdmodified_dt": "gbl_mdModified_dt",  # Note the capital M
        "gbl_mdversion_s": "gbl_mdVersion_s",  # Note the capital V
        "gbl_filesize_s": "gbl_fileSize_s",  # Note the capital S
        "gbl_wxsidentifier_s": "gbl_wxsIdentifier_s",  # Note the capital I
    }
    
    mapped_dict = {}
    for key, value in resource_dict.items():
        # Use the mapped name if it exists, otherwise use the original key
        aardvark_key = field_mapping.get(key, key)
        mapped_dict[aardvark_key] = value
    
    return mapped_dict


def build_pagination_links(base_url: str, current_page: int, total_pages: int, params: dict = None) -> dict:
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
        "last": f"{url_with_params}&page={total_pages}" if total_pages > 0 else f"{url_with_params}&page=1"
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
                "https://opengeometadata.org/profile/mcp/search"
            ]
        },
        "links": links,
        "meta": meta,
        "data": data
    }
    
    if included:
        response["included"] = included
    
    return response


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

    # Add thumbnail URL
    image_service = ImageService(resource_dict)
    thumbnail_url = image_service.get_thumbnail_url()

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

    # Map database column names to official Aardvark field names
    aardvark_attributes = map_to_aardvark_fields(resource_dict)
    
    # Build the resource object in JSON:API format
    resource_object = {
        "type": "resource",
        "id": str(resource_dict["id"]),
        "attributes": clean_dict(aardvark_attributes),
        "meta": clean_dict({
            "@context": "https://static.opengeometadata.org/contexts/aardvark-1.0.jsonld",
            "@type": "AardvarkRecord",
            "human_readable": {
                "file_size": format_file_size(resource_dict.get("gbl_filesize_s"))
            },
            "ui": {
                "allmaps": allmaps_attributes,
                "citation": citation,
                "downloads": downloads,
                "relationships": relationships,
                "summaries": summaries,
                "thumbnail_url": thumbnail_url,
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


@router.get("/resources/{id}/ogm")
@cached_endpoint(ttl=ITEM_CACHE_TTL)
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


@router.get("/resources/")
@cached_endpoint(ttl=LIST_CACHE_TTL)
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
                "perPage": per_page
            }
            
            # Build the full JSON:API response
            response = build_jsonapi_response(processed_resources, links, meta)

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
    per_page: int = Query(10, ge=1, le=100, description="Resources per page (max 100)"),
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

        # Extract pagination info from existing meta
        pages_info = results.get("meta", {}).get("pages", {})
        total_count = pages_info.get("total_count", 0)
        total_pages = pages_info.get("total_pages", 0)
        current_page = pages_info.get("current_page", 1)

        # Process each resource to ensure consistent structure
        processed_resources = []
        async with async_session() as session:
            for item in results.get("data", []):
                try:
                    # Extract the resource data from the search result
                    resource_dict = item.get("attributes", {})
                    if not resource_dict:
                        continue
                    
                    # Process the resource using the same logic as other endpoints
                    resource_object = await process_resource(resource_dict, session)
                    processed_resources.append(resource_object)
                except Exception as e:
                    logger.error(f"Error processing search result: {str(e)}", exc_info=True)
                    continue

        # Build JSON:API pagination links
        base_url = "https://ogm.geo4lib.app/api/v1/search"
        params = {}
        if q:
            params["q"] = q
        if sort:
            params["sort"] = sort
        if per_page != 10:  # Only include if not default
            params["per_page"] = per_page
        
        links = build_pagination_links(base_url, current_page, total_pages, params)

        # Build meta information
        meta = {
            "totalCount": total_count,
            "totalPages": total_pages,
            "currentPage": current_page,
            "perPage": per_page,
            "query": q,
            "sort": sort,
            "query_time": results.get("query_time", {}),
            "spelling_suggestions": results.get("meta", {}).get("spelling_suggestions", [])
        }

        # Extract included data (facets/aggregations) from search results
        included = results.get("included", [])

        # Build the response with consistent structure
        response = build_jsonapi_response(processed_resources, links, meta, included)

        # Create the response
        response = create_response(response, callback)

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
    