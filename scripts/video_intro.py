"""Art-directed reveals for the finished painting and the return to its ground."""

import argparse
import secrets

import numpy as np
import xfade_transitions as xfade
from PIL import Image, ImageFilter

TRANSITIONS = {
    "ink-bloom": "水墨晕染",
    "dry-brush": "干刷横扫",
    "page-curl": "纸角翻页",
    "iris": "镜头光圈",
    "mosaic": "马赛克显影",
    "ribbon": "绸带交错",
    "prism": "棱镜折光",
    "focus": "柔焦显影",
    "charcoal": "炭粉聚散",
    "silk-fan": "折扇开合",
    **xfade.PRESETS,
}


def transition_id(value):
    key = value.strip().lower()
    for number, (slug, name) in enumerate(TRANSITIONS.items(), 1):
        if key in (slug, name, str(number), f"{number:02}"):
            if slug in xfade.PRESETS and slug not in xfade.available():
                raise argparse.ArgumentTypeError(
                    f"This FFmpeg build does not support {slug}; see --list-transitions"
                )
            return slug
    raise argparse.ArgumentTypeError(
        f"Unknown transition {value!r}. Choose from " + ", ".join(TRANSITIONS.values())
    )


def transition_options(parser):
    parser.add_argument(
        "--transition",
        type=transition_id,
        help="Entrance and exit by ID, Chinese name, or number; default: random",
    )
    parser.add_argument(
        "--transition-out",
        type=transition_id,
        help="Optional different transition back to paper",
    )

    class ListTransitions(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            supported = xfade.available()
            for i, (key, name) in enumerate(TRANSITIONS.items(), 1):
                if key not in xfade.PRESETS or key in supported:
                    print(f"{i:02}  {key:12}  {name}")
            parser.exit()

    parser.add_argument("--list-transitions", nargs=0, action=ListTransitions)
    parser.formatter_class = argparse.RawDescriptionHelpFormatter


def choose_transitions(entrance, exit_effect):
    if entrance is None:
        supported = xfade.available()
        entrance = secrets.choice(
            [key for key in TRANSITIONS if key not in xfade.PRESETS or key in supported]
        )
    return entrance, exit_effect or entrance


def preview_frames(count, fps, enabled):
    if not enabled or count < 3:
        return 0
    return min(round(2.3 * fps), max(1, count // 5))


class Reveal:
    def __init__(self, artwork, paper, effect):
        self.art, self.paper, self.effect = artwork, paper, effect
        # Build masks at display resolution, capped for large export canvases.
        w, h = artwork.size
        scale = min(1, 1024 / max(w, h))
        mw, mh = max(2, round(w * scale)), max(2, round(h * scale))
        y, x = np.mgrid[0:mh, 0:mw].astype("float32")
        x /= mw - 1
        y /= mh - 1
        rng = np.random.default_rng(708)

        def texture(cols, rows):
            noise = Image.fromarray(rng.uniform(-1, 1, (rows, cols)).astype("float32"))
            return np.asarray(noise.resize((mw, mh), Image.Resampling.BICUBIC))

        self.soft = 0.043
        if effect == "ink-bloom":
            field = np.minimum.reduce(
                [
                    np.hypot((x - cx) * w / max(w, h), (y - cy) * h / max(w, h))
                    for cx, cy in ((0.34, 0.41), (0.69, 0.60), (0.46, 0.72))
                ]
            )
            field += 0.085 * texture(10, 8) + 0.023 * texture(54, 38)
        elif effect == "dry-brush":
            field = x + 0.14 * texture(3, max(24, mh // 3)) + 0.026 * texture(27, mh)
            self.soft = 0.023
        elif effect == "page-curl":
            field = 0.72 * x + 0.45 * y + 0.16 * (y - 0.5) ** 2
            self.soft = 0.022
        elif effect == "iris":
            dx, dy = (x - 0.5) * w / max(w, h), (y - 0.47) * h / max(w, h)
            angle = np.arctan2(dy, dx)
            field = np.hypot(dx, dy) * np.cos(
                (angle + np.pi / 6) % (np.pi / 3) - np.pi / 6
            )
            self.soft = 0.022
        elif effect == "mosaic":
            cols = max(4, round(19 * w / max(w, h)))
            rows = max(4, round(19 * h / max(w, h)))
            cx, cy = x * cols, y * rows
            tiles = rng.uniform(0, 0.55, (rows + 1, cols + 1))
            field = (
                0.36 * x
                + 0.18 * y
                + tiles[cy.astype(int), cx.astype(int)]
                + 0.13 * np.maximum(abs(cx % 1 - 0.5), abs(cy % 1 - 0.5))
            )
        elif effect == "ribbon":
            row = (y * 8).astype(int)
            field = (
                np.where(row % 2, 1 - x, x) * 0.76
                + row * 0.032
                + 0.10 * np.sin(y * 8 * np.pi)
            )
        elif effect == "prism":
            field = 0.76 * x + 0.38 * y
        elif effect == "focus":
            self.blur = artwork.filter(
                ImageFilter.GaussianBlur(max(2, min(w, h) * 0.027))
            )
            return
        elif effect == "charcoal":
            field = (
                0.34 * x
                + 0.28 * y
                + 0.21 * texture(24, 16)
                + 0.40 * rng.random((mh, mw))
            )
            self.soft = 0.022
        elif effect == "silk-fan":
            angle = np.arctan2((x - 0.5) * w, (1.05 - y) * h)
            field = angle + 0.055 * np.cos(15 * angle)
        else:
            raise ValueError(effect)
        self.field = (
            (field - field.min()) / max(1e-6, field.max() - field.min())
        ).astype("float32")

    def frame(self, visibility):
        if visibility <= 0:
            return self.paper
        if visibility >= 1:
            return self.art
        p = visibility * visibility * (3 - 2 * visibility)
        if self.effect == "focus":
            focused = Image.blend(self.blur, self.art, p**2)
            return Image.blend(self.paper, focused, p**0.64)
        distance = p * (1 + 2 * self.soft) - self.soft - self.field

        def mask(values):
            im = Image.fromarray((255 * np.clip(values, 0, 1)).astype("uint8"))
            return (
                im.resize(self.art.size, Image.Resampling.BILINEAR)
                if im.size != self.art.size
                else im
            )

        alpha = mask(0.5 + distance / (2 * self.soft))
        exposed = self.art
        if self.effect == "prism":
            shift = round(self.art.width * 0.023 * np.sin(np.pi * p))
            bands = self.art.split()
            displaced = Image.merge(
                "RGB",
                tuple(
                    b.transform(b.size, Image.Transform.AFFINE, (1, 0, d, 0, 1, 0))
                    for b, d in zip(bands, (-shift, 0, shift))
                ),
            )
            exposed = Image.composite(
                displaced, self.art, mask(1 - abs(distance) / 0.15)
            )
        frame = Image.composite(exposed, self.paper, alpha)
        if self.effect == "page-curl":
            # Cast shadow on the sheet, then a warm highlight on the rolled edge.
            frame = Image.composite(
                Image.new("RGB", frame.size, (84, 70, 58)),
                frame,
                mask(0.34 * np.exp(-(((distance + 0.041) / 0.035) ** 2))),
            )
            frame = Image.composite(
                Image.new("RGB", frame.size, (255, 250, 233)),
                frame,
                mask(0.88 * np.exp(-(((distance - 0.009) / 0.021) ** 2))),
            )
        return frame


def intro_images(art, paper, count, entrance, exit_effect):
    """Yield entrance, an unobstructed hold, then the exit to the actual ground."""
    if count < 3:
        for _ in range(count):
            yield art
        return
    enter = max(1, round(count * 5 / 23))
    leave = max(1, round(count * 6 / 23))
    if entrance in xfade.PRESETS:
        yield from xfade.frames(paper, art, enter, entrance)
    else:
        reveal = Reveal(art, paper, entrance)
        for i in range(enter):
            yield reveal.frame((i + 1) / enter)
    for _ in range(count - enter - leave):
        yield art
    if exit_effect in xfade.PRESETS:
        yield from xfade.frames(art, paper, leave, exit_effect)
    else:
        if exit_effect != entrance:
            reveal = Reveal(art, paper, exit_effect)
        for i in range(leave):
            yield reveal.frame(1 - (i + 1) / leave)
