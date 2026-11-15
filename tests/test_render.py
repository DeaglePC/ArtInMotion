"""Regression checks for the public CLI. Run python -m unittest discover -s tests."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

RENDER = Path(__file__).resolve().parents[1] / "scripts" / "render_art.py"


class ExportTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)

    def run_cli(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(RENDER), *args],
            cwd=self.folder,
            capture_output=True,
            check=check,
        )

    @unittest.skipUnless(shutil.which("ffmpeg"), "video check needs FFmpeg")
    def test_photo_exports_share_canvas(self):
        photo = Image.new("RGB", (70, 48), "linen")
        ImageDraw.Draw(photo).ellipse((4, 6, 38, 39), fill="indianred")
        exif = Image.Exif()
        exif[274] = 6
        photo.save(self.folder / "input.jpg", exif=exif)
        options = (
            "--input",
            "input.jpg",
            "--style",
            "04",
            "--size",
            "70",
            "--seed",
            "17",
        )
        self.run_cli(*options, "--image", "still.png")
        self.run_cli(
            *options,
            "--no-board",
            "--image",
            "both.png",
            "--video",
            "draw.mp4",
            "--no-tool",
            "--seconds",
            "1",
            "--fps",
            "8",
            "--opening-seconds",
            "0.3",
        )
        with Image.open(self.folder / "still.png") as im:
            self.assertEqual(im.size, (48, 70))
            expected = np.array(im, dtype=float)
        with Image.open(self.folder / "both.png") as im:
            np.testing.assert_array_equal(expected, np.array(im))
        raw = subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                "draw.mp4",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-",
            ],
            cwd=self.folder,
        )
        frames = np.frombuffer(raw, dtype=np.uint8).reshape(8, 70, 48, 3)
        self.assertLess(np.abs(frames[0] - expected).mean(), 5.5)
        self.assertLess(frames[1].std(axis=(0, 1)).max(), 1)
        self.assertLess(np.abs(frames[-1] - expected).mean(), 5.5)

    @unittest.skipUnless(shutil.which("ffmpeg"), "video check needs FFmpeg")
    def test_default_drawing_board_and_orientation_aspect(self):
        photo = Image.new("RGB", (180, 120), (235, 224, 210))
        ImageDraw.Draw(photo).ellipse((65, 25, 115, 85), fill=(196, 112, 88))
        photo.save(self.folder / "src.png")

        # 1. Default video uses studio drawing board; --image stays clean paper
        res = self.run_cli(
            "--input",
            "src.png",
            "--style",
            "04",
            "--size",
            "240",
            "--seconds",
            "1",
            "--fps",
            "6",
            "--silent",
            "--image",
            "clean.png",
            "--video",
            "board.mp4",
        )
        info = json.loads(res.stdout.decode("utf8"))
        self.assertEqual(info["board"], "tape")
        self.assertEqual(info["video_size"][0], 240)
        self.assertGreater(info["video_size"][0], info["size"][0])
        self.assertGreater(info["video_size"][1], info["size"][1])
        with Image.open(self.folder / "clean.png") as clean_im:
            self.assertEqual(list(clean_im.size), info["size"])

        # 2. Explicit portrait 9:16 video + 3:4 aspect crop + brass clip + --image-board
        res_v = self.run_cli(
            "--input",
            "src.png",
            "--style",
            "06",
            "--size",
            "320",
            "--orientation",
            "竖屏",
            "--aspect",
            "3:4",
            "--board",
            "clip",
            "--image-board",
            "--seconds",
            "1",
            "--fps",
            "6",
            "--silent",
            "--image",
            "framed.png",
            "--video",
            "vertical.mp4",
        )
        v_info = json.loads(res_v.stdout.decode("utf8"))
        self.assertEqual(v_info["board"], "clip")
        self.assertEqual(v_info["video_size"], [180, 320])
        self.assertLess(v_info["size"][0], v_info["size"][1])
        with Image.open(self.folder / "framed.png") as framed_im:
            self.assertEqual(list(framed_im.size), v_info["video_size"])

    def test_pencil_covers_dark_regions_and_preserves_small_highlights(self):
        photo = Image.new("RGB", (160, 96), (25, 21, 30))
        draw = ImageDraw.Draw(photo)
        draw.rectangle((63, 23, 66, 74), fill=(248, 245, 243))
        photo.save(self.folder / "contrast.png")
        self.run_cli(
            "--input",
            "contrast.png",
            "--style",
            "colored-pencil",
            "--size",
            "160",
            "--image",
            "drawing.png",
        )
        with Image.open(self.folder / "drawing.png") as im:
            actual = np.asarray(im).mean(axis=2)
        self.assertLess(actual[np.asarray(photo)[:, :, 0] < 40].max(), 76)
        self.assertGreater(actual[26:70, 64:66].mean(), 210)

    def test_plan_and_no_overwrite(self):
        plan = {
            "size": [96, 64],
            "ground": [255] * 3,
            "tool": "pencil",
            "marks": [{"points": [[8, 16], [24, 16]], "color": [30, 78, 119]}],
        }
        (self.folder / "scene.json").write_text(json.dumps(plan))
        opts = ("--plan", "scene.json", "--image", "scene.png")
        self.run_cli(*opts)
        with Image.open(self.folder / "scene.png") as im:
            self.assertEqual(im.getpixel((16, 16)), (30, 78, 119))
            self.assertEqual(im.getpixel((60, 36)), (255, 255, 255))
        self.assertNotEqual(self.run_cli(*opts, check=False).returncode, 0)

    @unittest.skipUnless(shutil.which("ffmpeg"), "video check needs FFmpeg")
    def test_impasto_oil_3d_relief_and_chinese_aliases(self):
        photo = Image.new("RGB", (144, 144), (222, 220, 216))
        draw = ImageDraw.Draw(photo)
        draw.ellipse((34, 26, 110, 118), fill=(214, 156, 128))
        photo.save(self.folder / "portrait.png")
        self.run_cli(
            "--input",
            "portrait.png",
            "--style",
            "厚涂油画",
            "--size",
            "144",
            "--no-board",
            "--seconds",
            "1.5",
            "--fps",
            "8",
            "--silent",
            "--image",
            "oil.png",
            "--video",
            "oil.mp4",
        )
        with Image.open(self.folder / "oil.png") as im:
            arr = np.asarray(im, dtype=float)
            self.assertEqual(im.size, (144, 144))
            # Impasto bristle ridges create tangible local luminance relief even on uniform source patches
            self.assertGreater(arr[10:30, 10:30].std(), 3.0)

