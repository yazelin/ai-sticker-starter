#!/usr/bin/env python3
"""Background cut-out tests. Deterministic, no key, no network."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.sticker import chroma_key, remove_bg_naive, split_grid  # noqa: E402
from tests.fixtures import CELL, make_grid_png  # noqa: E402


def main():
    tile = split_grid(make_grid_png())[0]  # green bg + a centered coloured square

    # Part 2 chroma_key: green corner -> transparent, subject center -> opaque
    out = np.array(chroma_key(tile))
    assert out[2, 2, 3] == 0, "corner (green) should be transparent"
    assert out[CELL // 2, CELL // 2, 3] == 255, "center (subject) should be opaque"

    # Part 1 naive also clears the green corner (but is cruder)
    naive = np.array(remove_bg_naive(tile))
    assert naive[2, 2, 3] == 0, "naive should also clear the green corner"
    assert naive[CELL // 2, CELL // 2, 3] == 255, "naive keeps the subject center"

    print("OK: chroma key test passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
