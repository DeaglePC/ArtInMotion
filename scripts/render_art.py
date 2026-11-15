"""Render photo-driven or explicitly authored marks to a still and/or a process movie."""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

import numpy as np
from art_styles import STYLES, Mark, Study
from drawing_audio import CONTACT, TOOL_MEDIUM, write_soundtrack
from drawing_board import (
    BoardComposer,
    compute_layout,
    parse_aspect,
    parse_board,
    parse_orientation,
    resolve_board_mode,
    smart_reframe,
)
from PIL import Image, ImageDraw, ImageOps
from sand_table import hand_shadow
from video_intro import (
    choose_transitions,
    intro_images,
    preview_frames,
    transition_options,
)


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, help="Source photograph or illustration")
    source.add_argument(
        "--plan", type=Path, help="Custom JSON mark sequence, see references/marks.md"
    )
    parser.add_argument(
        "--style", default=None, help="Preset ID, Chinese label or two-digit number"
    )
    parser.add_argument("--list-styles", action="store_true")
    parser.add_argument(
        "--image", type=Path, help="PNG, JPEG or WebP, clean final canvas"
    )
    parser.add_argument("--video", type=Path, help="MP4, full drawing process")
    parser.add_argument(
        "--no-preview", action="store_true", help="Start directly on paper"
    )
    parser.add_argument("--seconds", type=float, default=24)
    parser.add_argument(
        "--opening-seconds",
        type=float,
        help="Time for the first four marks (default one fifth of duration)",
    )
    parser.add_argument(
        "--pigment",
        type=float,
        default=1.0,
        help="Photo mark opacity multiplier, 0.25 to 2",
    )
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument(
        "--size", type=int, default=960, help="Longest edge of output"
    )
    parser.add_argument(
        "--board",
        default="auto",
        help="Drawing board style for video: auto (default), tape, clip, easel, clean, or none",
    )
    parser.add_argument(
        "--no-board",
        action="store_true",
        help="Disable drawing board and export full-bleed canvas video",
    )
    parser.add_argument(
        "--image-board",
        action="store_true",
        help="Include the drawing board on the exported --image still as well",
    )
    parser.add_argument(
        "--orientation",
        default="auto",
        help="Output orientation: auto (default), landscape (横屏), portrait (竖屏), or square",
    )
    parser.add_argument(
        "--aspect",
        default=None,
        help="Artwork aspect ratio: original (default) or W:H such as 16:9, 9:16, 4:3, 3:4, 1:1",
    )
    parser.add_argument(
        "--fit",
        choices=("crop", "pad"),
        default="crop",
        help="How --aspect reframes photos: smart crop (default) or paper ground pad",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--no-tool", action="store_true", help="Hide the on-screen drawing tool"
    )
    audio = parser.add_mutually_exclusive_group()
    audio.add_argument(
        "--music",
        type=Path,
        help="Replace the generated piano with a local backing track",
    )
    audio.add_argument(
        "--no-music", action="store_true", help="Keep drawing sounds only"
    )
    audio.add_argument(
        "--silent", action="store_true", help="Export video without audio"
    )
    transition_options(parser)
    args = parser.parse_args()
    if args.list_styles:
        for i, (key, medium) in enumerate(STYLES.items(), 1):
            print(f"{i:02}  {key:15}  {medium.name}")
        parser.exit()
    if not (args.input or args.plan) or not (args.image or args.video):
        parser.error("choose --input or --plan and at least one of --image / --video")
    if (
        args.opening_seconds is not None
        and not 0 <= args.opening_seconds <= args.seconds * 0.85
    ):
        parser.error("--opening-seconds must be between zero and 85% of the duration")
    if not 0.25 <= args.pigment <= 2 or (args.plan and args.pigment != 1):
        parser.error("--pigment is a photo option in the range 0.25..2")
    if args.plan and args.style:
        parser.error("--plan defines its own medium; omit --style")
    if args.music and not args.video:
        parser.error("--music needs --video")
    if (
        not 1 <= args.seconds <= 600
        or not 1 <= args.fps <= 60
        or not 64 <= args.size <= 4096
        or args.seed < 0
    ):
        parser.error("seconds 1..600; fps 1..60; size 64..4096; seed >= 0")
    if args.image and args.image.suffix.lower() not in (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    ):
        parser.error("--image must be PNG, JPEG or WebP")
    if args.video and args.video.suffix.lower() != ".mp4":
        parser.error("--video must end in .mp4")
    if args.video and not shutil.which("ffmpeg"):
        parser.error("put FFmpeg with libx264 on PATH for MP4 output")
    for p in (args.input, args.plan, args.music):
        if p and not p.is_file():
            parser.error(f"file not found: {p}")
    for p in (args.image, args.video):
        if p and p.exists():
            parser.error(f"choose a new output name: {p}")
    try:
        args.orientation = parse_orientation(args.orientation)
        args.board = parse_board(args.board, args.no_board)
        args.aspect_ratio = parse_aspect(args.aspect)
    except ValueError as exc:
        parser.error(str(exc))
    if args.plan and (args.aspect is not None or args.fit != "crop"):
        parser.error("--plan defines its own canvas size; omit --aspect and --fit")
    return args


def photo_plan(args):
    aliases = {medium.name: key for key, medium in STYLES.items()}
    aliases.update({f"{i:02}": key for i, key in enumerate(STYLES, 1)})
    style = aliases.get(args.style, args.style or "impasto")
    if style not in STYLES:
        raise ValueError(f"unknown style {style!r}; use --list-styles or --plan")
    medium = STYLES[style]
    with Image.open(args.input) as src:
        upright = ImageOps.exif_transpose(src).convert("RGBA")
        flat = Image.new("RGB", upright.size, medium.ground)
        flat.paste(upright, mask=upright.getchannel("A"))

    use_board = bool(args.video or args.image_board) and args.board != "none"
    board_mode = resolve_board_mode(args.board, style) if use_board else "none"

    target_ratio = args.aspect_ratio
    if target_ratio is None and board_mode == "none":
        if args.orientation == "landscape" and flat.width < flat.height:
            target_ratio = 16.0 / 9.0
        elif args.orientation == "portrait" and flat.width > flat.height:
            target_ratio = 9.0 / 16.0
        elif args.orientation == "square":
            target_ratio = 1.0

    flat = smart_reframe(flat, target_ratio, fit=args.fit, ground=medium.ground)
    size, frame_size, offset = compute_layout(
        flat.size, args.size, args.orientation, board_mode
    )
    composer = BoardComposer.create(size, frame_size, offset, board_mode, seed=args.seed)

    ref = flat.resize(size, Image.Resampling.LANCZOS)
    marks = Study(ref, style, args.seed).plan()
    if style == "colored-pencil":
        marks.extend(pencil_touchups(ref, medium.ground, marks))
    if args.pigment != 1:
        for mark in marks:
            mark.opacity = min(255, round(mark.opacity * args.pigment))
    return size, medium.ground, medium.tool, marks, style, composer


def pencil_touchups(reference, ground, marks):
    """Close bright gaps in the hatching with short, locally matched pencil strokes."""
    proof = Image.new("RGB", reference.size, ground)
    for mark in marks:
        paint(proof, mark)
    weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    source = np.asarray(reference)
    excess = np.asarray(proof) @ weights - source @ weights
    missing = excess > 24
    max_length = max(2, round(min(reference.size) / 100))
    repairs = []
    for y, row in enumerate(missing):
        bounds = np.flatnonzero(np.diff(np.r_[False, row, False])).reshape(-1, 2)
        for left, right in bounds:
            x = left
            while x < right:
                # Split at color boundaries so a repair cannot smear a highlight.
                end = min(x + max_length, right)
                colors = source[y, x:end].astype(int)
                changes = np.flatnonzero(
                    np.max(np.abs(colors - colors[0]), axis=1) > 10
                )
                if len(changes):
                    end = x + changes[0]
                color = tuple(
                    np.rint(source[y, x:end].mean(axis=0)).astype(int).tolist()
                )
                repairs.append(
                    Mark([(int(x), y), (int(end - 1), y)], color, opacity=245)
                )
                x = end
    return repairs


def ints(value, n, low, high):
    if (
        not isinstance(value, (list, tuple))
        or len(value) != n
        or any(type(i) is not int or not low <= i <= high for i in value)
    ):
        raise ValueError(f"expected {n} integers in {low}..{high}")
    return tuple(value)


def read_plan(path, args):
    data = json.loads(path.read_text(encoding="utf8"))
    size = ints(data["size"], 2, 2, 4096)
    if any(n % 2 for n in size):
        raise ValueError("use even canvas dimensions for a custom plan")
    ground = ints(data["ground"], 3, 0, 255)
    tool = data.get("tool", "pen")
    if tool not in {s.tool for s in STYLES.values()}:
        raise ValueError(f"unknown tool: {tool}")
    marks = []
    for item in data["marks"]:
        shape = item.get("shape", "line")
        points = [ints(point, 2, 0, max(size) - 1) for point in item["points"]]
        if any(x >= size[0] or y >= size[1] for x, y in points):
            raise ValueError("mark outside custom canvas")
        if (
            shape not in ("line", "dot", "polygon", "tile")
            or not points
            or (shape == "polygon" and len(points) < 3)
            or (shape == "tile" and len(points) != 2)
        ):
            raise ValueError("invalid shape or point count")
        if shape == "tile" and any(a > b for a, b in zip(points[0], points[1])):
            raise ValueError("tile corners must be top-left then bottom-right")
        (width,) = ints([item.get("width", 1)], 1, 1, 4096)
        (opacity,) = ints([item.get("opacity", 255)], 1, 0, 255)
        marks.append(
            Mark(points, ints(item["color"], 3, 0, 255), width, opacity, shape)
        )
    use_board = bool(args.video or args.image_board) and args.board != "none"
    board_mode = resolve_board_mode(args.board, None) if use_board else "none"
    if board_mode == "none":
        composer = BoardComposer.create(size, size, (0, 0), "none", seed=args.seed)
    else:
        margin = max(6, round(max(size) * 0.08 / 2) * 2)
        fw, fh = size[0] + 2 * margin, size[1] + 2 * margin
        if args.orientation == "landscape" and fw / fh < 16 / 9:
            fw = round(fh * 16 / 9 / 2) * 2
        elif args.orientation == "portrait" and fw / fh > 9 / 16:
            fh = round(fw * 16 / 9 / 2) * 2
        elif args.orientation == "square":
            side = max(fw, fh)
            fw = fh = side
        ox, oy = (fw - size[0]) // 2, (fh - size[1]) // 2
        composer = BoardComposer.create(
            size, (fw, fh), (ox, oy), board_mode, seed=args.seed
        )
    return size, ground, tool, marks, None, composer


def paint(canvas, mark, progress=1.0):
    if mark.shape in ("pour", "sweep", "rake", "groove"):
        return mark.table.paint(canvas, mark, progress)
    points = mark.points
    fill = (*mark.color, mark.opacity)
    draw = ImageDraw.Draw(canvas, "RGBA")
    if mark.shape in ("tile", "polygon"):
        if progress >= 1:
            if mark.shape == "tile":
                draw.rectangle(points, fill=fill)
            else:
                draw.polygon(points, fill=fill)
        return (points[0][0], points[0][1])
    if len(points) == 1 or mark.shape == "dot":
        x, y = points[0]
        if progress > 0:
            radius = (mark.width - 1) * 0.5 * progress
            if radius < 0.5:
                draw.point((x, y), fill=fill)
            else:
                draw.ellipse(
                    (x - radius, y - radius, x + radius, y + radius), fill=fill
                )
        return x, y
    if progress >= 1:
        draw.line(points, fill=fill, width=mark.width)
        return points[-1]
    coords = np.asarray(points, dtype=float)
    lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(coords, axis=0), axis=1))]
    distance = progress * lengths[-1]
    i = min(
        len(points) - 2, max(0, np.searchsorted(lengths, distance, side="right") - 1)
    )
    frac = (distance - lengths[i]) / max(1e-8, lengths[i + 1] - lengths[i])
    tip = tuple(coords[i] + frac * (coords[i + 1] - coords[i]))
    if progress > 0:
        draw.line(points[: i + 1] + [tip], fill=fill, width=mark.width)
    return tip


def tool_overlay(frame, point, tool, color, ref_size=None):
    w, h = frame.size
    rw, rh = ref_size or (w, h)
    x, y = np.clip(point, [0, 0], [w - 1, h - 1])
    scale = min(rw, rh) / 600
    angle = math.radians(32 if x < w * 0.70 else 148)
    if y > h * 0.70:
        angle = -angle
    dx, dy = math.cos(angle) * scale, math.sin(angle) * scale

    def pt(a, b, sx=0.0, sy=0.0):
        return (x + sx + a * dx - b * dy, y + sy + a * dy + b * dx)

    draw = ImageDraw.Draw(frame, "RGBA")

    def poly(vertices, c, sx=0.0, sy=0.0):
        draw.polygon([pt(a, b, sx, sy) for a, b in vertices], fill=c)

    if tool in ("tile", "piece", "grain"):
        # Placement cursor for non-pen media.
        draw.ellipse(
            [x - 5 * scale, y - 5 * scale, x + 5 * scale, y + 5 * scale],
            outline=(81, 65, 52, 235),
            width=max(1, round(scale)),
        )
        draw.line([pt(4, 0), pt(17, 0)], fill=(81, 65, 52, 235), width=max(1, round(scale)))
    elif tool == "roller":
        poly([(0, -10), (9, -10), (9, 10), (0, 10)], (22, 16, 12, 48), 3 * scale, 5 * scale)
        poly([(0, -10), (9, -10), (9, 10), (0, 10)], color)
        draw.line(
            [pt(8, -10), pt(16, -10), pt(22, 0), pt(44, 0)],
            fill=(87, 78, 67, 255),
            width=max(1, round(3 * scale)),
        )
    else:
        width = 6 if tool in ("brush", "chalk", "gouge") else 3.8
        barrel = color if tool in ("pencil", "chalk") else (92, 69, 57)
        body_pts = [
            (0, 0),
            (20, -width),
            (84, -width * 0.65),
            (87, 0),
            (84, width * 0.65),
            (20, width),
        ]
        # Subtle hovering tool shadow over paper and wooden board
        poly(body_pts, (24, 16, 10, 52), 3.2 * scale, 5.2 * scale)
        poly([(0, 0), (20, -width), (20, width)], (188, 148, 101))
        poly([(0, 0), (7, -width * 0.38), (7, width * 0.38)], color)
        poly(
            [
                (20, -width),
                (84, -width * 0.65),
                (87, 0),
                (84, width * 0.65),
                (20, width),
            ],
            barrel,
        )
        if tool == "pencil":
            draw.line(
                [pt(0, 0), pt(20, width), pt(84, width * 0.65), pt(87, 0)],
                fill=(77, 61, 53),
                width=max(1, round(scale)),
            )
        draw.line([pt(21, -width * 0.7), pt(82, -width * 0.45)], fill=(189, 171, 144))


def advance(t, n, opening):
    # Hold first contact, then draw a few opening marks at readable speed.
    slow = min(4, max(1, n // 8))
    if t == 0:
        return 0
    if t < opening:
        return slow * max(0, (t / opening - 0.06) / 0.94)
    if opening == 0:
        slow = 0
    if t >= 0.96:
        return n
    return slow + (n - slow) * (t - opening) / (0.96 - opening)


def paper_texture(size, style, seed):
    # A fixed paper tooth lifts pigment at the same locations in every frame.
    # Wet media have softer mottling; dry points skip more exposed fibers.
    texture = {
        "colored-pencil": (3, 5),
        "charcoal": (12, 20),
        "pastel": (16, 24),
        "crayon": (17, 31),
        "watercolor": (6, 13),
        "ink-wash": (4, 11),
    }
    if style not in texture:
        return None
    base, spread = texture[style]
    rng = np.random.default_rng(seed)
    shape = size[1], size[0]
    grain = rng.normal(base, spread, shape)
    if style in ("watercolor", "ink-wash"):
        coarse = rng.integers(
            0, 23, (max(2, size[1] // 9), max(2, size[0] // 9)), dtype=np.uint8
        )
        grain += np.asarray(
            Image.fromarray(coarse).resize(size, Image.Resampling.BICUBIC)
        )
    return Image.fromarray(grain.clip(0, 96).astype(np.uint8))


def movie(path, canvas, marks, tool, ground, texture, style, composer, args):
    count = round(args.seconds * args.fps)
    out_w, out_h = composer.frame_size
    ox, oy = composer.offset
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{out_w}x{out_h}",
        "-r",
        str(args.fps),
        "-i",
        "pipe:0",
    ]
    intro = preview_frames(count, args.fps, not args.no_preview)
    if args.opening_seconds is not None:
        # Leave room for the requested slow strokes and the final reveal.
        intro = min(
            intro, max(0, count - math.ceil(args.opening_seconds * args.fps / 0.95))
        )
    draw_count = count - intro
    opening = 0.20
    if args.opening_seconds is not None:
        opening = args.opening_seconds * args.fps / draw_count
    elif style == "sand":
        opening = min(0.20, 2.6 * args.fps / draw_count)
    positions = [0] * intro + [
        advance(i / max(1, draw_count - 1), len(marks), opening) if marks else 0
        for i in range(draw_count)
    ]
    positions[-1] = len(marks)
    if not args.silent:
        soundtrack = path.with_suffix(".wav")
        write_soundtrack(
            soundtrack,
            marks,
            positions,
            args.fps,
            canvas.width,
            style or TOOL_MEDIUM[tool],
            args.seed,
            not (args.no_music or args.music),
            opening_end=(intro + math.floor(opening * (draw_count - 1))) / args.fps,
        )
        cmd += ["-i", str(soundtrack)]
        if args.music:
            cmd += [
                "-stream_loop",
                "-1",
                "-i",
                str(args.music),
                "-filter_complex",
                "[2:a:0]volume=0.26[music];[1:a:0][music]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.94:level=0:latency=1[mix]",
                "-map",
                "0:v:0",
                "-map",
                "[mix]",
            ]
        else:
            cmd += ["-map", "0:v:0", "-map", "1:a:0"]
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += [
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "17",
        "-movflags",
        "+faststart",
        str(path),
    ]
    completed = 0
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as proc:
        try:
            if intro:
                preview = canvas.copy()
                for mark in marks:
                    paint(preview, mark)
                if texture is not None:
                    preview.paste(ground, (0, 0, *preview.size), texture)
                effects = choose_transitions(args.transition, args.transition_out)
                print("Transitions:", *effects, file=sys.stderr, flush=True)
                blank = canvas.copy()
                if texture is not None:
                    blank.paste(ground, (0, 0, *blank.size), texture)
                for frame in intro_images(preview, blank, intro, *effects):
                    proc.stdin.write(composer.compose(frame).tobytes())
            for i, pos in enumerate(positions[intro:]):
                t = i / max(1, draw_count - 1)
                while completed < int(pos):
                    paint(canvas, marks[completed])
                    completed += 1
                frame = canvas.copy()
                show_tool = not args.no_tool
                if marks:
                    mark = marks[min(completed, len(marks) - 1)]
                    if completed < len(marks):
                        fraction = pos - completed
                        tip = paint(frame, mark, min(1, fraction / CONTACT))
                        if fraction > CONTACT and completed + 1 < len(marks):
                            dest = marks[completed + 1].points[0]
                            tip = np.array(tip) + (np.array(dest) - tip) * (
                                fraction - CONTACT
                            ) / (1 - CONTACT)
                    else:
                        endpoint = (
                            mark.points[-1] if mark.shape == "line" else mark.points[0]
                        )
                        tip = np.asarray(endpoint, dtype=float)
                        if composer.mode != "none":
                            # Smoothly glide the finished pencil/brush off onto the board margin
                            pull = min(1.0, max(0.0, (t - 0.96) / 0.032))
                            if pull >= 1.0:
                                show_tool = False
                            else:
                                tip[0] += pull * max(ox * 1.15, canvas.width * 0.09)
                                tip[1] += pull * max(oy * 0.45, canvas.height * 0.04)
                        else:
                            tip[0] += min(0.04, t - 0.96) * canvas.width * 0.7
                else:
                    tip = (canvas.width * 0.5, canvas.height * 0.5)
                if texture is not None:
                    frame.paste(ground, (0, 0, *frame.size), texture)
                if style == "sand" and show_tool and completed < len(marks):
                    hand_shadow(frame, tip, mark.shape == "pour")
                out_frame = composer.compose(frame)
                if style != "sand" and show_tool:
                    tool_overlay(
                        out_frame,
                        (tip[0] + ox, tip[1] + oy),
                        tool,
                        mark.color if marks else (70, 60, 50),
                        ref_size=canvas.size,
                    )
                proc.stdin.write(out_frame.tobytes())
        finally:
            proc.stdin.close()
        if proc.wait():
            raise RuntimeError("FFmpeg encoding failed")


def main():
    args = arguments()
    size, ground, tool, marks, style, composer = (
        read_plan(args.plan, args) if args.plan else photo_plan(args)
    )
    canvas = (
        marks[0].table.base.copy()
        if style == "sand" and marks
        else Image.new("RGB", size, ground)
    )
    texture = paper_texture(size, style, args.seed)
    outputs = [p for p in (args.video, args.image) if p]
    staged = {}
    with ExitStack() as stack:
        for p in outputs:
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = stack.enter_context(tempfile.TemporaryDirectory(dir=p.parent))
            staged[p] = Path(tmp) / p.name
        if args.video:
            movie(
                staged[args.video],
                canvas,
                marks,
                tool,
                ground,
                texture,
                style,
                composer,
                args,
            )
        else:
            for mark in marks:
                paint(canvas, mark)
        if args.image:
            still = canvas.copy()
            if texture is not None:
                still.paste(ground, (0, 0, *size), texture)
            if args.image_board:
                still = composer.compose(still)
            still.save(staged[args.image])
        # Same-filesystem, no-overwrite publication after every encoder has succeeded.
        published = []
        try:
            for path in outputs:
                os.link(staged[path], path)
                published.append(path)
        except OSError:
            for path in published:
                path.unlink()
            raise
    summary = {"size": size, "marks": len(marks), "files": list(map(str, outputs))}
    if args.video and composer.mode != "none":
        summary["video_size"] = composer.frame_size
        summary["board"] = composer.mode
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
