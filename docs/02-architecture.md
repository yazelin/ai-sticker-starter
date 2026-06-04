# AI 貼圖入門模板：架構說明

## 一句話的管線

```
Gemini 生綠幕 grid  ->  split_grid 切片  ->  chroma_key 去背
                    ->  fit_pad 縮放置中  ->  build_line_pack 打包 ZIP
```

第一步要 API key(真正向 Gemini 生圖);後面四步全是本機像素 / 檔案運算,不碰網路。

## 核心檔案

- `app/gen.py` — 最小 Gemini client。`generate_grid()` 用「一次呼叫」要 Gemini 畫一張綠幕 grid,回 PNG bytes。形狀跟真實 Gemini image API 一樣,但帶可注入的 `base_url`,測試時指向本機假 server(免 key、免網路)。
- `app/sticker.py` — 後處理全在這一檔:
  - `split_grid(image_bytes, rows=3, cols=3)` — 把 grid 切成 `rows*cols` 格 RGBA tile(左到右、上到下)。
  - `remove_bg_naive(im, key=(0,255,0), tol=80)` — **Part 1 天真版**:粗略顏色門檻,接近 key 色就設透明。快,但邊緣留綠 halo。
  - `chroma_key(im, erode=1)` — **Part 2 正確版**:綠幕判定(`g` 明顯大於 `r`、`b`)→ 設 α → `MinFilter` 邊緣 erosion → despill(把留在邊上的綠往 `max(r,b)` 壓)。輸出乾淨去背。
  - `fit_pad(im, size)` — 等比縮放(`thumbnail` + LANCZOS)後置中貼到透明畫布,輸出剛好 `size`。
  - `build_line_pack(tiles)` — 取前 8 張,各 `fit_pad` 到貼圖規格寫進 ZIP,再加 `main.png`、`tab.png`,回 ZIP bytes。
- `demo_sticker.py` — Part 2 完整 demo:`generate_grid` → `split_grid` → `chroma_key` → `build_line_pack` → 存 `sticker_pack.zip`(要 key)。
- `part1_naive/naive.py` — Part 1 天真版:`generate_grid` → `split_grid` → `remove_bg_naive` → 存單張(要 key,給你看痛點)。
- `client_smoke_test.py` + `tests/` — 確定性驗證(免 key,見下)。

## LINE 規格(定義在 `app/sticker.py`)

```python
STICKER = (370, 320)   # 每張貼圖
MAIN    = (240, 240)   # 主圖
TAB     = (96, 74)     # 分頁縮圖
```

`build_line_pack` 打出來的 ZIP:`01.png`–`08.png`(各 370×320)+ `main.png`(240×240)+ `tab.png`(96×74)。LINE 一組貼圖最少 8 張,所以這裡固定取前 8 張;`main` 與 `tab` 都用第一張縮出來。

## 資料流

1. (要 key)`generate_grid(prompt, api_key)` 向 Gemini 送一次 `generateContent`(`responseModalities: ["IMAGE"]`),從回應的 `inlineData.data`(base64)解出一張綠幕 grid PNG。
2. `split_grid(grid)` 用整除切成 9 格 RGBA。
3. 每格過 `chroma_key`:先以「綠明顯壓過紅藍」判定背景設透明 → `MinFilter` 把 α 邊緣往內縮 1px(吃掉綠毛邊)→ despill 把保留像素上殘留的綠壓下去。
4. `build_line_pack` 對前 8 張各 `fit_pad` 到 `STICKER` 寫進 ZIP,再寫 `main.png`(`MAIN`)、`tab.png`(`TAB`)。
5. 把 ZIP bytes 存成 `sticker_pack.zip`,可直接拖進 LINE Creators Market。

## 為什麼後處理可以「純像素測試」

第 2–5 步沒有任何網路 / 隨機 / API 依賴,輸入同一張圖,輸出永遠一樣——這就是確定性,可以直接斷言。`tests/fixtures.py` 用 Pillow 合成一張 3×3 綠幕 grid(每格中央一個彩色方塊)當輸入,於是:

- `test_grid.py` — 切完是 9 格、每格 100×100。
- `test_chroma.py` — 取第一格,角落(綠)α=0、中心(主體)α=255;`chroma_key` 與 `remove_bg_naive` 都驗。
- `test_pack.py` — ZIP 檔名剛好 `01.png`–`08.png` + `main.png` + `tab.png`,且 `01.png`=370×320、`main.png`=240×240、`tab.png`=96×74。
- `test_gen_fake.py` — 連「生圖」這步也能免 key 測:`tests/fake_gemini.py` 起一個本機 HTTP server,對任何 POST 都回「Gemini 形狀」的 JSON(`inlineData` 塞 fixture 圖)。`generate_grid` 把 `base_url` 指向它,就能驗證「生圖 → 切片」串得起來,完全不碰真 API。

`client_smoke_test.py` 依序跑這四個檔,全綠才印 `OK: all checks passed`。CI(`.github/workflows/ci.yml`)也是跑這支,所以 PR 不需要 secret 就能把關。

## 設計原則

- 先讓整條管線可跑、可驗,再談漂亮抽象。
- secret(`GEMINI_API_KEY`)只進環境變數,絕不進程式碼或 repo。
- 把「生圖」與「後處理」切乾淨:生圖要 key,後處理純本機——所以測試免 key。
- `app/gen.py` 的 `base_url` 可注入,就是為了讓測試用假 server 取代真 API。
- 範例刻意保持小,方便你看懂後改成自己的角色與規格。
