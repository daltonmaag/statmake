import enum
import functools
import os
from pathlib import Path
from typing import Any, List, Mapping, Optional, Tuple, Union

import attr
import cattr
import fontTools.designspaceLib
import fontTools.misc.plistlib

DESIGNSPACE_STYLESPACE_INLINE_KEY = "org.statmake.stylespace"
DESIGNSPACE_STYLESPACE_PATH_KEY = "org.statmake.stylespacePath"


class AxisValueFlag(enum.Flag):
    OlderSiblingFontAttribute = 0x0001
    ElidableAxisValueName = 0x0002


@attr.s(auto_attribs=True, frozen=True, slots=True)
class FlagList:
    """Represent a list of AxisValueFlags so I can implement a value
    property."""

    flags: List[AxisValueFlag] = attr.ib(factory=list)

    @property
    def value(self) -> int:
        """Return the value of all flags ORed together."""
        if not self.flags:
            return 0
        return functools.reduce(lambda x, y: x | y, self.flags).value


@attr.s(auto_attribs=True, frozen=True, slots=True)
class NameRecord:
    """Represent a IETF BCP 47 language code to name string mapping for the
    `name` table."""

    mapping: Mapping[str, str]

    def __getitem__(self, key):
        return self.mapping.__getitem__(key)

    @property
    def default(self):
        return self.mapping["en"]

    @classmethod
    def from_string(cls, name: str):
        return cls(mapping={"en": name})

    @classmethod
    def from_dict(cls, dictionary: Mapping):
        return cls(mapping=dictionary)

    @classmethod
    def structure(cls, data):
        if isinstance(data, str):
            return cls.from_string(data)
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise ValueError(f"Don't know how to construct NameRecord from '{data}'.")


@attr.s(auto_attribs=True, frozen=True, slots=True)
class LocationFormat1:
    name: NameRecord
    value: float
    flags: FlagList = attr.ib(factory=FlagList)

    def fill_in_AxisValue(self, axis_value: Any, axis_index: int, name_id: int):
        """Fill in a supplied fontTools AxisValue object."""
        axis_value.Format = 1
        axis_value.AxisIndex = axis_index
        axis_value.ValueNameID = name_id
        axis_value.Value = self.value
        axis_value.Flags = self.flags.value
        return axis_value


@attr.s(auto_attribs=True, frozen=True, slots=True)
class LocationFormat2:
    name: NameRecord
    value: float
    range: Tuple[float, float]
    flags: FlagList = attr.ib(factory=FlagList)

    def __attrs_post_init__(self):
        if len(self.range) != 2:
            raise ValueError("Range must be a value pair of (min, max).")

    def fill_in_AxisValue(self, axis_value: Any, axis_index: int, name_id: int):
        """Fill in a supplied fontTools AxisValue object."""
        axis_value.Format = 2
        axis_value.AxisIndex = axis_index
        axis_value.ValueNameID = name_id
        axis_value.NominalValue = self.value
        axis_value.RangeMinValue, axis_value.RangeMaxValue = self.range
        axis_value.Flags = self.flags.value
        return axis_value


@attr.s(auto_attribs=True, frozen=True, slots=True)
class LocationFormat3:
    name: NameRecord
    value: float
    linked_value: float
    flags: FlagList = attr.ib(factory=FlagList)

    def fill_in_AxisValue(self, axis_value: Any, axis_index: int, name_id: int):
        """Fill in a supplied fontTools AxisValue object."""
        axis_value.Format = 3
        axis_value.AxisIndex = axis_index
        axis_value.ValueNameID = name_id
        axis_value.Value = self.value
        axis_value.LinkedValue = self.linked_value
        axis_value.Flags = self.flags.value
        return axis_value


@attr.s(auto_attribs=True, frozen=True, slots=True)
class LocationFormat4:
    name: NameRecord
    axis_values: Mapping[str, float]
    flags: FlagList = attr.ib(factory=FlagList)

    def fill_in_AxisValue(
        self,
        axis_value: Any,
        axis_name_to_index: Mapping[str, int],
        name_id: int,
        axis_value_record_type: Any,
    ):
        """Fill in a supplied fontTools AxisValue object."""
        axis_value.Format = 4
        axis_value.ValueNameID = name_id
        axis_value.Flags = self.flags.value
        axis_value.AxisValueRecord = []
        for name, value in self.axis_values.items():
            record = axis_value_record_type()
            record.AxisIndex = axis_name_to_index[name]
            record.Value = value
            axis_value.AxisValueRecord.append(record)
        return axis_value


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Axis:
    name: NameRecord
    tag: str
    locations: List[Union[LocationFormat1, LocationFormat2, LocationFormat3]] = attr.ib(
        factory=list
    )
    ordering: Optional[int] = None


@attr.s(auto_attribs=True, frozen=True, slots=True)
class Stylespace:
    axes: List[Axis]
    locations: List[LocationFormat4] = attr.ib(factory=list)
    elided_fallback_name_id: int = 2

    def __attrs_post_init__(self):
        """Fill in a default ordering unless the user specified at least one
        custom one.

        This works around the frozen state with `object.__setattr__`.
        """
        if all(axis.ordering is None for axis in self.axes):
            for index, axis in enumerate(self.axes):
                object.__setattr__(axis, "ordering", index)
        elif not all(
            isinstance(axis.ordering, int) and axis.ordering >= 0 for axis in self.axes
        ):
            raise ValueError(
                "If you specify the ordering for one axis, you must specify all of "
                "them and they must be >= 0."
            )

    @classmethod
    def from_dict(cls, dict_data: dict):
        """Construct Stylespace from unstructured dict data."""
        converter = cattr.Converter()
        converter.register_structure_hook(
            FlagList,
            lambda list_of_str_flags, cls: cls(
                [getattr(AxisValueFlag, f) for f in list_of_str_flags]
            ),
        )
        converter.register_structure_hook(
            NameRecord, lambda data, cls: cls.structure(data)
        )
        return converter.structure(dict_data, cls)

    @classmethod
    def from_bytes(cls, stylespace_content: bytes):
        """Construct Stylespace from bytes containing (XML) plist data."""
        stylespace_content_parsed = fontTools.misc.plistlib.loads(stylespace_content)
        return cls.from_dict(stylespace_content_parsed)

    @classmethod
    def from_file(cls, stylespace_path: os.PathLike):
        """Construct Stylespace from path to (XML) plist file."""
        with open(stylespace_path, "rb") as fp:
            return cls.from_bytes(fp.read())

    @classmethod
    def from_designspace(
        cls, designspace: fontTools.designspaceLib.DesignSpaceDocument
    ):
        f"""Construct Stylespace from unstructured dict data or a path stored in a
        Designspace object's lib.

        The keys:

        - `{DESIGNSPACE_STYLESPACE_INLINE_KEY}`: The content of a regular Stylespace
          file as a dict.
        - `{DESIGNSPACE_STYLESPACE_PATH_KEY}`: A path to an external Stylespace file,
          relative to the Designspace file (the Designspace object must have the `path`
          attribute set).
        """
        stylespace_inline = designspace.lib.get(DESIGNSPACE_STYLESPACE_INLINE_KEY)
        stylespace_path = designspace.lib.get(DESIGNSPACE_STYLESPACE_PATH_KEY)

        if (stylespace_inline and stylespace_path) or (
            not stylespace_inline and not stylespace_path
        ):
            raise ValueError(
                "Designspace lib must contain EITHER inline Stylespace data OR a path "
                "to an external Stylespace file."
            )

        if stylespace_inline:
            return cls.from_dict(stylespace_inline)

        if not designspace.path:
            raise ValueError(
                "Designspace object must have `path` attribute set, because the "
                "Stylespace path is relative to the Designspace file."
            )
        stylespace_path_lookup = Path(designspace.path).parent / stylespace_path
        return cls.from_file(stylespace_path_lookup)
