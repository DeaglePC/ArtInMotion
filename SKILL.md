---
name: art-in-motion
description: 把用户的原照、插画或用代码设计的图形逐笔画成画板视频或静态成画。支持水彩、彩铅、油画、素描、钢笔排线、版画、拼贴、沙画等 20 种画法与 68 种转场，支持木纹画板装裱（美纹纸/画夹/画架）、横屏/竖屏/方屏画幅以及任意图片比例选择；用户未指定时自动使用默认画板与原图比例。
---

# 多画风逐笔绘制（ArtInMotion）

Use the bundled Python renderer to create the actual requested files. It runs locally without model inference, image generation services or API keys. Treat the supplied original as the reference.

1. Locate this skill directory. Use its virtual environment if installed. For a fresh install, create a virtual environment with Python 3.11 or 3.12 and install [requirements.txt](requirements.txt) with pip. For video export, check that FFmpeg is on PATH with libx264 and AAC encoders. All script paths below are relative to this directory. Pass absolute input/output paths when calling from elsewhere.

2. Run `python scripts/render_art.py --list-styles` to map the requested name, number or technique. Use the closest preset for a straightforward match. For a genuinely different technique or a text-only drawing, construct an ordered [custom mark plan](references/marks.md). A custom plan can specify linework, pigment, grounds, regions and placement order. For a photo-specific likeness, use the user's reference. Consult the [technique guide](references/media.md) for unfamiliar medium names and extension recipes.

3. **Drawing board, screen orientation, and image aspect ratio (use defaults whenever the user does not specify)**:
   - **Studio Drawing Board (`--board`)**:
     - **Default (`--board auto`)**: Process videos automatically mount the paper or canvas onto a realistic wooden artist's drawing board with cast shadows (`tape` corner masking tape for paper media, `easel` wooden ledge & clamp for `impasto`/`woodcut`, and `lightbox` dark walnut frame for `sand`), while the active pencil/brush glides naturally across the paper and board margin.
     - **Selectable styles**: `--board tape` (美纹纸胶带), `--board clip` (金属画板夹), `--board easel` (木质画架托槽), `--board clean` (极简无夹木板), or `--no-board` / `--board none` (铺满全屏、无画板).
     - **Still image behavior**: `--image` exports a clean, unframed canvas by default. Add `--image-board` only when the user explicitly asks for the still image to include the drawing board as well.
   - **Screen Orientation (`--orientation` · 横屏 / 竖屏 / 方屏)**:
     - **Default (`--orientation auto`)**: Follows the natural orientation of the artwork with balanced board margins.
     - **Selectable orientations**: `landscape` (`横屏`, frames outer board video at `16:9`), `portrait` (`竖屏`, frames outer board video at `9:16`), or `square` (`方屏`, `1:1`). When `--aspect` is not given, mounting on a `landscape` or `portrait` board preserves 100% of the source photo without cropping; when `--no-board` is used, it smart-crops to match the requested orientation.
   - **Image / Paper Aspect Ratio (`--aspect` & `--fit` · 图片比例)**:
     - **Default (`--aspect original` / omitted)**: Preserves the input image's original aspect ratio and framing.
     - **Selectable ratios**: Any `W:H` ratio such as `1:1`, `4:3`, `3:4`, `3:2`, `2:3`, `16:9`, `9:16`, `4:5`, `5:4`, `21:9`.
     - **Reframing mode (`--fit`)**: Defaults to `--fit crop` (portrait- and subject-aware saliency crop that protects faces and key contours); pass `--fit pad` if the user wants to keep the entire uncropped photo with paper ground margins.
   - **Rule of thumb**: Whenever the user does not specify board style, orientation, or image ratio, omit those flags so the renderer uses its defaults (`--board auto`, `--orientation auto`, `--aspect original`).

4. **Timing, transitions, tools, and soundtrack**:
   - `--image` writes the clean still, `--video` animates the marks on the drawing board, and supplying both shares the exact same drawn canvas.
   - Use **24 seconds** by default (`--seconds 24`, `--fps 30`, `--size 960` longest output edge), with slow opening marks, accelerated time-lapse work and a final hold.
   - Animate the finished artwork into view on the mounted paper, hold the clean preview for 1.2 seconds in a 24-second movie, then transition back to the blank ground. Choose from 10 art-specific effects and up to 58 FFmpeg presets (`--list-transitions` or [transition guide](references/transitions.md)). Pass `--transition NAME` for both directions and optionally `--transition-out NAME` for a separate exit; omit when unspecified so the renderer picks randomly. Use `--no-preview` to start directly on blank paper.
   - Keep the active tool visible by default (`--no-tool` hides it). Use `--opening-seconds` for a slower opening, and raise `--pigment` (e.g. `1.25`) for deeper color in transparent media. For sand (`17`), follow the [lightbox sand recipe](references/media.md#17-号灯箱沙画).
   - Play gentle, contact-synchronized tool foley **only on the first three slow opening marks**, keeping the preview free of tool sounds. From the fourth mark through the final hold, play only the warm synthesized solo piano (`--no-music` for foley alone, `--music FILE` for custom music, `--silent` for no audio).

```sh
# Default: wooden drawing board video + clean PNG still, preserving original orientation & aspect ratio
python scripts/render_art.py --input "/path/photo.jpg" --style colored-pencil --seconds 24 --video "/path/new.mp4" --image "/path/new.png"

# Explicit vertical 9:16 video with 3:4 portrait paper crop and brass sketchboard clip
python scripts/render_art.py --input "/path/photo.jpg" --style watercolor --orientation portrait --aspect 3:4 --board clip --video "/path/vertical.mp4" --image "/path/vertical.png"

# Full-bleed widescreen 16:9 video without drawing board
python scripts/render_art.py --input "/path/photo.jpg" --style impasto --aspect 16:9 --no-board --video "/path/fullbleed.mp4"

# Custom JSON mark plan
python scripts/render_art.py --plan "/path/drawing.json" --video "/path/drawing.mp4" --image "/path/drawing.png"
```

5. Choose unused output paths. Check exported dimensions, duration and streams with `ffprobe`. Inspect opening, middle and end frames to verify subject framing, drawing board presentation, medium texture and visible tool. Return links to the requested artifacts. When comparing media, keep source, seed, board, framing and timing consistent.

6. For the standalone 3D WebGL vertical oil cinema mode with camera push-in, live stroke counter and specular bristle lighting, use `scripts/paint_video.py` (see [classic oil recipe](references/classic-oil.md)).
