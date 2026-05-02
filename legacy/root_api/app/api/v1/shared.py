import functools
import os
from enum import Enum
from typing import Callable

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Lazy engine and session creation
_engine = None
_async_session = None

# Test isolation support
_test_session_factory = None


def set_test_session_factory(factory):
    """Set a test session factory for isolation."""
    global _test_session_factory
    _test_session_factory = factory


def clear_test_session_factory():
    """Clear the test session factory."""
    global _test_session_factory
    _test_session_factory = None


def get_engine():
    """Get the async engine, creating it if necessary."""
    global _engine
    if _engine is None:
        DATABASE_URL = os.getenv("DATABASE_URL")
        _engine = create_async_engine(DATABASE_URL)
    return _engine


def get_async_session():
    """Get the async session factory, creating it if necessary."""
    global _async_session, _test_session_factory

    # If we have a test session factory, use it
    if _test_session_factory is not None:
        return _test_session_factory

    if _async_session is None:
        engine = get_engine()
        _async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session


# For backward compatibility - this should be used as a context manager
def async_session():
    """Get an async session context manager."""
    session_factory = get_async_session()
    return session_factory()


class SortOption(str, Enum):
    RELEVANCE = "relevance"
    YEAR_NEWEST = "year_desc"
    YEAR_OLDEST = "year_asc"
    TITLE_AZ = "title_asc"
    TITLE_ZA = "title_desc"


SORT_MAPPINGS = {
    SortOption.RELEVANCE: [{"_score": "desc"}],
    SortOption.YEAR_NEWEST: [{"gbl_indexyear_im": "desc"}, {"_score": "desc"}],
    SortOption.YEAR_OLDEST: [{"gbl_indexyear_im": "asc"}, {"_score": "desc"}],
    SortOption.TITLE_AZ: [{"dct_title_s.keyword": "asc"}, {"_score": "desc"}],
    SortOption.TITLE_ZA: [{"dct_title_s.keyword": "desc"}, {"_score": "desc"}],
}

# Cache TTL constants
SEARCH_CACHE_TTL = 300  # 5 minutes
SUGGEST_CACHE_TTL = 600  # 10 minutes


def cached_endpoint(ttl: int = 300):
    """Decorator to cache endpoint responses."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # For now, just call the function directly
            # In a real implementation, this would check cache first
            return await func(*args, **kwargs)

        return wrapper

    return decorator
