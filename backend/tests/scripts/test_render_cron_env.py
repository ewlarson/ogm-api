from __future__ import annotations

import os

from scripts.render_cron_env import DEFAULT_OUTPUT_PATH, render_cron_env_exports, write_cron_env


def test_render_cron_env_exports_filters_and_quotes_values():
    rendered = render_cron_env_exports(
        {
            "CRON_LOCAL_TIMEZONE": "America/Chicago",
            "DATABASE_URL": "postgresql://user:p@ss word@db.example/btaa",
            "GITHUB_TOKEN": "ghp_example",
            "REDIS_HOST": "redis.internal",
            "OGM_NIGHTLY_CRON_ENABLED": "false",
            "BRIDGE_SYNC_LOCAL_TIMEZONE": "America/Chicago",
            "BACKUP_ENABLED": "true",
            "AWS_ACCESS_KEY_ID": "example-key",
            "UNRELATED_KEY": "ignore-me",
        }
    )

    assert "export CRON_LOCAL_TIMEZONE=America/Chicago" in rendered
    assert "export DATABASE_URL='postgresql://user:p@ss word@db.example/btaa'" in rendered
    assert "export GITHUB_TOKEN=ghp_example" in rendered
    assert "export REDIS_HOST=redis.internal" in rendered
    assert "export OGM_NIGHTLY_CRON_ENABLED=false" in rendered
    assert "export BRIDGE_SYNC_LOCAL_TIMEZONE=America/Chicago" in rendered
    assert "export BACKUP_ENABLED=true" in rendered
    assert "export AWS_ACCESS_KEY_ID=example-key" in rendered
    assert "UNRELATED_KEY" not in rendered


def test_write_cron_env_writes_private_bootstrap_file(tmp_path):
    output_path = tmp_path / "cron.env"

    written_path = write_cron_env(
        str(output_path),
        {
            "DATABASE_URL": "postgresql://example",
            "PYTHONPATH": "/app",
        },
    )

    assert written_path == output_path
    assert output_path.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash\n")
    assert os.stat(output_path).st_mode & 0o777 == 0o600


def test_default_output_path_is_tmp_bootstrap_file():
    assert DEFAULT_OUTPUT_PATH == "/tmp/cron-container-env.sh"
