"""Free automated QA for one generated talking clip (run right after it downloads, before the owner looks).

Compares the clip with the keyframe it was made from (the exact on-model frame we composed):
  duration vs the uploaded speech, resolution, first-frame match, mirror test (monocle side),
  beak/mouth motion while speaking (correlated with the voice), static overlay/watermark, and
  drift of the body over time. Consistency score 0-10; below 7 is flagged before the owner sees it.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from . import keyframes, media, preflight

QA_W, QA_H, QA_FPS = 360, 640, 12
MIN_SCORE = 7.0


def probe(clip: Path) -> dict:
    out = media.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                     "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(clip)])
    d = json.loads(out)
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"width": st["width"], "height": st["height"], "fps": round(float(num) / float(den), 2),
            "seconds": float(d["format"]["duration"])}


def frames(clip: Path) -> np.ndarray:
    raw = media.run_bytes(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(clip), "-vf",
                           f"fps={QA_FPS},scale={QA_W}:{QA_H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    return np.frombuffer(raw, np.uint8).reshape(-1, QA_H, QA_W, 3).astype(np.float32)


def envelope(wav: Path, n: int) -> np.ndarray:
    x, sr = preflight._read_wav(wav)
    hop = sr // QA_FPS
    env = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(x) else 0.0 for i in range(n)])
    return env / (env.max() + 1e-9)


def score(err: float) -> float:
    """Mean colour error (0-255) -> 0-10. ~4 = identical through compression; 40+ = a different picture."""
    return round(float(np.clip(10 * (1 - (err - 4) / 36), 0, 10)), 1)


def check(prod, shot, job, audio: Path | None = None) -> dict:
    """Talking clip. Action clips (Kling 3.0 start -> end frame) go to check_action."""
    if shot.kind != "talk":
        return check_action(prod, shot, job)
    clip = job.out_path
    if audio is None:
        rv = clip.parent / "voice_revoiced.wav"
        audio = rv if rv.exists() else Path(job.files["audio_url"]) if "audio_url" in job.files else None
    p = probe(clip)
    W, H = prod.size
    rows = []
    exp = float(job.extra.get("duration", job.audio_seconds))      # Wan 2.7 renders whole seconds
    rows.append(("Duration matches audio", f"~{exp:.2f}s", f"{p['seconds']:.2f}s",
                 "PASS" if abs(p["seconds"] - exp) <= 0.25 else "FAIL"))
    same_aspect = abs(p["width"] / p["height"] - W / H) < 0.01
    rows.append(("Resolution", f"{W}x{H}", f"{p['width']}x{p['height']} @ {p['fps']:g} fps",
                 "PASS" if (p["width"], p["height"]) == (W, H) else ("WARN" if same_aspect else "FAIL")))

    from .pipeline import frame_paths
    first_kf, _ = frame_paths(prod, shot)
    kf = np.asarray(Image.open(first_kf).convert("RGB").resize((QA_W, QA_H), Image.LANCZOS)).astype(np.float32)
    fr = frames(clip)
    _, placed = keyframes.layout(shot.scene, shot.cast, prod.chars, (W, H), zoom=shot.zoom)
    pl = placed[0]
    sx = QA_W / W
    alpha = np.asarray(pl["art"])[..., 3]
    mask_full = np.zeros((H, W), bool)
    x, y = pl["x"], pl["top"]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + alpha.shape[1], W), min(y + alpha.shape[0], H)
    mask_full[y0:y1, x0:x1] = alpha[y0 - y:y1 - y, x0 - x:x1 - x] > 128
    mask = np.asarray(Image.fromarray(mask_full).resize((QA_W, QA_H), Image.NEAREST))
    ys, xs = np.nonzero(mask)
    top, bot = ys.min(), ys.max()
    split = int(top + (0.45 if pl["framing"] == "closeup" else 0.30) * (bot - top))
    face = mask.copy(); face[split:] = False
    body = mask.copy(); body[:split] = False

    def err(a, b, m):
        return float(np.abs(a[m] - b[m]).mean())

    first_err = err(fr[0], kf, mask)
    first_score = score(first_err)
    rows.append(("First frame on-model", "matches keyframe", f"score {first_score}/10 (err {first_err:.1f})",
                 "PASS" if first_score >= MIN_SCORE else "FAIL"))

    flipped = kf[:, ::-1]
    fmask = mask[:, ::-1]
    mid = fr[len(fr) // 2]
    mir_ok = all(err(f, kf, mask) < 0.85 * err(f, flipped, fmask) for f in (fr[0], mid))
    rows.append(("Monocle on left eye (not mirrored)", "Yes", "same side as keyframe" if mir_ok else "looks MIRRORED",
                 "PASS" if mir_ok else "FAIL"))

    diffs = np.array([np.abs(fr[i] - fr[i - 1])[face].mean() for i in range(1, len(fr))])
    bg_diffs = np.array([np.abs(fr[i] - fr[i - 1])[~mask].mean() for i in range(1, len(fr))])
    env = envelope(audio, len(fr))[1:] if audio is not None else np.zeros(len(diffs))
    corr = float(np.corrcoef(diffs, env)[0, 1]) if len(diffs) > 3 and diffs.std() > 0 and env.std() > 0 else 0.0
    moving = diffs.mean() > max(1.5, 2 * bg_diffs.mean())
    rows.append(("Beak moves in speech", "Yes", f"face motion {diffs.mean():.1f} (background {bg_diffs.mean():.1f}), "
                 f"sync with voice r={corr:.2f}", "PASS" if moving and corr > 0.1 else ("WARN" if moving else "FAIL")))

    med = np.median(fr, axis=0)
    gx = lambda im: np.abs(np.diff(im.mean(axis=2), axis=1))[:-1, :] + np.abs(np.diff(im.mean(axis=2), axis=0))[:, :-1]
    e_med, e_kf = gx(med), gx(kf)
    ch, cw = int(QA_H * 0.10), int(QA_W * 0.35)
    corners = {"top-left": (slice(0, ch), slice(0, cw)), "top-right": (slice(0, ch), slice(-cw, None)),
               "bottom-left": (slice(-ch, None), slice(0, cw)), "bottom-right": (slice(-ch, None), slice(-cw, None))}
    extra = {k: float(np.clip(e_med[s] - e_kf[s], 0, None).mean()) for k, s in corners.items()}
    worst_corner = max(extra, key=extra.get)
    clean = extra[worst_corner] < 6
    rows.append(("No watermark", "Clean", "no static overlay in the corners" if clean else
                 f"possible overlay ({worst_corner}, {extra[worst_corner]:.1f})", "PASS" if clean else "WARN"))

    body_scores = [score(err(f, kf, body)) for f in fr[:: max(1, len(fr) // 8)]]
    face_scores = [score(err(f, kf, face)) for f in fr[:: max(1, len(fr) // 8)]]
    consistency = round(min(body_scores) * 0.6 + float(np.median(face_scores)) * 0.4, 1)
    rows.append(("No style drift", "Consistent", f"consistency {consistency}/10 (body min {min(body_scores)}, "
                 f"face median {float(np.median(face_scores))})", "PASS" if consistency >= MIN_SCORE else "FAIL"))

    verdict = "FAIL" if any(r[3] == "FAIL" for r in rows) else ("WARN" if any(r[3] == "WARN" for r in rows) else "PASS")
    report = {"shot": shot.id, "clip": str(clip), "verdict": verdict, "consistency": consistency,
              "rows": [dict(zip(("check", "expected", "actual", "result"), r)) for r in rows]}
    sheet = clip.with_name(clip.stem + "_qa.jpg")
    picks = [fr[0], fr[len(fr) // 3], fr[2 * len(fr) // 3], fr[-1]]
    canvas = Image.new("RGB", (QA_W * 5, QA_H))
    canvas.paste(Image.fromarray(kf.astype(np.uint8)), (0, 0))
    for i, f in enumerate(picks):
        canvas.paste(Image.fromarray(f.astype(np.uint8)), (QA_W * (i + 1), 0))
    canvas.save(sheet, quality=88)
    report["sheet"] = str(sheet)
    clip.with_name(clip.stem + "_qa.json").write_text(json.dumps(report, indent=2))
    return report


def check_action(prod, shot, job) -> dict:
    """Kling 3.0 action clip: duration, size, starts on the first keyframe, lands on the last keyframe,
    the character is not mirrored at the end, no watermark, real motion."""
    from .pipeline import frame_paths
    clip = job.out_path
    p = probe(clip)
    W, H = prod.size
    rows = [("Duration", f"{job.audio_seconds:g}s", f"{p['seconds']:.2f}s",
             "PASS" if abs(p["seconds"] - job.audio_seconds) <= 0.3 else "FAIL")]
    rows.append(("Resolution", f"{W}x{H}", f"{p['width']}x{p['height']} @ {p['fps']:g} fps",
                 "PASS" if (p["width"], p["height"]) == (W, H) else
                 ("WARN" if abs(p["width"] / p["height"] - W / H) < 0.01 else "FAIL")))
    fr = frames(clip)
    first, last = frame_paths(prod, shot)
    load = lambda f: np.asarray(Image.open(f).convert("RGB").resize((QA_W, QA_H), Image.LANCZOS)).astype(np.float32)
    s0 = score(float(np.abs(fr[0] - load(first)).mean()))
    rows.append(("Starts on the first keyframe", "matches", f"score {s0}/10", "PASS" if s0 >= MIN_SCORE else "FAIL"))
    consistency = s0
    if shot.end_cast and last.exists():
        lk = load(last)
        s1 = score(float(np.abs(fr[-1] - lk).mean()))
        mir = float(np.abs(fr[-1] - lk[:, ::-1]).mean())
        rows.append(("Ends on the last keyframe", "matches", f"score {s1}/10", "PASS" if s1 >= MIN_SCORE else "WARN"))
        rows.append(("Not mirrored at the end", "Yes", "same side as keyframe" if float(np.abs(fr[-1] - lk).mean()) < 0.85 * mir
                     else "looks MIRRORED", "PASS" if float(np.abs(fr[-1] - lk).mean()) < 0.85 * mir else "FAIL"))
        consistency = round(min(s0, s1), 1)
    motion = float(np.mean([np.abs(fr[i] - fr[i - 1]).mean() for i in range(1, len(fr))])) if len(fr) > 1 else 0.0
    rows.append(("Real motion", "moves", f"motion {motion:.1f} (your Kling references: 3.7-14)",
                 "PASS" if motion >= 2.0 else "WARN"))
    verdict = "FAIL" if any(r[3] == "FAIL" for r in rows) else ("WARN" if any(r[3] == "WARN" for r in rows) else "PASS")
    report = {"shot": shot.id, "clip": str(clip), "verdict": verdict, "consistency": consistency,
              "rows": [dict(zip(("check", "expected", "actual", "result"), r)) for r in rows]}
    sheet = clip.with_name(clip.stem + "_qa.jpg")
    picks = [fr[int(i * (len(fr) - 1) / 5)] for i in range(6)]
    canvas = Image.new("RGB", (QA_W * 6, QA_H))
    for i, f in enumerate(picks):
        canvas.paste(Image.fromarray(f.astype(np.uint8)), (QA_W * i, 0))
    canvas.save(sheet, quality=88)
    report["sheet"] = str(sheet)
    clip.with_name(clip.stem + "_qa.json").write_text(json.dumps(report, indent=2))
    return report
