from scripts.ogm_importer import derive_repo_name_from_path, inject_ogm_repo_tags


def test_derive_repo_name_from_metadata_aardvark_path(tmp_path):
    ogm_path = tmp_path / "opengeometadata"
    record_path = ogm_path / "edu.unr" / "metadata-aardvark" / "records" / "item.json"

    assert derive_repo_name_from_path(str(record_path), str(ogm_path)) == "edu.unr"


def test_inject_ogm_repo_tags_preserves_existing_tags_and_adds_alias():
    record = {"id": "unr-test", "b1g_adminTags_sm": ["curated"]}

    inject_ogm_repo_tags(record, "edu.unr")

    assert record["b1g_adminTags_sm"] == ["curated", "ogm_repo:edu.unr", "ogm:unr"]
