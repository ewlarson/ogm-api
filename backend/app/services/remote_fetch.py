from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urldefrag, urljoin, urlsplit

import requests


class UnsafeRemoteUrl(ValueError):
    """Raised when a metadata-controlled URL could reach a non-public network."""


class RemotePayloadTooLarge(ValueError):
    """Raised when a remote response exceeds its configured byte budget."""


@dataclass(frozen=True)
class RemoteBytes:
    body: bytes
    content_type: str
    final_url: str


def validate_public_http_url(url: str, *, resolve_dns: bool = True) -> str:
    """Validate an HTTP(S) URL and reject local, private, or reserved destinations."""
    cleaned, _fragment = urldefrag(str(url or "").strip())
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise UnsafeRemoteUrl("remote URL must use http or https and include a host")
    if parsed.username or parsed.password:
        raise UnsafeRemoteUrl("remote URL must not contain credentials")

    hostname = parsed.hostname.rstrip(".").casefold()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise UnsafeRemoteUrl("localhost is not an allowed remote thumbnail host")

    try:
        literal_address = ipaddress.ip_address(hostname)
    except ValueError:
        literal_address = None
    if literal_address is not None and not literal_address.is_global:
        raise UnsafeRemoteUrl("non-public IP addresses are not allowed")

    if resolve_dns and literal_address is None:
        try:
            addresses = {
                ipaddress.ip_address(sockaddr[0])
                for _family, _type, _proto, _canonname, sockaddr in socket.getaddrinfo(
                    hostname,
                    parsed.port or (443 if parsed.scheme.lower() == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            }
        except (OSError, ValueError) as exc:
            raise UnsafeRemoteUrl(
                f"remote thumbnail host could not be resolved: {hostname}"
            ) from exc
        if not addresses or any(not address.is_global for address in addresses):
            raise UnsafeRemoteUrl("remote thumbnail host resolves to a non-public address")
    return cleaned


def fetch_public_http_bytes(
    url: str,
    *,
    timeout: int,
    max_bytes: int,
    headers: Mapping[str, str] | None = None,
    max_redirects: int = 5,
) -> RemoteBytes:
    """Fetch bounded bytes while validating every redirect destination."""
    current_url = validate_public_http_url(url)
    request_headers = dict(headers or {})

    for redirect_count in range(max_redirects + 1):
        response = requests.get(
            current_url,
            timeout=timeout,
            headers=request_headers,
            allow_redirects=False,
            stream=True,
        )
        if response.is_redirect or response.is_permanent_redirect:
            if redirect_count >= max_redirects:
                response.close()
                raise requests.TooManyRedirects(f"too many redirects fetching {url}")
            location = response.headers.get("Location")
            if not location:
                response.raise_for_status()
            current_url = validate_public_http_url(urljoin(current_url, str(location)))
            response.close()
            continue

        try:
            response.raise_for_status()
        except requests.RequestException:
            response.close()
            raise
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                declared_length = int(content_length)
            except ValueError:
                declared_length = 0
            if declared_length > max_bytes:
                response.close()
                raise RemotePayloadTooLarge(f"remote payload exceeds {max_bytes} bytes")

        chunks: list[bytes] = []
        byte_count = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            byte_count += len(chunk)
            if byte_count > max_bytes:
                response.close()
                raise RemotePayloadTooLarge(f"remote payload exceeds {max_bytes} bytes")
            chunks.append(chunk)
        if not chunks:
            body = bytes(response.content or b"")
            if len(body) > max_bytes:
                response.close()
                raise RemotePayloadTooLarge(f"remote payload exceeds {max_bytes} bytes")
            chunks.append(body)
        response.close()
        return RemoteBytes(
            body=b"".join(chunks),
            content_type=response.headers.get("Content-Type", ""),
            final_url=current_url,
        )

    raise requests.TooManyRedirects(f"too many redirects fetching {url}")
