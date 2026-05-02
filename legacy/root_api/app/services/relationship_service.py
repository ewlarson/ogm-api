import logging
from typing import Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RelationshipService:
    """Service for handling item relationships."""

    @staticmethod
    async def get_resource_relationships(resource_id: str, session: AsyncSession) -> Dict:
        """Get all relationships for a resource."""
        try:
            logger.info(f"Fetching relationships for resource: {resource_id}")

            # Get outgoing relationships (where resource is subject)
            relationships_query = text("""
                SELECT predicate, object_id, dct_title_s
                FROM item_relationships
                JOIN items 
                ON items.id = item_relationships.object_id
                WHERE subject_id = :resource_id
                ORDER BY dct_title_s ASC
            """)
            result = await session.execute(relationships_query, {"resource_id": resource_id})
            db_relationships = result.fetchall()
            logger.info(f"Found {len(db_relationships)} relationships")
            logger.info(f"Relationships: {db_relationships}")

            relationships = {}

            # Process outgoing relationships
            for rel in db_relationships:
                if rel.predicate not in relationships:
                    relationships[rel.predicate] = []
                relationships[rel.predicate].append(
                    {
                        "resource_id": rel.object_id,
                        "resource_title": rel.dct_title_s,
                        "link": f"/resources/{rel.object_id}",  # Using relative URL
                    }
                )
                logger.debug(f"Added relationship: {rel.predicate} -> {rel.object_id}")

            logger.info(f"Final relationships structure: {relationships}")
            return relationships

        except Exception as e:
            logger.error(f"Error getting relationships: {e}", exc_info=True)
            return {}
