# Part 1 · 天真版(baseline)

`naive.py` 用最直接的方式做貼圖:生一張 3×3 grid → 切 9 格 → 用「顏色門檻」把綠底去掉 → 存成單張。

```
GEMINI_API_KEY=xxx uv run python part1_naive/naive.py
```

會動,但問題很明顯:
- **綠邊/halo**:門檻去背在邊緣留一圈綠色毛邊。
- **尺寸不對**:單張不是 LINE 規格(貼圖 370×320、main 240×240、tab 96×74)。
- **沒打包**:還要自己一張張弄、命名、壓成上架 ZIP。

→ Part 2(`app/sticker.py` 的 `chroma_key` + `build_line_pack`)把這些修好:綠幕去背 + despill 去綠邊 + 邊緣 erosion,再 padding/縮放到 LINE 規格、打包成可直接上架的 ZIP。對照課:`docs/08-sticker-pipeline.md`。
