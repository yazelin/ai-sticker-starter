#!/usr/bin/env python3
"""Split a fixture grid into tiles. Deterministic, no key, no network."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.sticker import split_grid  # noqa: E402
from tests.fixtures import CELL, make_grid_png  # noqa: E402


def main():
    tiles = split_grid(make_grid_png(), rows=3, cols=3)
    assert len(tiles) == 9, len(tiles)
    assert all(t.size == (CELL, CELL) for t in tiles), [t.size for t in tiles]
    print("OK: grid split test passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
