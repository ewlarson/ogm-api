from scripts import report_thumbnail_completeness as report


def test_total_row_and_success_percentage_classify_outcomes():
    rows = [
        {
            "source_bucket": "iiif",
            "total": 4,
            "eligible": 4,
            "gallery_ready": 3,
            "success": 2,
            "placeheld": 1,
            "failed": 0,
            "queued": 0,
            "stale_success": 1,
            "not_attempted": 0,
            "no_source": 0,
            "restricted": 0,
        },
        {
            "source_bucket": "bridge_asset",
            "total": 2,
            "eligible": 2,
            "gallery_ready": 1,
            "success": 1,
            "placeheld": 0,
            "failed": 1,
            "queued": 0,
            "stale_success": 0,
            "not_attempted": 0,
            "no_source": 0,
            "restricted": 0,
        },
    ]

    total = report._total_row(rows)

    assert total["total"] == 6
    assert total["eligible"] == 6
    assert total["gallery_ready"] == 4
    assert total["success"] == 3
    assert total["placeheld"] == 1
    assert total["failed"] == 1
    assert total["stale_success"] == 1
    assert report._success_pct(total) == 50.0
    assert report._gallery_ready_pct(total) == 66.67


def test_scope_conditions_are_specific():
    assert "gbl_resourceClass_sm" in report._scope_condition("maps")
    assert "'Maps'" in report._scope_condition("maps")
    assert "b1g_urbanBaseLayers" in report._scope_condition("urban")
    assert "iiif" in report._scope_condition("iiif").lower()
    assert report._scope_condition("all") == "TRUE"


def test_percentages_exclude_restricted_records_from_denominator():
    row = {"total": 10, "eligible": 8, "success": 6, "gallery_ready": 8}

    assert report._success_pct(row) == 75.0
    assert report._gallery_ready_pct(row) == 100.0


def test_summary_sql_tracks_source_buckets_and_real_durable_bytes():
    sql = report._summary_sql("all")

    for bucket in (
        "iiif",
        "b1g_image",
        "schema_thumbnail",
        "service",
        "cog",
        "pmtiles",
        "schema_image",
        "download_image",
        "download_pdf",
        "bridge_asset",
        "no_source",
    ):
        assert bucket in sql

    assert "gva.byte_size > 0" in sql
    assert "gva.content_type LIKE 'image/%'" in sql
    assert "gva.asset_kind LIKE 'thumbnail%'" in sql
    assert "links.asset_kind = 'resource-class-icon'" in sql
    assert "gallery_ready" in sql
    assert "stale_success" in sql
    assert "not_attempted" in sql


def test_report_sql_supports_provider_and_source_filters():
    sql = report._summary_sql(
        "maps",
        provider="OpenGeoMetadata",
        source_bucket="iiif",
    )

    assert "r.schema_provider_s = :provider" in sql
    assert "source_bucket = 'iiif'" in sql


def test_provider_filter_is_never_applied_implicitly(monkeypatch):
    monkeypatch.setenv("THUMBNAIL_REPORT_PROVIDER", "UNR")
    monkeypatch.setattr(report.sys, "argv", ["report_thumbnail_completeness.py"])

    assert report._parse_args().provider is None


def test_source_filter_rejects_unknown_bucket():
    import pytest

    with pytest.raises(ValueError, match="Unknown thumbnail source bucket"):
        report._summary_sql("maps", source_bucket="not-real")


def test_table_output_includes_missing_sample():
    rows = [
        {
            "source_bucket": "iiif",
            "total": 1,
            "eligible": 1,
            "gallery_ready": 0,
            "success": 0,
            "placeheld": 0,
            "failed": 0,
            "queued": 0,
            "stale_success": 1,
            "not_attempted": 0,
            "no_source": 0,
            "restricted": 0,
        }
    ]
    sample = [
        {
            "id": "resource-1",
            "dct_title_s": "A stale thumbnail",
            "source_bucket": "iiif",
            "outcome": "stale_success",
        }
    ]

    output = report._format_table(rows, sample)

    assert "stale" in output
    assert "missing sample:" in output
    assert "resource-1 | iiif | stale_success" in output
