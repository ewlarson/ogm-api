import pytest

from app.services.ogm_harvest import repository as ogm_repository
from app.services.ogm_harvest.repository import OGMHarvestRepository
from db.database import database


def _compile_like_databases(query) -> str:
    compiled = query.compile(
        dialect=database._backend._dialect,
        compile_kwargs={"render_postcompile": True},
    )
    compiled_params = sorted(compiled.params.items())
    mapping = {key: f"${i}" for i, (key, _) in enumerate(compiled_params, start=1)}
    return compiled.string % mapping


@pytest.mark.asyncio
async def test_public_repo_summaries_query_casts_static_string_parameters(monkeypatch):
    captured = {}

    async def fake_fetch_all(query):
        captured["query"] = query
        return []

    monkeypatch.setattr(ogm_repository.database, "fetch_all", fake_fetch_all)

    summaries = await OGMHarvestRepository().list_public_repo_summaries()

    assert summaries == []
    sql = _compile_like_databases(captured["query"])
    assert "concat(CAST(" in sql
    assert "nullif(resources.b1g_publication_state_s, CAST(" in sql
    assert "nullif(resources.publication_state, CAST(" in sql
    assert ") = CAST(" in sql
