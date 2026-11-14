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
        self.assertLess(np.abs(frames[0] - expected).mean(), 5)
        self.assertLess(frames[1].std(axis=(0, 1)).max(), 1)
        self.assertLess(np.abs(frames[-1] - expected).mean(), 5)

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
