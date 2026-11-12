"""Render a coarse-to-fine oil painting as a portrait-format MP4."""
import argparse
import base64
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).resolve().parents[1] / "assets"
FPS = 30
DEFAULT_SECONDS = 32.5


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="油画")
    parser.add_argument("--focus", nargs=2, type=float, default=(.5, .37), metavar=("X", "Y"))
    parser.add_argument("--detail", nargs=2, type=float, metavar=("X", "Y"))
    parser.add_argument("--radius", nargs=2, type=float, default=(.26, .21), metavar=("RX", "RY"))
    parser.add_argument("--seconds", type=float, default=DEFAULT_SECONDS)
    parser.add_argument("--browser", type=Path, help="Optional Chrome/Chromium executable")
    parser.add_argument("--no-overlay", action="store_true")
    audio = parser.add_mutually_exclusive_group()
    audio.add_argument("--music", type=Path)
    audio.add_argument("--silent", action="store_true")
    args = parser.parse_args()
    args.detail = args.detail or args.focus
    if not all(0 <= n <= 1 for n in (*args.focus, *args.detail)):
        parser.error("focus/detail must be normalized post-crop coordinates in [0, 1]")
    if not all(0 < n <= 1 for n in args.radius):
        parser.error("radius components must be in (0, 1]")
    if not 1 <= args.seconds <= 3600:
        parser.error("seconds must be between 1 and 3600")
    for file in (args.image, args.music, args.browser):
        if file is not None and not file.is_file():
            parser.error(f"File not found: {file}")
    if args.output.suffix.lower() != ".mp4" or args.output.exists():
        parser.error("Choose a new output path ending in .mp4")
    if not shutil.which("ffmpeg"):
        parser.error("ffmpeg is missing from PATH")
    return args


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def open_browser(pw, args):
    candidates = [args.browser] if args.browser else [
        Path(pw.chromium.executable_path),
        Path(os.environ.get("PROGRAMFILES", "/nonexistent")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "/nonexistent")) / "Microsoft/Edge/Application/msedge.exe",
        shutil.which("chromium") or shutil.which("google-chrome"),
    ]
    executable = next((p for p in candidates if p and Path(p).is_file()), None)
    if not executable:
        raise RuntimeError("Install Chromium with 'python -m playwright install chromium' or pass --browser")
    return pw.chromium.launch(executable_path=str(executable), headless=True,
        args=["--enable-webgl", "--enable-unsafe-swiftshader", "--disable-renderer-backgrounding"])


def encode(page, args, destination):
    page.evaluate("""() => {
      const c = document.createElement('canvas');
      c.width = 1080; c.height = 1920;
      const ctx = c.getContext('2d', {alpha:false});
      const gl = document.getElementById('gl'), overlay = document.getElementById('ov');
      window.jpegAt = t => {
        window.render(t); ctx.drawImage(gl,0,0); ctx.drawImage(overlay,0,0);
        return c.toDataURL('image/jpeg', .94).split(',')[1];
      };
    }""")
    count = round(args.seconds * FPS)
    duration = count / FPS
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe",
           "-framerate", str(FPS), "-vcodec", "mjpeg", "-i", "pipe:0"]
    if not args.silent:
        music = args.music or ASSETS / "mix_oil.wav"
        # Keep the built-in score and brush sounds in sync with the scaled timeline.
        if args.music:
            cmd.extend(["-stream_loop", "-1", "-i", str(music.resolve())])
            fade = min(1, duration / 4)
            audio_filter = f"afade=t=out:st={duration-fade}:d={fade}"
        else:
            cmd.extend(["-i", str(music)])
            tempo = DEFAULT_SECONDS / duration
            chain = []
            while tempo < .5 or tempo > 2:
                step = .5 if tempo < .5 else 2
                chain.append(f"atempo={step}")
                tempo /= step
            audio_filter = ",".join([*chain, f"atempo={tempo}", "apad"])
        cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-af", audio_filter,
                    "-c:a", "aac", "-b:a", "192k"])
    cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", "-t", str(duration), str(destination)])
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as encoder:
        try:
            for i in range(count):
                data = page.evaluate("t => jpegAt(t)", i * DEFAULT_SECONDS / count)
                encoder.stdin.write(base64.b64decode(data))
                if i % 90 == 0:
                    print(f"Frame {i+1}/{count}", flush=True)
        finally:
            encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError("FFmpeg failed")


def main():
    args = arguments()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory(dir=output.parent) as staging:
        folder = Path(work)
        for name in ("oil.js", "index.html"):
            shutil.copyfile(ASSETS / name, folder / name)
        config = dict(focus=args.focus, detail=args.detail, radius=args.radius,
                      title=args.title, overlay=not args.no_overlay)
        (folder / "config.json").write_text(json.dumps(config), encoding="utf8")
        subprocess.run([sys.executable, "-u", str(Path(__file__).with_name("strokes.py").resolve()),
                        str(args.image.resolve()), "config.json"], cwd=work, check=True)
        handler = functools.partial(QuietHandler, directory=work)
        movie = Path(staging) / "movie.mp4"
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                with sync_playwright() as pw:
                    browser = open_browser(pw, args)
                    page = browser.new_page(viewport={"width":1080, "height":1920})
                    page.on("pageerror", lambda err: print(err, file=sys.stderr))
                    page.goto(f"http://127.0.0.1:{server.server_port}/index.html")
                    page.wait_for_function("window.READY === true", timeout=120000)
                    encode(page, args, movie)
                    browser.close()
            finally:
                server.shutdown()
        # Reserve the destination only when a complete movie is ready.
        with output.open("xb"):
            pass
        try:
            os.replace(movie, output)
        except OSError:
            output.unlink(missing_ok=True)
            raise
    print(output)


if __name__ == "__main__":
    main()
