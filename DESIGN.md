# AI 貼圖製造機 CI Design

> English name: AI Sticker Starter

## 定位

**主要受眾:** 已經會用 AI 生圖、想把生圖變成可上架 LINE 貼圖組的人。
**核心承諾:** 看懂「生圖之後」的後處理管線 — 切格、綠幕去背、縮放到 LINE 規格、打包成 ZIP。
**痛點切入:** 會生圖不等於有成品;真正的產品價值在生圖之後的後處理。
**類別提示:** Gemini grid / 綠幕去背 / LINE 規格 / ZIP

## 設計理念

- **後處理才是真正的產品價值。** 呼叫模型生一張圖,前置模組(生圖入門)已經教過;這個模組把焦點放在「拿到圖之後」要做的事 — 把一張綠幕九宮格變成 8 張乾淨、合規、打包好的貼圖。會生圖的人很多,能把生圖做成成品的人才稀有。

- **naive → proper chroma,讓差距自己說話。** Part 1(`remove_bg_naive`)用最直覺的顏色門檻去背,跑得動但留綠邊 halo、尺寸不對、沒打包;Part 2(`chroma_key` + `fit_pad` + `build_line_pack`)補上綠幕判定、despill 去綠邊、邊緣 erosion、縮放到規格、打包成 ZIP。把兩版並排,學員不必被說服,自己就看得到「能動」與「能交付」之間的距離。

- **純像素 → 免 key 的確定性測試。** 整條後處理都是 Pillow + numpy 的像素/檔案運算,沒有任何不確定性。所以四個測試完全不需要 API key、不連網:`test_grid` 切 9 格、`test_chroma` 驗綠角落 α=0 / 主體 α=255、`test_pack` 驗 ZIP 檔名與三種尺寸、`test_gen_fake` 對本地假 Gemini server 取圖。生圖那一步用一個 in-process fake server 替身,讓「取圖 → 切格」的路徑也能確定性驗證,而真正的金鑰只留給真的要畫圖時。

- **前置接生圖入門。** 這個模組刻意不重教「怎麼呼叫 Gemini」;`app/gen.py` 就是生圖入門裡那種影像呼叫,只是改成一次要一張綠幕九宮格。學員照著系列順序走:先會生圖,再學把生圖做成貼圖。

## 視覺識別

- **主色:** `#fb7185`
- **輔色:** `#e11d48`
- **背景:** `#1a0a12`
- **語言策略:** 繁體中文為主,英文產品名作為輔助與 SEO。
- **風格:** 玫瑰色深色系 landing page、技術網格、高對比 CTA。

## Landing Page CTA

主要 CTA:**收到更新 / 小班開課通知**(email 名單)。
Landing 專心收名單,不放延伸資源或外部連結卡;延伸資源放在 README / 教學文件。
表單以 MailerLite embedded 形式掛上,並提供 `yazelin@ching-tech.com` 來信 fallback。

## 功能賣點

- 一次 Gemini 呼叫產一張綠幕九宮格,本地切成 9 格
- 綠幕去背 + despill 去綠邊 + 邊緣 erosion,不留 halo
- 縮放到 LINE 規格:貼圖 370×320、main 240×240、tab 96×74
- 打包成可直接拖進 LINE Creators Market 的 ZIP
- Part 1 天真門檻 vs Part 2 正規管線的對照組
- 後處理全是純像素運算 → 免 API key 的確定性測試

## Assets

- `assets/banner.svg`:README / Open Graph / hero banner
- `index.html`:繁中 GitHub Pages CTA landing page
