from app.services.iiif_url import is_iiif_info_url, is_iiif_manifest_url


def test_dataset_manifest_is_not_a_iiif_manifest():
    assert not is_iiif_manifest_url("https://example.com/uploads/item/dataset_manifest.json")


def test_manifest_final_path_component_is_detected():
    assert is_iiif_manifest_url("https://example.com/iiif/item/manifest.json")
    assert is_iiif_manifest_url("https://example.com/iiif/item/manifest2.json")
    assert is_iiif_manifest_url("https://example.com/concern/scanned_maps/item/manifest")


def test_michigan_image_api_manifest_is_detected():
    assert is_iiif_manifest_url("https://quod.lib.umich.edu/cgi/i/image/api/search/collection:id")


def test_info_document_is_not_a_manifest():
    url = "https://example.com/iiif/item/info.json"
    assert is_iiif_info_url(url)
    assert not is_iiif_manifest_url(url)
