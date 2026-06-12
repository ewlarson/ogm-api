"""
Tests for Elasticsearch indexing transformations.
"""

import pytest

import app.elasticsearch.index as index_module


@pytest.mark.asyncio
async def test_fetch_resources_for_index_attaches_active_ogm_repos(monkeypatch):
    calls = []

    async def fake_fetch_all(query):
        calls.append(query)
        if len(calls) == 1:
            return [
                {"id": "unr-record"},
                {"id": "stale-ogm-record"},
                {"id": "non-ogm-record"},
            ]
        return [
            {
                "ogm_resource_id": "unr-record",
                "ogm_repo_name": "edu.unr",
                "ogm_missing_since": None,
            },
            {
                "ogm_resource_id": "unr-record",
                "ogm_repo_name": "edu.unr",
                "ogm_missing_since": None,
            },
            {
                "ogm_resource_id": "unr-record",
                "ogm_repo_name": "edu.example",
                "ogm_missing_since": None,
            },
            {
                "ogm_resource_id": "stale-ogm-record",
                "ogm_repo_name": "edu.unr",
                "ogm_missing_since": object(),
            },
        ]

    monkeypatch.setattr(index_module.database, "fetch_all", fake_fetch_all)

    rows = await index_module.fetch_resources_for_index()

    assert rows == [
        {"id": "unr-record", "ogm_repo": ["edu.unr", "edu.example"]},
        {"id": "stale-ogm-record", "ogm_repo": []},
        {"id": "non-ogm-record"},
    ]


@pytest.fixture
def stub_process_resource_lookups(monkeypatch):
    async def fake_get_resource_summaries(resource_id):
        return []

    async def fake_get_spatial_facets(resource_id):
        return None

    async def fake_get_allmaps_overlay_status(resource_id):
        return resource_id == "allmaps-map"

    monkeypatch.setattr(
        index_module,
        "get_resource_summaries",
        fake_get_resource_summaries,
    )
    monkeypatch.setattr(index_module, "get_spatial_facets", fake_get_spatial_facets)
    monkeypatch.setattr(
        index_module,
        "get_allmaps_overlay_status",
        fake_get_allmaps_overlay_status,
    )


@pytest.mark.asyncio
async def test_process_resource_adds_allmaps_overlay_status(stub_process_resource_lookups):
    indexed = await index_module.process_resource(
        {
            "id": "allmaps-map",
            "dct_title_s": "Annotated map",
            "gbl_indexYear_im": "1929",
        }
    )

    assert indexed["b1g_georeferenced_allmaps_b"] is True


@pytest.mark.asyncio
async def test_process_resource_uses_explicit_ogm_repo(stub_process_resource_lookups):
    indexed = await index_module.process_resource(
        {
            "id": "unr-record",
            "dct_title_s": "UNR record",
            "ogm_repo": "edu.unr",
        }
    )

    assert indexed["ogm_repo"] == ["edu.unr"]


@pytest.mark.asyncio
async def test_process_resource_prefers_explicit_ogm_repo_over_tags(
    stub_process_resource_lookups,
):
    indexed = await index_module.process_resource(
        {
            "id": "unr-record",
            "dct_title_s": "UNR record",
            "ogm_repo": ["edu.unr"],
            "b1g_adminTags_sm": ["ogm_repo:edu.stale", "ogm:stale"],
        }
    )

    assert indexed["ogm_repo"] == ["edu.unr"]


@pytest.mark.asyncio
async def test_process_resource_does_not_fallback_to_tags_with_empty_explicit_ogm_repo(
    stub_process_resource_lookups,
):
    indexed = await index_module.process_resource(
        {
            "id": "stale-ogm-record",
            "dct_title_s": "Stale OGM record",
            "ogm_repo": [],
            "b1g_adminTags_sm": ["ogm_repo:edu.unr", "ogm:unr"],
        }
    )

    assert "ogm_repo" not in indexed
