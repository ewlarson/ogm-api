import hashlib
import json
from unittest.mock import MagicMock, patch

from app.services.image_service import REMOTE_THUMBNAIL_PREFIX, ImageService

RESOURCE_ID = "unr-74479f22-0e6b-4c13-b376-0195a7461525"
INFO_URL = f"https://s3.amazonaws.com/ogm-metadata-studio/uploads/{RESOURCE_ID}/iiif/info.json"
THUMBNAIL_URL = (
    f"https://s3.amazonaws.com/ogm-metadata-studio/uploads/{RESOURCE_ID}/thumbnail/thumbnail.jpg"
)
DATASET_MANIFEST_URL = (
    f"https://s3.amazonaws.com/ogm-metadata-studio/uploads/{RESOURCE_ID}/dataset_manifest.json"
)
LEVEL_ZERO_INFO = {
    "@context": "http://iiif.io/api/image/2/context.json",
    "@id": INFO_URL.removesuffix("/info.json"),
    "protocol": "http://iiif.io/api/image",
    "width": 7392,
    "height": 6270,
    "profile": ["http://iiif.io/api/image/2/level0.json"],
    "sizes": [
        {"width": 7392, "height": 6270},
        {"width": 3696, "height": 3135},
        {"width": 1848, "height": 1568},
        {"width": 924, "height": 784},
    ],
}


def test_explicit_iiif_info_source_is_preserved_for_capability_resolution():
    service = ImageService({"id": RESOURCE_ID})

    assert service._get_thumbnail_source_url({"http://iiif.io/api/image": INFO_URL}) == INFO_URL


def test_dataset_manifest_is_not_selected_ahead_of_published_thumbnail():
    service = ImageService({"id": RESOURCE_ID})
    references = {
        "https://opengeometadata.org/reference/dataset-manifest": DATASET_MANIFEST_URL,
        "http://schema.org/thumbnailUrl": THUMBNAIL_URL,
    }

    assert service._get_thumbnail_source_url(references) == THUMBNAIL_URL
    assert service._is_manifest_url(DATASET_MANIFEST_URL) is False


def test_level_zero_info_selects_closest_advertised_static_size():
    service = ImageService({"id": RESOURCE_ID})

    assert service._extract_thumbnail_from_iiif_info_json(LEVEL_ZERO_INFO, INFO_URL) == (
        INFO_URL.removesuffix("/info.json") + "/full/924,/0/default.jpg"
    )


def test_level_one_info_keeps_bounded_box_request():
    service = ImageService({"id": RESOURCE_ID})
    info = {
        "@id": INFO_URL.removesuffix("/info.json"),
        "profile": ["http://iiif.io/api/image/2/level1.json"],
    }

    assert service._extract_thumbnail_from_iiif_info_json(info, INFO_URL) == (
        INFO_URL.removesuffix("/info.json") + "/full/!800,800/0/default.jpg"
    )


def test_level_zero_hash_uses_resolved_advertised_size():
    service = ImageService({"id": RESOURCE_ID})
    service.cache = MagicMock()
    service.cache.get.return_value = json.dumps(LEVEL_ZERO_INFO)
    resolved_url = INFO_URL.removesuffix("/info.json") + "/full/924,/0/default.jpg"

    assert (
        service.thumbnail_image_hash_for_source_sync(INFO_URL)
        == hashlib.sha256((REMOTE_THUMBNAIL_PREFIX + resolved_url).encode()).hexdigest()
    )


def test_get_iiif_image_thumbnail_reads_info_document():
    service = ImageService({"id": RESOURCE_ID})
    with patch.object(service, "_get_manifest", return_value=LEVEL_ZERO_INFO) as mock_get:
        assert service.get_iiif_image_thumbnail(INFO_URL) == (
            INFO_URL.removesuffix("/info.json") + "/full/924,/0/default.jpg"
        )
    mock_get.assert_called_once_with(INFO_URL)
