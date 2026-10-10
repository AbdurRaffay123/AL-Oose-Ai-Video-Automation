"""The clip library (library/clips/clips.yaml): paid clips reused for free in new episodes (owner 2026-10-06).

Script tags:
  ACTION [reuse:EP001_S07, from:2.5]: …      plays the clip (from 2.5 s) under the pending narration;
  BILLY [reuse:EP001_S08, canon:p31]: Oh POOP!  a talking clip WITH its own approved line audio (text must match).
The clip is fitted to the shot: trimmed, or slowed down by up to MAX_SLOW when the narration is longer (never a
frozen still: a longer narration than that is refused). Known fixes travel with the clip: `hold_frames` (Saul blinks)
and, for Billy clips flagged `chin_white`, a `trapped_white` fix that must be set per clip (clips.yaml `fixes:`).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

from .paths import LIBRARY

LIB = LIBRARY / "clips" / "clips.yaml"
MAX_SLOW = 1.35                                    # a reused clip may play at most this much slower


def load() -> dict:
    return yaml.safe_load(LIB.read_text()) or {}


def entry(clip_id: str) -> dict:
    lib = load()
    if clip_id not in lib:
        raise KeyError(f"unknown clip '{clip_id}' (see library/clips/CLIP_INVENTORY.md)")
    e = dict(lib[clip_id])
    if e.get("reusable") == "no":
        raise ValueError(f"clip {clip_id} is marked 'no' (rejected/test): {e.get('notes')}")
    e["abs"] = LIBRARY.parent / e["path"]
    return e


def window(e: dict, start: float) -> tuple[float, float]:
    """Usable [start, end] seconds: `best: a-b` limits the window (e.g. a crash clip that melts after 3.2 s)."""
    a, b = 0.0, float(e["duration"])
    if e.get("best"):
        lo, hi = (float(x) for x in str(e["best"]).split("-"))
        a, b = lo, hi
    return max(a, start), b


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def talk_audio(e: dict, line_text: str) -> tuple[Path, float]:
    """(audio file, lead seconds) of a talking clip; refuses a different line (the beak moves to ITS words)."""
    if not e.get("audio"):
        raise ValueError("this clip has no recorded line to reuse")
    if norm(line_text) != norm(e.get("line", "")):
        raise ValueError(f"reused talking clip says \"{e.get('line')}\" - the script line must be the same words")
    return LIBRARY.parent / e["audio"], float(e.get("audio_lead", 0.0))


def frame(e: dict, t: float, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(e["abs"]), "-frames:v", "1", str(dst)],
                   check=True)
    return dst


def fitted(e: dict, start: float, seconds: float, size: tuple[int, int], dst: Path, fixes: dict | None = None,
           plate=None) -> Path:
    """The clip window from `start`, fixed (clip_fixes), stretched up to MAX_SLOW if needed, exactly `seconds` long."""
    from . import clipfix, media
    src = e["abs"]
    allfix = {**(e.get("fixes") or {}), **({"hold_frames": e["hold_frames"]} if e.get("hold_frames") else {}),
              **(fixes or {})}
    if allfix:
        from PIL import Image
        src = clipfix.apply(src, plate if plate is not None else Image.new("RGB", size), allfix,
                            dst.with_name(dst.stem + "_fix.mp4"))
    a, b = window(e, start)
    avail = b - a
    slow = max(1.0, seconds / avail) if avail > 0 else 99
    if slow > MAX_SLOW + 1e-6:
        raise ValueError(f"clip window {avail:.2f}s can't cover {seconds:.2f}s even at {MAX_SLOW}x slow-down")
    W, H = size
    vf = (f"trim={a:.3f}:{b:.3f},setpts=(PTS-STARTPTS)*{slow:.4f},scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps=24,format=yuv420p")
    media.ffmpeg("-i", str(src), "-vf", vf, "-t", f"{seconds:.3f}", "-an", "-c:v", "libx264", "-crf", "16", str(dst))
    return dst
