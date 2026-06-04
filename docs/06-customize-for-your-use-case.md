# AI 貼圖入門模板:改成你的使用場景

模板用一隻通用吉祥物示範。真正好玩的是把它換成你自己的角色、你自己的規格。以下都是改一兩個地方就能跑的小改造。

## 換成你自己的角色 prompt

角色長相、風格、姿勢全在 prompt 裡決定,後處理不碰。改 `demo_sticker.py`(Part 2)或 `part1_naive/naive.py`(Part 1)最上方的 `PROMPT` 即可:

```python
PROMPT = (
    "a 3x3 grid of one <你的角色描述> in 9 different poses and expressions, "
    "flat solid pure green (#00ff00) background, consistent character, sticker style"
)
```

兩個不要動的關鍵字:

- **背景一定要 `flat solid pure green (#00ff00)`**——後處理靠綠幕去背,背景不純綠,`chroma_key` 就抓不到。
- **`one ... character` / `consistent character`**——這是叫模型「同一隻、九種姿勢」。角色一致性是生圖那一步的功課,先去 `gemini-image-starter` 練熟。

姿勢、表情、配件可以放開寫(揮手、哭、比讚、拿咖啡…),只要主體留在格子中央、別碰到綠底邊緣。

## 調 chroma 去背門檻與 erosion

去背好不好,看 `app/sticker.py` 的 `chroma_key`。兩個可調點:

- **判綠的條件**(`is_green`):預設 `(g > 90) & (g > r + 25) & (g > b + 25)`。背景偏暗綠就把 `90` 調低;主體本身有綠(綠衣服、綠葉)被誤挖,就把 `+25` 的差值調大,讓「只有非常綠的」才算背景。
- **`erode`**(邊緣內縮):預設 1。邊緣還有殘綠就調到 2;主體太細(線條、觸角)被吃掉就調回 0。

```python
def chroma_key(im, erode=1):
    ...
    is_green = (g > 90) & (g > r + 25) & (g > b + 25)
```

改完用 smoke test 確認沒把基本邏輯弄壞:`uv run python client_smoke_test.py`(`tests/test_chroma.py` 會檢查「綠底透明、主體中心不透明」)。

## 改張數與規格

LINE 規格與張數定義在 `app/sticker.py` 最上方與 `build_line_pack`:

```python
STICKER = (370, 320)
MAIN = (240, 240)
TAB = (96, 74)
...
stickers = tiles[:8]   # 取前 8 張
```

- **改張數**:LINE 一組可 8 / 16 / 24 / 32 / 40 張。想做 16 張,grid 要生足夠格子(例如 4×4),`split_grid(grid, rows=4, cols=4)`,並把 `tiles[:8]` 改成 `tiles[:16]`、檔名迴圈範圍跟著改。
- **改規格**:LINE 偶有調整,或你想做別的平台(Telegram 貼圖是 512×512),直接改 `STICKER` / `MAIN` / `TAB` 的數字。`fit_pad` 會自動按新尺寸縮放置中,不用改其他地方。

改完務必對照 `tests/test_pack.py` 的斷言(檔名清單、尺寸),必要時一起更新測試。

## 加白邊描邊(sticker outline)

很多貼圖會在主體外圍加一圈白邊,放在彩色聊天背景上更跳。最小做法:在 `chroma_key` 之後、`fit_pad` 之前,對 alpha 做一次膨脹當底,填白,再把原圖疊上去。

概念(可加成 `app/sticker.py` 的新函式):

```python
from PIL import ImageFilter

def add_outline(im, width=4, color=(255, 255, 255, 255)):
    a = im.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(1 + 2 * width))  # 把不透明區往外撐
    base = Image.new("RGBA", im.size, (0, 0, 0, 0))
    base.paste(color, (0, 0), grown)   # 撐大的形狀填成白色當描邊底
    base.alpha_composite(im)           # 原圖疊上去
    return base
```

接進 pipeline:`tiles = [add_outline(chroma_key(t)) for t in split_grid(grid)]`。`width` 太大會吃掉細節,先從 3~4 試。

## 改造原則

- 一次只改一個層次:先把角色 prompt 換好生得出乾淨 grid,再調去背門檻,最後才動張數/規格。
- 先保留原本可跑的範例,另開 branch 做實驗。
- 每改一處,跑一次 `uv run python client_smoke_test.py`——它不用 key、秒回,是你最快的安全網。
- 真正生圖要花 quota,先用 fixture / smoke test 把後處理調到滿意,再上 GEMINI_API_KEY 實生。

## 適合拿來做課程 / 工作坊的題目

- 從零跑起這個 starter(免 key 的 smoke test 開場)。
- 把吉祥物換成學員自己的角色,現場生一組貼圖。
- 對照 Part 1 天真去背 vs Part 2 chroma_key,實際看 halo 消失。
- 加白邊、改張數、改成 Telegram 規格等小挑戰。
- 現場 debug 學員的綠幕沒打乾淨 / 切割錯位 / 上架被退。
