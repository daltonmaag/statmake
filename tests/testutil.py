import io
from pathlib import Path
from typing import Mapping, Optional

import fontTools.designspaceLib
import fontTools.ttLib
import fontTools.ttLib.tables._n_a_m_e
import fontTools.varLib
import ufo2ft
import ufoLib2

import statmake.classes
import statmake.lib


def dump_axes(font, axes_array):
    dump_list = []
    for axis in axes_array:
        entry = {
            "Name": statmake.lib._default_name_string(font, axis.AxisNameID),
            "AxisTag": axis.AxisTag,
            "AxisOrdering": axis.AxisOrdering,
        }
        dump_list.append(entry)
    return dump_list


def dump_axis_values(font, axis_value_array):
    dump_list = []
    for axis in axis_value_array:
        entry = {
            "Format": axis.Format,
            "Name": dump_name_ids(font, axis.ValueNameID),
            "Flags": axis.Flags,
        }
        if axis.Format == 1:
            entry["AxisIndex"] = axis.AxisIndex
            entry["Value"] = axis.Value
        elif axis.Format == 2:
            entry["AxisIndex"] = axis.AxisIndex
            entry["NominalValue"] = axis.NominalValue
            entry["RangeMinValue"] = axis.RangeMinValue
            entry["RangeMaxValue"] = axis.RangeMaxValue
        elif axis.Format == 3:
            entry["AxisIndex"] = axis.AxisIndex
            entry["Value"] = axis.Value
            entry["LinkedValue"] = axis.LinkedValue
        elif axis.Format == 4:
            entry["AxisValueRecord"] = [
                (r.AxisIndex, r.Value) for r in axis.AxisValueRecord
            ]
        else:
            raise ValueError("Unknown format")
        dump_list.append(entry)
    return dump_list


def dump_name_ids(otfont: fontTools.ttLib.TTFont, name_id: int) -> Mapping[str, str]:
    """Return a mapping of language codes to name strings."""
    name_mapping = fontTools.ttLib.tables._n_a_m_e._WINDOWS_LANGUAGES
    name_table = otfont["name"].names
    matches = {
        name_mapping[n.langID]: n.toUnicode()
        for n in name_table
        if n.platformID == 3 and n.nameID == name_id
    }
    return matches


def empty_UFO(style_name: str) -> ufoLib2.Font:
    ufo = ufoLib2.Font()
    ufo.info.familyName = "Test"
    ufo.info.styleName = style_name
    ufo.info.unitsPerEm = 1000
    ufo.info.ascender = 800
    ufo.info.descender = -200
    ufo.info.xHeight = 500
    ufo.info.capHeight = 700
    ufo.info.postscriptUnderlineThickness = 50
    ufo.info.postscriptUnderlinePosition = -75
    g = ufo.newGlyph("a")
    g.width = 500
    return ufo


def reload_font(font):
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    return fontTools.ttLib.TTFont(buf)


def generate_variable_font(
    designspace_path: Path,
    stylespace_path: Path,
    additional_locations: Optional[Mapping[str, float]] = None,
) -> fontTools.ttLib.TTFont:
    designspace = fontTools.designspaceLib.DesignSpaceDocument.fromfile(
        designspace_path
    )
    for source in designspace.sources:
        source.font = empty_UFO(source.styleName)
    ufo2ft.compileInterpolatableTTFsFromDS(designspace, inplace=True)
    varfont, _, _ = fontTools.varLib.build(designspace)

    stylespace = statmake.classes.Stylespace.from_file(stylespace_path)
    if additional_locations is None:
        additional_locations = designspace.lib.get(
            "org.statmake.additionalLocations", {}
        )
    statmake.lib.apply_stylespace_to_variable_font(
        stylespace, varfont, additional_locations
    )
    return reload_font(varfont)
