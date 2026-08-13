from unittest.mock import MagicMock, patch

import pytest

from app.services.remote_fetch import (
    RemotePayloadTooLarge,
    UnsafeRemoteUrl,
    fetch_public_http_bytes,
    validate_public_http_url,
)


@pytest.mark.parametrize(
    "url",
    (
        "http://127.0.0.1/secret",
        "http://169.254.169.254/latest/meta-data",
        "http://localhost/internal",
        "file:///etc/passwd",
        "https://user:password@example.com/image.jpg",
    ),
)
def test_validate_public_http_url_rejects_unsafe_destinations(url):
    with pytest.raises(UnsafeRemoteUrl):
        validate_public_http_url(url, resolve_dns=False)


def test_fetch_public_http_bytes_validates_redirect_and_enforces_size():
    redirect = MagicMock(
        is_redirect=True,
        is_permanent_redirect=False,
        headers={"Location": "https://cdn.example.org/map.pdf"},
    )
    response = MagicMock(
        is_redirect=False,
        is_permanent_redirect=False,
        headers={"Content-Type": "application/pdf"},
    )
    response.iter_content.return_value = [b"%PDF", b"-payload"]

    with (
        patch(
            "app.services.remote_fetch.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ),
        patch("app.services.remote_fetch.requests.get", side_effect=[redirect, response]),
    ):
        result = fetch_public_http_bytes(
            "https://example.org/map.pdf",
            timeout=5,
            max_bytes=32,
        )

    assert result.body == b"%PDF-payload"
    assert result.final_url == "https://cdn.example.org/map.pdf"

    response.iter_content.return_value = [b"x" * 33]
    with (
        patch(
            "app.services.remote_fetch.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 443))],
        ),
        patch("app.services.remote_fetch.requests.get", return_value=response),
        pytest.raises(RemotePayloadTooLarge),
    ):
        fetch_public_http_bytes("https://example.org/map.pdf", timeout=5, max_bytes=32)
