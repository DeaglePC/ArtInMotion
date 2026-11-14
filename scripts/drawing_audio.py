"""Synthesize drawing foley and a quiet piano score against the renderer's frame clock."""

import wave
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

RATE = 44100
CONTACT = 0.86  # The remaining fraction moves the tool to the next mark.

# Friction band (Hz), surface roughness, level and contact resonance (Hz).
# Wider, lower bands give wet media a softer swish; dry points have more grain.
MATERIALS = {
    "contour": (1350, 5400, 0.35, 0.19, 1400),
    "hatching": (1650, 6200, 0.62, 0.18, 1700),
    "charcoal": (310, 2800, 0.84, 0.24, 440),
    "ink-wash": (180, 1550, 0.22, 0.17, 330),
    "watercolor": (290, 2400, 0.18, 0.18, 460),
    "gongbi": (650, 3300, 0.26, 0.17, 730),
    "realist": (350, 2850, 0.37, 0.18, 530),
    "impasto": (210, 2050, 0.76, 0.24, 300),
    "pastel": (510, 3500, 0.75, 0.21, 580),
    "crayon": (250, 2250, 0.88, 0.23, 420),
    "flat": (540, 3100, 0.36, 0.17, 680),
    "woodcut": (370, 4200, 0.91, 0.23, 760),
    "block-print": (110, 1550, 0.72, 0.23, 240),
    "stipple": (1350, 6700, 0.31, 0.20, 1830),
    "collage": (740, 4400, 0.67, 0.22, 530),
    "sand": (420, 4300, 0.74, 0.065, 420),
    "marbling": (145, 1400, 0.27, 0.17, 355),
    "facets": (460, 3500, 0.37, 0.19, 950),
    "pixel": (1150, 4900, 0.20, 0.17, 2080),
}
TOOL_MEDIUM = {
    "pen": "contour",
    "pencil": "colored-pencil",
    "chalk": "pastel",
    "brush": "watercolor",
    "gouge": "woodcut",
    "roller": "block-print",
    "grain": "sand",
    "piece": "collage",
    "tile": "pixel",
    "stylus": "marbling",
}


def piano_notes(duration, rng):
    """Voice a repeating four-chord phrase with sparse upper notes."""
    root = int(rng.choice([48, 50, 53, 55]))
    beat = rng.uniform(0.76, 0.89)
    voicings = [(0, 4, 7, 11), (-3, 0, 4, 7), (-7, -3, 0, 4), (-5, 0, 2, 7)]
    notes = []
    for bar in range(int(duration / (4 * beat)) + 1):
        bass, third, fifth, top = voicings[bar % 4]
        phrase = [
            (0, bass - 12, 0.105),
            (0.52, fifth, 0.075),
            (1.03, third, 0.083),
            (2.03, top + 12, 0.088),
            (3.05, fifth + 12, 0.061),
        ]
        if bar % 4 == 3:
            phrase.pop()
        for offset, interval, velocity in phrase:
            start = 0.06 + (4 * bar + offset) * beat + rng.uniform(0, 0.028)
            notes.append(
                (
                    start,
                    440 * 2 ** ((root + interval - 69) / 12),
                    velocity * rng.uniform(0.82, 1),
                )
            )
    return notes


def piano_block(t, notes, duration):
    stereo = np.zeros((len(t), 2))
    for start, frequency, velocity in notes:
        if start > t[-1] or start + 3.8 < t[0]:
            continue
        section = slice(np.searchsorted(t, start), np.searchsorted(t, start + 3.8))
        age = t[section] - start
        phase = 2 * np.pi * frequency * age
        # Slightly detuned strings and quickly decaying upper partials.
        body = np.sin(phase) + 0.34 * np.sin(phase * 1.0011)
        body += 0.42 * np.exp(-1.5 * age) * np.sin(phase * 2.001)
        body += 0.19 * np.exp(-2.6 * age) * np.sin(phase * 3.005)
        note = (
            velocity
            * body
            * (-np.expm1(-age / 0.009))
            * np.exp(-age * (1.35 + frequency / 2100))
        )
        pan = np.clip(0.43 + 0.00028 * (frequency - 220), 0.27, 0.72)
        stereo[section] += note[:, None] * np.array([1 - pan, pan])
    return stereo * np.clip((duration - t) / min(1.3, duration * 0.32), 0, 1)[:, None]


def recorded_pencil(path, marks, positions, fps, width, rng, notes, opening_end):
    """Place natural-speed pencil phrases on the same timeline as the drawing."""
    rate, pcm = wavfile.read(
        Path(__file__).resolve().parents[1] / "assets/pencil-strokes.wav"
    )
    if rate != RATE or pcm.ndim != 1 or len(pcm) % RATE:
        raise ValueError("Expected one-second mono pencil takes at the mix rate")
    takes = pcm.reshape(-1, RATE).astype(float) / 32768
    positions = np.asarray(positions, dtype=float)
    frame_clock = np.arange(len(positions)) / fps
    duration = len(positions) / fps
    total = round(duration * RATE)
    # Only schedule gestures on the slow opening segment of the picture clock.
    events = []
    next_time = 0.0
    bag = []
    while next_time < min(opening_end, frame_clock[-1]) and marks:
        pos = np.interp(next_time, frame_clock, positions)
        index = int(pos)
        if index >= len(marks):
            break
        # Skip static frames, including the pause before first contact.
        frame = min(int(next_time * fps), len(positions) - 2)
        if positions[frame + 1] <= pos:
            later = np.searchsorted(positions, pos, side="right")
            if later >= len(positions):
                break
            next_time = max(next_time + 1 / RATE, frame_clock[later - 1])
            continue
        if pos - index >= CONTACT:
            next_time = np.interp(index + 1, positions, frame_clock) + 1 / RATE
            continue
        lift = np.interp(index + CONTACT, positions, frame_clock)
        length = min(rng.uniform(0.58, 0.94), min(lift, opening_end) - next_time)
        start = round(next_time * RATE)
        length_samples = min(round(length * RATE), total - start)
        if length_samples > RATE * 0.012:
            if not bag:
                bag = rng.permutation(len(takes)).tolist()
            take = bag.pop()
            gain = rng.uniform(0.65, 0.95)
            pan = 0.40 + 0.20 * marks[index].points[0][0] / width
            events.append((start, start + length_samples, take, gain, pan))
        next_time += max(length, 0.006)
        if next_time < lift - 0.002:
            next_time += 0.018

    active = 0
    with wave.open(str(path), "wb") as out:
        out.setparams((2, 2, RATE, 0, "NONE", "not compressed"))
        for offset in range(0, total, RATE):
            stop = min(total, offset + RATE)
            t = np.arange(offset, stop) / RATE
            stereo = piano_block(t, notes, duration) * 0.35
            writing = np.zeros_like(stereo)
            while active < len(events) and events[active][1] <= offset:
                active += 1
            for i in range(active, len(events)):
                start, end, take, gain, pan = events[i]
                if start >= stop:
                    break
                lo, hi = max(start, offset), min(end, stop)
                edge = np.arange(lo, hi)
                fade = np.minimum(1, (edge - start) / (RATE * 0.010)) * np.minimum(
                    1, (end - edge - 1) / (RATE * 0.022)
                )
                z = takes[take, lo - start : hi - start] * fade * gain
                writing[lo - offset : hi - offset] += (
                    z[:, None] * np.array([1 - pan, pan]) * 1.85
                )
            # Keep any pause between visible marks silent.
            f = np.minimum((t * fps).astype(int), len(positions) - 1)
            moving = positions[np.minimum(f + 1, len(positions) - 1)] > positions[f]
            stereo += writing * moving[:, None]
            out.writeframesraw((stereo.clip(-1, 1) * 32767).astype("<i2").tobytes())


def write_soundtrack(
    path, marks, positions, fps, width, style, seed, with_piano, *, opening_end
):
    """Integrate contact occupancy across audio samples, even in accelerated passages."""
    rng, music_rng = [
        np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2)
    ]
    duration = len(positions) / fps
    notes = piano_notes(duration, music_rng) if with_piano else []
    if style == "colored-pencil":
        return recorded_pencil(
            path, marks, positions, fps, width, rng, notes, opening_end
        )
    low, high, roughness, level, resonance = MATERIALS[style]
    band = butter(2, [low, high], btype="bandpass", fs=RATE, output="sos")
    state = np.zeros((len(band), 2))
    # A tile arrives when the visible placement completes. Dots touch at onset.
    placed = np.fromiter((m.shape in ("polygon", "tile") for m in marks), bool)
    dots = np.fromiter((m.shape == "dot" or len(m.points) == 1 for m in marks), bool)
    taps = placed | dots
    begin = np.where(placed, CONTACT, 0.0)
    end = np.where(placed, 0.995, np.where(dots, 0.34, CONTACT))
    occupancy = np.r_[0.0, np.cumsum(end - begin)]
    pan = np.array([m.points[0][0] / width for m in marks])
    pressure = np.array(
        [0.70 + 0.25 * m.opacity / 255 + 0.05 * min(1, m.width / 4) for m in marks]
    )
    # For a single-frame clip the finished canvas is already present at time zero.
    frame_times = np.arange(len(positions)) / fps
    total = round(duration * RATE)
    with wave.open(str(path), "wb") as out:
        out.setparams((2, 2, RATE, 0, "NONE", "not compressed"))
        for offset in range(0, total, RATE):
            boundary = np.arange(offset, min(offset + RATE, total) + 1) / RATE
            t = boundary[:-1]
            stereo = piano_block(t, notes, duration)
            if marks:
                pos = np.interp(boundary, frame_times, positions)
                index = np.minimum(pos.astype(int), len(marks) - 1)
                phase = pos - index
                integral = occupancy[index] + np.clip(
                    phase - begin[index], 0, end[index] - begin[index]
                )
                delta = np.diff(pos)
                gate = np.divide(
                    np.diff(integral), delta, out=np.zeros_like(delta), where=delta > 0
                )
                # Resolve very fast time-lapse marks over a short acoustic window.
                # Repeated sub-millisecond lift gates would otherwise buzz at a fixed pitch.
                fast = delta * RATE > 100
                if np.any(fast):
                    span = np.maximum(1.0, delta[fast] * RATE * 0.012)
                    left = np.maximum(0.0, pos[:-1][fast] - span / 2)
                    right = np.minimum(len(marks), left + span)

                    def contact_total(at):
                        i = np.minimum(at.astype(int), len(marks) - 1)
                        return occupancy[i] + np.clip(
                            at - i - begin[i], 0, end[i] - begin[i]
                        )

                    gate[fast] = (contact_total(right) - contact_total(left)) / (
                        right - left
                    )
                # Ease the pressure at both ends on individually visible strokes.
                age = (phase[:-1] - begin[index[:-1]]) / np.maximum(delta * RATE, 1e-8)
                remaining = (end[index[:-1]] - phase[:-1]) / np.maximum(
                    delta * RATE, 1e-8
                )
                edge = np.clip(np.minimum(age, remaining) / 0.009, 0, 1)
                gate *= np.where(delta * RATE < 25, edge, 1.0)
                noise, state = sosfilt(band, rng.normal(size=len(t)), zi=state)
                noise *= np.sqrt(RATE / (2 * (high - low)))
                grain = (
                    0.58
                    + 0.42
                    * np.sin(2 * np.pi * 7.3 * t + 1.5 * np.sin(2 * np.pi * 1.82 * t))
                    ** 2
                )
                grain *= 1 + roughness * 0.42 * np.sin(
                    2 * np.pi * 57 * t + 3 * np.sin(2 * np.pi * 4.1 * t)
                )
                # A short contact attack distinguishes discrete placements from sliding tools.
                hit = np.exp(-np.maximum(age, 0) * 75) * np.sin(
                    2 * np.pi * resonance * age
                )
                hit *= (delta * RATE < 25) * np.where(taps[index[:-1]], 0.95, 0.18)
                discrete = taps[index[:-1]]
                grain *= np.where(
                    discrete & (delta * RATE < 25),
                    0.14 + 0.86 * np.exp(-np.maximum(age, 0) * 36),
                    1.0,
                )
                grain *= np.where(
                    discrete & (delta * RATE >= 25),
                    0.46 + 0.54 * np.sin(2 * np.pi * 12 * t + 2 * np.sin(24 * t)) ** 8,
                    1.0,
                )
                mono = level * gate * pressure[index[:-1]] * (noise * grain + hit)
                balance = 0.35 + 0.30 * pan[index[:-1]]
                stereo += mono[:, None] * np.column_stack((1 - balance, balance))
            out.writeframesraw((np.tanh(stereo * 1.55) * 32760).astype("<i2").tobytes())
