import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from video_intro import TRANSITIONS, choose_transitions, intro_images, transition_id


class TransitionTest(unittest.TestCase):
    def test_aliases_and_random_pair(self):
        for i, (key, name) in enumerate(TRANSITIONS.items(), 1):
            self.assertEqual(transition_id(name), key)
            self.assertEqual(transition_id(f"{i:02}"), key)
        with patch("video_intro.secrets.choice", return_value="iris") as pick:
            self.assertEqual(choose_transitions(None, None), ("iris", "iris"))
            pick.assert_called_once()
        self.assertEqual(choose_transitions("prism", "focus"), ("prism", "focus"))

    def test_all_pairs_enter_hold_and_return_to_actual_paper(self):
        rng = np.random.default_rng(34)
        art = Image.fromarray(rng.integers(0, 256, (46, 62, 3), dtype=np.uint8))
        paper = Image.new("RGB", art.size, (143, 101, 67))
        masks = set()
        for key in TRANSITIONS:
            frames = list(intro_images(art, paper, 69, key, key))
            self.assertEqual(len(frames), 69)
            self.assertEqual(frames[30].tobytes(), art.tobytes())
            self.assertEqual(frames[-1].tobytes(), paper.tobytes())
            for frame in (frames[7], frames[-9]):
                self.assertNotIn(frame.tobytes(), (art.tobytes(), paper.tobytes()))
            masks.add(frames[7].tobytes())
        self.assertEqual(len(masks), 10)
