import collections
import copy
from typing import Dict, Mapping, Optional, Set

import fontTools.misc.py23
import fontTools.ttLib
import fontTools.ttLib.tables.otTables as otTables

import statmake.classes


def apply_stylespace_to_variable_font(
    stylespace: statmake.classes.Stylespace,
    varfont: fontTools.ttLib.TTFont,
    additional_locations: Mapping[str, float],
):
    """Generate and apply a STAT table to a variable font.

    additional_locations: used in subset Designspaces to express where on which other
    axes not defined by an <axis> element the varfont stands. The primary use-case is
    defining a complete STAT table for variable fonts that do not include all axes of a
    family (either because they intentionally contain just a subset of axes or because
    the designs are incompatible).
    """
    name_table, stat_table = generate_name_and_STAT_variable(
        stylespace, varfont, additional_locations
    )
    varfont["name"] = name_table
    varfont["STAT"] = stat_table


def generate_name_and_STAT_variable(
    stylespace: statmake.classes.Stylespace,
    varfont: fontTools.ttLib.TTFont,
    additional_locations: Mapping[str, float],
):
    """Generate a new name and STAT table ready for insertion."""

    if "fvar" not in varfont:
        raise ValueError(
            "Need a variable font with the fvar table to determine which instances "
            "are present."
        )

    stylespace_name_to_axis = {a.name.default: a for a in stylespace.axes}
    fvar_name_to_axis = {}
    name_to_tag: Dict[str, str] = {}
    name_to_index: Dict[str, int] = {}
    index = 0
    for index, fvar_axis in enumerate(varfont["fvar"].axes):
        fvar_axis_name = _default_name_string(varfont, fvar_axis.axisNameID)
        try:
            stylespace_axis = stylespace_name_to_axis[fvar_axis_name]
        except KeyError:
            raise ValueError(
                f"No stylespace entry found for axis name '{fvar_axis_name}'."
            )
        if fvar_axis.axisTag != stylespace_axis.tag:
            raise ValueError(
                f"fvar axis '{fvar_axis_name}' tag is '{fvar_axis.axisTag}', but "
                f"Stylespace tag is '{stylespace_axis.tag}'."
            )
        fvar_name_to_axis[fvar_axis_name] = fvar_axis
        name_to_tag[fvar_axis_name] = fvar_axis.axisTag
        name_to_index[fvar_axis_name] = index

    for axis_name in additional_locations:
        try:
            stylespace_axis = stylespace_name_to_axis[axis_name]
        except KeyError:
            raise ValueError(f"No stylespace entry found for axis name '{axis_name}'.")
        name_to_tag[stylespace_axis.name.default] = stylespace_axis.tag
        index += 1
        name_to_index[stylespace_axis.name.default] = index

    # First, determine which stops are used on which axes. The STAT table must contain
    # a name for each stop that is used on each axis, so each stop must have an entry
    # in the Stylespace. Also include locations in additional_locations that can refer
    # to axes not present in the current varfont.
    stylespace_stops: Dict[str, Set[float]] = {}
    for axis in stylespace.axes:
        stylespace_stops[axis.tag] = {l.value for l in axis.locations}
    for named_location in stylespace.locations:
        for name, value in named_location.axis_values.items():
            stylespace_stops[name_to_tag[name]].add(value)

    axis_stops: Mapping[str, Set[float]] = collections.defaultdict(set)  # tag to stops
    for instance in varfont["fvar"].instances:
        for k, v in instance.coordinates.items():
            if v not in stylespace_stops[k]:
                raise ValueError(
                    f"There is no Stylespace entry for stop {v} on the '{k}' axis."
                )
            axis_stops[k].add(v)

    for k, v in additional_locations.items():
        axis_tag = name_to_tag[k]
        if v not in stylespace_stops[axis_tag]:
            raise ValueError(
                f"There is no Stylespace entry for stop {v} on the '{k}' axis (from "
                "additional locations)."
            )
        axis_stops[axis_tag].add(v)

    # Construct temporary name and STAT tables for returning at the end.
    name_table = copy.deepcopy(varfont["name"])
    stat_table = _new_empty_STAT_table()

    # Generate axis records. Reuse an axis' name ID if it exists, else make a new one.
    for axis_name, axis_tag in name_to_tag.items():
        stylespace_axis = stylespace_name_to_axis[axis_name]
        if axis_name in fvar_name_to_axis:
            axis_name_id = fvar_name_to_axis[axis_name].axisNameID
        else:
            axis_name_id = name_table.addMultilingualName(
                stylespace_axis.name.mapping, mac=False
            )
        axis_record = _new_axis_record(
            tag=axis_tag, name_id=axis_name_id, ordering=stylespace_axis.ordering
        )
        stat_table.table.DesignAxisRecord.Axis.append(axis_record)

    # Generate formats 1, 2 and 3.
    for axis in stylespace.axes:
        for location in axis.locations:
            if location.value not in axis_stops[axis.tag]:
                continue
            axis_value = otTables.AxisValue()
            name_id = name_table.addMultilingualName(location.name.mapping, mac=False)
            location.fill_in_AxisValue(
                axis_value, axis_index=name_to_index[axis.name.default], name_id=name_id
            )
            stat_table.table.AxisValueArray.AxisValue.append(axis_value)

    # Generate format 4.
    for named_location in stylespace.locations:
        if all(
            name_to_tag[k] in axis_stops and v in axis_stops[name_to_tag[k]]
            for k, v in named_location.axis_values.items()
        ):
            stat_table.table.Version = 0x00010002
            axis_value = otTables.AxisValue()
            name_id = name_table.addMultilingualName(
                named_location.name.mapping, mac=False
            )
            named_location.fill_in_AxisValue(
                axis_value,
                axis_name_to_index=name_to_index,
                name_id=name_id,
                axis_value_record_type=otTables.AxisValueRecord,
            )
            stat_table.table.AxisValueArray.AxisValue.append(axis_value)

    stat_table.table.ElidedFallbackNameID = stylespace.elided_fallback_name_id

    return name_table, stat_table


def _default_name_string(otfont: fontTools.ttLib.TTFont, name_id: int) -> str:
    """Return English name for name_id."""
    name = otfont["name"].getDebugName(name_id)
    if name is not None:
        return name
    raise ValueError(f"No English record for id {name_id} for Windows platform.")


def _new_empty_STAT_table():
    stat_table = fontTools.ttLib.newTable("STAT")
    stat_table.table = otTables.STAT()
    stat_table.table.Version = 0x00010001
    stat_table.table.DesignAxisRecord = otTables.AxisRecordArray()
    stat_table.table.DesignAxisRecord.Axis = []
    stat_table.table.AxisValueArray = otTables.AxisValueArray()
    stat_table.table.AxisValueArray.AxisValue = []
    return stat_table


def _new_axis_record(tag: str, name_id: int, ordering: Optional[int]):
    if ordering is None:
        raise ValueError("ordering must be an integer.")
    axis_record = otTables.AxisRecord()
    axis_record.AxisTag = fontTools.misc.py23.Tag(tag)
    axis_record.AxisNameID = name_id
    axis_record.AxisOrdering = ordering
    return axis_record
