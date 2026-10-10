"""Free pre-flight checks that run before ANY paid talking-shot request (and in every free run).

Keyframe: exists, exact size, not mirrored (pixel test against the canonical cut-out), facing, monocle,
hat tilt, subject size, 4:5 safe area, real background, lip-sync suitability of the pose.
Audio: exists, right speaker, final voice, silence trimmed to <= 0.2 s each end, clipping, noise floor,
loudness; then a trimmed copy normalised to -16 LUFS is written for upload (the billed seconds).
Any FAIL is a hard stop for that shot. WARN = allowed, but shown to the owner before approval.
"""
from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from . import assemble, keyframes, media

SAFE_TOP, SAFE_BOTTOM = 0.148, 0.852        # 4:5 crop of a 9:16 frame (middle 70% of the height)
EDGE = 8                                    # px clearance from the frame sides
BILLY_FILL = (0.60, 0.70)                   # owner rule: Billy's body fills 60-70% of the frame height
MAX_EDGE_SILENCE = 0.20                     # owner rule: <= 0.2 s silence at either end
KEEP_EDGE = 0.05                            # silence kept at each end after trimming
SILENCE_DB = -45.0
TARGET_LUFS = -16.0
MAX_TILT = 10.0                             # degrees
# Lip-sync suitability by what the art shows (front = best, 3/4 = good, profile/looking down = risky).
RISKY_ART = {"billy_tophat_scroll_reading": "looking down at the scroll; beak partly side-on",
             "billy_tophat_sideleft": "side profile", "billy_tophat_sideright": "side profile"}


@dataclass
class Check:
    name: str
    status: str            # PASS | WARN | FAIL
    detail: str = ""


def worst(checks: list[Check]) -> str:
    order = {"PASS": 0, "WARN": 1, "FAIL": 2}
    return max((c.status for c in checks), key=order.get, default="PASS")


# ---------------------------------------------------------------- keyframes

def _variant(char: dict, variant: str | None) -> dict:
    return char["variants"].get(variant or char.get("default_variant"), {})


def facing_of(char: dict, on) -> str:
    v = _variant(char, on.variant)
    name = next((n for g in ("expressions", "poses") for n, a in v.get(g, {}).items() if a == on.art), None)
    return v.get("facing", {}).get(name, "front")


def _region(kf: np.ndarray, p: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    """Keyframe pixels, art pixels and art alpha where the cut-out was placed (clipped to the frame)."""
    H, W = kf.shape[:2]
    art = np.asarray(p["art"]).astype(np.float32)
    x, y = p["x"], p["top"]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + art.shape[1], W), min(y + art.shape[0], H)
    a = art[y0 - y:y1 - y, x0 - x:x1 - x]
    return kf[y0:y1, x0:x1].astype(np.float32), a[..., :3], a[..., 3] / 255.0, (x0, y0, x1, y1)


def mirror_score(kf: np.ndarray, p: dict) -> tuple[float, float]:
    """(error vs the canonical art, error vs the mirrored art) over the character's pixels.
    A correctly composed frame matches the canonical art far better than its mirror image."""
    region, rgb, alpha, _ = _region(kf, p)
    full = np.asarray(p["art"]).astype(np.float32)
    flipped = full[:, ::-1]
    _, frgb, falpha, _ = _region(kf, {**p, "art": Image.fromarray(flipped.astype(np.uint8))})
    m = alpha > 0.9
    fm = falpha > 0.9
    true_err = float(np.abs(region[m] - rgb[m]).mean()) if m.any() else 999.0
    flip_err = float(np.abs(region[fm] - frgb[fm]).mean()) if fm.any() else 999.0
    return true_err, flip_err


def hat_tilt(kf: np.ndarray, p: dict) -> float | None:
    """Degrees the top hat leans from vertical: centre of its crown vs centre just above the brim."""
    region, _, alpha, _ = _region(kf, p)
    lum = region.mean(axis=2)
    dark = (alpha > 0.5) & (lum < 45)
    rows = np.nonzero(dark.sum(axis=1) > 3)[0]
    if len(rows) < 20:
        return None
    top = rows[0]
    # the hat is the first tall dark run from the top of the art
    run_end = top
    for r in rows:
        if r - run_end > 3:
            break
        run_end = r
    hh = run_end - top
    if hh < 20:
        return None
    def cx(r0, r1):
        ys, xs = np.nonzero(dark[r0:r1])
        return xs.mean() if len(xs) else None
    a, b = cx(top, top + int(hh * 0.15)), cx(top + int(hh * 0.55), top + int(hh * 0.75))
    if a is None or b is None:
        return None
    return math.degrees(math.atan2(a - b, hh * 0.55))


def keyframe_checks(prod, shot, frame: Path | None = None, cast: list | None = None) -> list[Check]:
    """Checks one composed frame (default: the shot's first frame with its cast)."""
    from .pipeline import frame_paths
    first = frame or frame_paths(prod, shot)[0]
    if cast is None:                                   # the first frame is drawn from start_cast when there is one
        cast = shot.start_cast if shot.start_cast else shot.cast
    out: list[Check] = []
    if not first.exists():
        return [Check("file exists", "FAIL", f"{first.name} missing - run `bbtb make` (free) first")]
    out.append(Check("file exists", "PASS", first.name))
    img = Image.open(first).convert("RGB")
    W, H = prod.size
    out.append(Check("resolution", "PASS" if img.size == (W, H) else "FAIL", f"{img.size[0]}x{img.size[1]}"))
    for o in cast or []:                               # Jason 2026-10-06: mandatory red-background white test
        from . import cutout
        r = cutout.red_test(o.art)
        out.append(Check("red test (white)", "PASS" if r["ok"] else "FAIL",
                         f"{o.art}: no white on red ({r['kept']} approved white details)" if r["ok"] else
                         f"{o.art}: {len(r['undecided'])} undecided white patch(es) at {r['undecided'][:3]}, edge white "
                         f"{r['edge_white']}px - review with `bbtb cutouts --review {o.art}`"))
    if img.size != (W, H) or not cast:
        return out
    kf = np.asarray(img)
    on = cast[0]
    char = prod.chars[on.char]
    bg_plate, placed = keyframes.layout(shot.scene, cast, prod.chars, (W, H), zoom=shot.zoom,
                                        place=shot.place_end if cast is shot.end_cast else shot.place)
    from . import grounding                       # owner 2026-10-06: feet on the flat walkable ground, or FAIL
    for idx, status, detail in grounding.check(shot.scene, placed, bg_plate):
        name = prod.chars[cast[idx].char]["display_name"]
        out.append(Check("grounding", status, f"{name}: {detail}"))
    p = placed[0]

    te, fe = mirror_score(kf, p)
    not_mirrored = (not on.mirror) and te < 25 and te < 0.7 * fe
    if not char.get("mirror_ok", True):
        out.append(Check("not mirrored", "PASS" if not_mirrored else "FAIL",
                         f"matches canonical art (err {te:.1f}) vs mirror (err {fe:.1f})"))
    else:
        out.append(Check("not mirrored", "PASS", "mirroring allowed for this character; frame matches its art"
                         if te < 25 else f"frame differs from art (err {te:.1f})"))
    face = facing_of(char, on)
    out.append(Check("facing", "PASS", f"{face} (as drawn on the model sheet; never flipped)"))
    if on.char == "bad_billy":
        out.append(Check("monocle on LEFT eye", "PASS" if not_mirrored else "FAIL",
                         "canonical sheet art, unmirrored" if not_mirrored else "frame looks mirrored"))
        tilt = hat_tilt(kf, p)
        if tilt is None:
            out.append(Check("hat upright", "WARN", "could not measure"))
        else:
            out.append(Check("hat upright", "PASS" if abs(tilt) <= MAX_TILT else "WARN",
                             f"{tilt:+.0f} deg" + ("" if abs(tilt) <= MAX_TILT else " (tilted in the original art; can't be changed without redrawing)")))

    region, _, alpha, (x0, y0, x1, y1) = _region(kf, p)
    ys, xs = np.nonzero(alpha > 0.5)
    top, bottom = y0 + ys.min(), y0 + ys.max()
    left, right = x0 + xs.min(), x0 + xs.max()
    visible = (bottom - top + 1) / H
    if p["framing"] == "closeup":
        out.append(Check("subject size", "PASS", f"close-up bust: head-to-knees fills {visible:.0%} of the height "
                         f"(the 60-70% rule is for full-body shots)"))
    elif p.get("zoomed"):
        out.append(Check("subject size", "PASS", f"camera push-in x{shot.zoom:g}: {visible:.0%} of the height visible "
                         f"(the 60-70% rule is for full-body medium shots)"))
    elif p["framing"] == "far":
        out.append(Check("subject size", "PASS", f"far shot: fills {visible:.0%} (a small figure in a big world)"))
    elif on.char == "bad_billy" and p["framing"] == "wide":
        out.append(Check("subject size", "PASS", f"wide shot: Billy fills {visible:.0%} (the 60-70% rule is for medium shots)"))
    elif on.char == "bad_billy":
        ok = BILLY_FILL[0] - 0.005 <= visible <= BILLY_FILL[1] + 0.005
        out.append(Check("subject size", "PASS" if ok else "FAIL", f"Billy fills {visible:.0%} of the height (rule 60-70%)"))
    else:
        out.append(Check("subject size", "PASS", f"fills {visible:.0%} of the height (small character; 60-70% rule is Billy's)"))

    face_only = p["framing"] == "closeup" or p.get("zoomed")
    head_bottom = top + 0.45 * (bottom - top) if face_only else bottom
    inside = (top >= SAFE_TOP * H and head_bottom <= SAFE_BOTTOM * H
              and (face_only or (left >= EDGE and right <= W - EDGE)))
    what = "hat and face" if face_only else "whole character"
    out.append(Check("inside 4:5 safe area", "PASS" if inside else "FAIL",
                     f"{what}: y {top / H:.2f}-{head_bottom / H:.2f} (safe {SAFE_TOP:.2f}-{SAFE_BOTTOM:.2f}), "
                     f"x {left}-{right} of {W}"))

    mask = np.zeros(kf.shape[:2], bool)
    mask[y0:y1, x0:x1] = alpha > 0.1
    bg = kf[~mask].astype(np.float32)
    plain = bg.std() < 12 or bg.mean() > 235
    out.append(Check("real background", "FAIL" if plain else "PASS",
                     f"scene {shot.scene} (pixel spread {bg.std():.0f})"))

    if shot.kind != "talk":
        return out
    v = _variant(char, on.variant)
    open_heads = set(v.get("open_mouth", []))
    name = next((n for g in ("expressions", "poses") for n, a in v.get(g, {}).items() if a == on.art), on.art)
    if on.art in RISKY_ART:
        out.append(Check("lip-sync pose", "WARN", f"{name}: {RISKY_ART[on.art]}"))
    elif name in open_heads:
        out.append(Check("lip-sync pose", "WARN", f"{name}: beak already wide open in the start frame; "
                         f"the model may not be able to close it"))
    else:
        grade = "best (front)" if face == "front" else "good (3/4 view)"
        out.append(Check("lip-sync pose", "PASS", f"{name}: {grade}"))
    return out


# ---------------------------------------------------------------- audio

def _read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float32)
    x /= float(2 ** (8 * sw - 1))
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def audio_stats(path: Path) -> dict:
    tmp = path.parent / f".{path.stem}.stats.wav"
    media.to_wav(path, tmp)                        # analysis copy only (48 kHz mono)
    x, sr = _read_wav(tmp)
    tmp.unlink(missing_ok=True)
    hop = int(sr * 0.01)
    frames = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    loud = np.nonzero(db > SILENCE_DB)[0]
    dur = len(x) / sr
    lead = loud[0] * 0.01 if len(loud) else dur
    tail = dur - (loud[-1] + 1) * 0.01 if len(loud) else 0.0
    quiet = np.sort(db)[: max(1, len(db) // 10)]
    return {"seconds": round(dur, 3), "lead_silence": round(lead, 3), "tail_silence": round(max(tail, 0.0), 3),
            "peak_db": round(20 * math.log10(np.abs(x).max() + 1e-9), 1),
            "clipped": int((np.abs(x) >= 0.999).sum()), "noise_floor_db": round(float(quiet.mean()), 1)}


def prepare_audio(src: Path, dst: Path, keep_lead: bool = False) -> dict:
    """Trimmed (KEEP_EDGE s each end) and -16 LUFS copy for upload. Returns stats incl. head_trim.
    keep_lead: the leading silence is part of the timing (an Avatar driver track) and is kept."""
    st = audio_stats(src)
    head = 0.0 if keep_lead else max(st["lead_silence"] - KEEP_EDGE, 0.0)
    keep = st["seconds"] - head - max(st["tail_silence"] - KEEP_EDGE, 0.0)
    dst.parent.mkdir(parents=True, exist_ok=True)
    cut = dst.with_suffix(".cut.wav")
    media.ffmpeg("-i", str(src), "-ss", f"{head:.3f}", "-t", f"{keep:.3f}", "-ac", "1", "-ar", "48000",
                 "-c:a", "pcm_s16le", str(cut))
    assemble.normalize(cut, dst, target=TARGET_LUFS, peak_db=-1.5)
    cut.unlink(missing_ok=True)
    out = audio_stats(dst)
    return {"source": st, "prepared": out, "head_trim": round(head, 3),
            "lufs": media.loudness(dst)["lufs"]}


def audio_checks(prod, shot, prepared: dict | None) -> list[Check]:
    out: list[Check] = []
    if not shot.lines:
        return [Check("line audio", "FAIL", "talking shot without a line")]
    drv = (prepared or {}).get("driver") or {}
    lid = drv.get("line") or shot.lines[0]
    e = prod.lines.get(lid) or {}
    path = Path(e.get("path", ""))
    if not path.exists():
        return [Check("file exists", "FAIL", f"{lid}: no audio file")]
    out.append(Check("file exists", "PASS", path.name))
    speaker_ok = shot.cast and e.get("speaker") == shot.cast[0].char
    out.append(Check("speaker", "PASS" if speaker_ok else "FAIL",
                     f"{e.get('speaker')} line, {shot.cast[0].char if shot.cast else 'nobody'} on screen"))
    out.append(Check("final voice", "PASS" if e.get("final") else "FAIL",
                     {"original": "original book recording", "elevenlabs": "approved ElevenLabs clone"}.get(
                         e.get("source"), e.get("source", "?"))))
    if prepared is None:
        return out
    s, p = prepared["source"], prepared["prepared"]
    if drv:
        out.append(Check("driver timing", "PASS", f"{p['lead_silence']:.2f}s silence, then {lid} (starts at {drv['start']:g}s "
                                                    f"in the shot); the narrator is NOT fed to Avatar"))
    else:
        out.append(Check("silence trimmed", "PASS" if max(p["lead_silence"], p["tail_silence"]) <= MAX_EDGE_SILENCE else "FAIL",
                         f"was {s['lead_silence']:.2f}s / {s['tail_silence']:.2f}s, now {p['lead_silence']:.2f}s / {p['tail_silence']:.2f}s"))
    out.append(Check("no clipping", "PASS" if s["clipped"] < 3 else "WARN",
                     f"source peak {s['peak_db']} dBFS, {s['clipped']} clipped samples"))
    out.append(Check("low noise", "PASS" if s["noise_floor_db"] < -50 else "WARN", f"floor {s['noise_floor_db']} dBFS"))
    lufs = prepared["lufs"]
    out.append(Check("loudness -16 LUFS", "PASS" if lufs is not None and abs(lufs - TARGET_LUFS) <= 1.0 else "WARN",
                     f"{lufs} LUFS (upload copy only; the final mix is normalised separately)"))
    return out
