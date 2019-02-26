import argparse
import sys
from pathlib import Path

import fontTools.designspaceLib
import fontTools.ttLib

import statmake.classes
import statmake.lib


def main(args=None):
    if not args:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stylespace_file", type=Path, help="The path to the Stylespace file."
    )
    parser.add_argument(
        "designspace_file",
        type=Path,
        help="The path to the Designspace file used to generate the variable font.",
    )
    parser.add_argument(
        "variable_font", type=Path, help="The path to the variable font file."
    )
    parsed_args = parser.parse_args(args)

    stylespace = statmake.classes.Stylespace.from_file(parsed_args.stylespace_file)
    designspace = fontTools.designspaceLib.DesignSpaceDocument.fromfile(
        parsed_args.designspace_file
    )
    additional_locations = designspace.lib.get("org.statmake.additionalLocations", {})

    font = fontTools.ttLib.TTFont(parsed_args.variable_font)
    statmake.lib.apply_stylespace_to_variable_font(
        stylespace, font, additional_locations
    )
    font.save(parsed_args.variable_font)
