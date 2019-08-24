import fontTools.designspaceLib
import pytest
import ufo2ft
import fontTools.ttLib

import statmake.cli

from . import testutil


def test_cli_stylespace_in_designspace(datadir, tmp_path):
    varfont = empty_varfont(datadir / "Test_Wght_Upright.designspace")
    varfont.save(tmp_path / "varfont.ttf")

    statmake.cli.main(
        [
            "-m",
            str(datadir / "TestInlineStylespace.designspace"),
            str(tmp_path / "varfont.ttf"),
        ]
    )

    font = fontTools.ttLib.TTFont(tmp_path / "varfont.ttf")
    v = testutil.dump_axis_values(font, font["STAT"].table.AxisValueArray.AxisValue)
    assert v == TEST_WGHT_UPRIGHT_STAT_DUMP


def test_cli_designspace_stylespace_external(datadir, tmp_path):
    varfont = empty_varfont(datadir / "Test_Wght_Upright.designspace")
    varfont.save(tmp_path / "varfont.ttf")

    statmake.cli.main(
        [
            "-m",
            str(datadir / "TestExternalStylespace.designspace"),
            str(tmp_path / "varfont.ttf"),
        ]
    )

    font = fontTools.ttLib.TTFont(tmp_path / "varfont.ttf")
    v = testutil.dump_axis_values(font, font["STAT"].table.AxisValueArray.AxisValue)
    assert v == TEST_WGHT_UPRIGHT_STAT_DUMP


def test_cli_stylespace_external(datadir, tmp_path):
    varfont = empty_varfont(datadir / "Test_Wght_Upright.designspace")
    varfont.save(tmp_path / "varfont.ttf")

    statmake.cli.main(
        [
            "-m",
            str(datadir / "Test_Wght_Upright.designspace"),
            "--stylespace",
            str(datadir / "Test.stylespace"),
            str(tmp_path / "varfont.ttf"),
        ]
    )

    font = fontTools.ttLib.TTFont(tmp_path / "varfont.ttf")
    v = testutil.dump_axis_values(font, font["STAT"].table.AxisValueArray.AxisValue)
    assert v == TEST_WGHT_UPRIGHT_STAT_DUMP


def test_cli_stylespace_in_broken_designspace(datadir, tmp_path):
    with pytest.raises(SystemExit):
        statmake.cli.main(
            [
                "-m",
                str(datadir / "Test_Wght_Upright.designspace"),
                str(tmp_path / "varfont.ttf"),
            ]
        )


def empty_varfont(designspace_path):
    designspace = fontTools.designspaceLib.DesignSpaceDocument.fromfile(
        designspace_path
    )
    for source in designspace.sources:
        source.font = testutil.empty_UFO(source.styleName)
    ufo2ft.compileInterpolatableTTFsFromDS(designspace, inplace=True)
    varfont, _, _ = fontTools.varLib.build(designspace)
    return varfont


TEST_WGHT_UPRIGHT_STAT_DUMP = [
    {"Format": 1, "Name": {"en": "XLight"}, "Flags": 0, "AxisIndex": 0, "Value": 200.0},
    {"Format": 1, "Name": {"en": "Light"}, "Flags": 0, "AxisIndex": 0, "Value": 300.0},
    {
        "Format": 3,
        "Name": {"de": "Regulär", "en": "Regular"},
        "Flags": 2,
        "AxisIndex": 0,
        "Value": 400.0,
        "LinkedValue": 700.0,
    },
    {
        "Format": 1,
        "Name": {"en": "Semi Bold"},
        "Flags": 0,
        "AxisIndex": 0,
        "Value": 600.0,
    },
    {"Format": 1, "Name": {"en": "Bold"}, "Flags": 0, "AxisIndex": 0, "Value": 700.0},
    {
        "Format": 2,
        "Name": {"en": "Black"},
        "Flags": 0,
        "AxisIndex": 0,
        "NominalValue": 900.0,
        "RangeMinValue": 701.0,
        "RangeMaxValue": 900.0,
    },
    {
        "Format": 3,
        "Name": {"en": "Upright"},
        "Flags": 2,
        "AxisIndex": 1,
        "Value": 0.0,
        "LinkedValue": 1.0,
    },
]
