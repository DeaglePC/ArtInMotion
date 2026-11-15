"""Atelier drawing board framing, orientation, and smart aspect-ratio cropping."""

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BOARD_MODES = ("auto", "tape", "clip", "easel", "clean", "none")

ORIENTATION_ALIASES = {
    "auto": "auto",
    "default": "auto",
    "原方向": "auto",
    "landscape": "landscape",
    "horizontal": "landscape",
    "wide": "landscape",
    "横屏": "landscape",
    "横版": "landscape",
    "横向": "landscape",
    "portrait": "portrait",
    "vertical": "portrait",
    "tall": "portrait",
    "竖屏": "portrait",
    "竖版": "portrait",
    "纵向": "portrait",
    "square": "square",
    "方屏": "square",
    "方形": "square",
}

ASPECT_PRESETS = {
    "auto": None,
    "original": None,
    "keep": None,
    "原比例": None,
    "原图": None,
    "square": (1.0, 1.0),
    "方形": (1.0, 1.0),
}

BOARD_ALIASES = {
    "auto": "auto",
    "default": "auto",
    "默认": "auto",
    "画板": "auto",
    "tape": "tape",
    "美纹纸": "tape",
    "胶带": "tape",
    "clip": "clip",
    "画夹": "clip",
    "写生板": "clip",
    "easel": "easel",
    "画架": "easel",
    "clean": "clean",
    "极简": "clean",
    "木板": "clean",
    "none": "none",
    "off": "none",
    "无": "none",
    "无画板": "none",
}


def parse_orientation(value):
    if value is None:
        return "auto"
    key = str(value).strip().lower()
    if key in ORIENTATION_ALIASES:
        return ORIENTATION_ALIASES[key]
    raise ValueError(
        f"unknown orientation {value!r}; use auto, landscape (横屏), portrait (竖屏), or square"
    )


def parse_board(value, no_board=False):
    if no_board:
        return "none"
    if value is None:
        return "auto"
    key = str(value).strip().lower()
    if key in BOARD_ALIASES:
        return BOARD_ALIASES[key]
    raise ValueError(
        f"unknown board style {value!r}; use auto, tape, clip, easel, clean, or none"
    )


def parse_aspect(value):
    """Return float width/height ratio, or None to keep source aspect ratio."""
    if value is None:
        return None
    raw = str(value).strip().lower().replace("：", ":").replace("比", ":")
    if raw in ASPECT_PRESETS:
        pair = ASPECT_PRESETS[raw]
        return None if pair is None else pair[0] / pair[1]
    for sep in (":", "/", "x"):
        if sep in raw:
            parts = raw.split(sep)
            if len(parts) == 2:
                try:
                    w, h = float(parts[0]), float(parts[1])
                except ValueError as exc:
                    raise ValueError(f"invalid aspect ratio {value!r}") from exc
                if w > 0 and h > 0:
                    return w / h
    raise ValueError(
        f"invalid aspect ratio {value!r}; use original or W:H such as 16:9, 9:16, 4:3, 3:4, 1:1"
    )


def smart_reframe(image, target_ratio, fit="crop", ground=(251, 248, 238)):
    """Reframe an RGB image to target_ratio via saliency-guided crop or ground pad."""
    if target_ratio is None:
        return image
    w, h = image.size
    current = w / h
    if abs(current - target_ratio) / max(current, target_ratio) < 0.006:
        return image

    if fit == "pad":
        if current > target_ratio:
            out_w = w
            out_h = max(2, round(w / target_ratio))
        else:
            out_w = max(2, round(h * target_ratio))
            out_h = h
        padded = Image.new("RGB", (out_w, out_h), ground)
        padded.paste(image, ((out_w - w) // 2, (out_h - h) // 2))
        return padded

    # Saliency + skin/subject awareness + portrait gravity crop (clamped so busy backgrounds don't pull off-center)
    scale = min(1.0, 240.0 / max(w, h))
    sw, sh = max(8, round(w * scale)), max(8, round(h * scale))
    small = np.asarray(image.resize((sw, sh), Image.Resampling.BILINEAR), dtype=np.float32)
    r, g, b = small[:, :, 0], small[:, :, 1], small[:, :, 2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    gy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    edges = np.minimum(gx + gy, 22.0)

    # Subtle warm skin-tone & midtone subject cue for portraits
    warm = np.clip((r - b) / 45.0, 0.0, 1.0) * np.clip((r - g) / 25.0, 0.0, 1.0)
    midtone = np.exp(-(((gray - 145.0) / 85.0) ** 2))
    subject = 1.0 + 1.35 * warm * midtone

    yy, xx = np.mgrid[0:sh, 0:sw]
    prior = np.exp(
        -(((xx / max(1, sw - 1) - 0.5) / 0.29) ** 2)
        - (((yy / max(1, sh - 1) - 0.38) / 0.38) ** 2)
    )
    energy = (edges + 6.0) * subject * (0.25 + 0.75 * prior)

    if current > target_ratio:
        crop_w = max(2, min(w, round(h * target_ratio)))
        win = max(1, min(sw, round(crop_w * sw / w)))
        col_scores = energy.sum(axis=0)
        csum = np.r_[0.0, np.cumsum(col_scores)]
        totals = csum[win:] - csum[:-win]
        best_s = int(np.argmax(totals)) if len(totals) else 0
        x0 = round(best_s * (w - crop_w) / max(1, sw - win)) if sw > win else (w - crop_w) // 2
        x0 = max(0, min(w - crop_w, x0))
        return image.crop((x0, 0, x0 + crop_w, h))

    crop_h = max(2, min(h, round(w / target_ratio)))
    win = max(1, min(sh, round(crop_h * sh / h)))
    row_scores = energy.sum(axis=1)
    csum = np.r_[0.0, np.cumsum(row_scores)]
    totals = csum[win:] - csum[:-win]
    best_s = int(np.argmax(totals)) if len(totals) else 0
    y0 = round(best_s * (h - crop_h) / max(1, sh - win)) if sh > win else (h - crop_h) // 2
    y0 = max(0, min(h - crop_h, y0))
    return image.crop((0, y0, w, y0 + crop_h))


def resolve_board_mode(board_mode, style):
    if board_mode != "auto":
        return board_mode
    if style == "sand":
        return "lightbox"
    if style in ("impasto", "woodcut"):
        return "easel"
    return "tape"


def compute_layout(ref_size, max_edge, orientation, board_mode):
    """Compute even (paper_w, paper_h), (frame_w, frame_h), and (ox, oy)."""
    src_w, src_h = ref_size
    paper_ratio = src_w / src_h

    if board_mode == "none":
        factor = max_edge / max(src_w, src_h)
        pw = max(2, round(src_w * factor / 2) * 2)
        ph = max(2, round(src_h * factor / 2) * 2)
        return (pw, ph), (pw, ph), (0, 0)

    if orientation == "landscape":
        target_frame_ratio = max(16.0 / 9.0, paper_ratio)
    elif orientation == "portrait":
        target_frame_ratio = min(9.0 / 16.0, paper_ratio)
    elif orientation == "square":
        target_frame_ratio = 1.0
    else:
        target_frame_ratio = None

    if target_frame_ratio is None:
        # Equal physical studio wood margin around all four sides of the paper
        margin = max(4, round(max_edge * 0.074 / 2) * 2)
        inner_max = max(4, max_edge - 2 * margin)
        if paper_ratio >= 1.0:
            pw = max(2, (inner_max // 2) * 2)
            ph = max(2, round(pw / paper_ratio / 2) * 2)
        else:
            ph = max(2, (inner_max // 2) * 2)
            pw = max(2, round(ph * paper_ratio / 2) * 2)
        extra_bottom = max(0, round(margin * 0.14 / 2) * 2) if board_mode == "easel" else 0
        fw = pw + 2 * margin
        fh = ph + 2 * margin + extra_bottom
        ox = margin
        oy = margin
        return (pw, ph), (fw, fh), (ox, oy)

    # Explicit outer video aspect ratio (16:9 landscape, 9:16 portrait, 1:1 square)
    if target_frame_ratio >= 1.0:
        fw = max(8, (round(max_edge) // 2) * 2)
        fh = max(8, round(fw / target_frame_ratio / 2) * 2)
    else:
        fh = max(8, (round(max_edge) // 2) * 2)
        fw = max(8, round(fh * target_frame_ratio / 2) * 2)

    pad_x = max(4, round(fw * 0.068))
    pad_y = max(4, round(fh * 0.072))
    avail_w = max(2, fw - 2 * pad_x)
    avail_h = max(2, fh - 2 * pad_y)
    if avail_w / avail_h >= paper_ratio:
        ph = max(2, (avail_h // 2) * 2)
        pw = max(2, min((avail_w // 2) * 2, round(ph * paper_ratio / 2) * 2))
    else:
        pw = max(2, (avail_w // 2) * 2)
        ph = max(2, min((avail_h // 2) * 2, round(pw / paper_ratio / 2) * 2))
    ox = (fw - pw) // 2
    oy = (fh - ph) // 2
    if board_mode == "easel" and fh - (oy + ph) > 10:
        oy = max(4, oy - max(2, round(fh * 0.012)))
    return (pw, ph), (fw, fh), (ox, oy)


def _wood_surface(size, dark=False, seed=42):
    w, h = size
    rng = np.random.default_rng(seed + 911)
    horizontal = w >= h
    long_n = max(w, h)
    short_n = min(w, h)

    # Fine-planed studio basswood / walnut grain stretched along the board's long axis
    low_a = rng.normal(0.0, 1.0, (max(4, short_n // 8), max(4, long_n // 90))).astype(np.float32)
    low_b = rng.normal(0.0, 1.0, (max(8, short_n // 2), max(6, long_n // 36))).astype(np.float32)
    low_c = rng.normal(0.0, 1.0, (short_n, max(8, long_n // 14))).astype(np.float32)
    warp_im = Image.fromarray(((low_a * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)).resize(
        (long_n, short_n), Image.Resampling.BICUBIC
    )
    streak_im = Image.fromarray(((low_b * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)).resize(
        (long_n, short_n), Image.Resampling.BICUBIC
    )
    fiber_im = Image.fromarray(((low_c * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)).resize(
        (long_n, short_n), Image.Resampling.BILINEAR
    )
    warp = (np.asarray(warp_im, dtype=np.float32) / 255.0 - 0.5) * 2.0
    streak = (np.asarray(streak_im, dtype=np.float32) / 255.0 - 0.5) * 2.0
    fibers = (np.asarray(fiber_im, dtype=np.float32) / 255.0 - 0.5) * 2.0

    s_coord = np.linspace(0.0, 1.0, short_n, dtype=np.float32)[:, None]
    l_coord = np.linspace(0.0, 1.0, long_n, dtype=np.float32)[None, :]
    rings = np.sin((s_coord * 12.0 + warp * 0.55 + l_coord * 0.35) * math.pi)
    pores = rng.normal(0.0, 0.16, (short_n, long_n)).astype(np.float32)
    grain = 0.34 * rings + 0.36 * streak + 0.22 * fibers + 0.08 * pores

    if not horizontal:
        grain = grain.T  # shape (h, w)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx / max(1, w - 1)) - 0.45
    ny = (yy / max(1, h - 1)) - 0.40
    lamp = 1.038 - 0.19 * (nx * nx + ny * ny)

    if dark:
        base = np.array([96.0, 68.0, 48.0], dtype=np.float32)
        delta = np.array([10.5, 8.0, 5.8], dtype=np.float32)
    else:
        base = np.array([204.0, 171.0, 132.0], dtype=np.float32)
        delta = np.array([10.0, 8.2, 6.2], dtype=np.float32)

    rgb = (base[None, None, :] + grain[:, :, None] * delta[None, None, :]) * lamp[:, :, None]
    out = Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB")

    # Subtle outer board chamfer
    draw = ImageDraw.Draw(out, "RGBA")
    draw.rectangle((0, 0, w - 1, h - 1), outline=(44, 30, 19, 88), width=max(1, round(min(w, h) / 360)))
    return out


def _draw_masking_tape(size, paper_box, seed=42):
    """Render 4 smooth matte washi/masking-tape corner strips at 2x supersampling."""
    w, h = size
    ss = 2
    sw, sh = w * ss, h * ss
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    ox, oy, pw, ph = paper_box
    min_dim = min(pw, ph)

    tape_len = max(24, round(min_dim * 0.142)) * ss
    tape_w = max(8, round(min_dim * 0.036)) * ss
    inset = max(6, round(min_dim * 0.026)) * ss

    rng = np.random.default_rng(seed + 307)
    corners = [
        (ox * ss + inset, oy * ss + inset, -43.5 + rng.uniform(-2.5, 2.5)),
        ((ox + pw) * ss - inset, oy * ss + inset, 43.5 + rng.uniform(-2.5, 2.5)),
        (ox * ss + inset, (oy + ph) * ss - inset, 43.5 + rng.uniform(-2.5, 2.5)),
        ((ox + pw) * ss - inset, (oy + ph) * ss - inset, -43.5 + rng.uniform(-2.5, 2.5)),
    ]

    s_draw = ImageDraw.Draw(shadow, "RGBA")
    t_draw = ImageDraw.Draw(layer, "RGBA")

    for cx, cy, deg in corners:
        ang = math.radians(deg)
        ux, uy = math.cos(ang), math.sin(ang)
        vx, vy = -uy, ux
        hl = tape_len * 0.5
        hw = tape_w * 0.5

        # Subtle torn short ends along the two ends of the masking tape
        pts = []
        teeth = 7
        for k in range(teeth + 1):
            f = -1.0 + 2.0 * k / teeth
            jag = (ss * 1.1) if (k % 2 == 1) else -(ss * 0.8)
            pts.append((cx - (hl + jag) * ux + f * hw * vx, cy - (hl + jag) * uy + f * hw * vy))
        for k in range(teeth + 1):
            f = 1.0 - 2.0 * k / teeth
            jag = (ss * 1.1) if (k % 2 == 1) else -(ss * 0.8)
            pts.append((cx + (hl + jag) * ux + f * hw * vx, cy + (hl + jag) * uy + f * hw * vy))

        s_pts = [(px + ss * 1.2, py + ss * 1.8) for px, py in pts]
        s_draw.polygon(s_pts, fill=(28, 19, 12, 38))
        # Semi-translucent warm cream drafting tape (lets paper corner subtly show through!)
        t_draw.polygon(pts, fill=(246, 239, 220, 206), outline=(226, 215, 191, 145))

    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=ss * 1.3))
    combined = Image.alpha_composite(shadow, layer)
    return combined.resize((w, h), Image.Resampling.LANCZOS)


def _draw_metal_clip(size, paper_box):
    """Render a brushed brass/steel bulldog sketchboard clip at top center."""
    w, h = size
    ss = 2
    sw, sh = w * ss, h * ss
    ox, oy, pw, ph = paper_box
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))

    cw = max(36, round(min(pw, ph) * 0.17)) * ss
    jaw_h = max(14, round(oy * 0.56)) * ss
    overlap = max(6, round(min(pw, ph) * 0.020)) * ss
    cx = (ox + pw // 2) * ss
    top_y = max(ss * 2, oy * ss - jaw_h + overlap)
    bot_y = oy * ss + overlap

    sd = ImageDraw.Draw(shadow, "RGBA")
    ld = ImageDraw.Draw(layer, "RGBA")

    # Cast shadow on paper and wood
    sd.rounded_rectangle(
        (cx - cw // 2 + ss * 2, top_y + ss * 3, cx + cw // 2 + ss * 2, bot_y + ss * 4),
        radius=ss * 4,
        fill=(20, 14, 10, 78),
    )

    # Wire handle loop above clip
    wire_w = round(cw * 0.36)
    wire_top = max(ss, top_y - round(jaw_h * 0.48))
    ld.rounded_rectangle(
        (cx - wire_w // 2, wire_top, cx + wire_w // 2, top_y + ss * 4),
        radius=ss * 5,
        outline=(192, 162, 108, 245),
        width=max(2, ss * 2),
    )

    # Brushed antique-brass clip body
    ld.rounded_rectangle(
        (cx - cw // 2, top_y, cx + cw // 2, bot_y),
        radius=ss * 4,
        fill=(182, 148, 94, 255),
        outline=(122, 95, 56, 255),
        width=max(1, ss),
    )
    # Specular cylinder ridge across clip
    ridge_y = top_y + round((bot_y - top_y) * 0.28)
    ld.rectangle(
        (cx - cw // 2 + ss * 2, ridge_y, cx + cw // 2 - ss * 2, ridge_y + max(2, ss * 3)),
        fill=(228, 204, 154, 210),
    )
    # Bottom gripping lip bevel
    ld.line(
        [(cx - cw // 2 + ss, bot_y - ss), (cx + cw // 2 - ss, bot_y - ss)],
        fill=(96, 74, 42, 230),
        width=max(1, ss * 2),
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=ss * 2.0))
    return Image.alpha_composite(shadow, layer).resize((w, h), Image.Resampling.LANCZOS)


def _draw_easel_hardware(size, paper_box):
    """Render wooden studio easel bottom ledge & top mast clamp."""
    w, h = size
    ox, oy, pw, ph = paper_box
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow, "RGBA")
    ld = ImageDraw.Draw(layer, "RGBA")

    ledge_h = max(8, min(h - (oy + ph) - 2, round((h - (oy + ph)) * 0.46)))
    ledge_w = min(w - 8, round(pw * 1.10))
    lx0 = (w - ledge_w) // 2
    ly0 = oy + ph
    ly1 = min(h - 1, ly0 + ledge_h)

    if ly1 > ly0 + 3:
        sd.rectangle((lx0 + 2, ly0 + 2, lx0 + ledge_w + 3, min(h - 1, ly1 + 5)), fill=(12, 8, 5, 125))
        ld.rectangle((lx0, ly0, lx0 + ledge_w, ly1), fill=(74, 49, 33, 255), outline=(46, 29, 19, 255))
        ld.line([(lx0 + 1, ly0 + 1), (lx0 + ledge_w - 1, ly0 + 1)], fill=(138, 102, 74, 215), width=2)

    # Compact top center wooden clamp block
    cw = max(24, round(pw * 0.09))
    cx0 = ox + (pw - cw) // 2
    cy1 = oy + max(2, round(min(pw, ph) * 0.008))
    sd.rectangle((cx0 + 2, 0, cx0 + cw + 3, cy1 + 3), fill=(12, 8, 5, 105))
    ld.rectangle((cx0, 0, cx0 + cw, cy1), fill=(68, 45, 30, 255), outline=(44, 28, 18, 255))
    ld.line([(cx0 + 2, cy1 - 1), (cx0 + cw - 2, cy1 - 1)], fill=(126, 92, 66, 190), width=1)

    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(1.5, min(w, h) / 180)))
    return Image.alpha_composite(shadow, layer)


@dataclass
class BoardComposer:
    paper_size: tuple[int, int]
    frame_size: tuple[int, int]
    offset: tuple[int, int]
    mode: str
    background: Image.Image | None
    overlay: Image.Image | None

    @classmethod
    def create(cls, paper_size, frame_size, offset, mode, seed=42):
        if mode == "none" or paper_size == frame_size:
            return cls(paper_size, paper_size, (0, 0), "none", None, None)

        fw, fh = frame_size
        pw, ph = paper_size
        ox, oy = offset
        dark_wood = mode in ("easel", "lightbox")
        board = _wood_surface(frame_size, dark=dark_wood, seed=seed).convert("RGBA")

        if mode == "lightbox":
            # Recessed glowing lightbox frame around the sand glass
            bevel = Image.new("RGBA", frame_size, (0, 0, 0, 0))
            bd = ImageDraw.Draw(bevel, "RGBA")
            rim = max(2, round(min(fw, fh) / 150))
            bd.rectangle(
                (ox - rim, oy - rim, ox + pw + rim - 1, oy + ph + rim - 1),
                outline=(42, 26, 16, 225),
                width=rim,
            )
            bd.rectangle(
                (ox - 1, oy - 1, ox + pw, oy + ph),
                outline=(255, 214, 142, 95),
                width=1,
            )
            bg = Image.alpha_composite(board, bevel).convert("RGB")
            return cls(paper_size, frame_size, offset, mode, bg, None)

        # Realistic two-stage paper cast shadow + contact shadow onto the wooden board
        blur_r = max(2.0, min(fw, fh) * 0.012)
        shift_x = max(1, round(min(fw, fh) * 0.0045))
        shift_y = max(2, round(min(fw, fh) * 0.0075))

        cast = Image.new("RGBA", frame_size, (0, 0, 0, 0))
        ImageDraw.Draw(cast, "RGBA").rectangle(
            (ox + shift_x, oy + shift_y, ox + pw + shift_x - 1, oy + ph + shift_y - 1),
            fill=(22, 14, 8, 96 if dark_wood else 76),
        )
        cast = cast.filter(ImageFilter.GaussianBlur(radius=blur_r))

        contact = Image.new("RGBA", frame_size, (0, 0, 0, 0))
        ImageDraw.Draw(contact, "RGBA").rectangle(
            (ox + 1, oy + 1, ox + pw, oy + ph + 1),
            fill=(24, 15, 9, 118 if dark_wood else 92),
        )
        contact = contact.filter(ImageFilter.GaussianBlur(radius=max(1.0, blur_r * 0.22)))

        board = Image.alpha_composite(board, cast)
        board = Image.alpha_composite(board, contact)

        paper_box = (ox, oy, pw, ph)
        if mode == "tape":
            overlay = _draw_masking_tape(frame_size, paper_box, seed=seed)
        elif mode == "clip":
            overlay = _draw_metal_clip(frame_size, paper_box)
        elif mode == "easel":
            overlay = _draw_easel_hardware(frame_size, paper_box)
        else:
            overlay = None

        return cls(paper_size, frame_size, offset, mode, board.convert("RGB"), overlay)

    def compose(self, paper_frame):
        """Mount a paper RGB image onto the precomputed studio drawing board."""
        if self.mode == "none" or self.background is None:
            return paper_frame
        out = self.background.copy()
        ox, oy = self.offset
        pw, ph = self.paper_size
        out.paste(paper_frame, (ox, oy))

        # Subtle paper thickness highlight on top/left edge
        draw = ImageDraw.Draw(out, "RGBA")
        draw.line([(ox, oy), (ox + pw - 1, oy)], fill=(255, 252, 244, 58), width=1)
        draw.line([(ox, oy), (ox, oy + ph - 1)], fill=(255, 252, 244, 42), width=1)

        if self.overlay is not None:
            out = out.convert("RGBA")
            out.alpha_composite(self.overlay)
            return out.convert("RGB")
        return out
