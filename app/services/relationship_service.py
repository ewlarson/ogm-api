import logging
from typing import Dict

from db.database import database

logger = logging.getLogger(__name__)


class RelationshipService:
    """Service for handling item relationships."""

    @staticmethod
    async def get_resource_relationships(id: str) -> Dict:
        """Get all relationships for an resource."""
        try:
            logger.info(f"Fetching relationships for resource: {resource_id}")

            # Get outgoing relationships (where item is subject)
            relationships_query = """
                SELECT predicate, object_id, dct_title_s
                FROM item_relationships
                JOIN items 
                ON items.id = item_relationships.object_id
                WHERE subject_id = :id
                ORDER BY dct_title_s ASC
            """
            db_relationships = await database.fetch_all(relationships_query, {"item_id": item_id})
            logger.info(f"Found {len(db_relationships)} relationships")
            logger.info(f"Relationships: {db_relationships}")

            relationships = {}

            # Process outgoing relationships
            for rel in db_relationships:
                if rel["predicate"] not in relationships:
                    relationships[rel["predicate"]] = []
                relationships[rel["predicate"]].append(
                    {
                        "item_id": rel["object_id"],
                        "item_title": rel["dct_title_s"],
                        "link": f"/resources/{rel['object_id']}",  # Using relative URL
                    }
                )
                logger.debug(f"Added relationship: {rel['predicate']} -> {rel['object_id']}")

            logger.info(f"Final relationships structure: {relationships}")
            return relationships

        except Exception as e:
            logger.error(f"Error getting relationships: {e}", exc_info=True)
            return {}
