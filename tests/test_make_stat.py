import fontTools.designspaceLib
import fontTools.otlLib.builder
import pytest

import statmake.classes
import statmake.lib
from statmake.errors import Error, StylespaceError

from . import testutil


def test_load_stylespace_broken_range(datadir):
    with pytest.raises(ValueError, match=r"Not enough values .*"):
        statmake.classes.Stylespace.from_file(datadir / "TestBroken.stylespace")


def test_load_stylespace_broken_ordering(datadir):
    with pytest.raises(StylespaceError, match=r".* ordering .*"):
        statmake.classes.Stylespace.from_file(datadir / "TestBrokenAxes.stylespace")


def test_load_stylespace_broken_format4_1(datadir):
    with pytest.raises(
        StylespaceError, match=r".* must specify values for all axes .*"
    ):
        statmake.classes.Stylespace.from_file(datadir / "TestBogusFormat4.stylespace")


def test_load_stylespace_broken_format4_2(datadir):
    with pytest.raises(
        StylespaceError, match=r".* must specify values for all axes .*"
    ):
        statmake.classes.Stylespace.from_file(datadir / "TestBogusFormat4_2.stylespace")


def test_load_stylespace_missing_linked_value(datadir):
    with pytest.raises(
        StylespaceError,
        match=r".* location 'Regular' specifies a linked_value of '100.0'.*",
    ):
        statmake.classes.Stylespace.from_file(
            datadir / "TestMissingLinkedValue.stylespace"
        )


def test_load_stylespace_duplicate_value(datadir):
    with pytest.raises(
        StylespaceError,
        match=r".* 'Regular' specifies a duplicate location value of '400.0'.*",
    ):
        statmake.classes.Stylespace.from_file(datadir / "TestDuplicateValue.stylespace")


def test_load_stylespace_duplicate_value_format4(datadir):
    with pytest.raises(
        StylespaceError, match=r".* location 'fgfg' specifies a duplicate location .*"
    ):
        statmake.classes.Stylespace.from_file(
            datadir / "TestDuplicateValueFormat4.stylespace"
        )


def test_load_stylespace_broken_multilingual_no_en(datadir):
    with pytest.raises(StylespaceError, match=r".* must have a default English .*"):
        statmake.classes.Stylespace.from_file(
            datadir / "TestMultilingualNoEn.stylespace"
        )


def test_load_stylespace_broken_multilingual_incomplete_lang(datadir):
    with pytest.raises(
        StylespaceError, match=r".* languages \['en'\] but expected was \['de', 'en'\]."
    ):
        statmake.classes.Stylespace.from_file(
            datadir / "TestMultilingualBrokenAxisNameLang.stylespace"
        )


def test_load_stylespace_broken_multilingual_incomplete_lang2(datadir):
    with pytest.raises(
        StylespaceError, match=r".* languages \['en'\] but expected was \['de', 'en'\]."
    ):
        statmake.classes.Stylespace.from_file(
            datadir / "TestMultilingualBrokenLocNameLang.stylespace"
        )


def test_load_stylespace_no_format4(datadir):
    statmake.classes.Stylespace.from_file(datadir / "TestNoFormat4.stylespace")


def test_load_from_designspace(datadir):
    designspace = fontTools.designspaceLib.DesignSpaceDocument.fromfile(
        datadir / "TestInlineStylespace.designspace"
    )
    statmake.classes.Stylespace.from_designspace(designspace)


def test_load_from_broken_designspace(datadir):
    designspace = fontTools.designspaceLib.DesignSpaceDocument.fromfile(
        datadir / "TestNoFormat4.stylespace"
    )
    with pytest.raises(StylespaceError, match=r".* lib .*"):
        statmake.classes.Stylespace.from_designspace(designspace)


def test_generation_incomplete_stylespace(datadir):
    with pytest.raises(Error, match=r".* no Stylespace entry .*"):
        _ = testutil.generate_variable_font(
            datadir / "Test_Wght_Italic.designspace",
            datadir / "TestIncomplete.stylespace",
        )


def test_generation_incomplete_additional_location(datadir):
    with pytest.raises(
        Error, match=r".* no Stylespace entry .* additional locations.*"
    ):
        _ = testutil.generate_variable_font(
            datadir / "Test_Wght_Italic.designspace",
            datadir / "Test.stylespace",
            {"Italic": 2},
        )


def test_generation_disjunct_additional_location(datadir):
    with pytest.raises(Error, match=r".* the following aren't: Foo."):
        _ = testutil.generate_variable_font(
            datadir / "Test_Wght_Italic.designspace",
            datadir / "Test.stylespace",
            {"Foo": 2},
        )


def test_generation_superfluous_additional_location(datadir):
    with pytest.raises(
        Error, match=r"Rejecting the additional location for the axis named 'Italic'.*"
    ):
        _ = testutil.generate_variable_font(
            datadir / "Test_WghtItal.designspace",
            datadir / "Test.stylespace",
            {"Italic": 1},
        )


def test_generation_unknown_font_axis(datadir):
    with pytest.raises(
        Error, match=r"Font contains axis named 'Italic' which is not in Stylespace.*"
    ):
        _ = testutil.generate_variable_font(
            datadir / "Test_WghtItal.designspace",
            datadir / "TestJustWght.stylespace",
            {},
        )


def test_generation_wrong_tag(datadir):
    with pytest.raises(
        Error,
        match=r"Font axis named 'Italic' has tag 'ital' but Stylespace .* 'slnt'.",
    ):
        _ = testutil.generate_variable_font(
            datadir / "Test_WghtItal.designspace",
            datadir / "TestItalIsSlnt.stylespace",
            {},
        )


def test_generation_incomplete_location(datadir):
    with pytest.raises(
        Error, match=r"missing locations for the following axes: Italic."
    ):
        _ = testutil.generate_variable_font(
            datadir / "Test_Wght_Italic.designspace", datadir / "Test.stylespace", {}
        )


def test_generation_full(datadir):
    varfont = testutil.generate_variable_font(
        datadir / "Test_WghtItal.designspace", datadir / "Test.stylespace"
    )

    stat_table = varfont["STAT"]
    assert stat_table.table.Version == 0x00010002

    stat_axes = testutil.dump_axes(varfont, stat_table.table.DesignAxisRecord.Axis)
    stat_axes_expected = [
        {"Name": {"en": "Weight"}, "AxisTag": "wght", "AxisOrdering": 0},
        {"Name": {"en": "Italic"}, "AxisTag": "ital", "AxisOrdering": 1},
    ]
    assert stat_axes == stat_axes_expected

    stat_axis_values = testutil.dump_axis_values(
        varfont, stat_table.table.AxisValueArray.AxisValue
    )
    stat_axis_values_expected = [
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "XLight"},
            "Value": 200.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Light"},
            "Value": 300.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 2,
            "Format": 3,
            "LinkedValue": 700.0,
            "Name": {"en": "Regular"},
            "Value": 400.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Semi Bold"},
            "Value": 600.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Bold"},
            "Value": 700.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 2,
            "Name": {"en": "Black"},
            "NominalValue": 900.0,
            "RangeMaxValue": 900.0,
            "RangeMinValue": 701.0,
        },
        {
            "AxisIndex": 1,
            "Flags": 2,
            "Format": 3,
            "LinkedValue": 1.0,
            "Name": {"en": "Upright"},
            "Value": 0.0,
        },
        {
            "AxisIndex": 1,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Italic"},
            "Value": 1.0,
        },
        {
            "AxisValueRecord": [(0, 333.0), (1, 1.0)],
            "Flags": 0,
            "Format": 4,
            "Name": {"en": "ASDF"},
        },
        {
            "AxisValueRecord": [(0, 650.0), (1, 0.5)],
            "Flags": 2,
            "Format": 4,
            "Name": {"en": "fgfg"},
        },
    ]
    assert sorted(stat_axis_values, key=lambda x: x["Name"]["en"]) == sorted(
        stat_axis_values_expected, key=lambda x: x["Name"]["en"]
    )

    assert stat_table.table.ElidedFallbackNameID == 2


def test_generation_upright(datadir):
    varfont = testutil.generate_variable_font(
        datadir / "Test_Wght_Upright.designspace", datadir / "Test.stylespace"
    )

    stat_table = varfont["STAT"]
    assert stat_table.table.Version == 0x00010001

    stat_axes = testutil.dump_axes(varfont, stat_table.table.DesignAxisRecord.Axis)
    stat_axes_expected = [
        {"Name": {"en": "Weight"}, "AxisTag": "wght", "AxisOrdering": 0},
        {"Name": {"en": "Italic"}, "AxisTag": "ital", "AxisOrdering": 1},
    ]
    assert stat_axes == stat_axes_expected

    stat_axis_values = testutil.dump_axis_values(
        varfont, stat_table.table.AxisValueArray.AxisValue
    )
    stat_axis_values_expected = [
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "XLight"},
            "Value": 200.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Light"},
            "Value": 300.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 2,
            "Format": 3,
            "LinkedValue": 700.0,
            "Name": {"en": "Regular"},
            "Value": 400.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Semi Bold"},
            "Value": 600.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Bold"},
            "Value": 700.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 2,
            "Name": {"en": "Black"},
            "NominalValue": 900.0,
            "RangeMaxValue": 900.0,
            "RangeMinValue": 701.0,
        },
        {
            "AxisIndex": 1,
            "Flags": 2,
            "Format": 3,
            "LinkedValue": 1.0,
            "Name": {"en": "Upright"},
            "Value": 0.0,
        },
    ]
    assert stat_axis_values == stat_axis_values_expected

    assert stat_table.table.ElidedFallbackNameID == 2


def test_generation_italic(datadir):
    varfont = testutil.generate_variable_font(
        datadir / "Test_Wght_Italic.designspace", datadir / "Test.stylespace"
    )

    stat_table = varfont["STAT"]
    assert stat_table.table.Version == 0x00010002

    stat_axes = testutil.dump_axes(varfont, stat_table.table.DesignAxisRecord.Axis)
    stat_axes_expected = [
        {"Name": {"en": "Weight"}, "AxisTag": "wght", "AxisOrdering": 0},
        {"Name": {"en": "Italic"}, "AxisTag": "ital", "AxisOrdering": 1},
    ]
    assert stat_axes == stat_axes_expected

    stat_axis_values = testutil.dump_axis_values(
        varfont, stat_table.table.AxisValueArray.AxisValue
    )
    stat_axis_values_expected = [
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "XLight"},
            "Value": 200.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Light"},
            "Value": 300.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 2,
            "Format": 3,
            "LinkedValue": 700.0,
            "Name": {"en": "Regular"},
            "Value": 400.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Semi Bold"},
            "Value": 600.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Bold"},
            "Value": 700.0,
        },
        {
            "AxisIndex": 0,
            "Flags": 0,
            "Format": 2,
            "Name": {"en": "Black"},
            "NominalValue": 900.0,
            "RangeMaxValue": 900.0,
            "RangeMinValue": 701.0,
        },
        {
            "AxisIndex": 1,
            "Flags": 0,
            "Format": 1,
            "Name": {"en": "Italic"},
            "Value": 1.0,
        },
        {
            "AxisValueRecord": [(0, 333.0), (1, 1.0)],
            "Flags": 0,
            "Format": 4,
            "Name": {"en": "ASDF"},
        },
    ]
    assert sorted(stat_axis_values, key=lambda x: x["Name"]["en"]) == sorted(
        stat_axis_values_expected, key=lambda x: x["Name"]["en"]
    )

    assert stat_table.table.ElidedFallbackNameID == 2


def test_generation_full_multilingual(datadir):
    varfont = testutil.generate_variable_font(
        datadir / "Test_WghtItal.designspace", datadir / "TestMultilingual.stylespace"
    )

    stat_table = varfont["STAT"]
    assert stat_table.table.Version == 0x00010002

    stat_axes = testutil.dump_axes(varfont, stat_table.table.DesignAxisRecord.Axis)
    stat_axes_expected = [
        {
            "Name": {"de": "Gäwicht", "en": "Weight", "fr": "Géwicht"},
            "AxisTag": "wght",
            "AxisOrdering": 0,
        },
        {
            "Name": {"de": "Italienisch", "en": "Italic", "fr": "Itâlic"},
            "AxisTag": "ital",
            "AxisOrdering": 1,
        },
    ]
    assert stat_axes == stat_axes_expected

    stat_axis_values = testutil.dump_axis_values(
        varfont, stat_table.table.AxisValueArray.AxisValue
    )
    stat_axis_values_expected = [
        {
            "Format": 1,
            "Name": {"de": "Dünn", "en": "Thin", "fr": "Dûnn"},
            "Flags": 0,
            "AxisIndex": 0,
            "Value": 200.0,
        },
        {
            "Format": 1,
            "Name": {"de": "Leicht", "en": "Light", "fr": "vfdgf"},
            "Flags": 0,
            "AxisIndex": 0,
            "Value": 300.0,
        },
        {
            "Format": 3,
            "Name": {"de": "Regulär", "en": "Regular", "fr": "aaa"},
            "Flags": 2,
            "AxisIndex": 0,
            "Value": 400.0,
            "LinkedValue": 700.0,
        },
        {
            "Format": 1,
            "Name": {"de": "BB", "en": "AA", "fr": "CC"},
            "Flags": 0,
            "AxisIndex": 0,
            "Value": 600.0,
        },
        {
            "Format": 1,
            "Name": {"de": "Böld", "en": "Bold", "fr": "Bôld"},
            "Flags": 0,
            "AxisIndex": 0,
            "Value": 700.0,
        },
        {
            "Format": 1,
            "Name": {"de": "asdf", "en": "asdf", "fr": "asdf"},
            "Flags": 0,
            "AxisIndex": 0,
            "Value": 900.0,
        },
        {
            "Format": 3,
            "Name": {"de": "Aufrecht", "en": "Upright", "fr": "Ûpright"},
            "Flags": 2,
            "AxisIndex": 1,
            "Value": 0.0,
            "LinkedValue": 1.0,
        },
        {
            "Format": 1,
            "Name": {"de": "Italienisch", "en": "Italic", "fr": "Itâlic"},
            "Flags": 0,
            "AxisIndex": 1,
            "Value": 1.0,
        },
        {
            "Format": 4,
            "Name": {"de": "ASDF", "en": "ASDF", "fr": "ASDF"},
            "Flags": 0,
            "AxisValueRecord": [(0, 333.0), (1, 1.0)],
        },
        {
            "Format": 4,
            "Name": {"de": "FGFG", "en": "FGFG", "fr": "FGFG"},
            "Flags": 2,
            "AxisValueRecord": [(0, 650.0), (1, 0.5)],
        },
    ]
    assert sorted(stat_axis_values, key=lambda x: x["Name"]["en"]) == sorted(
        stat_axis_values_expected, key=lambda x: x["Name"]["en"]
    )

    assert stat_table.table.ElidedFallbackNameID == 2
