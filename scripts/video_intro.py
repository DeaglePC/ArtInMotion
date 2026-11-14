"""Frame budget for showing a clean finished painting before the first stroke."""


def preview_frames(count, fps, enabled):
    if not enabled or count < 3:
        return 0
    return min(round(1.2 * fps), max(1, count // 5))
