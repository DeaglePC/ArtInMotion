"""A finger pass clears an illuminated track and displaces sand to its lip."""

import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sand_table import Gesture, SandTable


class SandTest(unittest.TestCase):
    def test_pour_and_displace(self):
        table = SandTable(
            np.full((64, 80), 190, dtype="f"),
            np.random.default_rng(42),
            (255, 218, 145),
        )
        glass = table.base.copy()
        pour = Gesture(table, [(10, 32), (65, 32)], 8, "pour", 0)
        table.paint(glass, pour, 0.4)
        self.assertLess(glass.getpixel((18, 32))[0], table.base.getpixel((18, 32))[0])
        self.assertEqual(glass.getpixel((64, 32)), table.base.getpixel((64, 32)))
        bed = Image.new("RGB", glass.size, (90, 62, 43))
        before = np.asarray(bed).copy()
        table.paint(bed, Gesture(table, [(12, 32), (65, 32)], 8, "groove", 3), 1)
        after = np.asarray(bed)
        self.assertGreater(after[32, 35, 0], before[32, 35, 0])
        self.assertLess(after[40, 35, 0], before[40, 35, 0])
