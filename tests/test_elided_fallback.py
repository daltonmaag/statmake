import pytest

from statmake.errors import Error

from . import testutil


def test_elided_fallback_default(datadir):
    """Test that the default value for the elided fallback name is name ID 2
    when the stylespace key is omitted."""

    varfont = testutil.generate_variable_font(
        datadir / "elided_fallback" / "Font.designspace",
        datadir / "elided_fallback" / "Default.stylespace",
    )

    stat_table = varfont["STAT"]

    actual = stat_table.table.ElidedFallbackNameID
    assert actual == 2


def test_elided_fallback_int(datadir):
    """Test that an explicit integer name ID for the elided fallback name is
    parsed and applied from the stylespace."""

    varfont = testutil.generate_variable_font(
        datadir / "elided_fallback" / "Font.designspace",
        datadir / "elided_fallback" / "IntegerCorrect.stylespace",
    )

    stat_table = varfont["STAT"]

    actual = stat_table.table.ElidedFallbackNameID
    assert actual == 3


def test_elided_fallback_int_invalid(datadir):
    """Test that statmake will refuse to generate a STAT if the name ID integer
    specified for the elided fallback name does not exist in the final TTF."""

    with pytest.raises(
        Error, match=r"No English record for id 12345678 for Windows platform"
    ):
        testutil.generate_variable_font(
            datadir / "elided_fallback" / "Font.designspace",
            datadir / "elided_fallback" / "IntegerInvalid.stylespace",
        )


def test_elided_fallback_name_record(datadir):
    """Test that an explicit NameRecord (e.g. a string) for the elided fallback
    name is parsed and applied from the stylespace."""

    varfont = testutil.generate_variable_font(
        datadir / "elided_fallback" / "Font.designspace",
        datadir / "elided_fallback" / "NameRecord.stylespace",
    )

    stat_table = varfont["STAT"]

    actual = varfont["name"].getDebugName(stat_table.table.ElidedFallbackNameID)
    assert actual == "expected"
