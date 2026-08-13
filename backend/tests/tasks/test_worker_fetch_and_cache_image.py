import io
from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from PIL import Image

from app.tasks.worker import (
    _looks_like_manifest_url,
    _remote_thumbnail_image_hash,
    _resolve_image_url,
    fetch_and_cache_image,
)

UNR_RESOURCE_ID = "unr-74479f22-0e6b-4c13-b376-0195a7461525"
UNR_INFO_URL = (
    f"https://s3.amazonaws.com/ogm-metadata-studio/uploads/{UNR_RESOURCE_ID}/iiif/info.json"
)
UNR_IMAGE_URL = UNR_INFO_URL.removesuffix("/info.json") + "/full/924,/0/default.jpg"
UNR_LEVEL_ZERO_INFO = {
    "@id": UNR_INFO_URL.removesuffix("/info.json"),
    "profile": ["http://iiif.io/api/image/2/level0.json"],
    "width": 7392,
    "height": 6270,
    "sizes": [
        {"width": 7392, "height": 6270},
        {"width": 3696, "height": 3135},
        {"width": 1848, "height": 1568},
        {"width": 924, "height": 784},
    ],
}


def _valid_png_bytes() -> bytes:
    img = Image.new("RGBA", (64, 64), color=(0, 128, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _large_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (4500, 4300), color=(200, 180, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _cached_image_write(mock_redis) -> tuple[str, bytes]:
    for call in mock_redis.set.call_args_list:
        key, value = call.args
        if isinstance(key, str) and key.startswith("image:"):
            return key, value

    for call in mock_redis.setex.call_args_list:
        key, _ttl, value = call.args
        if isinstance(key, str) and key.startswith("image:"):
            return key, value

    raise AssertionError("Expected thumbnail image bytes to be written to Redis")


def test_fetch_and_cache_image_records_success_and_uses_provider_throttle():
    source_url = "https://example.com/thumb.png"
    response = MagicMock()
    response.status_code = 200
    response.is_redirect = False
    response.is_permanent_redirect = False
    response.content = _valid_png_bytes()
    response.headers = {"Content-Type": "image/png"}
    response.raise_for_status = MagicMock()

    with (
        patch("app.tasks.worker._resolve_image_url", return_value=source_url),
        patch("app.tasks.worker.redis_client") as mock_redis,
        patch("app.tasks.worker.store_durable_visual_asset", return_value=True),
        patch("app.tasks.worker.store_durable_visual_asset_link", return_value=True),
        patch(
            "app.services.remote_fetch.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ),
        patch("app.tasks.worker.requests.get", return_value=response),
        patch(
            "app.tasks.worker.provider_request_slot",
            side_effect=lambda *args, **kwargs: nullcontext(MagicMock(waited_seconds=0.0)),
        ) as mock_provider_slot,
        patch("app.tasks.worker.safe_record_thumbnail_state_sync") as mock_state,
        patch("app.tasks.worker.release_thumbnail_queue_slot"),
    ):
        mock_redis.exists.return_value = False

        result = fetch_and_cache_image(source_url, "resource-1")

        assert result is True
        mock_provider_slot.assert_called_once()
        payload = mock_state.call_args.args[0]
        assert payload.state == "success"
        assert payload.source_type == "remote"
        assert payload.resource_id == "resource-1"


def test_fetch_and_cache_image_records_failure_for_invalid_content():
    source_url = "https://example.com/thumb.png"
    response = MagicMock()
    response.status_code = 200
    response.is_redirect = False
    response.is_permanent_redirect = False
    response.content = b"<html>not an image</html>"
    response.headers = {"Content-Type": "text/html"}
    response.raise_for_status = MagicMock()

    with (
        patch("app.tasks.worker._resolve_image_url", return_value=source_url),
        patch("app.tasks.worker.redis_client") as mock_redis,
        patch("app.tasks.worker.store_durable_visual_asset", return_value=True),
        patch("app.tasks.worker.store_durable_visual_asset_link", return_value=True),
        patch(
            "app.services.remote_fetch.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ),
        patch("app.tasks.worker.requests.get", return_value=response),
        patch(
            "app.tasks.worker.provider_request_slot",
            side_effect=lambda *args, **kwargs: nullcontext(MagicMock(waited_seconds=0.0)),
        ),
        patch("app.tasks.worker.safe_record_thumbnail_state_sync") as mock_state,
        patch("app.tasks.worker.release_thumbnail_queue_slot"),
    ):
        mock_redis.exists.return_value = False

        result = fetch_and_cache_image(source_url, "resource-2")

        assert result is False
        payload = mock_state.call_args.args[0]
        assert payload.state == "failure"
        assert payload.source_type == "remote"
        assert payload.resource_id == "resource-2"


def test_fetch_and_cache_image_resizes_large_remote_image_before_caching():
    source_url = "https://example.com/huge-thumb.jpg"
    response = MagicMock()
    response.status_code = 200
    response.is_redirect = False
    response.is_permanent_redirect = False
    response.content = _large_jpeg_bytes()
    response.headers = {"Content-Type": "image/jpeg"}
    response.raise_for_status = MagicMock()

    with (
        patch("app.tasks.worker._resolve_image_url", return_value=source_url),
        patch("app.tasks.worker.redis_client") as mock_redis,
        patch("app.tasks.worker.store_durable_visual_asset", return_value=True),
        patch("app.tasks.worker.store_durable_visual_asset_link", return_value=True),
        patch(
            "app.services.remote_fetch.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ),
        patch("app.tasks.worker.requests.get", return_value=response),
        patch(
            "app.tasks.worker.provider_request_slot",
            side_effect=lambda *args, **kwargs: nullcontext(MagicMock(waited_seconds=0.0)),
        ),
        patch("app.tasks.worker.safe_record_thumbnail_state_sync"),
        patch("app.tasks.worker.release_thumbnail_queue_slot"),
    ):
        mock_redis.exists.return_value = False

        result = fetch_and_cache_image(source_url, "resource-large")

        assert result is True
        image_key, cached_bytes = _cached_image_write(mock_redis)
        assert image_key == f"image:{_remote_thumbnail_image_hash(source_url)}"
        cached_image = Image.open(io.BytesIO(cached_bytes))
        assert max(cached_image.size) <= 512
        assert cached_image.format == "JPEG"
        assert len(cached_bytes) < len(response.content)


def test_worker_does_not_treat_dataset_manifest_as_iiif_manifest():
    assert not _looks_like_manifest_url(
        "https://example.com/uploads/unr-item/dataset_manifest.json"
    )


def test_worker_rejects_private_thumbnail_source_without_fetching():
    source_url = "http://127.0.0.1/private.png"

    with (
        patch("app.tasks.worker._resolve_image_url", return_value=source_url),
        patch("app.tasks.worker.requests.get") as request_get,
        patch("app.tasks.worker.safe_record_thumbnail_state_sync") as mock_state,
        patch("app.tasks.worker.release_thumbnail_queue_slot"),
    ):
        result = fetch_and_cache_image(source_url, "resource-private")

    assert result is False
    request_get.assert_not_called()
    payload = mock_state.call_args.args[0]
    assert payload.state == "failure"
    assert "unsafe or oversized" in payload.state_detail


def test_worker_resolves_iiif_info_before_fetching_image():
    info_url = "https://example.com/iiif/item/info.json"
    image_url = "https://example.com/iiif/item/full/924,/0/default.jpg"

    with patch(
        "app.services.image_service.ImageService.get_iiif_image_thumbnail",
        return_value=image_url,
    ) as mock_resolve:
        assert _resolve_image_url(info_url) == image_url

    mock_resolve.assert_called_once_with(info_url)


def test_unr_level_zero_info_worker_fetches_and_caches_real_rendition():
    """Exercise the complete raw info.json -> rendition -> image-cache worker path."""
    response = MagicMock()
    response.status_code = 200
    response.is_redirect = False
    response.is_permanent_redirect = False
    response.content = _valid_png_bytes()
    response.headers = {"Content-Type": "image/png"}
    response.raise_for_status = MagicMock()

    with (
        patch(
            "app.services.image_service.ImageService._get_manifest",
            return_value=UNR_LEVEL_ZERO_INFO,
        ),
        patch("app.tasks.worker.redis_client") as mock_redis,
        patch("app.tasks.worker.store_durable_visual_asset", return_value=True),
        patch("app.tasks.worker.store_durable_visual_asset_link", return_value=True),
        patch(
            "app.services.remote_fetch.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ),
        patch("app.tasks.worker.requests.get", return_value=response) as mock_get,
        patch(
            "app.tasks.worker.provider_request_slot",
            side_effect=lambda *args, **kwargs: nullcontext(MagicMock(waited_seconds=0.0)),
        ),
        patch("app.tasks.worker.safe_record_thumbnail_state_sync") as mock_state,
        patch("app.tasks.worker.release_thumbnail_queue_slot"),
    ):
        mock_redis.exists.return_value = False

        assert fetch_and_cache_image(UNR_INFO_URL, UNR_RESOURCE_ID) is True

        mock_get.assert_called_once_with(
            UNR_IMAGE_URL,
            timeout=30,
            headers={"User-Agent": "BTAA-Geospatial-Data-API/1.0 (https://geo.btaa.org/)"},
            allow_redirects=False,
            stream=True,
        )
        image_key, cached_bytes = _cached_image_write(mock_redis)
        resolved_hash = _remote_thumbnail_image_hash(UNR_IMAGE_URL)
        assert image_key == f"image:{resolved_hash}"
        assert Image.open(io.BytesIO(cached_bytes)).format == "PNG"

        success_payload = mock_state.call_args.args[0]
        assert success_payload.state == "success"
        assert success_payload.resource_id == UNR_RESOURCE_ID
        assert success_payload.source_url == UNR_INFO_URL
        assert success_payload.source_hash == resolved_hash
