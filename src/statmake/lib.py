import collections
from typing import Any, Dict, List, Mapping, Set, Tuple

import fontTools.otlLib.builder
import fontTools.ttLib

import statmake.classes


def apply_stylespace_to_variable_font(
    stylespace: statmake.classes.Stylespace,
    varfont: fontTools.ttLib.TTFont,
    additional_locations: Mapping[str, float],
) -> None:
    """Generate and apply a STAT table to a variable font.

    additional_locations: used in subset Designspaces to express where on which other
    axes not defined by an <axis> element the varfont stands. The primary use-case is
    defining a complete STAT table for variable fonts that do not include all axes of a
    family (either because they intentionally contain just a subset of axes or because
    the designs are incompatible).
    """

    axes, locations, elided_fallback_name = _generate_axes_and_locations_dict(
        stylespace, varfont, additional_locations
    )
    fontTools.otlLib.builder.buildStatTable(
        varfont, axes, locations, elided_fallback_name
    )


def _generate_axes_and_locations_dict(
    stylespace: statmake.classes.Stylespace,
    varfont: fontTools.ttLib.TTFont,
    additional_locations: Mapping[str, float],
) -> Tuple[List[Mapping[str, Any]], List[Mapping[str, Any]], int]:
    """Generate axes and locations dictionaries for use in
    fontTools.otlLib.builder.buildStatTable, tailored to the font."""

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

    # Generate formats 1, 2 and 3.
    otlLib_axes: List[Mapping[str, Any]] = []
    for axis in stylespace.axes:
        otlLib_axis_locations = []
        for location in axis.locations:
            if location.value not in axis_stops[axis.tag]:
                continue

            if isinstance(location, statmake.classes.LocationFormat1):
                otlLib_axis_locations.append(
                    {
                        "name": location.name.mapping,
                        "value": location.value,
                        "flags": location.flags.value,
                    }
                )
            elif isinstance(location, statmake.classes.LocationFormat2):
                otlLib_axis_locations.append(
                    {
                        "name": location.name.mapping,
                        "nominalValue": location.value,
                        "rangeMinValue": location.range[0],
                        "rangeMaxValue": location.range[1],
                        "flags": location.flags.value,
                    }
                )
            elif isinstance(location, statmake.classes.LocationFormat3):
                otlLib_axis_locations.append(
                    {
                        "name": location.name.mapping,
                        "value": location.value,
                        "linkedValue": location.linked_value,
                        "flags": location.flags.value,
                    }
                )
            else:
                raise ValueError("...")

        otlLib_axes.append(
            {
                "tag": axis.tag,
                "name": axis.name.mapping,
                "ordering": axis.ordering,
                "values": otlLib_axis_locations,
            }
        )

    # Generate format 4.
    otlLib_locations: List[Mapping[str, Any]] = []
    for named_location in stylespace.locations:
        if all(
            name_to_tag[k] in axis_stops and v in axis_stops[name_to_tag[k]]
            for k, v in named_location.axis_values.items()
        ):
            otlLib_locations.append(
                {
                    "name": named_location.name.mapping,
                    "location": {
                        name_to_tag[k]: v for k, v in named_location.axis_values.items()
                    },
                    "flags": named_location.flags.value,
                }
            )

    return otlLib_axes, otlLib_locations, stylespace.elided_fallback_name_id


def _default_name_string(otfont: fontTools.ttLib.TTFont, name_id: int) -> str:
    """Return English name for name_id."""
    name = otfont["name"].getDebugName(name_id)
    if name is not None:
        return name
    raise ValueError(f"No English record for id {name_id} for Windows platform.")
