#!/usr/bin/env python3
"""End-to-end: gen a grid from the fake Gemini server, then split it.
No API key, no network."""
import io
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.gen import generate_grid  # noqa: E402
from app.sticker import split_grid  # noqa: E402
from tests.fake_gemini import start  # noqa: E402
from tests.fixtures import make_grid_png  # noqa: E402


def main():
    server, base_url = start()
    try:
        grid = generate_grid("a green-screen 3x3 grid of poses", api_key="fake-key", base_url=base_url)
        assert Image.open(io.BytesIO(grid)).size == Image.open(io.BytesIO(make_grid_png())).size
        tiles = split_grid(grid)
        assert len(tiles) == 9, len(tiles)
        print("OK: gen grid against fake Gemini server passed")
    finally:
        server.shutdown()


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
