"""Reference-video analysis (free, local): what makes an owner-approved clip look natural.

`bbtb refs analyze <video or folder> ...` writes, per video, into library/reference/<slug>/:
  sheet.jpg   - 4 frames per second in a grid (motion, poses, ground contact at a glance)
  stats.json  - size, fps, duration, audio, cuts, camera motion and subject-motion curve
Reference files are only read (never copied, moved or re-encoded in place). The stats feed the
prompt notes in library/kling_prompts.yaml; the sheets are for Claude/the owner to look at.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from . import media
from .paths import LIBRARY

OUT = LIBRARY / "reference"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}
AW, AH, AFPS = 192, 256, 8          # analysis size/fps


def slug(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")[:60] or "video"


def probe(path: Path) -> dict:
    d = json.loads(media.run(["ffprobe", "-v", "error", "-show_entries",
                              "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", str(path)]))
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    num, den = v["r_frame_rate"].split("/")
    return {"width": v["width"], "height": v["height"], "fps": round(float(num) / float(den), 2),
            "seconds": round(float(d["format"]["duration"]), 2),
            "audio": any(s["codec_type"] == "audio" for s in d["streams"])}


def _frames(path: Path, max_seconds: float) -> np.ndarray:
    raw = media.run_bytes(["ffmpeg", "-hide_banner", "-loglevel", "error", "-t", str(max_seconds), "-i", str(path),
                           "-vf", f"fps={AFPS},scale={AW}:{AH}", "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    return np.frombuffer(raw, np.uint8).reshape(-1, AH, AW).astype(np.float32)


def _shift(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Global translation between two frames (phase correlation) = camera pan/tilt estimate."""
    fa, fb = np.fft.fft2(a - a.mean()), np.fft.fft2(b - b.mean())
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    c = np.abs(np.fft.ifft2(r))
    y, x = np.unravel_index(np.argmax(c), c.shape)
    return (x if x < AW / 2 else x - AW), (y if y < AH / 2 else y - AH)


def analyze(path: Path, max_seconds: float = 30.0) -> dict:
    path = Path(path)
    info = probe(path)
    fr = _frames(path, max_seconds)
    diffs = np.array([np.abs(fr[i] - fr[i - 1]).mean() for i in range(1, len(fr))])
    cuts = [round(i / AFPS, 2) for i in range(1, len(fr)) if diffs[i - 1] > max(25.0, 4 * np.median(diffs))]
    pans = [_shift(fr[i], fr[i - 1]) for i in range(1, len(fr))]
    cam = float(np.mean([abs(x) + abs(y) for x, y in pans])) if pans else 0.0
    stats = {**info, "file": str(path), "analysed_seconds": round(len(fr) / AFPS, 2), "cuts": cuts,
             "motion_mean": round(float(diffs.mean()), 2) if len(diffs) else 0.0,
             "motion_curve": [round(float(x), 1) for x in diffs],
             "camera_shift_px_per_frame": round(cam, 2),
             "camera": "static" if cam < 0.3 else ("slow move" if cam < 1.5 else "moving")}
    dst = OUT / slug(path)
    dst.mkdir(parents=True, exist_ok=True)
    tw = 240
    th = int(tw * info["height"] / info["width"])
    n = min(int(min(info["seconds"], max_seconds) * 4), 48)
    raw = media.run_bytes(["ffmpeg", "-hide_banner", "-loglevel", "error", "-t", str(max_seconds), "-i", str(path),
                           "-vf", f"fps=4,scale={tw}:{th}", "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    thumbs = np.frombuffer(raw, np.uint8).reshape(-1, th, tw, 3)
    cols = 8
    sheet = Image.new("RGB", (cols * tw, ((len(thumbs) + cols - 1) // cols) * th))
    for i, t in enumerate(thumbs):
        sheet.paste(Image.fromarray(t), ((i % cols) * tw, (i // cols) * th))
    sheet.save(dst / "sheet.jpg", quality=85)
    (dst / "stats.json").write_text(json.dumps(stats, indent=2))
    stats["sheet"] = str(dst / "sheet.jpg")
    return stats


def collect(paths: list[str]) -> list[Path]:
    out = []
    for p in map(Path, paths):
        if p.is_dir():
            out += sorted(x for x in p.iterdir() if x.suffix.lower() in VIDEO_EXT)
        elif p.suffix.lower() in VIDEO_EXT:
            out.append(p)
    return out
