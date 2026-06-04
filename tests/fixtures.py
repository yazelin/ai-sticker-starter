"""Deterministic test fixture: a 3x3 green-screen grid with a coloured square
in each cell, so the cut-out / split / pack steps have something real to chew on
without calling any API.
"""
import io

from PIL import Image, ImageDraw

CELL = 100
ROWS = 3
COLS = 3
GREEN = (0, 255, 0, 255)
COLORS = [
    (220, 40, 40), (40, 80, 220), (230, 180, 30),
    (150, 40, 180), (40, 170, 120), (230, 110, 40),
    (60, 60, 60), (200, 60, 140), (40, 160, 210),
]


def make_grid_png() -> bytes:
    """A COLS*CELL x ROWS*CELL green grid, each cell a centered 50x50 square."""
    im = Image.new("RGBA", (COLS * CELL, ROWS * CELL), GREEN)
    draw = ImageDraw.Draw(im)
    for i in range(ROWS * COLS):
        r, c = divmod(i, COLS)
        x0, y0 = c * CELL + 25, r * CELL + 25
        draw.rectangle([x0, y0, x0 + 49, y0 + 49], fill=COLORS[i] + (255,))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()
