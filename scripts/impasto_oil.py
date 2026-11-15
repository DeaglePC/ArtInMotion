"""3D impasto oil painting: multi-bristle pigment ridges, canvas weave, and raking specular light."""

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd


@dataclass
class OilStroke:
    table: object
    index: int
    points: list
    color: tuple
    radius: float
    width: int
    seed: int
    opacity: int = 255
    shape: str = "impasto"


def _clamp_rgb(arr):
    return tuple(int(v) for v in np.clip(np.rint(arr), 0, 255))


class ImpastoTable:
    """Stateful heightfield + bristle-ridge oil canvas with WebGL-equivalent raking light."""

    def __init__(self, src_rgb, rng, ground):
        self.src = np.asarray(src_rgb, dtype=np.float32)
        self.h, self.w = self.src.shape[:2]
        self.rng = rng
        self.scale = max(0.25, min(self.w, self.h) / 720.0)
        self.ground_col = np.asarray(ground, dtype=np.float32)

        # Build procedural woven linen ground + subtle organic fBm variation
        yy, xx = np.mgrid[0 : self.h, 0 : self.w].astype(np.float32)
        n1 = nd.gaussian_filter(
            rng.normal(0, 1, (self.h, self.w)).astype(np.float32),
            max(1.2, 6.0 * self.scale),
        )
        n2 = nd.gaussian_filter(
            rng.normal(0, 1, (self.h, self.w)).astype(np.float32),
            max(4.0, 24.0 * self.scale),
        )
        n1 /= max(1e-5, n1.std())
        n2 /= max(1e-5, n2.std())

        wx = xx + n1 * 1.35
        wy = yy + n2 * 1.35
        warp = np.sin(wx * (2.15 / max(0.55, self.scale)))
        weft = np.sin(wy * (2.15 / max(0.55, self.scale)))
        weave = (
            0.5
            + 0.25 * warp * (np.sin(wy * (1.075 / max(0.55, self.scale))) >= 0)
            + 0.25 * weft * (np.sin(wx * (1.075 / max(0.55, self.scale))) >= 0)
        ).astype(np.float32)
        mottle = np.clip(1.0 + 0.055 * n2 + 0.025 * n1, 0.86, 1.14)

        self.weave = weave
        self.ground_rgb = np.clip(
            self.ground_col[None, None, :]
            * (0.90 + 0.20 * weave[:, :, None])
            * mottle[:, :, None],
            0.0,
            255.0,
        ).astype(np.float32)

        # Upper-left studio raking light & Blinn-Phong half-vector
        lx, ly, lz = -0.48, -0.46, 0.75
        ln = math.sqrt(lx * lx + ly * ly + lz * lz)
        self.lx, self.ly, self.lz = lx / ln, ly / ln, lz / ln
        hx, hy, hz = self.lx, self.ly, self.lz + 1.0
        hn = math.sqrt(hx * hx + hy * hy + hz * hz)
        self.hx, self.hy, self.hz = hx / hn, hy / hn, hz / hn

        self._reset_buffers()
        shaded0 = self._shade_box(
            0, 0, self.w, self.h, self._albedo, self._height, self._cov
        )
        self.base = Image.fromarray(shaded0)

    def _reset_buffers(self):
        self._albedo = self.ground_rgb.copy()
        self._height = np.zeros((self.h, self.w), dtype=np.float32)
        self._cov = np.zeros((self.h, self.w), dtype=np.float32)
        self._committed_count = 0

    def _subject_mask(self):
        """Estimate portrait / high-detail subject focus so fine brushes crisp up features."""
        gray = self.src @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        blur = nd.gaussian_filter(gray, max(1.0, 2.2 * self.scale))
        gx = nd.sobel(blur, axis=1)
        gy = nd.sobel(blur, axis=0)
        edge = np.minimum(np.hypot(gx, gy), 95.0)
        edge_smooth = nd.gaussian_filter(edge, max(4.0, 18.0 * self.scale))
        edge_norm = edge_smooth / max(1.0, float(np.percentile(edge_smooth, 96)))

        r, g, b = self.src[..., 0], self.src[..., 1], self.src[..., 2]
        warm = np.clip((r - b) / 65.0, 0.0, 1.0) * np.clip(
            1.0 - np.abs(g - 0.52 * (r + b)) / 55.0, 0.0, 1.0
        )
        warm = nd.gaussian_filter(warm, max(4.0, 16.0 * self.scale))

        yy, xx = np.mgrid[0 : self.h, 0 : self.w].astype(np.float32)
        center = np.exp(
            -(
                ((xx - self.w * 0.5) / (self.w * 0.38)) ** 2
                + ((yy - self.h * 0.44) / (self.h * 0.40)) ** 2
            )
        )
        score = 0.52 * np.clip(edge_norm, 0, 1.4) + 0.48 * warm + 0.28 * center
        return score, edge_norm

    def plan(self):
        """Plan coarse-to-fine curved hog-bristle oil strokes."""
        luma = (self.src @ np.array([0.299, 0.587, 0.114], dtype=np.float32))[:, :, None]
        oil_target = np.clip(luma + (self.src - luma) * 1.15, 0.0, 255.0)

        sim = Image.fromarray(np.rint(self.ground_rgb).clip(0, 255).astype(np.uint8))
        subj_score, edge_norm = self._subject_mask()

        # (radius_px_at_720, grid_mult, diff_thr, maxlen, minlen, curvature_follow, min_subj, force_subj)
        passes = [
            (26.0, 0.82, 10.0, 9, 4, 0.58, 0.00, False),
            (14.0, 0.88, 18.0, 10, 3, 0.64, 0.00, False),
            (7.5, 0.95, 21.0, 10, 3, 0.74, 0.00, False),
            (4.0, 1.08, 20.0, 9, 2, 0.85, 0.38, True),
            (2.2, 1.25, 18.0, 8, 2, 0.92, 0.64, False),
        ]

        raw_strokes = []
        for pass_idx, (
            r_base,
            g_mult,
            thr,
            maxlen,
            minlen,
            fc,
            min_subj,
            force_detail,
        ) in enumerate(passes):
            R = max(1.2, r_base * self.scale)
            sigma = max(0.55, R * 0.42)
            ref = np.stack(
                [nd.gaussian_filter(oil_target[..., c], sigma) for c in range(3)],
                axis=-1,
            )
            lum = ref @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
            gx = nd.sobel(lum, axis=1)
            gy = nd.sobel(lum, axis=0)

            cur = np.asarray(sim, dtype=np.float32)
            diff = np.abs(cur - ref).sum(axis=-1)
            g = max(3, int(round(R * g_mult)))
            area = nd.uniform_filter(diff, g)

            pass_strokes = []
            for y0 in range(g // 2, self.h, g):
                for x0 in range(g // 2, self.w, g):
                    forced = force_detail and subj_score[y0, x0] > 0.78
                    if area[y0, x0] < thr and not forced:
                        continue
                    if (
                        min_subj > 0
                        and subj_score[y0, x0] < min_subj
                        and edge_norm[y0, x0] < 0.46
                    ):
                        continue

                    ya, yb = max(0, y0 - g // 2), min(self.h, y0 + g // 2 + 1)
                    xa, xb = max(0, x0 - g // 2), min(self.w, x0 + g // 2 + 1)
                    k = int(np.argmax(diff[ya:yb, xa:xb]))
                    py, px = divmod(k, xb - xa)
                    x, y = float(xa + px), float(ya + py)
                    col = ref[int(y), int(x)].copy()

                    # Subtle warm/cool tonal play in broad background underpainting
                    if pass_idx <= 1 and edge_norm[int(y), int(x)] < 0.14:
                        delta = float(self.rng.normal(0.0, 3.2))
                        col = np.clip(
                            col + np.array([delta * 1.1, delta * 0.7, -delta * 0.6]),
                            0.0,
                            255.0,
                        )

                    pts = [(x, y)]
                    lx = ly = 0.0
                    step_len = max(1.2, R * 0.88)
                    for i in range(maxlen):
                        xi, yi = int(x), int(y)
                        if i >= minlen:
                            cur_err = np.abs(ref[yi, xi] - cur[yi, xi]).sum()
                            new_err = np.abs(ref[yi, xi] - col).sum()
                            if cur_err < new_err * 0.90:
                                break
                        dx, dy = float(-gy[yi, xi]), float(gx[yi, xi])
                        norm = math.hypot(dx, dy)
                        if norm < 1.35:
                            if i == 0:
                                # Diagonal atelier brushwork sweep in low-gradient zones
                                ang = -0.62 + 0.18 * math.sin(
                                    x / max(18.0, 95.0 * self.scale)
                                    + y / max(18.0, 110.0 * self.scale)
                                )
                                dx, dy, norm = math.cos(ang), math.sin(ang), 1.0
                            else:
                                break
                        dx, dy = dx / norm, dy / norm
                        if lx * dx + ly * dy < 0:
                            dx, dy = -dx, -dy
                        if i > 0:
                            dx = fc * dx + (1.0 - fc) * lx
                            dy = fc * dy + (1.0 - fc) * ly
                            norm = math.hypot(dx, dy) or 1.0
                            dx, dy = dx / norm, dy / norm
                        nx, ny = x + step_len * dx, y + step_len * dy
                        lx, ly = dx, dy
                        if not (0 <= nx < self.w and 0 <= ny < self.h):
                            break
                        x, y = nx, ny
                        pts.append((x, y))

                    if len(pts) < 2:
                        ang = -0.60 + float(self.rng.uniform(-0.20, 0.20))
                        pts.append(
                            (
                                float(
                                    np.clip(
                                        pts[0][0] + R * 1.05 * math.cos(ang),
                                        0,
                                        self.w - 1,
                                    )
                                ),
                                float(
                                    np.clip(
                                        pts[0][1] + R * 1.05 * math.sin(ang),
                                        0,
                                        self.h - 1,
                                    )
                                ),
                            )
                        )
                    pass_strokes.append((R, col, pts, pass_idx))

            if pass_idx == 0:
                pass_strokes.sort(
                    key=lambda s: -(
                        subj_score[int(s[2][0][1]), int(s[2][0][0])] * 1.5
                        + 0.09 * len(s[2])
                        + float(self.rng.normal(0, 0.18))
                    )
                )
            else:
                pass_strokes.sort(
                    key=lambda s: (
                        subj_score[int(s[2][0][1]), int(s[2][0][0])]
                        + float(self.rng.normal(0, 0.16))
                    )
                )

            # Update simulation canvas conservatively (matching real bristle width) so gaps get filled
            draw = ImageDraw.Draw(sim)
            for R_, col, pts, _ in pass_strokes:
                c_tup = _clamp_rgb(col)
                wd = max(1, int(round(R_ * 1.55)))
                int_pts = [(int(round(px)), int(round(py))) for px, py in pts]
                draw.line(int_pts, fill=c_tup, width=wd, joint="curve")
            raw_strokes.extend(pass_strokes)

        marks = []
        for idx, (R_, col, pts, _) in enumerate(raw_strokes):
            int_pts = [
                (
                    int(np.clip(round(px), 0, self.w - 1)),
                    int(np.clip(round(py), 0, self.h - 1)),
                )
                for px, py in pts
            ]
            stroke_seed = int(self.rng.integers(1, 2**31 - 1))
            marks.append(
                OilStroke(
                    table=self,
                    index=idx,
                    points=int_pts,
                    color=_clamp_rgb(col),
                    radius=float(R_),
                    width=max(2, int(round(R_ * 2.0))),
                    seed=stroke_seed,
                )
            )
        return marks

    def _shade_box(self, left, top, right, bottom, albedo_roi, height_roi, cov_roi):
        """Compute normal-mapped 3D impasto diffuse + oil-varnish specular lighting on an ROI."""
        weave_roi = self.weave[top:bottom, left:right]
        ground_roi = self.ground_rgb[top:bottom, left:right]

        h_tot = height_roi * cov_roi + (1.0 - 0.78 * cov_roi) * weave_roi * 0.22
        if h_tot.shape[0] >= 3 and h_tot.shape[1] >= 3:
            hy, hx = np.gradient(h_tot)
        else:
            hx = np.zeros_like(h_tot)
            hy = np.zeros_like(h_tot)

        bump = 2.35 / max(0.65, self.scale * 0.85)
        nx = -hx * bump
        ny = -hy * bump
        nz = np.ones_like(h_tot)
        inv_len = 1.0 / np.sqrt(nx * nx + ny * ny + 1.0)
        nx *= inv_len
        ny *= inv_len
        nz *= inv_len

        diff = nx * self.lx + ny * self.ly + nz * self.lz
        shade = 0.59 + 0.56 * diff

        ndoth = np.maximum(0.0, nx * self.hx + ny * self.hy + nz * self.hz)
        spec = (ndoth**48.0) * 35.0 * (0.22 + 0.78 * cov_roi)

        base_rgb = (
            ground_roi * (1.0 - cov_roi[:, :, None])
            + albedo_roi * cov_roi[:, :, None]
        )
        lit = base_rgb * shade[:, :, None] + spec[:, :, None]

        u = np.clip(lit / 255.0, 0.0, 1.0)
        varnished = (0.86 * u + 0.14 * (u * u * (3.0 - 2.0 * u))) * 255.0
        return np.rint(varnished).clip(0, 255).astype(np.uint8)

    def paint(self, canvas, mark, progress=1.0, transient=False):
        """Render a multi-bristle impasto stroke onto canvas; commit to buffers unless transient."""
        if mark.index < self._committed_count or (mark.index == 0 and not transient):
            self._reset_buffers()

        pts = np.asarray(mark.points, dtype=np.float32)
        if len(pts) < 2:
            return tuple(pts[0])

        seg = np.diff(pts, axis=0)
        lengths = np.hypot(seg[:, 0], seg[:, 1])
        total_len = float(lengths.sum())
        if total_len < 1e-4:
            return tuple(pts[-1])

        dist = float(np.clip(progress, 0.0, 1.0)) * total_len
        ends = np.cumsum(lengths)
        idx = min(len(seg) - 1, int(ends.searchsorted(dist)))
        prev_end = float(ends[idx] - lengths[idx])
        frac = float(
            np.clip((dist - prev_end) / max(1e-5, float(lengths[idx])), 0.0, 1.0)
        )
        tip = pts[idx] + seg[idx] * frac
        if progress <= 0.0 or mark.opacity <= 0:
            return (float(tip[0]), float(tip[1]))

        P = np.vstack([pts[: idx + 1], tip])
        n_pts = len(P)
        R = float(mark.radius)

        normals = np.zeros_like(P)
        for i in range(n_pts):
            a = P[max(0, i - 1)]
            b = P[min(n_pts - 1, i + 1)]
            dx, dy = float(b[0] - a[0]), float(b[1] - a[1])
            l = math.hypot(dx, dy) or 1.0
            normals[i, 0] = -dy / l
            normals[i, 1] = dx / l

        pad = int(math.ceil(R * 1.85 + 5))
        left = max(0, int(math.floor(P[:, 0].min())) - pad)
        top = max(0, int(math.floor(P[:, 1].min())) - pad)
        right = min(self.w, int(math.ceil(P[:, 0].max())) + pad)
        bottom = min(self.h, int(math.ceil(P[:, 1].max())) + pad)
        bw, bh = right - left, bottom - top
        if bw <= 1 or bh <= 1:
            return (float(tip[0]), float(tip[1]))

        sd = mark.seed & 0xFFFFFFFF

        def rnd():
            nonlocal sd
            sd = (sd * 1664525 + 1013904223) & 0xFFFFFFFF
            return sd / 4294967296.0

        nb = max(4, min(13, int(round(R / max(0.95, 1.35 * self.scale)))))
        lw = max(2, int(round(2.0 * R / nb * 2.05)))
        thick = min(1.0, (R / max(6.0, 22.0 * self.scale)) ** 0.72)
        jit = 0.042 + 0.055 * min(1.0, R / max(5.0, 18.0 * self.scale))

        col_patch = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        hgt_patch = Image.new("L", (bw, bh), 0)
        wgt_patch = Image.new("L", (bw, bh), 0)
        dc = ImageDraw.Draw(col_patch)
        dh = ImageDraw.Draw(hgt_patch)
        dw = ImageDraw.Draw(wgt_patch)

        r0, g0, b0 = mark.color
        chroma = max(r0, g0, b0) - min(r0, g0, b0)
        tint_amp = (18.0 + 0.45 * chroma) * jit
        alpha_b = int(round(min(255, mark.opacity * 0.98)))

        for b_idx in range(nb):
            u = b_idx / max(1, nb - 1) - 0.5
            off = u * 2.0 * R * 0.84
            lum_jit = 1.0 + (rnd() - 0.5) * jit * 1.15
            tint = (rnd() - 0.5) * tint_amp
            cr = int(np.clip(r0 * lum_jit + tint, 0, 255))
            cg = int(np.clip(g0 * lum_jit + tint * 0.2, 0, 255))
            cb = int(np.clip(b0 * lum_jit - tint * 0.85, 0, 255))

            is_edge = b_idx == 0 or b_idx == nb - 1
            groove = 25.0 if (b_idx % 2 == 0) else -17.0
            edge_bead = 42.0 if is_edge else 0.0
            h_val = int(
                np.clip(
                    132.0
                    + ((rnd() - 0.5) * 76.0 + groove + edge_bead)
                    * (0.42 + 0.58 * thick),
                    18,
                    255,
                )
            )

            j_start = (rnd() - 0.5) * R * 0.45
            j_end = (rnd() - 0.5) * R * 0.45
            b_pts = []
            for i in range(n_pts):
                px = float(P[i, 0] + normals[i, 0] * off - left)
                py = float(P[i, 1] + normals[i, 1] * off - top)
                if i == 0:
                    px += float(normals[i, 1] * j_start)
                    py -= float(normals[i, 0] * j_start)
                elif i == n_pts - 1:
                    px -= float(normals[i, 1] * j_end)
                    py += float(normals[i, 0] * j_end)
                b_pts.append((px, py))

            dc.line(b_pts, fill=(cr, cg, cb, alpha_b), width=lw, joint="curve")
            dh.line(b_pts, fill=h_val, width=lw, joint="curve")
            dw.line(b_pts, fill=242, width=lw, joint="curve")

        col_arr = np.asarray(col_patch, dtype=np.float32)
        hgt_arr = np.asarray(hgt_patch, dtype=np.float32) / 255.0
        wgt_arr = (np.asarray(wgt_patch, dtype=np.float32) / 255.0) * (
            col_arr[..., 3] / 255.0
        )

        tx, ty = float(tip[0] - left), float(tip[1] - top)
        yy_l, xx_l = np.ogrid[0:bh, 0:bw]
        dab_lip = np.exp(
            -(((xx_l - tx) ** 2 + (yy_l - ty) ** 2) / max(1.5, (R * 0.75) ** 2))
        ).astype(np.float32)
        hgt_arr = np.clip(hgt_arr + 0.14 * dab_lip * wgt_arr, 0.0, 1.25)

        s_slice = np.s_[top:bottom, left:right]
        a_cur = self._albedo[s_slice]
        h_cur = self._height[s_slice]
        c_cur = self._cov[s_slice]

        w3 = wgt_arr[:, :, None]
        a_next = a_cur * (1.0 - w3) + col_arr[..., :3] * w3
        h_next = h_cur * (1.0 - 0.72 * wgt_arr) + (hgt_arr + 0.16 * h_cur) * (
            0.72 * wgt_arr
        )
        c_next = np.clip(c_cur + wgt_arr * (1.0 - c_cur), 0.0, 1.0)

        if not transient:
            self._albedo[s_slice] = a_next
            self._height[s_slice] = h_next
            self._cov[s_slice] = c_next
            self._committed_count = mark.index + 1

        shaded = self._shade_box(left, top, right, bottom, a_next, h_next, c_next)
        canvas.paste(Image.fromarray(shaded), (left, top, right, bottom))
        return (float(tip[0]), float(tip[1]))
