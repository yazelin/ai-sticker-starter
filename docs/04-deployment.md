# AI 貼圖入門模板：真正生圖與上架

前面的測試與步驟都免 key,因為後處理是純本機運算。這份文件講最後一哩:**真正向 Gemini 生圖**(要 API key),產出 `sticker_pack.zip`,再把它上架到 LINE Creators Market。最後給「production 化」的方向。

## 上線前檢查

- 已跑過 `uv sync`,且 `uv run python client_smoke_test.py` 印出 `OK: all checks passed`(確認後處理整條 OK,免 key)。
- 你已經會用 Gemini 生圖(前置模組 生圖入門:<https://github.com/yazelin/gemini-image-starter>)。
- 拿到 `GEMINI_API_KEY`(免費:<https://aistudio.google.com/apikey>)。
- key 只放環境變數,**不要** commit 進 repo。`.gitignore` 已忽略 `*.zip`、`sticker_pack.zip`、`naive_*.png`,生出來的圖與 ZIP 不會被誤上傳。

## 步驟 1:設定 GEMINI_API_KEY

Ubuntu / macOS:

```bash
export GEMINI_API_KEY="你的key"
```

Windows(PowerShell):

```powershell
$env:GEMINI_API_KEY="你的key"
```

key 是綁在環境變數上的,`app/gen.py` / `demo_sticker.py` 都從 `os.environ` 讀,程式裡不存任何 key。

## 步驟 2:用 demo_sticker.py 真正生一組

`demo_sticker.py` 就是 Part 2 完整管線:生綠幕 grid → 切 → `chroma_key` 去背 → 打包,存成 `sticker_pack.zip`。

```bash
uv run python demo_sticker.py
```

成功的話你會看到:

```
saved sticker_pack.zip  (drag into LINE Creators Market)
```

(如果**沒設** key,它不會報錯,而是印一行提示要你去拿 key 後結束——這是設計好的,方便你先確認環境。)

它預設用的 prompt(在 `demo_sticker.py` 裡)是:

```
a 3x3 grid of one cute mascot character in 9 different poses and expressions,
flat solid pure green (#00ff00) background, consistent character, sticker style
```

兩個重點讓後處理好做:**flat solid pure green 背景**(去背的乾淨 key)、**consistent character**(同一角色 9 種姿勢,整組才像一套)。要做你自己的角色,就改這段 prompt(prompt 怎麼寫見前置模組;管理多版 prompt 可用 PromptFill:<https://github.com/yazelin/PromptFill>)。

## 步驟 3:檢查產出的 ZIP

生完先打開 `sticker_pack.zip` 看一眼。裡面應該是:

- `01.png` – `08.png`:8 張貼圖,各 370×320。
- `main.png`:主圖,240×240。
- `tab.png`:分頁縮圖,96×74。

肉眼確認:角色去背乾淨(沒綠邊)、主體完整沒被切掉、置中。若邊緣還有綠,通常是 grid 背景不夠純綠——回去把 prompt 的綠背景講更死,或重生一張。

## 步驟 4:上架 LINE Creators Market(流程概要)

`sticker_pack.zip` 裡的尺寸與檔名就是照 LINE 規格做的,可直接用。流程概要:

1. 到 LINE Creators Market 登入:<https://creator.line.me/>
2. 註冊成為貼圖創作者(填基本資料、收款資訊)。
3. 建立新的 **Sticker** 貼圖商品,填標題、說明、語言。
4. 上傳貼圖圖檔(`01.png`–`08.png`)、主圖(`main.png`)、分頁圖(`tab.png`)。
5. 設定售價與販售地區,送出審查。
6. 通過 LINE 審查後即上架販售。

> 規格小抄(本 repo 已照此產出):一組最少 8 張、貼圖 370×320、main 240×240、tab 96×74,背景透明 PNG。LINE 官方規範可能調整,上傳介面會以當下要求為準。

## 安全與實務提醒

- `GEMINI_API_KEY` 只進環境變數,別寫進程式、別 commit、別貼到截圖。
- 每次 `generate_grid` 都是一次計費的 API 呼叫;批次生很多組前,先估配額與成本。
- 生出來的 `sticker_pack.zip` / `naive_*.png` 已被 `.gitignore` 擋住,但 push 前還是掃一眼 `git status`。
- 角色版權、肖像權自負;別用受保護的 IP 去生圖上架。

## 想做成正式服務?(production 化)

這個 starter 是「一人在自己機器上跑」的教學版:key 放本機環境變數、自己跑指令。如果你要把它變成「給很多人用的網站 / App」,就不能把 key 放前端,還要擋濫用、算配額。完整做法請看真實案例:

- **line-sticker-studio** — 把這條同樣的 pipeline 包成正式服務:用 Cloudflare Worker 當 proxy 代管 Gemini key(前端永遠拿不到 key)、加上使用配額、用 Turnstile 擋機器人濫用。<https://github.com/yazelin/line-sticker-studio>

延伸資源:line-sticker-studio(production 範例)、PromptFill(<https://github.com/yazelin/PromptFill>,管理 prompt)、LINE Creators Market(<https://creator.line.me/>)。

要把這條 pipeline 包成自家產品(配額、付費、防濫用、上架自動化),歡迎聊:yazelin@ching-tech.com
