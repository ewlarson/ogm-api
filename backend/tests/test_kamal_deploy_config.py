import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_deploy_config(path: str) -> dict:
    config_text = (REPO_ROOT / path).read_text()
    config_text = re.sub(r"<%.*?%>", "", config_text, flags=re.DOTALL)
    return yaml.safe_load(config_text)


def test_prd_secret_override_keeps_base_secrets():
    if not (REPO_ROOT / "config/deploy.prd.yml").exists():
        pytest.skip("config/deploy.prd.yml is not included in this downstream")

    base_config = _load_deploy_config("config/deploy.yml")
    prd_config = _load_deploy_config("config/deploy.prd.yml")

    base_secrets = set(base_config["env"]["secret"])
    prd_secrets = set(prd_config["env"]["secret"])

    missing = base_secrets - prd_secrets
    assert not missing, (
        "config/deploy.prd.yml env.secret replaces the base list; "
        f"missing inherited secrets: {sorted(missing)}"
    )


def test_kamal_cron_role_and_crontab_are_wired():
    base_config = _load_deploy_config("config/deploy.yml")
    cron_config = base_config["servers"]["cron"]
    crontab = (REPO_ROOT / "config/crontab").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    assert "start_cron.sh" in cron_config["cmd"]
    assert cron_config["options"]["user"] == "root"
    assert base_config["env"]["clear"]["OGM_NIGHTLY_CRON_ENABLED"] == "false"
    assert "GITHUB_TOKEN" in base_config["env"]["secret"]

    assert "trigger_ogm_nightly_sync.py" in crontab
    assert "OGM_NIGHTLY_CRON_ENABLED" in crontab
    assert "generate_sitemap.py" in crontab
    assert "prune_generated_api_response_cache.py" in crontab

    assert "cron" in dockerfile
    assert "COPY config/crontab ./config/crontab" in dockerfile
    assert "start_cron.sh" in dockerfile


def test_kamal_accessory_directories_preserve_live_production_binds():
    base_config = _load_deploy_config("config/deploy.yml")
    accessories = base_config["accessories"]

    assert accessories["elasticsearch"]["directories"] == ["esdata:/usr/share/elasticsearch/data"]
    assert accessories["postgres"]["directories"] == ["pgdata:/var/lib/postgresql/data"]
    assert accessories["redis"]["directories"] == ["redisdata:/data"]
