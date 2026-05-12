from db.migrations.backfill_resources_from_legacy_items import (
    LEGACY_ITEMS_TO_RESOURCE_COLUMNS,
    build_backfill_statement,
)


def test_build_backfill_statement_marks_records_as_published():
    sql = str(build_backfill_statement())

    assert "INSERT INTO resources" in sql
    assert "FROM items" in sql
    assert ":publication_state" in sql
    assert "ON CONFLICT (id) DO NOTHING" in sql


def test_legacy_column_mapping_covers_core_search_fields():
    mapping = dict(LEGACY_ITEMS_TO_RESOURCE_COLUMNS)

    assert mapping["gbl_displayNote_sm"] == "gbl_displaynote_sm"
    assert mapping["gbl_resourceClass_sm"] == "gbl_resourceclass_sm"
    assert mapping["pcdm_memberOf_sm"] == "pcdm_memberof_sm"
    assert mapping["dct_accessRights_s"] == "dct_accessrights_s"
    assert mapping["gbl_mdVersion_s"] == "gbl_mdversion_s"
