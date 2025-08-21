import functools
import os
from enum import Enum
from typing import Callable

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Create async engine and session
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
