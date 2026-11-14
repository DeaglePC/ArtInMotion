---
name: art-in-motion
description: 把用户的原照、插画或用代码设计的图形逐笔画成视频或静态成画。支持水彩、彩铅、油画、素描、钢笔排线、版画、拼贴等多种画法，适用于看绘制过程、全程显示笔尖、换画风或只导出图片的请求。
---

# 多画风逐笔绘制

Use the bundled Python renderer to create the actual requested files. It runs locally without model inference, image generation services or API keys. Treat the supplied original as the reference. Preserve its framing unless the user asks for a different crop.

1. Locate this skill directory. Use its virtual environment if installed. For setup see [README.md](README.md) or [README.en.md](README.en.md). All script paths below are relative to this directory. Pass absolute input/output paths when calling from elsewhere.
2. Run `python scripts/render_art.py --list-styles` to map the requested name, number or technique. Use the closest preset for a straightforward match. For a genuinely different technique or a text-only drawing, construct an ordered [custom mark plan](references/marks.md). A custom plan can specify linework, pigment, grounds, regions and placement order. For a photo-specific likeness, use the user's reference. Consult the [technique guide](references/media.md) for unfamiliar medium names and extension recipes.
3. Choose outputs from the request. `--image` writes a clean still, `--video` animates the marks, and supplying both shares the exact same canvas. For a drawing-process video use 24 seconds by default, with slow opening marks, accelerated work and a final hold. The active tool stays visible throughout by default. For a slower opening, set `--opening-seconds`. For stronger color in transparent media, raise `--pigment` from 1 to around 1.25. Placement media use a cursor. All 20 presets mix tool-specific contact sounds and a quiet synthesized piano score by default. The sound follows the picture timeline. Colored pencil plays recorded strokes only during the slow opening, then the backing music continues alone. Use `--no-music` for drawing sounds alone, `--music FILE` to replace the piano, or `--silent` for a silent video.

```sh
python scripts/render_art.py --input "/path/photo.jpg" --style colored-pencil --seconds 24 --video "/path/new.mp4" --image "/path/new.png"
python scripts/render_art.py --input "/path/photo.jpg" --style watercolor --image "/path/watercolor.png"
python scripts/render_art.py --plan "/path/drawing.json" --image "/path/drawing.png"
```

4. Choose unused output paths. Check the exported dimensions, duration and streams with ffprobe. Inspect the opening, middle and end and verify the subject, medium and visible tool where requested. Return links to the requested artifacts. When comparing media, use the same source, seed, framing and timing.
5. For the original cinematic vertical oil demo with camera moves, stroke counter and bundled score, use `scripts/paint_video.py` with the original photo. See [the legacy oil recipe](references/classic-oil.md). The portable `impasto` preset also exports stills and keeps the input aspect ratio.
