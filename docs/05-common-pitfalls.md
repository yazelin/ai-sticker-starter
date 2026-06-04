# AI 貼圖入門模板:常見踩雷清單

這些是「把一張生圖做成 LINE 貼圖組」時真的會踩到的坑,附上真實症狀與修法。整條後處理是純像素/檔案運算,所以你可以**不用 API key** 就重現大多數問題:`uv run python client_smoke_test.py`。

## 1. 綠幕沒打乾淨,邊緣留一圈綠 halo

Part 1 的 `remove_bg_naive` 用「顏色距離門檻」去背:像素跟純綠 `(0,255,0)` 的距離小於 `tol`(預設 80)就設成透明,其餘全保留。

```python
# app/sticker.py
dist = np.abs(arr[:, :, :3].astype(int) - np.array(key)).sum(axis=2)
arr[:, :, 3] = np.where(dist < tol, 0, 255).astype(np.uint8)
```

症狀:主體輪廓外圍留一圈半綠的毛邊。因為 Gemini 生的綠底不是死板的 `#00ff00`——壓縮、抗鋸齒、陰影會讓邊緣出現「介於綠和主體之間」的過渡色。這些過渡色距離純綠 > `tol`,沒被去掉,就成了 halo。

為什麼調 `tol` 不能根治:`tol` 調大會把主體裡偏綠的部分一起挖掉(破洞);調小則 halo 更明顯。單一門檻在「全留」和「全去」之間沒有中間地帶。

怎麼修:改用 Part 2 的 `chroma_key`。它不是比「離純綠多近」,而是判斷「這個像素綠不綠」(綠通道明顯高過紅、藍),再用 erosion + despill 處理邊緣(見下一條)。

## 2. 沒做 despill,主體邊緣整圈偏綠

就算 alpha 已經切對(該透明的透明、該保留的保留),**保留下來的邊緣像素本身可能就是偏綠的**——綠幕的綠光「溢」到主體邊緣(spill)。只去 alpha 不處理顏色,主體看起來像鑲了綠框。

`chroma_key` 多做兩步收尾:

```python
# app/sticker.py
if erode > 0:
    a_im = Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(1 + 2 * erode))
    alpha = np.array(a_im)
# despill: pull leftover green down toward max(r,b) on kept pixels
keep = alpha > 0
spill = keep & (g > np.maximum(r, b))
g2 = g.copy()
g2[spill] = np.maximum(r, b)[spill]
```

- **erosion**(`MinFilter`)把 alpha 邊界往內縮 1px,吃掉最外圈那層最可疑的半透明過渡像素。
- **despill** 對「保留下來、但綠通道高過紅藍」的像素,把綠壓到 `max(r,b)`,中和殘留綠光。

少了這兩步,你看到的就是「乾淨切割但邊緣偏綠」。這正是 Part 1 → Part 2 的核心差異(對照課:`docs/08-sticker-pipeline.md`)。

## 3. 尺寸沒到 LINE 規格,上架被退件

LINE Creators Market 對每張圖有明確的尺寸上限,本模板定義在 `app/sticker.py` 最上方:

```python
STICKER = (370, 320)   # 每張貼圖
MAIN = (240, 240)      # 主圖
TAB = (96, 74)         # 分頁標籤
```

症狀:直接把切出來的單張(本模板 fixture 是 100×100)丟去上架,被擋下;或自己亂縮放,變形、邊緣糊掉。

怎麼修:用 `fit_pad`——**保持長寬比縮放、置中貼到透明畫布**,而不是硬拉伸。`build_line_pack` 已經把每張套到對的規格、產出 main / tab 並打包成 ZIP:

```python
z.writestr(f"{i:02d}.png", _png(fit_pad(t, STICKER)))
z.writestr("main.png", _png(fit_pad(stickers[0], MAIN)))
z.writestr("tab.png", _png(fit_pad(stickers[0], TAB)))
```

驗證(`tests/test_pack.py` 已斷言):ZIP 內檔名為 `01.png`..`08.png` + `main.png` + `tab.png`,且 `01.png` 是 370×320、`main.png` 240×240、`tab.png` 96×74。另外 LINE 規定**一組最少 8 張**——`build_line_pack` 取前 8 張(`tiles[:8]`),grid 至少要生出 8 格可用的圖。

## 4. grid 切割對不齊,每格切到隔壁

`split_grid` 用整數除法決定每格寬高,再逐格 crop:

```python
cw, ch = w // cols, h // rows
tiles.append(im.crop((c * cw, r * ch, c * cw + cw, r * ch + ch)))
```

這要求**生出來的 grid 真的是規律的 rows×cols 等分**。常見對不齊原因:

- 你叫 Gemini 生「3×3 grid」但它排成 2×4、或格子大小不一、或加了標題列/邊框——整數等分就會切到隔壁格或切掉主體。
- grid 總寬高不能被 `cols`/`rows` 整除時,`w // cols` 會丟掉餘數那幾個 pixel,最右/最下一排可能少一條。

怎麼修:prompt 明確要求「規律的 3×3 網格、每格一個姿勢、純綠背景、不要標題不要邊框」(見 `demo_sticker.py` 的 `PROMPT`);生完先肉眼確認排版規律,再進切割。本模板的 fixture(`tests/fixtures.py`)就是一張乾淨的 300×300 等分綠 grid,可當「切割正常」的對照基準。

## 5. 角色一致性靠 prompt,而不是後處理

九宮格裡每格是同一隻角色的不同姿勢——這件事**只能在生圖那一步靠 prompt 控制**,後處理(去背/縮放/打包)完全不會幫你修角色長相。

`demo_sticker.py` 的做法是在 prompt 裡明寫一致性要求:

```python
PROMPT = (
    "a 3x3 grid of one cute mascot character in 9 different poses and expressions, "
    "flat solid pure green (#00ff00) background, consistent character, sticker style"
)
```

關鍵字 `one ... character`、`consistent character` 是在請模型「同一隻、九種姿勢」。即使如此,單次生成的一致性仍可能不穩(臉、配色、比例飄)。這屬於**生圖入門**的範疇:先去把生圖那一關練熟(https://github.com/yazelin/gemini-image-starter),再回來做貼圖會順很多。需要更可控的角色一致性,通常要靠 reference image / 多輪修圖,本入門模板不涵蓋。

## 6. 沒裝 uv,或忘了先 `uv sync`

本教學用 uv 管理環境。兩個最常見的卡點:

- **沒裝 uv**:打 `uv ...` 直接 `command not found: uv`(Windows 是 `'uv' 不是內部或外部命令`)。先安裝 uv,裝完**重開終端機**讓 PATH 生效,`uv --version` 印得出版本再繼續。
- **裝了 uv 但忘了先 `uv sync`**:在沒有 `.venv` 的情況下直接 `uv run python demo_sticker.py`,會找不到 Pillow / numpy / httpx。先在 repo 根目錄跑一次 `uv sync`(建立 `.venv` 並裝好相依),之後 `uv run python client_smoke_test.py`、`uv run python demo_sticker.py` 才會在對的環境裡執行。

`uv sync` / `uv run` 在 Ubuntu 與 Windows 完全相同,平台差異只在「怎麼安裝 uv」這一步。

## 7. 把缺 GEMINI_API_KEY 當成壞掉

真正生圖才需要 key;**測試完全不用 key**。如果你直接跑 `demo_sticker.py` / `part1_naive/naive.py` 卻沒設 key,程式不會崩潰,只會提示:

```
(set GEMINI_API_KEY to actually generate: https://aistudio.google.com/apikey)
```

這不是錯誤——它是在告訴你「後處理邏輯都在,但沒 key 不會去呼叫 Gemini」。想驗證整條 pipeline 對不對,跑 smoke test(它用本地假 Gemini server,見 `tests/fake_gemini.py`):

```
uv run python client_smoke_test.py
```

## Debug 順序

1. 先 `uv run python client_smoke_test.py`——四項全過代表切割 / 去背 / 打包 / 生圖串接的邏輯本身正常,問題出在你的圖或你的 prompt。
2. halo / 邊緣偏綠:確認你用的是 `chroma_key`(Part 2)而不是 `remove_bg_naive`(Part 1);需要時調 `erode`。
3. 切割錯位:先肉眼看 grid 是不是規律等分,再回去改 prompt;確認 `rows`/`cols` 跟實際排版相符。
4. 上架被退:用 ZIP 解開逐張確認尺寸,對照 `STICKER` / `MAIN` / `TAB`,以及張數是否 ≥ 8。
5. 角色飄:這是生圖那一步的問題,回 `gemini-image-starter` 練 prompt,不要指望後處理。

## 問別人前準備

- repo / branch
- 你打的完整指令與完整輸出
- 問題是出在「生圖那張 grid」還是「後處理」(先跑 smoke test 判斷)
- 你用的 prompt 全文、以及那張 grid 截圖(可遮蔽敏感部分)
- 你已經檢查過哪些設定(uv sync 跑過沒、用的是 naive 還是 chroma_key)
