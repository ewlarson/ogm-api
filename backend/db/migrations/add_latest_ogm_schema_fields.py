import logging
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_latest_ogm_schema_fields():
    """
    Add latest OGM schema compatibility fields to the resources table.

    This migration is idempotent and safe to re-run.
    """
    try:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:2345/opengeometadata_api",
        )
        sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

        engine = create_engine(sync_database_url)
        inspector = inspect(engine)

        if not inspector.has_table("resources"):
            logger.error("Resources table does not exist. Cannot add latest OGM fields.")
            return

        # Field names/types requested for latest OGM schema support.
        # Mixed-case names are quoted to preserve exact column casing.
        latest_ogm_fields = [
            ("b1g_adminNote_sm", "VARCHAR[]"),
            ("b1g_dateAccessioned_dt", "TIMESTAMP"),
            ("b1g_dateRetired_dt", "TIMESTAMP"),
            ("b1g_deprioritized_b", "BOOLEAN"),
            ("b1g_harvestWorkflow_s", "VARCHAR"),
            ("b1g_isHarvested_b", "BOOLEAN"),
            ("b1g_lastHarvested_dt", "TIMESTAMP"),
            ("b1g_dct_provenance_sm", "VARCHAR[]"),
            ("b1g_dcat_spatialResolutionInMeters_s", "VARCHAR"),
            ("b1g_websitePlatform_s", "VARCHAR"),
        ]

        with engine.connect() as conn:
            for field_name, field_type in latest_ogm_fields:
                try:
                    conn.execute(
                        text(f'ALTER TABLE resources ADD COLUMN "{field_name}" {field_type}')
                    )
                    conn.commit()
                    logger.info(f"Added column {field_name} to resources table")
                except Exception as e:
                    conn.rollback()
                    msg = str(e).lower()
                    if "already exists" in msg or "duplicate column" in msg:
                        logger.info(f"Column {field_name} already exists in resources table")
                    else:
                        logger.warning(f"Could not add column {field_name}: {e}")

            logger.info("Successfully added latest OGM schema fields.")

    except Exception as e:
        logger.error(f"Error adding latest OGM schema fields: {e}")
        raise


if __name__ == "__main__":
    add_latest_ogm_schema_fields()
