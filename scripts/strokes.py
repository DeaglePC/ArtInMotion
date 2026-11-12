import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import gaussian_filter, sobel, uniform_filter

W, H = 1080, 1920
rng = np.random.default_rng(427)
image_path, config_path = sys.argv[1:3]
with open(config_path, encoding='utf8') as f:
    config = json.load(f)
with Image.open(image_path) as image:
    image = ImageOps.exif_transpose(image).convert('RGBA')
    matte = Image.new('RGB', image.size, (242, 234, 219))
    matte.paste(image, mask=image.getchannel('A'))
    tgt = ImageOps.fit(matte, (W, H), method=Image.Resampling.LANCZOS)
T = np.asarray(tgt, np.float32)
FACE = (config['focus'][0] * W, config['focus'][1] * H)
radius_x, radius_y = config['radius'][0] * W, config['radius'][1] * H
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
face_d = np.hypot((xx - FACE[0]) / radius_x, (yy - FACE[1]) / radius_y)       # <1 = 脸
GROUND = np.array([126, 92, 66], np.float32)        # 底色：熟褐色的底
canvas = Image.new('RGB', (W, H), tuple(int(v) for v in GROUND))

def layer(R, Tthr, maxlen, minlen, fc, mask=None, grid=None, force=None):
    global canvas
    ref = np.stack([gaussian_filter(T[..., c], R * .45) for c in range(3)], -1)
    lum = ref @ np.array([.3, .59, .11], np.float32)
    gx, gy = sobel(lum, 1), sobel(lum, 0)
    C = np.asarray(canvas, np.float32)
    diff = np.abs(C - ref).sum(-1)
    g = grid or max(2, int(round(R)))
    area = uniform_filter(diff, g)
    strokes = []
    for y0 in range(g // 2, H, g):
        for x0 in range(g // 2, W, g):
            if area[y0, x0] < Tthr and not (force is not None and force[y0, x0]): continue
            if mask is not None and not mask[y0, x0]: continue
            ya, yb, xa, xb = max(0, y0 - g // 2), min(H, y0 + g // 2 + 1), max(0, x0 - g // 2), min(W, x0 + g // 2 + 1)
            k = int(np.argmax(diff[ya:yb, xa:xb])); py, px = divmod(k, xb - xa); x, y = float(xa + px), float(ya + py)
            col = ref[int(y), int(x)]; pts = [(x, y)]; lx = ly = 0.0
            for i in range(maxlen):
                xi, yi = int(x), int(y)
                if i > minlen and np.abs(ref[yi, xi] - C[yi, xi]).sum() < np.abs(ref[yi, xi] - col).sum(): break
                dx, dy = -gy[yi, xi], gx[yi, xi]; n = math.hypot(dx, dy)
                if n < 1e-3:
                    if i == 0: dx, dy, n = math.cos(1.1), math.sin(1.1), 1.0      # 平的地方：给一个默认的斜向
                    else: break
                dx, dy = dx / n, dy / n
                if lx * dx + ly * dy < 0: dx, dy = -dx, -dy
                dx, dy = fc * dx + (1 - fc) * lx, fc * dy + (1 - fc) * ly; n = math.hypot(dx, dy) or 1; dx, dy = dx / n, dy / n
                x, y = x + R * dx, y + R * dy; lx, ly = dx, dy
                if not (0 <= x < W and 0 <= y < H): break
                pts.append((x, y))
            if len(pts) < 2: pts.append((min(W - 1, pts[0][0] + R * .8), min(H - 1, pts[0][1] + R * .5)))
            strokes.append((R, col, pts))
    # 落笔顺序：大致从外往里，脸留到最后（加一点随机）
    sgn = 1 if R > 40 else -1     # 第一层大笔先把人起出来（从脸往外），之后每层都是从外往里、脸留到最后
    strokes.sort(key=lambda s: sgn * np.hypot((s[2][0][0] - FACE[0]) / radius_x, (s[2][0][1] - (FACE[1] + 150)) / radius_y) + rng.normal(0, .9))
    d = ImageDraw.Draw(canvas)
    for R_, col, pts in strokes:
        c = tuple(int(v) for v in col); wd = max(1, int(round(R_ * 2)))
        d.line(pts, fill=c, width=wd, joint='curve')
        for p in (pts[0], pts[-1]): d.ellipse((p[0] - R_, p[1] - R_, p[0] + R_, p[1] + R_), fill=c)
    return strokes

out, counts = [], []
plan = [  # 半径, 阈值, 最长, 最短, 曲率平滑, 只画哪里
    (56, 30, 9, 3, .6, None), (28, 32, 10, 3, .6, None), (14, 30, 12, 3, .7, None), (7, 26, 12, 2, .8, None),
    (3.6, 24, 10, 2, .9, lambda: face_d < 2.2), (2.0, 20, 9, 2, 1.0, lambda: face_d < 1.15),
]
for R, th, ml, mn, fc, mk in plan:
    ss = layer(R, th, ml, mn, fc, mk() if mk else None, force=(face_d < 1.12) if R == 3.6 else None)   # 脸上用小笔整个盖一遍，不留大笔的厚痕
    counts.append(len(ss)); print('R', R, len(ss))
    for R_, col, pts in ss:
        out.append([R_, int(col[0]), int(col[1]), int(col[2])] + [int(round(v)) for p in pts for v in p])
with open('oil.json', 'w', encoding='utf8') as f:
    json.dump(dict(layers=counts, ground=GROUND.astype(int).tolist(), strokes=out, **config), f, separators=(',', ':'))
print('total', len(out), flush=True)
