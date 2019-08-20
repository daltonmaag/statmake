# statmake

`statmake` takes a user-written Stylespace that defines [OpenType `STAT` information](https://docs.microsoft.com/en-us/typography/opentype/spec/stat) for an entire font family and then (potentially subsets and) applies it to a specific variable font. This spares users from having to deal with [raw TTX dumps](https://github.com/fonttools/fonttools/) and juggling with nameIDs.

## Installation

The easiest way is by installing it with `pip`. You need at least Python 3.6.

```
pip3 install statmake
```

## Usage

1. Write a Stylespace file that describes each stop of all axes available in the entire family. See [tests/data/Test.stylespace](tests/data/Test.stylespace) for an annotated example.
2. If you have one or more Designspace files which do not define all axes available to the family, you have to annotate them with the missing axis locations to get a complete `STAT` table. See the lib key at the bottom of [tests/data/Test_Wght_Upright.designspace](tests/data/Test_Wght_Upright.designspace) and [tests/data/Test_Wght_Italic.designspace](tests/data/Test_Wght_Italic.designspace) for an example.
3. Generate the variable font(s) as normal
4. Run `statmake your.stylespace variable_font.designspace variable_font.ttf`. Take care to use the Designspace file that was used to generate the font to get the correct missing axis location definitions.

### Q: Can I please have something other than a .plist file?

Yes, but you have to convert it to `.plist` yourself, as statmake currently only read `.plist` files. One possible converter is Adam Twardoch's [yaplon](https://pypi.org/project/yaplon/).
