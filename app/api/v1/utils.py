import json
import logging
from typing import Any, Dict, List, Optional

from fastapi.responses import JSONResponse

from app.api.v1.jsonp import JSONPResponse

logger = logging.getLogger(__name__)


def sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize an object for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif hasattr(obj, "isoformat"):  # Handle datetime objects
        return obj.isoformat()
    elif hasattr(obj, "__dict__"):  # Handle objects with __dict__
        return sanitize_for_json(obj.__dict__)
    return obj


def create_response(
    content: Dict | JSONResponse, callback: Optional[str] = None, status_code: int = 200
) -> JSONResponse:
    """Create either a JSON or JSONP response based on callback parameter."""
    # If content is already a JSONResponse, return it as is
    if isinstance(content, JSONResponse):
        return content

    # Sanitize content before serialization
    sanitized_content = sanitize_for_json(content)

    if callback:
        return JSONPResponse(content=sanitized_content, callback=callback, status_code=status_code)
    return JSONResponse(content=sanitized_content, status_code=status_code)


def add_thumbnail_url(item: Dict) -> Dict:
    """Add the ui_thumbnail_url to the item attributes."""
    # Ensure 'attributes' key exists
    if "attributes" not in item:
        item["attributes"] = {}

    from app.services.image_service import ImageService

    image_service = ImageService(item)
    thumbnail_url = image_service.get_thumbnail_url()
    item["attributes"]["ui_thumbnail_url"] = thumbnail_url
    return item


def add_citations(item: Dict) -> Dict:
    """Add citations to an item."""
    # Ensure 'attributes' key exists
    if "attributes" not in item:
        item["attributes"] = {}

    try:
        from app.services.citation_service import CitationService

        citation_service = CitationService(item)
        item["attributes"]["ui_citation"] = citation_service.get_citation()
    except Exception as e:
        logger.error(f"Failed to generate citation: {str(e)}")
        item["attributes"]["ui_citation"] = "Citation unavailable"
    return item


def add_ui_attributes(item: Dict) -> Dict:
    """Add UI attributes to an item."""
    # Parse references if needed
    if isinstance(item.get("dct_references_s"), str):
        try:
            item["dct_references_s"] = json.loads(item["dct_references_s"])
        except json.JSONDecodeError:
            item["dct_references_s"] = {}

    # Create services
    from app.services.citation_service import CitationService
    from app.services.download_service import DownloadService
    from app.services.image_service import ImageService
    from app.services.viewer_service import create_viewer_attributes

    image_service = ImageService(item)
    citation_service = CitationService(item)
    download_service = DownloadService(item)

    # Add viewer attributes
    item.update(create_viewer_attributes(item))

    # Add thumbnail URL if available
    if thumbnail_url := image_service.get_thumbnail_url():
        item["ui_thumbnail_url"] = thumbnail_url

    # Add citation
    item["ui_citation"] = citation_service.get_citation()

    # Add download links
    item["ui_download_links"] = download_service.get_download_links()

    return item


async def process_resource(resource_dict: Dict, session) -> Dict:
    """Process a single resource and return the JSON:API formatted object."""
    try:
        # Add citation
        from app.services.citation_service import CitationService

        citation_service = CitationService(resource_dict)
        citation = citation_service.get_citation()

        # Add download options
        from app.services.download_service import DownloadService
        download_service = DownloadService(resource_dict)
        downloads = download_service.get_download_options()

        # Add viewer attributes
        from app.services.viewer_service import ViewerService
        viewer_service = ViewerService(resource_dict)
        viewer_attributes = viewer_service.get_viewer_attributes()

        # Add thumbnail URL
        from app.services.image_service import ImageService
        image_service = ImageService(resource_dict)
        thumbnail_url = image_service.get_thumbnail_url()

        # Add relationships
        from app.services.relationship_service import RelationshipService

        relationship_service = RelationshipService()
        relationships = await relationship_service.get_resource_relationships(resource_dict["id"])

        # Add summaries
        from sqlalchemy import text
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
        from app.services.allmaps_service import AllmapsService
        allmaps_service = AllmapsService({"id": resource_dict["id"], "attributes": resource_dict})
        allmaps_attributes = await allmaps_service.get_allmaps_attributes(session)
        logger.info(f"Got Allmaps attributes: {allmaps_attributes}")

        # Map database column names to official Aardvark field names
        from app.api.v1.endpoint_modules.utils import clean_dict, map_to_aardvark_fields, format_file_size
        aardvark_attributes = map_to_aardvark_fields(resource_dict)

        # Build the resource object in JSON:API format
        resource_object = {
            "type": "resource",
            "id": str(resource_dict["id"]),
            "attributes": clean_dict(aardvark_attributes),
            "meta": clean_dict(
                {
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
                            "geometry": viewer_attributes.get("geometry"),
                        },
                    },
                }
            ),
        }

        return resource_object
    except Exception as e:
        logger.error(f"Error processing resource: {str(e)}", exc_info=True)
        # Return a minimal resource object if processing fails
        return {"type": "resource", "id": resource_dict.get("id"), "attributes": resource_dict}


def build_jsonapi_response(
    data: List[Dict], links: Dict = None, meta: Dict = None, included: List = None
) -> Dict:
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


def build_pagination_links(
    base_url: str, current_page: int, total_pages: int, params: Dict = None
) -> Dict:
    """Build JSON:API pagination links."""
    links = {}

    # Build query string from params
    query_parts = []
    if params:
        for key, value in params.items():
            if value is not None:
                query_parts.append(f"{key}={value}")

    query_string = "&".join(query_parts)
    separator = "&" if query_string else ""

    # Self link (current page)
    links["self"] = f"{base_url}?page={current_page}{separator}{query_string}"

    # First page
    if current_page > 1:
        links["first"] = f"{base_url}?page=1{separator}{query_string}"

    # Previous page
    if current_page > 1:
        links["prev"] = f"{base_url}?page={current_page - 1}{separator}{query_string}"

    # Next page
    if current_page < total_pages:
        links["next"] = f"{base_url}?page={current_page + 1}{separator}{query_string}"

    # Last page
    if current_page < total_pages:
        links["last"] = f"{base_url}?page={total_pages}{separator}{query_string}"

    return links
