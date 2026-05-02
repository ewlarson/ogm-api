import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from app.api.v1.endpoints import router as public_router
from app.api.v1.shared import get_engine
from app.elasticsearch import close_elasticsearch, init_elasticsearch

# Load environment variables from .env file
load_dotenv()

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log"),
    ],
)
logger = logging.getLogger(__name__)

# Get CORS origins from environment variable - allow all origins for maximum permissiveness
cors_origins = ["*"]  # Allow all origins

# Create security scheme
security = HTTPBasic()


class PermissiveSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to set permissive security headers for data reuse and embedding."""

    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)

        # Set permissive Referrer Policy for data reuse
        response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"

        # Set permissive Content Security Policy for embedding
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: *; frame-ancestors *;"
        )

        # Allow embedding in frames
        response.headers["X-Frame-Options"] = "ALLOWALL"

        # Remove any restrictive headers that might interfere with embedding
        if "X-Content-Type-Options" in response.headers:
            del response.headers["X-Content-Type-Options"]

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    # Startup
    try:
        engine = get_engine()
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

    try:
        await init_elasticsearch()
        logger.info("Connected to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        # Don't raise the exception, allow the app to start without Elasticsearch

    yield

    # Shutdown
    try:
        engine.dispose()
        logger.info("Disconnected from database")
    except Exception as e:
        logger.error(f"Error disconnecting from database: {str(e)}")

    try:
        await close_elasticsearch()
        logger.info("Disconnected from Elasticsearch")
    except Exception as e:
        logger.error(f"Error disconnecting from Elasticsearch: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="OpenGeoMetadata API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware - very permissive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Add permissive security headers middleware
app.add_middleware(PermissiveSecurityHeadersMiddleware)

# Include routers
app.include_router(public_router, prefix="/api/v1")


# Add redirect routes
@app.get("/")
async def redirect_root():
    """Redirect root path to API docs."""
    return RedirectResponse(url="/api/docs", status_code=302)


@app.get("/api")
async def redirect_api():
    """Redirect /api path to API docs."""
    return RedirectResponse(url="/api/docs", status_code=302)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the application."""
    logger.error(f"Global exception handler caught: {str(exc)}", exc_info=True)

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred",
            "error": str(exc),
        },
    )


# Add uvicorn configuration for running the application directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
