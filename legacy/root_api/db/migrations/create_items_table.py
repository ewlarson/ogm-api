import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from db.config import DATABASE_URL
from db.models import items

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_items_table():
    """Create the items table."""
    try:
        # Convert async URL to sync URL for SQLAlchemy
        sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        # Create engine
        engine = create_engine(sync_url)
        inspector = inspect(engine)

        # Check if the table already exists
        if inspector.has_table("items"):
            logger.info("Table items already exists. Skipping creation.")
            return

        with engine.connect() as conn:
            # Create the table
            items.create(engine)
            logger.info("Successfully created items table.")

    except Exception as e:
        logger.error(f"Error creating items table: {e}")
        raise


if __name__ == "__main__":
    create_items_table()
