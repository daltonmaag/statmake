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
    fontTools.otlLib.builder.buildStatTable, tailored to the font.

    Rules:
        1. There must be a fvar table so we know which named instances are defined.
            Every named instance needs a STAT entry for every point of its axis
            definition, i.e. an instance at {"Weight": 300, "Slant": 5} must have a
            Stylespace entry for Weight=300 and for Slant=5.
        2. The Stylespace must contain all axis tags the varfont does.
        3. All name IDs must have a default English (United States) entry for the
            Windows platform, Unicode BMP encoding, to match axis names to tags.

    XXX: Enforce that all namerecords must have the same language keys at Stylespace
    instantiation time?
    """

    # XXX ensure all namerecords have default "en" name we use to map names -> tags
    # XXX in varfont compare them to (name.platformID, name.langID) == (3, 0x409) nameID to map axis names -> axis tags

    _sanity_check(stylespace, varfont, additional_locations)

    # Match the plain English names for the axis in the Stylespace to the axis names
    # in the font.
    stylespace_name_to_axis = {a.name.default: a for a in stylespace.axes}
    fvar_name_to_axis = {}
    name_to_tag: Dict[str, str] = {}
    for fvar_axis in varfont["fvar"].axes:
        fvar_axis_name = _default_name_string(varfont, fvar_axis.axisNameID)
        try:
            stylespace_axis = stylespace_name_to_axis[fvar_axis_name]
        except KeyError:
            raise ValueError(
                f"No stylespace entry found for axis name '{fvar_axis_name}'."
            )
        # Check that axes with the same name have the same tag.
        if fvar_axis.axisTag != stylespace_axis.tag:
            raise ValueError(
                f"fvar axis '{fvar_axis_name}' tag is '{fvar_axis.axisTag}', but "
                f"Stylespace tag is '{stylespace_axis.tag}'."
            )
        fvar_name_to_axis[fvar_axis_name] = fvar_axis
        name_to_tag[fvar_axis_name] = fvar_axis.axisTag

    for axis_name in additional_locations:
        try:
            stylespace_axis = stylespace_name_to_axis[axis_name]
        except KeyError:
            raise ValueError(f"No stylespace entry found for axis name '{axis_name}'.")
        name_to_tag[stylespace_axis.name.default] = stylespace_axis.tag

    # # Make sure that all tags present in the Stylespace are accounted for.
    # font_axes = {axis.axisTag for axis in varfont["fvar"].axes}.union(
    #     {name_to_tag[a] for a in additional_locations}
    # )
    # stylespace_axes = {a.tag for a in stylespace.axes}
    # if stylespace_axes != font_axes:
    #     missing_axes = ", ".join(stylespace_axes - font_axes)
    #     raise ValueError(
    #         f"Stylespace is missing definitions for axes with the tags: {missing_axes}."
    #     )

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


def _sanity_check(
    stylespace: statmake.classes.Stylespace,
    varfont: fontTools.ttLib.TTFont,
    additional_locations: Mapping[str, float],
) -> None:
    if "fvar" not in varfont:
        raise ValueError(
            "Need a variable font with the fvar table to determine which instances "
            "are present."
        )

    # Sanity check: only allow axis names in additional_locations that are present in
    # the Stylespace.
    stylespace_name_to_tag = {a.name.default: a.tag for a in stylespace.axes}
    stylespace_names_set = set(stylespace_name_to_tag.keys())
    additional_names_set = set(additional_locations.keys())
    if not additional_names_set.issubset(stylespace_names_set):
        surplus_keys = ", ".join(additional_names_set - stylespace_names_set)
        raise ValueError(
            "Additional locations must only contain axis names that are present in "
            f"the Stylespace, the following aren't: {surplus_keys}."
        )

    # Sanity check: Ensure all font axes are present in the Stylespace and tags match.
    font_name_to_tag = {
        _default_name_string(varfont, axis.axisNameID): axis.axisTag
        for axis in varfont["fvar"].axes
    }
    for name, tag in font_name_to_tag.items():
        if name not in stylespace_name_to_tag:
            raise ValueError(
                f"Font contains axis named '{name}' which is not in Stylespace. The "
                "Stylespace must contain all axes any font from the same family "
                "contains."
            )
        if stylespace_name_to_tag[name] != tag:
            raise ValueError(
                f"Font axis named '{name}' has tag '{tag}' but Stylespace defines it "
                f"to be {stylespace_name_to_tag[name]}. Axis names and tags must match "
                "between the font and the Stylespace."
            )

    # Sanity check: Ensure the location of the font is fully specified. This means
    # the font axis names plus additional_locations axis names must equal Stylespace
    # axis names.
    font_names_set = set(font_name_to_tag.keys()).union(additional_names_set)
    if font_names_set != stylespace_names_set:
        missing_axis_names = ", ".join(stylespace_names_set - font_names_set)
        raise ValueError(
            "The location of the font is not fully specified, missing locations "
            f"for the following axes: {missing_axis_names}"
        )


def _font_axis_tags(font: fontTools.ttLib.TTFont) -> Set[str]:
    return {axis.axisTag for axis in font["fvar"].axes}


def _default_name_string(otfont: fontTools.ttLib.TTFont, name_id: int) -> str:
    """Return English name for name_id."""
    name = otfont["name"].getName(name_id, 3, 1, 0x409)
    if name is None:
        raise ValueError(f"No English record for id {name_id} for Windows platform.")
    return name.toStr()
