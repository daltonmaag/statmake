# statmake

`statmake` takes a user-written Stylespace that defines [OpenType `STAT` information](https://docs.microsoft.com/en-us/typography/opentype/spec/stat) for an entire font family and then (potentially subsets and) applies it to a specific variable font. This spares users from having to deal with [raw TTX dumps](https://github.com/fonttools/fonttools/) and juggling with nameIDs.

## Installation

The easiest way is by installing it with `pip`. You need at least Python 3.8.

```
pip3 install statmake
```

## Usage


### External Stylespace file, stand-alone or referenced from a Designspace file

If you are producing more than one variable font (i.e. you have multiple Designspace files), you can avoid duplicated information by writing a single all-encompassing Stylespace file which statmake will subset for each variable font.

**Attention:** A `STAT` table is supposed to describe a font's relationship to the _entire_ family. If you have separate upright and italic variable fonts with a `wght` axis each, you need to mark each font's position on the `ital` axis _in the Designspace lib `org.statmake.additionalLocations` key_. The Designspace `<axes>` elements are not supposed to hold this information, so it must be done in a separate lib key.

1. Write a Stylespace file that describes each stop of all axes available in the entire family. See [tests/data/Test.stylespace](tests/data/Test.stylespace) for an annotated example. You can also use it as a starting point.
2. You can have the file stand-alone or use the Designspace lib's `org.statmake.stylespacePath` key to store the path to the Stylespace file relative to the Designspace file. See [tests/data/TestExternalStylespace.designspace](tests/data/TestExternalStylespace.designspace) for an example.
3. If you have one or more Designspace files which do not define all axes available to the family, you have to annotate them with the missing axis locations to get a complete `STAT` table. See the lib key at the bottom of [tests/data/Test_Wght_Upright.designspace](tests/data/Test_Wght_Upright.designspace) and [tests/data/Test_Wght_Italic.designspace](tests/data/Test_Wght_Italic.designspace) for an example.
4. Generate the variable font(s) as normal
5. If...
    1. ... you store the Stylespace file stand-alone: run `statmake --designspace variable_font.designspace --stylespace your.stylespace variable_font.ttf`.
    2. ... you store the Stylespace inline in the Designspace file or as a stand-alone file and added the relative path to it in the Designspace's `org.statmake.stylespacePath` key: run `statmake --designspace variable_font.designspace variable_font.ttf`

Be sure to use the Designspace file that was used to generate the font to get the correct missing axis location definitions.

### Designspace file with inline Stylespace data

If you are producing a single variable font containing an entire family, this approach will save you an external file.

1. Write the file as above, point 1.
2. Insert it into the Designspace file's lib under the `org.statmake.stylespace` key. See [tests/data/TestInlineStylespace.designspace](tests/data/TestInlineStylespace.designspace) for an example.
3. Proceed from point 3 above.

## Q: Can I please have something other than a .plist file?

Yes, but you have to convert it to `.plist` yourself, as statmake currently only read `.plist` files. One possible converter is Adam Twardoch's [yaplon](https://pypi.org/project/yaplon/).

## Q: I'm getting errors about how statmake doesn't like the way I wrote the Stylespace, but I want the data to be that way?

Use a custom script with the https://fonttools.readthedocs.io/en/latest/otlLib/builder.html#fontTools.otlLib.builder.buildStatTable API instead.

## Development setup

The project uses `uv`; install it from https://docs.astral.sh/uv/, and then:

```bash
# Install this project and its dependencies
uv sync
# Install tox globally for your user with uv support (if your other projects use it too)
uv tool install tox --with tox-uv
# Run tests on various Python versions
tox
```