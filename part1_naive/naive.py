"""Part 1 baseline: split + crude threshold cut-out.

Generates a grid, splits it, and removes the green with a naive colour
threshold. It runs -- but you get green halos around the edges and the singles
are not sized for LINE. That is the pain Part 2 (chroma_key + LINE pack) fixes.

    GEMINI_API_KEY=xxx uv run python part1_naive/naive.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.gen import generate_grid  # noqa: E402
from app.sticker import remove_bg_naive, split_grid  # noqa: E402

PROMPT = (
    "a 3x3 grid of one cute mascot character in 9 different poses and expressions, "
    "flat solid pure green (#00ff00) background, consistent character"
)


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("set GEMINI_API_KEY first (free: https://aistudio.google.com/apikey)")
        sys.exit(1)
    grid = generate_grid(PROMPT, key)
    for i, tile in enumerate(split_grid(grid), 1):
        remove_bg_naive(tile).save(f"naive_{i:02d}.png")
    print("saved naive_01.png .. naive_09.png  (note the green halos + wrong sizes)")


if __name__ == "__main__":
    main()
