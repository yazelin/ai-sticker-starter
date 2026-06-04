# AI 貼圖入門模板：總覽

把「一張 AI 生圖」做成「一組可上架的 LINE 貼圖」。這是「繪圖魔法師」系列的第一個進階模組:生圖你已經會了,這裡學的是把生圖變成產品。

## 前置:先會生圖

這個模組假設你已經跑過前置模組 **生圖入門**(gemini-image-starter):

- 生圖入門:<https://github.com/yazelin/gemini-image-starter>

前置模組教你「怎麼呼叫 Google Gemini 把文字變成圖」。這個模組接著教你「圖生出來之後,怎麼切、去背、縮放、打包成 LINE 規格的貼圖組」。如果你還不會呼叫 Gemini 生圖,請先把前置模組跑過一遍。

引擎一樣是 Google Gemini(`gemini-2.5-flash-image`):這裡只用「一次呼叫」要它畫一張綠幕 3×3 grid(一個角色的 9 種姿勢),其餘全是本機的像素 / 檔案後處理(Pillow + numpy)。

## 兩段:先天真版、再正確版

這份教材分兩段,讓你親眼看到「會動」和「能上架」之間的差距:

- **Part 1(天真版,`part1_naive/naive.py`)** — 切 grid → 用粗略的顏色門檻(`remove_bg_naive`)去綠底 → 存成單張。會動,但邊緣留一圈綠色 halo、尺寸不是 LINE 規格、也沒打包。
- **Part 2(正確版,`app/sticker.py` + `demo_sticker.py`)** — 綠幕去背(`chroma_key`:despill 去綠邊 + 邊緣 erosion)→ `fit_pad` 縮放到 LINE 規格 → `build_line_pack` 打包成可直接上架的 ZIP。

先看天真版痛在哪,再看正確版怎麼一一修好,你會更清楚每一步後處理在解決什麼問題。

## 適合誰

想把自己的角色 / 吉祥物 / 梗圖做成 LINE 貼圖上架,或想學「AI 生圖 → 產品化」這條 pipeline 的人。

## 你會做出什麼

- 用一次 Gemini 呼叫生出一張綠幕角色 grid
- 把 grid 切成單張、乾淨去背(無綠邊)
- 把每張縮放置中到 LINE 規格尺寸
- 打包成可直接拖進 LINE Creators Market 的 ZIP

## 為什麼後處理可以「免 key 測試」

整條後處理(切 grid → 去背 → 縮放 → 打包)是**純像素 / 檔案運算**,不碰網路、不需要 API key。所以這個 repo 的測試是**確定性的**:用一張本機合成的綠幕 fixture 圖就能驗證去背正確、尺寸正確、ZIP 檔名正確;連「跟 Gemini 取 grid」這步都用本機假 server 模擬。真正要生圖才需要 `GEMINI_API_KEY`,但測試不用。

## 建議學習方式

1. 先照 `01-quickstart.md` 把測試跑起來(免 key,確認環境 OK)。
2. 再看 `02-architecture.md` 理解 grid → split → chroma_key → fit_pad → build_line_pack 這條管線。
3. 照 `03-step-by-step.md` 親手做出 `split_grid` / `chroma_key` / `build_line_pack` 並各自驗證。
4. 想真正生圖、上架時看 `04-deployment.md`(需要 `GEMINI_API_KEY`)。

## 免費與付費怎麼分

這個 repo 公開最小可跑版本與完整操作步驟。真正適合工作坊或顧問的,是陪你把自己的角色做成穩定的貼圖組、處理配額與上架實務。

- 免費:可重現的 starter、教學文件、整條後處理 pipeline。
- 付費工作坊:手把手把你的角色做成上架貼圖、調 prompt 與去背參數。
- 企業顧問:把這條 pipeline 包成自家服務(配額、付費、防濫用),參考下方真實案例。

## 延伸資源

- **真實案例(production)**:line-sticker-studio — 把這條 pipeline 包成正式服務(Cloudflare Worker proxy 代管 key、使用配額、Turnstile 防濫用)。<https://github.com/yazelin/line-sticker-studio>
- **PromptFill**:管理 / 填充 prompt 模板的小工具。<https://github.com/yazelin/PromptFill>
- **LINE Creators Market**:貼圖上架平台。<https://creator.line.me/>

問題 / 合作:yazelin@ching-tech.com
