#!/usr/bin/env python3
"""LINE-spec ZIP packaging test. Deterministic, no key, no network."""
import io
import pathlib
import sys
import zipfile

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.sticker import MAIN, STICKER, TAB, build_line_pack, chroma_key, split_grid  # noqa: E402
from tests.fixtures import make_grid_png  # noqa: E402


def main():
    tiles = [chroma_key(t) for t in split_grid(make_grid_png())]
    zbytes = build_line_pack(tiles)

    z = zipfile.ZipFile(io.BytesIO(zbytes))
    names = z.namelist()
    expected = [f"{i:02d}.png" for i in range(1, 9)] + ["main.png", "tab.png"]
    assert names == expected, names

    def size(n):
        return Image.open(io.BytesIO(z.read(n))).size

    assert size("01.png") == STICKER, size("01.png")
    assert size("main.png") == MAIN, size("main.png")
    assert size("tab.png") == TAB, size("tab.png")

    print("OK: LINE pack test passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
