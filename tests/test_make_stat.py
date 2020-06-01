import fontTools.designspaceLib
import pytest

import statmake.classes
import statmake.lib

from . import testutil


def test_load_stylespace_broken_range(datadir):
    with pytest.raises(ValueError, match=r"Range .*"):
        statmake.classes.Stylespace.from_file(datadir / "TestBroken.stylespace")


def test_load_stylespace_broken_ordering(datadir):
    with pytest.raises(ValueError, match=r".* ordering .*"):
        statmake.classes.Stylespace.from_file(datadir / "TestBrokenAxes.stylespace")


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
    with pytest.raises(ValueError, match=r".* lib .*"):
        statmake.classes.Stylespace.from_designspace(designspace)


def test_generation_incomplete_stylespace(datadir):
    with pytest.raises(ValueError, match=r".* no Stylespace entry .*"):
        _ = testutil.generate_variable_font(
            datadir / "Test_Wght_Italic.designspace",
            datadir / "TestIncomplete.stylespace",
        )


def test_generation_incomplete_additional_location(datadir):
    with pytest.raises(
        ValueError, match=r".* no Stylespace entry .* additional locations.*"
    ):
        _ = testutil.generate_variable_font(
            datadir / "Test_Wght_Italic.designspace",
            datadir / "Test.stylespace",
            {"Italic": 2},
        )


def test_generation_full(datadir):
    varfont = testutil.generate_variable_font(
        datadir / "Test_WghtItal.designspace", datadir / "Test.stylespace"
    )

    stat_table = varfont["STAT"]
    assert stat_table.table.Version == 0x00010002

    stat_axes = testutil.dump_axes(varfont, stat_table.table.DesignAxisRecord.Axis)
    stat_axes_expected = [
        {"Name": "Weight", "AxisTag": "wght", "AxisOrdering": 0},
        {"Name": "Italic", "AxisTag": "ital", "AxisOrdering": 1},
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
            "Name": {"de": "Regulär", "en": "Regular"},
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
    assert stat_axis_values == stat_axis_values_expected

    assert stat_table.table.ElidedFallbackNameID == 2


def test_generation_upright(datadir):
    varfont = testutil.generate_variable_font(
        datadir / "Test_Wght_Upright.designspace", datadir / "Test.stylespace"
    )

    stat_table = varfont["STAT"]
    assert stat_table.table.Version == 0x00010001

    stat_axes = testutil.dump_axes(varfont, stat_table.table.DesignAxisRecord.Axis)
    stat_axes_expected = [
        {"Name": "Weight", "AxisTag": "wght", "AxisOrdering": 0},
        {"Name": "Italic", "AxisTag": "ital", "AxisOrdering": 1},
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
            "Name": {"de": "Regulär", "en": "Regular"},
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
        {"Name": "Weight", "AxisTag": "wght", "AxisOrdering": 0},
        {"Name": "Italic", "AxisTag": "ital", "AxisOrdering": 1},
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
            "Name": {"de": "Regulär", "en": "Regular"},
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
    assert stat_axis_values == stat_axis_values_expected

    assert stat_table.table.ElidedFallbackNameID == 2
