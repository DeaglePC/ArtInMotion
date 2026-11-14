"""Drawing sounds follow contact, placement and lift on the shared movie timeline."""

import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from art_styles import STYLES, Mark
from drawing_audio import MATERIALS, RATE, TOOL_MEDIUM, write_soundtrack


class SoundtrackTest(unittest.TestCase):
    def test_preset_coverage(self):
        self.assertEqual(set(MATERIALS) | {"colored-pencil"}, set(STYLES))
        self.assertEqual(set(TOOL_MEDIUM), {medium.tool for medium in STYLES.values()})

    def render(self, shape, style, music=False, opening_end=1.0, count=1, positions=(0, 0.5, 1, 1)):
        mark = Mark([(10, 20), (50, 45)], (20, 40, 60), shape=shape)
        # First mark runs from zero to one second, then the tool rests.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.wav"
            write_soundtrack(
                path,
                [mark] * count,
                positions,
                2,
                60,
                style,
                42,
                music,
                opening_end=opening_end,
            )
            with wave.open(str(path)) as reader:
                self.assertEqual(reader.getnframes(), len(positions) * RATE // 2)
                return np.frombuffer(
                    reader.readframes(reader.getnframes()), "<i2"
                ).reshape(-1, 2)

    def test_pencil_stops_during_lift_and_hold(self):
        samples = self.render("line", "colored-pencil")
        contact = samples[: int(RATE * 0.85)].std()
        self.assertGreater(contact, 80)
        self.assertLess(contact, 1400)
        self.assertFalse(samples[int(RATE * 0.87) :].any())
        mixed = self.render("line", "colored-pencil", True)
        self.assertGreater(mixed[RATE : int(RATE * 1.4)].std(), 20)

    def test_pencil_only_in_slow_opening(self):
        opening = self.render("line", "colored-pencil", opening_end=0.25)
        self.assertTrue(opening[: RATE // 4].any())
        self.assertFalse(opening[RATE // 4 :].any())
        self.assertFalse(self.render("line", "colored-pencil", opening_end=0).any())
        mixed = self.render("line", "colored-pencil", True, opening_end=0.25)
        piano = self.render("line", "colored-pencil", True, opening_end=0)
        np.testing.assert_array_equal(mixed[RATE // 4 :], piano[RATE // 4 :])

    def test_only_first_three_marks_have_sound_in_every_style(self):
        # Two preview frames, then five marks and a final hold.
        timeline = (0, 0, 0, 1, 2, 3, 4, 5, 5)
        for style, medium in STYLES.items():
            with self.subTest(style=style):
                shape = "tile" if medium.tool in ("tile", "piece") else "line"
                audio = self.render(shape, style, opening_end=4, count=5, positions=timeline)
                self.assertFalse(audio[:RATE].any())
                for i in range(3):
                    start = RATE + i * RATE // 2
                    self.assertTrue(audio[start:start + RATE // 2].any())
                self.assertFalse(audio[5 * RATE // 2:].any())

    def test_tile_taps_on_placement(self):
        samples = self.render("tile", "pixel")
        self.assertFalse(samples[: int(RATE * 0.85)].any())
        self.assertGreater(samples[int(RATE * 0.86) : int(RATE * 0.93)].std(), 100)
        self.assertFalse(samples[RATE:].any())
