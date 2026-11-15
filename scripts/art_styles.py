"""Photo-driven marks for the portable renderer. Coordinates are in output pixels."""

import math
from dataclasses import dataclass

import numpy as np
from impasto_oil import ImpastoTable
from PIL import Image
from sand_table import SandTable
from scipy import ndimage as nd
from scipy.spatial import Delaunay
from skimage import feature, measure


@dataclass(frozen=True)
class Medium:
    name: str
    tool: str
    ground: tuple = (251, 248, 238)


STYLES = {
    "contour": Medium("轮廓线描", "pen"),
    "hatching": Medium("密线排绘", "pen"),
    "charcoal": Medium("黑白明暗素描", "chalk"),
    "colored-pencil": Medium("彩铅细绘", "pencil"),
    "ink-wash": Medium("黑白水墨", "brush"),
    "watercolor": Medium("透明水彩与彩墨", "brush"),
    "gongbi": Medium("工笔设色与重彩", "brush"),
    "realist": Medium("细腻写实绘画", "brush"),
    "impasto": Medium("厚涂油画", "oil-brush", (139, 112, 91)),
    "pastel": Medium("干粉柔绘", "chalk", (221, 211, 195)),
    "crayon": Medium("蜡笔与油画棒", "chalk"),
    "flat": Medium("平涂插画与漫画", "brush"),
    "woodcut": Medium("黑白刻印与剪影", "gouge", (43, 39, 37)),
    "block-print": Medium("套色版画", "roller"),
    "stipple": Medium("点描与网点", "pen"),
    "collage": Medium("拼贴与镶嵌", "piece"),
    "sand": Medium("沙画与颗粒画", "grain", (255, 218, 145)),
    "marbling": Medium("流体与拓纹", "stylus"),
    "facets": Medium("几何切面", "piece"),
    "pixel": Medium("像素与字符", "tile"),
}


@dataclass
class Mark:
    points: list
    color: tuple
    width: int = 1
    opacity: int = 255
    shape: str = "line"


def rgb(value):
    return tuple(np.clip(value, 0, 255).astype(int).tolist())


class Study:
    def __init__(self, image, style, seed):
        self.style = style
        self.rng = np.random.default_rng(seed)
        self.src = np.asarray(image, dtype=np.float32)
        self.h, self.w = self.src.shape[:2]
        self.scale = min(self.h, self.w) / 600
        self.gray = self.src @ np.array([0.299, 0.587, 0.114], dtype="f")
        self.ground = np.array(STYLES[style].ground)
        self.y, self.x = np.mgrid[: self.h, : self.w]

    def size(self, units):
        return max(1, round(units * self.scale))

    def contours(self, ink, strength=0.9):
        gray = self.gray / 255
        edges = feature.canny(
            gray,
            sigma=max(1.25, self.scale * 1.75),
            low_threshold=0.045,
            high_threshold=0.115,
        )
        result = []
        for trace in measure.find_contours(edges, 0.5):
            if len(trace) < max(8, 13 * self.scale):
                continue
            if np.linalg.norm(trace[0] - trace[-1]) < 1:
                trace = trace[: len(trace) // 2 + 1]
            curve = measure.approximate_polygon(trace, max(0.45, self.scale * 0.65))
            if len(curve) < 2:
                continue
            points = [(int(x), int(y)) for y, x in curve]
            result.append(Mark(points, ink, self.size(1.25), round(255 * strength)))
        # Significant long contours make legible, slow opening strokes on any subject.
        return sorted(result, key=lambda m: -max(np.ptp(m.points, axis=0)))

    def grid(self, spacing):
        step = self.size(spacing)
        y, x = np.mgrid[step // 2 : self.h : step, step // 2 : self.w : step]

        def jitter(values, limit):
            return np.clip(
                values + self.rng.integers(-step // 3, step // 3 + 1, values.shape),
                0,
                limit - 1,
            )

        x, y = jitter(x, self.w).ravel(), jitter(y, self.h).ravel()
        # Serpentine traversal of small neighborhoods avoids frequent jumps across the paper.
        tile = self.size(75)
        row, col = y // tile, x // tile
        order = np.lexsort((x, y, np.where(row % 2, -col, col), row))
        return x[order], y[order]

    def fibers(self, target, spacing, length, width, opacity, rotation=0, dry=False):
        step = self.size(spacing)
        smooth = nd.gaussian_filter(target, (step * 0.22, step * 0.22, 0))
        gy, gx = np.gradient(smooth @ np.array([0.299, 0.587, 0.114], dtype="f"))
        sigma = max(0.8, step * 0.35)
        a = nd.gaussian_filter(gx * gx - gy * gy, sigma)
        b = nd.gaussian_filter(2 * gx * gy, sigma)
        angle = (
            np.where(
                np.hypot(a, b) > 0.12,
                0.5 * np.arctan2(b, a) + np.pi / 2,
                -0.70 + 0.28 * np.sin(self.x / self.size(75)),
            )
            + rotation
        )
        x, y = self.grid(spacing)
        length_px = self.size(length) * self.rng.uniform(0.65, 1.35, len(x))
        dx, dy = length_px * np.cos(angle[y, x]), length_px * np.sin(angle[y, x])
        colors = smooth[y, x]
        if dry:
            colors = colors + self.rng.normal(0, 8, colors.shape)
        marks = []
        for i, (cx, cy) in enumerate(zip(x, y)):
            if np.linalg.norm(colors[i] - self.ground) < 8:
                continue
            px = np.clip(
                np.rint(cx + dx[i] * np.array([-0.5, 0, 0.5])), 0, self.w - 1
            ).astype(int)
            py = np.clip(
                np.rint(cy + dy[i] * np.array([-0.5, 0, 0.5])), 0, self.h - 1
            ).astype(int)
            # Shorten marks at chromatic boundaries (glasses, eyes, petals, lettering).
            keep = np.linalg.norm(smooth[py, px] - smooth[cy, cx], axis=1) < 48
            points = list(zip(px[keep].tolist(), py[keep].tolist()))
            marks.append(Mark(points, rgb(colors[i]), self.size(width), opacity))
        return marks

    def painterly(self):
        s = self.style
        gray = np.repeat(self.gray[:, :, None], 3, axis=2)
        target = self.src
        if s in ("charcoal", "ink-wash"):
            target = self.ground * (0.11 + 0.89 * (gray / 255) ** 0.92)
        elif s in ("watercolor", "gongbi", "crayon", "impasto"):
            target = np.clip(gray + (target - gray) * 1.28, 0, 255)
        if s == "watercolor":
            target = 0.90 * target + 0.10 * self.ground
        if s == "pastel":
            target = 0.88 * target + 0.12 * self.ground
        # spacing, length, width, pressure; measured relative to the short side
        recipes = {
            "colored-pencil": [
                (6, 37, 2, 136),
                (4, 27, 2, 160),
                (3, 16, 1, 195),
                (2, 8, 1, 195),
            ],
            "charcoal": [(10, 43, 13, 110), (5, 21, 6, 142), (2.8, 11, 2, 182)],
            "ink-wash": [(16, 55, 25, 111), (8, 33, 12, 140), (4, 17, 5, 170)],
            "watercolor": [
                (16, 59, 24, 95),
                (9, 34, 15, 117),
                (5, 20, 8, 141),
                (2.7, 11, 4, 154),
            ],
            "gongbi": [(9, 27, 11, 154), (4, 15, 6, 179), (2, 8, 3, 201)],
            "realist": [
                (12, 43, 16, 180),
                (6, 23, 9, 202),
                (3, 12, 5, 213),
                (1.8, 6, 3, 222),
            ],
            "impasto": [(17, 48, 21, 246), (10, 31, 12, 245), (5, 16, 7, 240)],
            "pastel": [(13, 44, 15, 138), (6, 24, 8, 147), (3, 13, 3, 180)],
            "crayon": [(11, 41, 9, 195), (6, 28, 5, 195), (4, 19, 3, 195)],
        }
        outline = self.contours((82, 64, 65), 0.43)
        result = outline[:4]
        dry = s in ("colored-pencil", "pastel", "crayon", "charcoal")
        for n, (spacing, length, width, alpha) in enumerate(recipes[s]):
            layer = self.fibers(
                target,
                spacing,
                length,
                width,
                alpha,
                (-1) ** n * 0.27 if dry else 0,
                dry,
            )
            if s == "impasto":
                for mark in layer:
                    result.append(mark)
                    result.append(
                        Mark(
                            [(x, y - 1) for x, y in mark.points],
                            rgb(np.array(mark.color) * 0.93 + 23),
                            1,
                            160,
                        )
                    )
            else:
                result.extend(layer)
        if s == "gongbi":
            result.extend(outline)
        return result

    def hatching(self):
        marks = self.contours((64, 48, 40), 0.7)
        spacing = max(3, self.size(4.8))
        blur = nd.gaussian_filter(self.gray, max(0.7, self.scale))
        reach = int(math.hypot(self.w, self.h)) + 1
        axis = np.arange(-reach, reach + 1, dtype=float)
        for angle, threshold in [(-0.62, 202), (0.78, 121), (-1.34, 63)]:
            ca, sa = math.cos(angle), math.sin(angle)
            for row in range(-reach, reach, spacing):
                x = self.w * 0.5 + ca * axis - sa * row
                y = self.h * 0.5 + sa * axis + ca * row
                warp = self.size(3) * np.sin(
                    x / max(12, self.size(53)) + y / max(16, self.size(87))
                )
                ix = np.rint(x - sa * warp).astype(int)
                iy = np.rint(y + ca * warp).astype(int)
                good = (ix >= 0) & (ix < self.w) & (iy >= 0) & (iy < self.h)
                good[good] = blur[iy[good], ix[good]] < threshold
                for start, end in np.flatnonzero(
                    np.diff(np.r_[False, good, False])
                ).reshape(-1, 2):
                    if end - start < 2:
                        continue
                    ids = list(range(start, end - 1, 3)) + [end - 1]
                    points = list(zip(ix[ids].tolist(), iy[ids].tolist()))
                    marks.append(Mark(points, (73, 55, 46), self.size(1.2), 205))
        return marks

    def particles(self):
        marks = []
        spacing = 3.6
        x, y = self.grid(spacing)
        for cx, cy in zip(x, y):
            darkness = 1 - self.gray[cy, cx] / 255
            if self.rng.random() > 0.94:
                continue
            width = max(1, round(self.size(spacing * 1.5) * darkness**0.65))
            marks.append(
                Mark(
                    [(int(cx), int(cy))],
                    rgb(self.src[cy, cx] * 0.72),
                    width,
                    205,
                    "dot",
                )
            )
        return marks

    def geometry(self):
        s = self.style
        cell = self.size(8 if s == "pixel" else 17)
        marks = []
        if s == "pixel":
            for y in range(0, self.h, cell):
                for x in range(0, self.w, cell):
                    tile = self.src[y : y + cell, x : x + cell]
                    c = rgb(np.round(tile.mean(axis=(0, 1)) / 28) * 28)
                    marks.append(
                        Mark(
                            [
                                (x, y),
                                (
                                    min(self.w - 1, x + cell - 1),
                                    min(self.h - 1, y + cell - 1),
                                ),
                            ],
                            c,
                            shape="tile",
                        )
                    )
            return marks
        xs, ys = self.grid(17 if s == "facets" else 14)
        corners = [(0, 0), (0, self.h - 1), (self.w - 1, 0), (self.w - 1, self.h - 1)]
        vertices = np.unique(np.vstack((np.column_stack([xs, ys]), corners)), axis=0)
        for triangle in Delaunay(vertices).simplices:
            pts = vertices[triangle]
            samples = (pts * 0.45 + pts.mean(axis=0) * 0.55).astype(int)
            color = rgb(self.src[samples[:, 1], samples[:, 0]].mean(axis=0))
            points = [tuple(p) for p in pts.tolist()]
            if s == "collage":
                a, b, c = pts
                jitter = self.rng.uniform(-0.12, 0.12) * (c - a)
                points.insert(
                    1, tuple(np.rint((a + b) / 2 + jitter).astype(int).tolist())
                )
            marks.append(Mark(points, color, shape="polygon"))
            if s == "collage":
                marks.append(Mark(points[:2], rgb(np.array(color) * 0.8 + 40), 1, 185))
        return marks

    def bands(self):
        s = self.style
        if s == "flat":
            quant = Image.fromarray(self.src.astype("uint8")).quantize(
                9, method=Image.Quantize.MEDIANCUT
            )
            colors = np.array(quant.getpalette(), dtype="uint8").reshape(-1, 3)
            idx = nd.median_filter(np.asarray(quant), size=self.size(3) | 1)
            masks = [(idx == i, rgb(colors[i])) for i in np.unique(idx)]
        elif s == "block-print":
            # Registered separations, light pigments first, followed by the dark key plate.
            r, g, b = self.src.transpose(2, 0, 1)
            masks = [
                (np.minimum(g, b) < 225, (227, 179, 103)),
                ((r - b > 11) & (self.gray < 165), (192, 98, 66)),
                ((r < b + 8) & (self.gray < 185), (77, 130, 130)),
                (self.gray < 82, (44, 53, 65)),
            ]
        elif s == "woodcut":
            smooth = nd.gaussian_filter(self.gray, max(1, self.scale))
            cut = (smooth > 125) | (
                (smooth > 65) & ((self.x + self.y * 2) % self.size(13) < self.size(1))
            )
            masks = [(cut, (245, 230, 198))]
        else:
            phase = (
                self.x / self.size(11)
                + self.y / self.size(19)
                + nd.gaussian_filter(self.gray, self.size(5)) / 15
            )
            stripe = np.sin(phase)
            masks = [
                (stripe < t, c)
                for t, c in [
                    (1.1, (81, 114, 137)),
                    (0.58, (211, 152, 99)),
                    (-0.20, (82, 70, 102)),
                    (-0.76, (221, 186, 138)),
                ]
            ]
            # Use local luminance to let the marbled bands preserve the subject.
            bins = np.digitize(self.gray, [70, 142, 196])
            masks = [
                (mask & (bins == i), rgb(np.array(c) * (0.40 + 0.24 * i)))
                for mask, c in masks
                for i in range(4)
            ]
        marks = []
        for mask, color in masks:
            # Horizontal ink impressions, applied on paper in registration.
            for y, row in enumerate(mask):
                ends = np.flatnonzero(np.diff(np.r_[False, row, False]))
                for x0, x1 in ends.reshape(-1, 2):
                    marks.append(Mark([(int(x0), y), (int(x1 - 1), y)], color))
        if s == "flat":
            marks.extend(self.contours((53, 48, 48), 0.76))
        return marks

    def plan(self):
        if self.style == "contour":
            return self.contours((51, 43, 40))
        if self.style == "hatching":
            return self.hatching()
        if self.style in ("pixel", "facets", "collage"):
            return self.geometry()
        if self.style == "sand":
            return SandTable(self.gray, self.rng, self.ground).plan()
        if self.style == "impasto":
            return ImpastoTable(self.src, self.rng, self.ground).plan()
        if self.style == "stipple":
            return self.particles()
        if self.style in ("flat", "block-print", "woodcut", "marbling"):
            return self.bands()
        return self.painterly()
