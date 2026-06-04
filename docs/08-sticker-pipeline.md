# AI 貼圖入門模板:Part 1 天真版 vs Part 2 完整 pipeline(對照課)

前面你已經看過怎麼把一張 grid 切開、去背、打包。這一段是對照課:同一個目標——「把一張綠幕九宮格做成可上架的 LINE 貼圖組」——用兩種寫法,讓你親眼看到「能動」和「能上架」的差距。

兩個版本的入口:

- **Part 1(天真版)**:`part1_naive/naive.py` + `app/sticker.py` 的 `remove_bg_naive`。生 grid → 切 → 顏色門檻去背 → 存單張。會動,但有綠邊、尺寸不對、沒打包。
- **Part 2(完整版)**:`demo_sticker.py` + `app/sticker.py` 的 `chroma_key` / `fit_pad` / `build_line_pack`。生 grid → 切 → 綠幕去背(despill + erosion)→ 縮放到 LINE 規格 → 打包成可上架 ZIP。

這是獨立的一課——你可以先只跑 Part 1,真的看到綠 halo、看到單張不能上架,再回來看 Part 2,對照感最強。

## 先講結論:差在哪

| 面向 | Part 1 天真版(`remove_bg_naive`) | Part 2 完整版(`chroma_key` + pack) |
|---|---|---|
| 去背方法 | 跟純綠的顏色距離 < `tol` 就透明 | 判斷「綠通道明顯高過紅藍」才算背景 |
| 邊緣 halo | 留一圈半綠毛邊 | erosion 內縮 1px 吃掉過渡像素 |
| 邊緣偏綠(spill) | 不處理,主體像鑲綠框 | despill 把殘綠壓到 `max(r,b)` |
| 尺寸 | 切出來多大就多大(不合規格) | `fit_pad` 保比例縮放置中到 LINE 規格 |
| main / tab | 沒有,要自己另外做 | 自動產 `main.png` 240×240、`tab.png` 96×74 |
| 打包 | 散落一堆 `naive_0X.png` | 一個可直接拖上架的 ZIP |
| 結果 | 能動,但不能上架 | 能直接丟進 LINE Creators Market |

兩條核心訊息:

1. **「去掉背景」和「乾淨去背」是兩回事**:天真門檻能把大片純綠變透明(smoke test 裡它跟 chroma_key 一樣能清掉綠角落),但它對付不了壓縮/抗鋸齒造成的邊緣過渡色——halo 與 spill 都出在邊緣。Part 2 的 erosion + despill 就是專門收這一圈。
2. **「做出圖」和「能上架」差了一段打包工**:LINE 要求固定尺寸、main/tab、最少 8 張、打包成 ZIP。`fit_pad` + `build_line_pack` 把這段瑣事一次做完,這才是把 PoC 變成成品的那一哩路。

## 步驟 1:跑 Part 1,看它哪裡不夠

```
GEMINI_API_KEY=xxx uv run python part1_naive/naive.py
```

它會存出 `naive_01.png` .. `naive_09.png`,並印:

```
saved naive_01.png .. naive_09.png  (note the green halos + wrong sizes)
```

放大看任一張的邊緣——綠毛邊。看尺寸——不是 370×320。沒有 main/tab,沒有 ZIP。這就是「會動但不能上架」。

核心那幾行(`app/sticker.py`):

```python
def remove_bg_naive(im, key=(0, 255, 0), tol=80):
    arr = np.array(im.convert("RGBA"))
    dist = np.abs(arr[:, :, :3].astype(int) - np.array(key)).sum(axis=2)
    arr[:, :, 3] = np.where(dist < tol, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")
```

對照點:**只有一個全域門檻**,在「全留」和「全去」之間沒有中間地帶,邊緣那層過渡色註定處理不好。

## 步驟 2:跑 Part 2,看它怎麼補上

```
GEMINI_API_KEY=xxx uv run python demo_sticker.py
```

它會存出單一檔案並印:

```
saved sticker_pack.zip  (drag into LINE Creators Market)
```

`chroma_key` 的三段收尾(`app/sticker.py`):

```python
is_green = (g > 90) & (g > r + 25) & (g > b + 25)        # 判綠不靠絕對距離
alpha = np.where(is_green, 0, 255).astype(np.uint8)
if erode > 0:                                            # erosion:邊界往內縮
    a_im = Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(1 + 2 * erode))
    alpha = np.array(a_im)
spill = (alpha > 0) & (g > np.maximum(r, b))             # despill:壓掉殘綠
g2[spill] = np.maximum(r, b)[spill]
```

打包則由 `build_line_pack` 一手包辦:取前 8 張、各自 `fit_pad` 到 `STICKER`,再生 `main.png` / `tab.png`,全壓進 ZIP。對照點:**從「一堆散圖」變成「一個能上架的檔案」。**

## 步驟 3:跑同一份免-key 測試,證明邏輯對

整條後處理是純像素/檔案運算,所以**不用 API key、不連網**就能確定性驗證。一鍵跑全部:

```
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

四項各自驗一段(都用 `tests/fixtures.py` 的假綠 grid,`tests/test_gen_fake.py` 還會起一個 `tests/fake_gemini.py` 的本地假 Gemini server):

- `test_grid`:`split_grid` 把 grid 切成 9 格、每格尺寸正確。
- `test_chroma`:`chroma_key` 讓綠角落 α=0、主體中心 α=255(同檔也驗 `remove_bg_naive` 能清綠角落——兩版差在邊緣,不在大片背景)。
- `test_pack`:ZIP 內檔名 `01.png`..`08.png` + `main.png` + `tab.png`,尺寸 370×320 / 240×240 / 96×74。
- `test_gen_fake`:對假 Gemini server 取一張 grid 再切,串起「生圖 → 切割」這條線而完全不用 key。

## 何時用哪一種

- **Part 1**(天真版):教學、理解「去背到底在做什麼」、或背景本來就乾淨到不需要收邊。
- **Part 2**(完整版):你真的要產出能上架的貼圖組——綠幕生圖、要消 halo/spill、要 LINE 規格與打包。

兩者不是取代關係:先看天真版踩到 halo 與「不能上架」,再看完整版怎麼一步步補上,你會更知道每一段後處理在解什麼問題。

## 延伸資源

把這個入門做完後,想往真實產品走:

- **line-sticker-studio**(本作者的 production 版貼圖產生器,Cloudflare Worker proxy + 配額 + Turnstile 防濫用):[github.com/yazelin/line-sticker-studio](https://github.com/yazelin/line-sticker-studio)
- **PromptFill**(把生圖 prompt 模板化、批次填變數):[github.com/yazelin/PromptFill](https://github.com/yazelin/PromptFill)
- **LINE Creators Market**(貼圖上架平台與官方規格):https://creator.line.me/

## 前置模組

這個模組假設你已經會「呼叫 Gemini 生圖」。如果生圖那一關還不熟(prompt 怎麼寫、API 怎麼接、角色一致性怎麼控),先去把入門練起來,再回來做貼圖會順很多:

- **生圖入門**:[github.com/yazelin/gemini-image-starter](https://github.com/yazelin/gemini-image-starter)
