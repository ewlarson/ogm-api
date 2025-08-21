import os
import asyncio
import logging
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect

from db.config import DATABASE_URL
from db.migrations.create_items_table import create_items_table
from db.migrations.create_gazetteer_tables import create_gazetteer_tables
from db.migrations.create_item_relationships import create_relationships_table
from db.migrations.create_fast_embeddings import create_fast_embeddings_table
from db.migrations.create_ai_enrichments import create_ai_enrichments_table
from db.migrations.add_enrichment_type import add_enrichment_type_column
from db.migrations.add_fast_gazetteer import add_fast_gazetteer
from db.migrations.update_fast_gazetteer import update_fast_gazetteer
from db.migrations.rename_ai_enrichments import rename_ai_enrichments_table
from db.migrations.rename_document_id_to_item_id import rename_document_id_to_item_id
from db.migrations.create_item_allmaps_table import create_item_allmaps_table

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migrations():
    """Run all database migrations."""
    logger.info("Running database migrations...")
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL)
    
    try:
        # Create items table
        logger.info("Creating items table...")
        create_items_table()
        
        # Create gazetteer tables
        logger.info("Creating gazetteer tables...")
        create_gazetteer_tables()
        
        # Create item relationships table
        logger.info("Creating item relationships table...")
        create_relationships_table()
        
        # Create FAST embeddings table
        logger.info("Creating FAST embeddings table...")
        create_fast_embeddings_table()
        
        # Create AI enrichments table
        logger.info("Creating AI enrichments table...")
        create_ai_enrichments_table()
        
        # Add enrichment type column
        logger.info("Adding enrichment type column...")
        add_enrichment_type_column()
        
        # Add FAST gazetteer
        logger.info("Adding FAST gazetteer...")
        add_fast_gazetteer()
        
        # Update FAST gazetteer
        logger.info("Updating FAST gazetteer...")
        update_fast_gazetteer()
        
        # Rename AI enrichments table
        logger.info("Renaming AI enrichments table...")
        rename_ai_enrichments_table()
        
        # Rename document_id to item_id in item_ai_enrichments table
        logger.info("Renaming document_id to item_id in item_ai_enrichments table...")
        rename_document_id_to_item_id()
        
        # Create item_allmaps table
        logger.info("Creating item_allmaps table...")
        await create_item_allmaps_table()
        
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run migrations
    asyncio.run(run_migrations()) 