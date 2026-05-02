import logging
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from db.models import ogm_harvest_runs, ogm_repos, ogm_resource_state

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_ogm_harvest_tables():
    """Create OpenGeoMetadata harvest/admin tables from SQLAlchemy metadata (idempotent)."""
    try:
        # Get database URL from environment and ensure it's synchronous
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:2345/btaa_ogm_api_test",
        )
        sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

        engine = create_engine(sync_database_url)
        inspector = inspect(engine)

        existing_tables = set(inspector.get_table_names())
        logger.info("Existing tables count: %s", len(existing_tables))

        tables = [ogm_repos, ogm_harvest_runs, ogm_resource_state]
        missing = [table.name for table in tables if table.name not in existing_tables]

        if not missing:
            logger.info("OGM harvest tables already exist")
            return

        for table in tables:
            table.create(engine, checkfirst=True)

        logger.info("✓ OGM harvest tables ensured: %s", ", ".join(missing))
    except Exception as e:
        logger.error("Error creating OGM harvest tables: %s", e)
        raise


if __name__ == "__main__":
    create_ogm_harvest_tables()
