import io
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from app.services.remote_fetch import RemoteBytes
from app.tasks import worker


def _png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(output, format="PNG")
    return output.getvalue()


def test_render_pdf_first_page_rejects_non_pdf_bytes():
    assert worker._render_pdf_first_page(b"not a pdf") is None


def test_render_pdf_first_page_reads_poppler_output():
    expected = _png_bytes()

    def fake_run(args, **_kwargs):
        Path(f"{args[-1]}.png").write_bytes(expected)
        return MagicMock(returncode=0)

    with (
        patch("app.tasks.worker.shutil.which", return_value="/usr/bin/pdftoppm"),
        patch("app.tasks.worker.subprocess.run", side_effect=fake_run),
    ):
        result = worker._render_pdf_first_page(b"%PDF-1.7\nmock")

    assert result == expected


def test_generate_pdf_thumbnail_bytes_fetches_bounded_pdf_then_renders():
    fetched = RemoteBytes(
        body=b"%PDF-1.7\nmock",
        content_type="application/pdf",
        final_url="https://example.org/map.pdf",
    )
    expected = _png_bytes()
    with (
        patch("app.tasks.worker.fetch_public_http_bytes", return_value=fetched) as fetch,
        patch("app.tasks.worker._render_pdf_first_page", return_value=expected) as render,
    ):
        result = worker._generate_pdf_thumbnail_bytes("https://example.org/map.pdf")

    assert result == expected
    assert fetch.call_args.kwargs["max_bytes"] == worker.PDF_THUMBNAIL_MAX_BYTES
    render.assert_called_once_with(fetched.body)


def test_persist_thumbnail_succeeds_durably_when_redis_is_unavailable():
    with (
        patch("app.tasks.worker.store_durable_visual_asset", return_value=True) as store,
        patch("app.tasks.worker.store_durable_visual_asset_link", return_value=True) as link,
        patch("app.tasks.worker.cache_visual_asset", side_effect=RuntimeError("redis down")),
        patch("app.tasks.worker.durable_visual_asset_enabled", return_value=True),
    ):
        result = worker._persist_thumbnail_bytes(
            "a" * 64,
            _png_bytes(),
            "image/png",
            resource_id="resource-1",
            asset_kind="thumbnail:pdf",
        )

    assert result is True
    store.assert_called_once()
    link.assert_called_once()
