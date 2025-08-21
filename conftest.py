import os
import pytest
import pytest_asyncio
import warnings
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse
import asyncio
import atexit

# Load test environment variables
load_dotenv(".env.test", override=True)

# Get test database URL from environment or use default
# ALWAYS ensure we use a test database, never production
DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:2345/btaa_ogm_api_test"
)

# Safety check: If someone passes production DATABASE_URL, convert it to test
if "DATABASE_URL" in os.environ and "btaa_ogm_api_test" not in os.environ.get("DATABASE_URL", ""):
    production_url = os.environ["DATABASE_URL"]
    # Convert production URL to test URL by replacing database name
    if "btaa_ogm_api" in production_url and "btaa_ogm_api_test" not in production_url:
        DATABASE_URL = production_url.replace("btaa_ogm_api", "btaa_ogm_api_test")
        print(f"WARNING: Converted production DATABASE_URL to test database: {DATABASE_URL}")
    else:
        DATABASE_URL = "postgresql://postgres:postgres@localhost:2345/btaa_ogm_api_test"
        print(f"WARNING: Using default test database URL: {DATABASE_URL}")

# Parse database URL
parsed = urlparse(DATABASE_URL)
db_name = parsed.path[1:]  # Remove leading '/'
db_user = parsed.username
db_password = parsed.password
db_host = parsed.hostname
db_port = parsed.port

# Final safety check: NEVER allow production database in tests
if db_name == "btaa_ogm_api":
    raise ValueError(
        f"CRITICAL ERROR: Tests attempted to use production database '{db_name}'! "
        f"Tests must only use test databases. Current DATABASE_URL: {DATABASE_URL}"
    )

# Create test database engine
engine = create_engine(DATABASE_URL)

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("addopts", "--cov=app --cov-report=term-missing --cov-report=html")
    
    # Set test environment variables
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["ELASTICSEARCH_INDEX"] = "btaa_ogm_api_test"
    os.environ["LOG_PATH"] = "./test_logs"
    os.environ["ENDPOINT_CACHE"] = "true"
    
    # Filter out pytesseract deprecation warnings
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=".*pkgutil.find_loader.*",
        module="pytesseract.*"
    )

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Set up test database tables before running tests."""
    from db.migrations.create_ai_enrichments import create_ai_enrichments_table
    from db.migrations.create_gazetteer_tables import create_gazetteer_tables
    from db.migrations.create_item_relationships import create_relationships_table
    from db.migrations.add_enrichment_type import add_enrichment_type_column
    
    # Connect to default database to create test database
    conn = psycopg2.connect(
        dbname='postgres',
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    conn.autocommit = True  # Required for database creation/deletion
    
    try:
        with conn.cursor() as cur:
            # Drop database if it exists
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            # Create database
            cur.execute(f'CREATE DATABASE "{db_name}"')
    except Exception as e:
        print(f"Error creating database: {e}")
        raise
    finally:
        conn.close()

    # Create tables in the correct order
    try:
        # Create base tables
        create_ai_enrichments_table()
        create_gazetteer_tables()
        create_relationships_table()
        
        # Add any additional columns or modifications
        add_enrichment_type_column()
        
        print("All database migrations completed successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

    yield

    # Cleanup after all tests are done
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Terminate all connections to the test database
            cur.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid()
            """)
            
            # Drop the test database
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
    except Exception as e:
        print(f"Error cleaning up database: {e}")
        raise
    finally:
        conn.close()
