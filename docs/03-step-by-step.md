# AI 貼圖入門模板：帶你走一遍

這份文件不是六條指路,而是帶你「實際走過」整條後處理:切片 → 去背 → 打包,每一步都自己跑、自己驗。全程**不需要 API key**,因為這幾步都是純像素 / 檔案運算,用本機合成的 fixture 圖就能做。

> 開始前先在 repo 根目錄跑過一次 `uv sync`(uv 安裝方式見 `01-quickstart.md`)。本文所有指令都用 `uv run python -c "..."` 或 `uv run python <檔>`,會在 uv 建好的 `.venv` 裡執行;`uv sync` / `uv run` 在 Ubuntu 與 Windows 完全相同。下面 bash 的多行 `python -c` 在 Windows PowerShell 用反引號或寫成單行即可。

先記住一件事:**這條管線就是「圖 → 切 → 去背 → 縮放 → 打包」**。生圖你在前置模組(生圖入門)已經會了;這裡每一步都拿一張本機綠幕 fixture 圖來練,不碰網路。

`app/sticker.py` 的核心就是這幾個函式:

- `split_grid(image_bytes)` — 把一張 grid 切成多格 tile。
- `chroma_key(im)` — 把綠幕背景去乾淨(Part 2)。
- `build_line_pack(tiles)` — 把去背後的 tile 打包成 LINE 規格 ZIP。

我們會先用 `tests/fixtures.py` 的 `make_grid_png()` 當輸入——它合成一張 3×3 綠底、每格中央一個彩色方塊的圖,專門給這條管線練。

## 步驟 1:split_grid — 把一張 grid 切成 9 格

Gemini 一次給你一張「9 個姿勢拼在一起」的 grid。第一步是切開。`split_grid` 用整除算出每格寬高,左到右、上到下 crop 出來:

```python
def split_grid(image_bytes, rows=3, cols=3):
    im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = im.size
    cw, ch = w // cols, h // rows
    tiles = []
    for r in range(rows):
        for c in range(cols):
            tiles.append(im.crop((c*cw, r*ch, c*cw+cw, r*ch+ch)))
    return tiles
```

自己跑一次(用 fixture 圖):

```bash
uv run python -c "
from app.sticker import split_grid
from tests.fixtures import make_grid_png
tiles = split_grid(make_grid_png())
print('tiles:', len(tiles))
print('each:', tiles[0].size)
"
```

真實輸出:

```
tiles: 9
each: (100, 100)
```

成功的話你會看到:`9` 格、每格 `(100, 100)`(fixture 是 300×300,3×3 整除成 100×100)。這對應 `tests/test_grid.py` 的斷言。

> 動手:把 `split_grid(make_grid_png(), rows=2, cols=2)` 改成 2×2 看會切幾格(答案 4)。grid 是幾乘幾、就傳對應的 rows/cols。

## 步驟 2:chroma_key — 把綠幕去乾淨(對照天真版)

去背是這整個模組的重點。先看 **Part 1 天真版** 為什麼不夠好。`remove_bg_naive` 只比「顏色離純綠多近」,近就設透明:

```python
def remove_bg_naive(im, key=(0,255,0), tol=80):
    arr = np.array(im.convert("RGBA"))
    dist = np.abs(arr[:, :, :3].astype(int) - np.array(key)).sum(axis=2)
    arr[:, :, 3] = np.where(dist < tol, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")
```

問題:邊緣那圈「半綠半主體」的像素離純綠不夠近,沒被去掉,就留成綠色 halo。

**Part 2 正確版** `chroma_key` 做三件事:綠幕判定 + 邊緣 erosion + despill:

```python
def chroma_key(im, erode=1):
    arr = np.array(im.convert("RGBA")).astype(int)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    is_green = (g > 90) & (g > r + 25) & (g > b + 25)     # 綠明顯壓過紅藍才算背景
    alpha = np.where(is_green, 0, 255).astype(np.uint8)
    if erode > 0:                                          # 把 alpha 邊緣往內縮,吃掉綠毛邊
        a_im = Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(1 + 2*erode))
        alpha = np.array(a_im)
    keep = alpha > 0                                       # despill:保留像素上殘留的綠壓下去
    spill = keep & (g > np.maximum(r, b))
    g2 = g.copy()
    g2[spill] = np.maximum(r, b)[spill]
    out = np.dstack([r, g2, b, alpha]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")
```

判定不是「離純綠多近」,而是「綠是否明顯壓過紅藍」,所以半透明的邊緣綠也吃得到;`MinFilter` 再把 α 邊界往內縮 1px 刮掉毛邊;despill 把保留下來、卻還偏綠的像素壓回 `max(r,b)`。

自己跑一次,比較兩版在「綠角落」和「主體中心」的 α:

```bash
uv run python -c "
import numpy as np
from app.sticker import split_grid, chroma_key, remove_bg_naive
from tests.fixtures import make_grid_png, CELL
tile = split_grid(make_grid_png())[0]
ck = np.array(chroma_key(tile))
nv = np.array(remove_bg_naive(tile))
print('chroma_key  corner alpha:', ck[2,2,3], ' center alpha:', ck[CELL//2,CELL//2,3])
print('naive       corner alpha:', nv[2,2,3], ' center alpha:', nv[CELL//2,CELL//2,3])
"
```

真實輸出:

```
chroma_key  corner alpha: 0  center alpha: 255
naive       corner alpha: 0  center alpha: 255
```

成功的話你會看到:兩版都把綠角落設成透明(α=0)、主體中心保留(α=255)。fixture 用的是純色方塊,所以兩版在「中心 vs 角落」都過;差別在真實照片的**邊緣 halo**——`chroma_key` 的 erosion + despill 才看得出來。這對應 `tests/test_chroma.py` 的斷言。

> 動手:把 `chroma_key(tile, erode=0)` 關掉 erosion,再跑一次,確認角落仍 α=0、中心仍 α=255(erosion 只動邊界,不動這兩點)。

## 步驟 3:build_line_pack — 打包成 LINE 規格 ZIP

最後一步把去背後的 tile 縮放置中、塞進一個可上架的 ZIP。先看 `fit_pad`(等比縮放後置中到透明畫布,輸出剛好目標尺寸):

```python
def fit_pad(im, size):
    im = im.copy()
    im.thumbnail(size, Image.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(im, ((size[0]-im.width)//2, (size[1]-im.height)//2), im)
    return canvas
```

`build_line_pack` 取前 8 張各 `fit_pad` 到貼圖規格寫進 ZIP,再加 `main.png`、`tab.png`:

```python
STICKER, MAIN, TAB = (370, 320), (240, 240), (96, 74)

def build_line_pack(tiles):
    stickers = tiles[:8]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, t in enumerate(stickers, 1):
            z.writestr(f"{i:02d}.png", _png(fit_pad(t, STICKER)))
        z.writestr("main.png", _png(fit_pad(stickers[0], MAIN)))
        z.writestr("tab.png",  _png(fit_pad(stickers[0], TAB)))
    return buf.getvalue()
```

自己跑一次,檢查 ZIP 裡的檔名與尺寸:

```bash
uv run python -c "
import io, zipfile
from PIL import Image
from app.sticker import split_grid, chroma_key, build_line_pack
from tests.fixtures import make_grid_png
tiles = [chroma_key(t) for t in split_grid(make_grid_png())]
z = zipfile.ZipFile(io.BytesIO(build_line_pack(tiles)))
print('names:', z.namelist())
sz = lambda n: Image.open(io.BytesIO(z.read(n))).size
print('01.png:', sz('01.png'), ' main.png:', sz('main.png'), ' tab.png:', sz('tab.png'))
"
```

真實輸出:

```
names: ['01.png', '02.png', '03.png', '04.png', '05.png', '06.png', '07.png', '08.png', 'main.png', 'tab.png']
01.png: (370, 320)  main.png: (240, 240)  tab.png: (96, 74)
```

成功的話你會看到:8 張 `01.png`–`08.png` + `main.png` + `tab.png`,且尺寸分別是 370×320 / 240×240 / 96×74——正好是 LINE 規格。這對應 `tests/test_pack.py` 的斷言。

> 為什麼只取 8 張?LINE 一組貼圖最少 8 張,所以 `build_line_pack` 固定取前 8 張;grid 是 3×3 給你 9 張,多的那張這裡不打包(你可以改成做更多張的大組)。

## 步驟 4:一次跑完全部驗證

上面三步分別對應 `tests/` 裡的三個檔,加上「對假 Gemini server 取 grid」的 `test_gen_fake.py`。一次跑完:

```bash
uv run python client_smoke_test.py
```

真實輸出:

```
== tests/test_grid.py ==
OK: grid split test passed

== tests/test_chroma.py ==
OK: chroma key test passed

== tests/test_pack.py ==
OK: LINE pack test passed

== tests/test_gen_fake.py ==
OK: gen grid against fake Gemini server passed

OK: all checks passed
```

看到 `OK: all checks passed` 就代表你親手走過的這條管線(切 → 去背 → 打包 + 生圖串接)全綠。

## 動手練習

換你動手把「正確版」整條串起來,輸出一個真的 ZIP 檔(仍然免 key,用 fixture 圖當輸入):

```bash
uv run python -c "
from app.sticker import split_grid, chroma_key, build_line_pack
from tests.fixtures import make_grid_png
tiles = [chroma_key(t) for t in split_grid(make_grid_png())]
open('my_pack.zip','wb').write(build_line_pack(tiles))
print('wrote my_pack.zip')
"
```

預期你會看到 `wrote my_pack.zip`,而且解開來裡面就是上面那 10 個檔。把 `make_grid_png()` 換成「你真的用 Gemini 生出來的 grid bytes」,就是 `demo_sticker.py` 在做的事——那一步要 key,見 `04-deployment.md`。
