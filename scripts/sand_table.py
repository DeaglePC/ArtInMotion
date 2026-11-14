"""Backlit sand: deposit a loose bed, pull the light out, and rake the edges."""

from dataclasses import dataclass
from itertools import pairwise

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from skimage import measure


@dataclass
class Gesture:
    table: object
    points: list
    width: int
    shape: str
    layer: int
    opacity: int = 255
    color: tuple = (68, 40, 24)


class SandTable:
    def __init__(self, gray, rng, ground):
        h, w = gray.shape
        self.h, self.w = h, w
        self.rng = rng
        self.scale = max(0.25, min(w, h) / 600)
        self.ground = np.array(ground, dtype="f")
        self.dark = np.array([37, 22, 18], dtype="f")
        y, x = np.ogrid[:h, :w]
        radius = ((x - w * 0.48) / w) ** 2 + ((y - h * 0.45) / h) ** 2
        self.light = (
            (self.ground[None, None, :] - radius[:, :, None] * np.array([20, 29, 37]))
            .clip(0, 255)
            .astype("uint8")
        )
        grain = rng.normal(0, 1, (h, w)).astype("f")
        grit = nd.gaussian_filter(grain, max(0.35, 0.58 * self.scale))
        self.grain = (0.50 * grain + 0.50 * grit / max(0.1, grit.std())).clip(-2.6, 2.6)
        gray = nd.gaussian_filter(gray / 255, max(0.6, 1.15 * self.scale))
        # Compress highlights and model broad tones as shallow terraces in sand.
        tone = np.clip((gray - 0.055) / 0.93, 0, 1)
        depth = 0.035 + 3.25 * (1 - tone) ** 1.65
        depth = 0.66 * depth + 0.34 * np.round(depth * 8) / 8
        self.layers = [
            nd.gaussian_filter(depth, max(0.8, s * self.scale)) for s in (13, 4, 1)
        ]
        self.layers.insert(0, np.maximum(0.40, self.layers[0] * 0.79 + 0.40))
        self.base = Image.fromarray(self.light)

    def plan(self):
        marks = []
        for level, (spacing, radius, action) in enumerate(
            ((88, 92, "pour"), (52, 56, "sweep"), (27, 29, "sweep"), (14, 17, "rake"))
        ):
            step = max(3, round(spacing * self.scale))
            r = max(2, round(radius * self.scale))
            layer = self.layers[level]
            gy, gx = np.gradient(layer)
            centers = []
            for j, y0 in enumerate(range(step // 2, self.h + step // 2, step)):
                row = []
                for x0 in range(step // 2, self.w + step // 2, step):
                    cx = int(
                        np.clip(
                            x0 + self.rng.uniform(-0.22, 0.22) * step, 0, self.w - 1
                        )
                    )
                    cy = int(
                        np.clip(
                            y0 + self.rng.uniform(-0.22, 0.22) * step, 0, self.h - 1
                        )
                    )
                    row.append((cx, cy))
                centers.extend(row[::-1] if j % 2 else row)
            if level == 0:
                centers.sort(key=lambda p: -layer[p[1], p[0]])
            for cx, cy in centers:
                angle = (
                    np.arctan2(gy[cy, cx], gx[cy, cx]) + np.pi / 2
                    if abs(gx[cy, cx]) + abs(gy[cy, cx]) > 0.0005
                    else -0.42
                )
                dx, dy = np.cos(angle) * step * 0.67, np.sin(angle) * step * 0.67
                bend = self.rng.uniform(-0.16, 0.16) * step
                pts = [
                    (cx - dx, cy - dy),
                    (cx - np.sin(angle) * bend, cy + np.cos(angle) * bend),
                    (cx + dx, cy + dy),
                ]
                pts = [
                    (int(np.clip(x, 0, self.w - 1)), int(np.clip(y, 0, self.h - 1)))
                    for x, y in pts
                ]
                marks.append(Gesture(self, pts, r, action, level))
        # Trace selected tone boundaries with the narrow edge of a fingertip.
        fine = self.layers[-1]
        gy, gx = np.gradient(nd.gaussian_filter(fine, max(0.8, 2 * self.scale)))
        edge = np.hypot(gx, gy) * self.scale
        for height in (0.35, 0.78, 1.4, 2.1):
            for line in measure.find_contours(fine, height):
                if len(line) < max(12, 30 * self.scale):
                    continue
                indices = np.rint(line).astype(int)
                if np.median(edge[indices[:, 0], indices[:, 1]]) < 0.032:
                    continue
                pts = [
                    (round(x), round(y))
                    for y, x in measure.approximate_polygon(line, max(0.7, self.scale))
                ]
                for i in range(0, len(pts) - 1, 7):
                    marks.append(
                        Gesture(
                            self,
                            pts[i : i + 8],
                            max(2, round(3.3 * self.scale)),
                            "groove",
                            3,
                        )
                    )
        return marks

    def paint(self, canvas, mark, progress):
        pts = np.asarray(mark.points, dtype="f")
        seg = np.diff(pts, axis=0)
        lengths = np.hypot(seg[:, 0], seg[:, 1])
        dist = progress * lengths.sum()
        ends = np.cumsum(lengths)
        i = min(len(seg) - 1, ends.searchsorted(dist))
        tip = pts[i] + seg[i] * np.clip(
            (dist - (ends[i] - lengths[i])) / max(0.001, lengths[i]), 0, 1
        )
        if progress <= 0 or mark.opacity == 0:
            return tip
        path = np.vstack((pts[: i + 1], tip))
        r = mark.width
        lo = np.maximum(0, np.floor(path.min(axis=0) - r * 1.32).astype(int))
        hi = np.minimum(
            canvas.size, np.ceil(path.max(axis=0) + r * 1.32 + 1).astype(int)
        )
        left, top = lo
        right, bottom = hi
        y, x = np.ogrid[top:bottom, left:right]
        d2 = np.full((bottom - top, right - left), np.inf, dtype="f")
        for p, q in pairwise(path):
            vx, vy = q - p
            u = np.clip(
                ((x - p[0]) * vx + (y - p[1]) * vy) / max(0.01, vx * vx + vy * vy), 0, 1
            )
            d2 = np.minimum(d2, (x - p[0] - u * vx) ** 2 + (y - p[1] - u * vy) ** 2)
        region = np.s_[top:bottom, left:right]
        grain = self.grain[region]
        rad = np.sqrt(d2) / r + 0.052 * grain
        fall = np.clip((1.18 - rad) / 0.67, 0, 1)
        weight = fall * fall * (3 - 2 * fall) * min(mark.opacity / 255, 1)
        box = (left, top, right, bottom)
        glass = self.light[region].astype("f")
        before = np.asarray(canvas.crop(box), dtype="f")
        # The red channel measures transmission through the current sand bed.
        depth = -np.log(
            np.clip(
                (before[:, :, 0] - self.dark[0]) / (glass[:, :, 0] - self.dark[0]),
                0.013,
                1,
            )
        )
        target = self.layers[mark.layer][region]
        wanted = np.maximum(0, target + (0.10 + 0.14 * np.minimum(target, 1.7)) * grain)
        if mark.shape == "pour":
            delta = np.maximum(0, wanted - depth) * weight * 0.83
        elif mark.shape == "groove":
            delta = -np.minimum(depth, 0.30) * weight * 0.44
        else:
            delta = (wanted - depth) * weight * (0.91 if mark.shape == "rake" else 0.78)
        # Set cleared grains down along the lip of the same gesture.
        rim = np.maximum(0, 1 - abs(rad - 1.03) / 0.21)
        if mark.shape != "pour":
            removed = np.maximum(-delta, 0).sum()
            delta += rim * min(0.50, 0.55 * removed / max(1, rim.sum()))
        final = np.clip(depth + delta, 0, 4.8)
        color = self.dark + (glass - self.dark) * np.exp(
            -final[:, :, None] * np.array([1, 1.30, 1.70], dtype="f")
        )
        out = np.where((np.abs(delta) > 0.002)[:, :, None], color, before)
        canvas.paste(Image.fromarray(np.rint(out).clip(0, 255).astype("uint8")), box)
        return tip


def hand_shadow(frame, point, pouring):
    """A backlit hand enters the glass from the side, with a pinched or extended index."""
    x, y = point
    w, h = frame.size
    scale = min(w, h) / 640

    reach = 2 * np.hypot(w, h) / scale

    # One orientation throughout the pass so the hand never flips at center.
    def uv(p):
        u, v = p
        return (x + (u * 0.82 - v * 0.57) * scale, y + (u * 0.57 + v * 0.82) * scale)

    if pouring:
        outline = [
            (5, -14),
            (1, -22),
            (4, -29),
            (16, -32),
            (27, -29),
            (38, -33),
            (52, -32),
            (67, -23),
            (83, -14),
            (104, -7),
            (138, -8),
            (185, -6),
            (reach, -10),
            (reach, 60),
            (185, 47),
            (134, 36),
            (99, 39),
            (79, 35),
            (64, 31),
            (50, 22),
            (37, 16),
            (23, 10),
            (13, 9),
            (7, 3),
            (10, -4),
            (19, -4),
            (29, 0),
            (21, -11),
            (14, -13),
        ]
    else:
        outline = [
            (-2, 0),
            (0, -6),
            (8, -10),
            (29, -13),
            (48, -17),
            (59, -22),
            (73, -22),
            (88, -14),
            (107, -8),
            (138, -8),
            (185, -6),
            (reach, -10),
            (reach, 60),
            (185, 47),
            (134, 36),
            (102, 39),
            (84, 34),
            (69, 33),
            (54, 26),
            (35, 24),
            (27, 18),
            (26, 12),
            (31, 9),
            (46, 12),
            (53, 10),
            (36, 4),
            (29, 1),
            (13, 5),
            (3, 5),
        ]
    # Corner cutting rounds the finger pads and knuckles.
    p = np.array(outline, dtype="f")
    for _ in range(2):
        q = np.roll(p, -1, axis=0)
        p = np.stack((0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q), axis=1).reshape(-1, 2)
    draw = ImageDraw.Draw(frame, "RGBA")
    draw.polygon([uv(a) for a in p], fill=(38, 24, 24, 215))
    if pouring:
        for i in range(13):
            d = i / 13
            dx = np.sin(i * 7.21 + x * 0.13) * d * 6
            px, py = uv((7 * (1 - d) + dx, -15 * (1 - d)))
            draw.ellipse((px, py, px + scale, py + scale), fill=(85, 52, 29, 175))
