from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

ACCESS_RIGHTS_KEYS = (
    "dct_accessRights_s",
    "dct_accessrights_s",
)


def resource_access_rights(metadata: Mapping[str, Any] | None) -> str | None:
    """Return a normalized access-rights value from canonical or legacy field names."""
    if not metadata:
        return None

    for key in ACCESS_RIGHTS_KEYS:
        value = metadata.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            value = next((item for item in value if item is not None), None)
        if value is None:
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return None


def is_restricted_resource(metadata: Mapping[str, Any] | None) -> bool:
    """Return True when a resource is explicitly marked Restricted."""
    access_rights = resource_access_rights(metadata)
    return bool(access_rights and access_rights.casefold() == "restricted")
