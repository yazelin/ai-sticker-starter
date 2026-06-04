# AI 貼圖入門模板：快速開始

這份文件帶你「不卡住、走完一遍、知道自己成功了」。重點:**第一次先不用 API key**。整條後處理是純像素運算,跑測試就能確認環境正確、去背 / 尺寸 / 打包都對。真正生圖要 key,放到 `04-deployment.md`。

## 前置需求

- Python 3.11+
- Git
- 會用終端機
- [uv](https://docs.astral.sh/uv/)(本教學的環境管理工具)
- (選用,真正生圖才需要)`GEMINI_API_KEY` — 跑測試不需要

> 概念前置:這個模組假設你已經跑過 **生圖入門**(<https://github.com/yazelin/gemini-image-starter>),也就是你已經會呼叫 Gemini 把文字變成圖。這裡接續教「圖生出來之後怎麼做成貼圖」。

### 安裝 uv(一次就好)

Ubuntu / macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows(PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

裝完重開終端機,`uv --version` 印得出版本就 OK。`uv sync` 會依 `pyproject.toml` + `uv.lock` 自動建立 `.venv` 並裝好套件(Pillow、numpy、httpx),不需要手動 venv / activate;`uv run` 直接在那個環境裡執行。**以下 `uv sync` / `uv run` 在 Ubuntu 與 Windows 完全相同。**

## 這個 repo 在做什麼(先讀一句)

一次 Gemini 呼叫產出一張綠幕 3×3 grid → 本機切成 9 格 → 綠幕去背 → 縮放置中到 LINE 規格 → 打包成上架 ZIP。前四步全是本機像素 / 檔案運算,所以**不用 API key 就能完整測試**。

## 步驟 1:取得程式

實際指令:

```bash
git clone https://github.com/yazelin/ai-sticker-starter.git
cd ai-sticker-starter
uv sync
```

成功的話你會看到:clone 完成,`ls` 看得到 `app/`、`part1_naive/`、`demo_sticker.py`、`client_smoke_test.py`、`tests/`、`docs/`,而 `uv sync` 印出建立 `.venv` 並裝好相依套件的訊息(Pillow / numpy / httpx 共數個套件)。

## 步驟 2:跑 smoke test(最快的驗證,免 key)

`client_smoke_test.py` 會依序跑四個確定性測試,全部不碰網路、不需要 API key:

- `tests/test_grid.py` — 把一張合成的 3×3 fixture grid 切成 9 格,驗證格數與每格尺寸。
- `tests/test_chroma.py` — 對單格做去背,驗證綠底角落 α=0(透明)、主體中心 α=255(不透明);天真版與正確版都檢查。
- `tests/test_pack.py` — 打包成 ZIP,驗證檔名是 `01.png`–`08.png` + `main.png` + `tab.png`,且尺寸分別是 370×320 / 240×240 / 96×74。
- `tests/test_gen_fake.py` — 對一個本機假 Gemini server 取 grid 再切,驗證「生圖 → 切片」這條串得起來(同樣不用 key)。

實際指令:

```bash
uv run python client_smoke_test.py
```

真實輸出(這是實際跑出來的,不是示意):

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

成功的話你會看到:四段 `OK: ... passed`,最後一行是 `OK: all checks passed`。看到這行就代表去背、尺寸、打包、以及「跟 Gemini 取 grid」的串接全都跑通了——而且這一切都不需要 API key。

> 為什麼免 key 就能測這麼多?因為切 grid、去背、縮放、打包都是純像素 / 檔案運算;連「向 Gemini 要 grid」這步,`test_gen_fake.py` 都用本機 `tests/fake_gemini.py`(回傳 fixture 圖的假 server)取代真的 API。真正要生圖才需要 key,見 `04-deployment.md`。

## 步驟 3(選用):看天真版的痛點

如果你有 `GEMINI_API_KEY`,可以跑 Part 1 天真版,親眼看到「會動但不能用」長什麼樣:

```bash
GEMINI_API_KEY=xxx uv run python part1_naive/naive.py
```

它會存出 `naive_01.png` .. `naive_09.png`。打開來看:綠底是去掉了,但邊緣留一圈綠色 halo,而且單張不是 LINE 規格、也沒打包。這正是 Part 2 要修的問題。Windows(PowerShell)設 key 改成:

```powershell
$env:GEMINI_API_KEY="xxx"; uv run python part1_naive/naive.py
```

(沒設 key 也能跑,它會印一行提示要你去 <https://aistudio.google.com/apikey> 拿免費 key 再結束。)

## 第一次成功的標準(整體確認)

跑完上面,你應該能勾掉這份清單:

- [ ] `uv run python client_smoke_test.py` 印出四段 `OK: ... passed` 並以 `OK: all checks passed` 收尾。
- [ ] 你理解這四項全程不需要 API key(純像素 / 檔案運算 + 本機假 Gemini server)。
- [ ] (選用)有 key 的話,`part1_naive/naive.py` 存出 9 張,你看得到綠邊 halo 的問題。
- [ ] 沒有把任何 secret 或本機絕對路徑誤 commit 到 GitHub。

接著看 `02-architecture.md` 理解整條管線,再用 `03-step-by-step.md` 親手做出每一步。要真正生圖、上架時看 `04-deployment.md`。
