"""FFmpeg's named xfade transitions in stable catalog order."""

import re
import subprocess
import tempfile
from functools import lru_cache

from PIL import Image

PRESETS = {
    "fade": "交叉淡化",
    "wipeleft": "向左擦除",
    "wiperight": "向右擦除",
    "wipeup": "向上擦除",
    "wipedown": "向下擦除",
    "slideleft": "左推画面",
    "slideright": "右推画面",
    "slideup": "上推画面",
    "slidedown": "下推画面",
    "circlecrop": "圆形裁切",
    "rectcrop": "矩形裁切",
    "distance": "色距溶合",
    "fadeblack": "淡经黑场",
    "fadewhite": "淡经白场",
    "radial": "旋转扫盘",
    "smoothleft": "柔边左移",
    "smoothright": "柔边右移",
    "smoothup": "柔边上移",
    "smoothdown": "柔边下移",
    "circleopen": "圆窗张开",
    "circleclose": "圆窗收拢",
    "vertopen": "中线左右开门",
    "vertclose": "两侧左右合门",
    "horzopen": "中线上下开帘",
    "horzclose": "两侧上下合帘",
    "dissolve": "颗粒溶解",
    "pixelize": "像素聚焦",
    "diagtl": "斜线左上",
    "diagtr": "斜线右上",
    "diagbl": "斜线左下",
    "diagbr": "斜线右下",
    "hlslice": "横切片向左",
    "hrslice": "横切片向右",
    "vuslice": "纵切片向上",
    "vdslice": "纵切片向下",
    "hblur": "横向动感模糊",
    "fadegrays": "灰阶显色",
    "wipetl": "左上角擦除",
    "wipetr": "右上角擦除",
    "wipebl": "左下角擦除",
    "wipebr": "右下角擦除",
    "squeezeh": "横向挤压",
    "squeezev": "纵向挤压",
    "zoomin": "推镜放大",
    "fadefast": "快速淡化",
    "fadeslow": "缓慢淡化",
    "hlwind": "左向风痕",
    "hrwind": "右向风痕",
    "vuwind": "上向风痕",
    "vdwind": "下向风痕",
    "coverleft": "向左覆盖",
    "coverright": "向右覆盖",
    "coverup": "向上覆盖",
    "coverdown": "向下覆盖",
    "revealleft": "向左揭幕",
    "revealright": "向右揭幕",
    "revealup": "向上揭幕",
    "revealdown": "向下揭幕",
}


@lru_cache(maxsize=1)
def available():
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-h", "filter=xfade"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return frozenset()
    return frozenset(
        re.findall(r"^\s+(\w+)\s+\d+\s+\.\.FV", result.stdout + result.stderr, re.MULTILINE)
    ).intersection(PRESETS)


def frames(start, end, count, effect):
    """Stream one leg using two stills; retain only the current frame in memory."""
    if count < 2:
        yield end
        return
    width, height = start.size
    frame_bytes = width * height * 3
    # gbrp avoids a YUV round trip at the transition boundaries.
    graph = (
        "[0:v]format=gbrp,split[a][b];"
        "[a]trim=end_frame=1,loop=-1:1:0,setpts=N[a0];"
        "[b]trim=start_frame=1:end_frame=2,loop=-1:1:0,setpts=N[b0];"
        f"[a0][b0]xfade=transition={effect}:duration={count / 25:.6f},trim=start_frame=1,format=rgb24"
    )
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        "25",
        "-i",
        "pipe:0",
        "-filter_complex_threads",
        "2",
        "-filter_complex",
        graph,
        "-frames:v",
        str(count - 1),
        "-fps_mode",
        "passthrough",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "pipe:1",
    ]
    with tempfile.TemporaryFile() as source:
        source.write(start.convert("RGB").tobytes())
        source.write(end.convert("RGB").tobytes())
        source.seek(0)
        with subprocess.Popen(cmd, stdin=source, stdout=subprocess.PIPE) as process:
            try:
                for _ in range(count - 1):
                    data = process.stdout.read(frame_bytes)
                    if len(data) != frame_bytes:
                        raise RuntimeError(
                            f"FFmpeg xfade failed to produce a frame for {effect}"
                        )
                    yield Image.frombytes("RGB", start.size, data)
                if process.wait():
                    raise RuntimeError(f"FFmpeg xfade failed for {effect}")
            finally:
                if process.poll() is None:
                    process.kill()
    yield end
