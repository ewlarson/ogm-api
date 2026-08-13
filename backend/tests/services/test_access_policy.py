from app.services.access_policy import is_restricted_resource, resource_access_rights
from app.services.thumbnail_state_service import infer_source_type


def test_resource_access_rights_prefers_canonical_field():
    metadata = {
        "dct_accessRights_s": "Restricted",
        "dct_accessrights_s": "Public",
    }

    assert resource_access_rights(metadata) == "Restricted"
    assert is_restricted_resource(metadata) is True


def test_restricted_resource_accepts_legacy_field_and_normalizes_case():
    assert is_restricted_resource({"dct_accessrights_s": " restricted "}) is True


def test_resource_access_rights_accepts_single_value_arrays():
    assert resource_access_rights({"dct_accessRights_s": ["Public"]}) == "Public"


def test_non_restricted_and_missing_values_are_not_restricted():
    assert is_restricted_resource({"dct_accessRights_s": "Public"}) is False
    assert is_restricted_resource({}) is False
    assert is_restricted_resource(None) is False


def test_thumbnail_state_infers_pdf_sources():
    assert infer_source_type("https://example.org/download/map.PDF?version=2") == "pdf"
