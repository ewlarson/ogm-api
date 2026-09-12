import pytest

from app.services.temporal_normalization import normalize_or_derive_index_year


@pytest.mark.parametrize(
    "supplied,ranges,expected",
    [
        ([1922, 1924], ["[1900 TO 1950]"], [1922, 1924]),
        (None, ["[1922 TO 1962]"], [1922]),
        ([], ["2024-2024"], [2024]),
        (None, ["[1922 TO 1962]", "[1800 TO 1850]"], [1922]),
        ([True, None, "bad"], ["[1922 TO 1962]"], [1922]),
        (" 1922 ", None, [1922]),
        (None, [], None),
        (None, ["unknown", "[1922 TO 1962]"], None),
        (None, ["[* TO 1962]"], None),
    ],
)
def test_temporal_fallback_preserves_explicit_years_and_uses_only_first_range(
    supplied, ranges, expected
):
    assert normalize_or_derive_index_year(supplied, ranges) == expected
