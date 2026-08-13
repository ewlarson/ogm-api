import asyncio
from unittest.mock import patch

import pytest

import scripts.clear_thumbnail_cache as clear_thumbnail_cache


@pytest.mark.asyncio
async def test_clear_multiple_resources_uses_one_event_loop():
    calls: list[tuple[str, asyncio.AbstractEventLoop]] = []

    async def fake_clear(resource_id: str) -> bool:
        calls.append((resource_id, asyncio.get_running_loop()))
        return resource_id != "unr-missing"

    with patch.object(
        clear_thumbnail_cache,
        "clear_thumbnail_for_resource",
        side_effect=fake_clear,
    ):
        cleared = await clear_thumbnail_cache.clear_thumbnails_for_resources(
            ["unr-one", "unr-missing", "unr-two"]
        )

    assert cleared == 2
    assert [resource_id for resource_id, _loop in calls] == [
        "unr-one",
        "unr-missing",
        "unr-two",
    ]
    assert len({id(loop) for _resource_id, loop in calls}) == 1


def test_main_runs_one_batch_and_prints_summary(capsys):
    with (
        patch.object(
            clear_thumbnail_cache.sys,
            "argv",
            ["clear_thumbnail_cache.py", "unr-one", "unr-two"],
        ),
        patch.object(clear_thumbnail_cache.asyncio, "run", return_value=1) as mock_run,
    ):
        clear_thumbnail_cache.main()

    batch_coroutine = mock_run.call_args.args[0]
    batch_coroutine.close()
    mock_run.assert_called_once()
    assert "Cleared cache for 1/2 resource(s)" in capsys.readouterr().out
