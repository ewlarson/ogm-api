from unittest.mock import AsyncMock, patch

import pytest

from app.services.ogm_harvest.importer import OGMResourceImporter


@pytest.mark.asyncio
async def test_changed_thumbnail_ids_detects_new_and_changed_sources_only():
    existing = {
        "id": "unchanged",
        "dct_references_s": '{"http://schema.org/thumbnailUrl":"https://example/a.jpg"}',
        "b1g_image_ss": None,
        "dct_accessRights_s": "Public",
        "gbl_resourceClass_sm": ["Maps"],
        "gbl_wxsIdentifier_s": None,
        "dcat_bbox": None,
        "locn_geometry": None,
    }
    changed = {**existing, "id": "changed"}
    incoming = [
        dict(existing),
        {
            **changed,
            "dct_references_s": '{"http://schema.org/thumbnailUrl":"https://example/b.jpg"}',
        },
        {**existing, "id": "new"},
    ]

    with patch(
        "app.services.ogm_harvest.importer.database.fetch_all",
        AsyncMock(return_value=[existing, changed]),
    ):
        result = await OGMResourceImporter()._changed_thumbnail_ids(incoming)

    assert result == {"changed", "new"}


def test_thumbnail_source_signature_is_stable_for_nested_metadata():
    left = {
        "gbl_resourceClass_sm": ["Maps", "Datasets"],
        "dct_references_s": {"image": {"url": "https://example/image.jpg"}},
    }
    right = {
        "dct_references_s": {"image": {"url": "https://example/image.jpg"}},
        "gbl_resourceClass_sm": ["Maps", "Datasets"],
    }

    assert OGMResourceImporter._thumbnail_source_signature(
        left
    ) == OGMResourceImporter._thumbnail_source_signature(right)
