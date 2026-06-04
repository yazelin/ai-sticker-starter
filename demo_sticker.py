"""Part 2: the full pipeline -> a ready-to-upload LINE sticker ZIP.

    GEMINI_API_KEY=xxx uv run python demo_sticker.py

grid -> split -> chroma_key (clean cut-out) -> LINE-spec pack -> sticker_pack.zip
"""
import os
import sys

from app.gen import generate_grid
from app.sticker import build_line_pack, chroma_key, split_grid

PROMPT = (
    "a 3x3 grid of one cute mascot character in 9 different poses and expressions, "
    "flat solid pure green (#00ff00) background, consistent character, sticker style"
)


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("(set GEMINI_API_KEY to actually generate: https://aistudio.google.com/apikey)")
        return
    grid = generate_grid(PROMPT, key)
    tiles = [chroma_key(t) for t in split_grid(grid)]
    with open("sticker_pack.zip", "wb") as f:
        f.write(build_line_pack(tiles))
    print("saved sticker_pack.zip  (drag into LINE Creators Market)")


if __name__ == "__main__":
    main()
