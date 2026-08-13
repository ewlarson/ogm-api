from __future__ import annotations

from urllib.parse import urlparse


def _path_basename(url: str | None) -> str:
    if not url:
        return ""
    try:
        path = urlparse(url).path.rstrip("/").lower()
    except (TypeError, ValueError):
        return ""
    return path.rsplit("/", 1)[-1]


def is_iiif_manifest_url(url: str | None) -> bool:
    """Return True for an actual IIIF Presentation manifest path.

    Matching the final path component avoids treating OGM package metadata such
    as ``dataset_manifest.json`` as a IIIF Presentation manifest.
    """
    basename = _path_basename(url)
    if basename == "manifest" or (basename.startswith("manifest") and basename.endswith(".json")):
        return True
    return isinstance(url, str) and "/cgi/i/image/api/" in url.lower()


def is_iiif_info_url(url: str | None) -> bool:
    """Return True for a IIIF Image API info document path."""
    return _path_basename(url) == "info.json"
