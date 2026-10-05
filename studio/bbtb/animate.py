"""Free local animation (cut-out style), rendered frame by frame with Pillow and piped to FFmpeg.

Motions:
  enter-left / enter-right : character hops in from off-screen (ease-out, small hops)
  pose:<art>               : pose change part-way through, on a small hop (cut-out "pop")
  shake                    : camera shake (fright, rumble), decaying
  (always)                 : gentle idle bob so nothing looks frozen
Talking (local_flap): the speaker's head swaps between the closed/open-mouth expression heads of
the same angle (library mouth_pairs), driven by the loudness of the line's audio. Art is only
moved/scaled - never redrawn.
"""
from __future__ import annotations

import math
import random
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from . import keyframes, voicelab
from .shots import Shot

FPS = 24


def _variant(char: dict, variant: str | None) -> dict:
    return char["variants"].get(variant or char.get("default_variant"), {})


def mouth_pair(char: dict, variant: str | None, art: str) -> tuple[str, str] | None:
    """(closed, open) head ids usable for this art, or None if the character can't flap here."""
    v = _variant(char, variant)
    pairs = v.get("mouth_pairs") or {}
    if not v.get("bust") or not pairs:
        return None
    name = next((n for g in ("expressions", "poses") for n, a in v.get(g, {}).items() if a == art), None)
    facing = v.get("facing", {}).get(name, "front")
    pair = pairs.get(facing)
    if not pair:
        return None
    if art in v.get("expressions", {}).values() and art not in pair:
        return None          # a specific expression (e.g. shock) has no matching open/closed partner
    if art in v.get("poses", {}).values() and art not in v["bust"]["bodies"].values():
        return None          # this body pose has no head-swap support (e.g. scroll poses)
    return tuple(pair)


def mouth_track(wav: Path, start: float, frames: int, threshold: float = 0.22, hold: int = 2) -> np.ndarray:
    """Per-frame open(1)/closed(0) from the line's loudness, starting `start` seconds into the shot."""
    x = voicelab.load(wav)
    hop = voicelab.SR // FPS
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) if i < len(x) else 0.0 for i in range(0, len(x) + hop, hop)])
    env = env / (env.max() + 1e-9)
    track = np.zeros(frames, dtype=np.int8)
    offset = int(round(start * FPS))
    for i, e in enumerate(env):
        if 0 <= offset + i < frames:
            track[offset + i] = 1 if e > threshold else 0
    # debounce: a state must last at least `hold` frames (avoids flicker)
    out, last, run = track.copy(), track[0] if frames else 0, 0
    for i in range(frames):
        if track[i] != last and run < hold:
            out[i] = last
            run += 1
        else:
            if track[i] != last:
                last, run = track[i], 1
            else:
                run += 1
            out[i] = last
    return out


def _ease_out(t: float) -> float:
    return 1 - (1 - min(max(t, 0.0), 1.0)) ** 3


def render(shot: Shot, chars: dict, size: tuple[int, int], dst: Path,
           lines: dict | None = None, line_starts: list[tuple[str, float]] | None = None) -> Path:
    W, H = size
    frames = max(1, round(shot.duration * FPS))
    cast = shot.cast

    # mouth flap: prepare aligned closed/open bust images for the speaker
    flap_imgs, flap = None, None
    if shot.kind == "talk" and cast:
        o = cast[0]
        pair = mouth_pair(chars[o.char], o.variant, o.art)
        if pair:
            v = _variant(chars[o.char], o.variant)
            name = next((n for g in ("expressions", "poses") for n, a in v.get(g, {}).items() if a == o.art), None)
            facing = v.get("facing", {}).get(name, "front")
            imgs = [keyframes.bust(chars[o.char], o.variant, head, crop=False, facing_override=facing) for head in pair]
            box = imgs[0].getbbox()
            b2 = imgs[1].getbbox()
            box = (min(box[0], b2[0]), min(box[1], b2[1]), max(box[2], b2[2]), max(box[3], b2[3]))
            flap_imgs = [im.crop(box) for im in imgs]
            if lines and line_starts:
                lid, start = line_starts[0]
                flap = mouth_track(Path(lines[lid]["path"]), start, frames)

    def placed_for(art_override: dict | None):
        return keyframes.layout(shot.scene, cast, chars, size, art_images=art_override, zoom=shot.zoom)

    bg, base = placed_for({0: flap_imgs[0]} if flap_imgs else None)
    open_layer = placed_for({0: flap_imgs[1]})[1] if flap_imgs else None

    pose_to = next((m.split(":", 1)[1] for m in shot.motion if m.startswith("pose:")), None)
    swapped = None
    if pose_to and cast:
        swap_cast = [type(cast[0])(**{**cast[0].__dict__, "art": pose_to})] + cast[1:]
        swapped = keyframes.layout(shot.scene, swap_cast, chars, size, zoom=shot.zoom)[1]
    t_swap = 0.45 * shot.duration

    enter = next((m for m in shot.motion if m.startswith("enter-")), None)
    glide = next((m for m in shot.motion if m.startswith("pass-")), None)   # smooth glide in from off-screen
    t_glide = min(max(t_swap, 0.9), shot.duration)
    shake = "shake" in shot.motion
    rng = random.Random(7)

    proc = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-pix_fmt", "yuv420p", str(dst)], stdin=subprocess.PIPE)
    try:
        for f in range(frames):
            t = f / FPS
            placed = base
            if swapped is not None and t >= t_swap:
                placed = swapped
            elif flap is not None and flap[f]:
                placed = open_layer
            offsets = {}
            for p in placed:
                dx = dy = 0
                dy += int(round(2.0 * math.sin(2 * math.pi * 0.8 * t + p["index"])))        # idle bob
                if flap is not None and flap[f] and p["index"] == 0:
                    dy -= 3                                                              # nod while talking
                if swapped is not None and p["index"] == 0 and 0 <= t - t_swap < 4 / FPS:
                    dy -= int(0.012 * H * math.sin(math.pi * (t - t_swap) * FPS / 4))     # little hop on pose change
                if glide and p["index"] == 0 and t < t_glide:
                    k = _ease_out(t / t_glide)
                    start_x = (-p["art"].width - 20) if glide == "pass-right" else (W + 20)
                    dx += int((1 - k) * (start_x - p["x"]))
                    dy -= int((1 - k) * 0.12 * H)                                         # descends as it lands
                if enter and p["index"] == 0:
                    k = _ease_out(t / 0.9)
                    start_x = (W + 20) if enter == "enter-right" else (-p["art"].width - 20)
                    dx += int((1 - k) * (start_x - p["x"]))
                    if t < 0.9:
                        dy -= int(abs(math.sin(math.pi * t / 0.3)) * 0.035 * H)            # hops
                offsets[p["index"]] = (dx, dy)
            frame = keyframes.draw(bg, placed, offsets)
            if shake:
                amp = 0.012 * W * max(0.25, 1 - t / max(shot.duration, 0.1))
                sx, sy = int(rng.uniform(-amp, amp)), int(rng.uniform(-amp, amp))
                big = frame.resize((int(W * 1.04), int(H * 1.04)))
                ox, oy = (big.width - W) // 2 + sx, (big.height - H) // 2 + sy
                frame = big.crop((ox, oy, ox + W, oy + H))
            proc.stdin.write(frame.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"local animation encode failed for {shot.id}")
    return dst


def render_card(shot: Shot, chars: dict, size: tuple[int, int], dst: Path) -> Path:
    """An END_CARD moment (card:tease / card:book frame by frame; card:title from the title video). Free and local."""
    W, H = size
    L = keyframes.card_layers(shot, chars, size)
    if shot.card == "title":
        from . import assemble, registry
        pngs = []
        for i, (layer, _, t_in) in enumerate(L):
            p = dst.with_name(f"{shot.id}_title_text{i}.png")
            layer.save(p)
            pngs.append((p, t_in))
        return assemble.title_card(registry.path_of(keyframes.TITLE_VIDEO), pngs, keyframes.TITLE_FOOTAGE,
                                   shot.duration, size, dst)
    proc = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-pix_fmt", "yuv420p", str(dst)], stdin=subprocess.PIPE)
    try:
        for f in range(max(1, round(shot.duration * FPS))):
            proc.stdin.write(keyframes.card_frame(shot, L, f / FPS).tobytes())
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"end card encode failed for {shot.id}")
    return dst
