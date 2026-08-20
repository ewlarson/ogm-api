"""Project identity shared by the API's public interfaces."""

import os
from importlib import metadata
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.11+ provides tomllib
    import tomli as tomllib

API_NAME = "OpenGeoMetadata API"
API_SLUG = "opengeometadata-api"
API_DESCRIPTION = (
    "A RESTful API for searching, harvesting, and delivering community-maintained "
    "OpenGeoMetadata Aardvark records."
)
DISTRIBUTION_NAME = "opengeometadata-api"


def _source_version() -> str | None:
    """Read the source-tree version when running from a checkout or container image."""
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as pyproject:
            return tomllib.load(pyproject)["project"]["version"]
    except (KeyError, OSError, tomllib.TOMLDecodeError):
        return None


def get_api_version() -> str:
    """Return the deployment override, source version, or installed package version."""
    if configured_version := os.getenv("OGM_API_VERSION"):
        return configured_version
    if source_version := _source_version():
        return source_version
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        return "0.0.0+unknown"


API_VERSION = get_api_version()
