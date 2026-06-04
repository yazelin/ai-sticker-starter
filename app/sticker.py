"""Turn a green-screen grid into a LINE-spec sticker pack.

The pipeline after generation is where the real craft lives:

    grid PNG  ->  split into tiles  ->  cut out the background  ->  pad/resize
              ->  pack into a LINE-spec ZIP

`remove_bg_naive` is the Part 1 baseline (a crude colour threshold: leaves green
halos). `chroma_key` is the Part 2 version (green-screen removal + despill +
1px edge erosion). Everything here is pure pixel/file work, so it tests
deterministically against a fixture image with no API key.
"""
from __future__ import annotations

import io
import zipfile

import numpy as np
from PIL import Image, ImageFilter

# LINE Creators Market sizes (max bounds)
STICKER = (370, 320)
MAIN = (240, 240)
TAB = (96, 74)


def split_grid(image_bytes: bytes, rows: int = 3, cols: int = 3) -> list[Image.Image]:
    """Cut a grid image into rows*cols tiles (RGBA), left-to-right, top-to-bottom."""
    im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = im.size
    cw, ch = w // cols, h // rows
    tiles = []
    for r in range(rows):
        for c in range(cols):
            tiles.append(im.crop((c * cw, r * ch, c * cw + cw, r * ch + ch)))
    return tiles


def remove_bg_naive(im: Image.Image, key=(0, 255, 0), tol: int = 80) -> Image.Image:
    """Part 1: crude threshold. Pixels near the key colour become transparent.
    Fast to write, but leaves green fringe/halos at the edges."""
    arr = np.array(im.convert("RGBA"))
    dist = np.abs(arr[:, :, :3].astype(int) - np.array(key)).sum(axis=2)
    arr[:, :, 3] = np.where(dist < tol, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def chroma_key(im: Image.Image, erode: int = 1) -> Image.Image:
    """Part 2: green-screen removal + despill + edge erosion -> clean cut-out."""
    arr = np.array(im.convert("RGBA")).astype(int)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    is_green = (g > 90) & (g > r + 25) & (g > b + 25)
    alpha = np.where(is_green, 0, 255).astype(np.uint8)
    if erode > 0:
        a_im = Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(1 + 2 * erode))
        alpha = np.array(a_im)
    # despill: pull leftover green down toward max(r,b) on kept pixels
    keep = alpha > 0
    spill = keep & (g > np.maximum(r, b))
    g2 = g.copy()
    g2[spill] = np.maximum(r, b)[spill]
    out = np.dstack([r, g2, b, alpha]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def fit_pad(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize keeping aspect ratio, centered on a transparent canvas of `size`."""
    im = im.copy()
    im.thumbnail(size, Image.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2), im)
    return canvas


def _png(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def build_line_pack(tiles: list[Image.Image]) -> bytes:
    """Pack the first 8 cut-out tiles into a LINE-spec sticker ZIP (bytes)."""
    stickers = tiles[:8]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, t in enumerate(stickers, 1):
            z.writestr(f"{i:02d}.png", _png(fit_pad(t, STICKER)))
        z.writestr("main.png", _png(fit_pad(stickers[0], MAIN)))
        z.writestr("tab.png", _png(fit_pad(stickers[0], TAB)))
    return buf.getvalue()
