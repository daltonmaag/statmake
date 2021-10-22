from pathlib import Path

from statmake.classes import Stylespace


def test_serialize(datadir: Path) -> None:
    stylespace = Stylespace.from_file(datadir / "Test.stylespace")
    stylespace_rt = Stylespace.from_dict(stylespace.to_dict())
    assert stylespace == stylespace_rt
