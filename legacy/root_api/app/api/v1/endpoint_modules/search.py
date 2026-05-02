import logging
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.api.v1.jsonp import create_response
from app.api.v1.shared import SEARCH_CACHE_TTL, SUGGEST_CACHE_TTL, async_session, cached_endpoint
from app.api.v1.utils import build_jsonapi_response, build_pagination_links, process_resource
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)
router = APIRouter()


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
            "spelling_suggestions": results.get("meta", {}).get("spelling_suggestions", []),
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
