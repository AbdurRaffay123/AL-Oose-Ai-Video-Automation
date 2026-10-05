"""Automated checks on a finished export. Writes productions/<ep>/reviews/qa.md."""
from __future__ import annotations

import re
import time
from pathlib import Path

from PIL import Image

from . import media


def black_segments(video: Path) -> list[tuple[float, float]]:
    out = media.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "blackdetect=d=0.4:pix_th=0.08",
                     "-an", "-f", "null", "-"])
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", out)]


def contact_sheet(prod, video: Path, dst: Path) -> Path:
    """One frame from the middle of every shot, for a 10-second visual check."""
    t0, frames = 0.0, []
    tmp = prod.root / "_work" / "qa_frames"
    tmp.mkdir(parents=True, exist_ok=True)
    for s in prod.shots:
        f = tmp / f"{s.id}.jpg"
        media.ffmpeg("-ss", f"{t0 + s.duration / 2:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(f))
        frames.append(Image.open(f).convert("RGB"))
        t0 += s.duration
    w, h = 240, int(240 * frames[0].height / frames[0].width)
    cols = 6
    sheet = Image.new("RGB", (cols * w, ((len(frames) + cols - 1) // cols) * h), (0, 0, 0))
    for i, fr in enumerate(frames):
        sheet.paste(fr.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    sheet.save(dst, quality=88)
    return dst


def check(prod, video: Path, failures: list[str]) -> dict:
    fails, warns, passes = [], [], []
    dur = media.duration(video)
    (passes if abs(dur - prod.total) < 0.5 else fails).append(f"duration {dur:.1f}s (planned {prod.total:.1f}s)")
    loud = media.loudness(video)
    if loud["lufs"] is not None and -17.5 <= loud["lufs"] <= -14.5 and (loud["true_peak"] or 0) <= -1.0:
        passes.append(f"loudness {loud['lufs']} LUFS, true peak {loud['true_peak']} dBTP")
    else:
        fails.append(f"loudness {loud['lufs']} LUFS / {loud['true_peak']} dBTP (target -16 LUFS, <= -1 dBTP)")
    blacks = black_segments(video)
    (fails if blacks else passes).append(f"black frames: {blacks or 'none'}")
    not_final = [f"{k} ({v['source']})" for k, v in prod.lines.items() if not v.get("final")]
    if not_final:
        fails.append(f"{len(not_final)} line(s) use a voice that is not final (placeholder or unapproved clone): "
                     + ", ".join(not_final))
    else:
        passes.append("all lines use original recordings or owner-approved cloned voices")
    still = [s.id for s in prod.shots if (s.engine.startswith("ltx")
             and not (prod.root / "shots" / s.id / "ltx.mp4").exists())
             or (s.engine == "kling_avatar" and not any((prod.root / "shots" / s.id / n).exists()
                                                        for n in ("kling_avatar.mp4", "kling.mp4", "kling_test.mp4")))
             or (s.engine.startswith("kling3") and not (prod.root / "shots" / s.id / "kling3.mp4").exists())
             or (s.engine == "wan_talk" and not (prod.root / "shots" / s.id / "wan.mp4").exists())]
    if still:
        warns.append(f"shots shown as storyboard stills / local animation because no generated clip exists: {', '.join(still)}")
    for f in failures:
        warns.append(f"generation problem - {f}")
    if not any(fx for s in prod.shots for fx in s.sfx) and not prod.script.meta.get("music"):
        warns.append("no music or SFX requested")
    verdict = "FAIL" if fails else ("PASS with warnings" if warns else "PASS")

    reviews = prod.root / "reviews"
    reviews.mkdir(exist_ok=True)
    sheet = contact_sheet(prod, video, reviews / "frames.jpg")
    md = [f"# QA: {video.name}", f"{time.strftime('%Y-%m-%d %H:%M')} - **{verdict}**", ""]
    md += [f"- FAIL: {x}" for x in fails] + [f"- WARN: {x}" for x in warns] + [f"- ok: {x}" for x in passes]
    md += ["", f"Frame check (one frame per shot): `{sheet.name}`",
           "", "Human check before posting: characters on-model in every shot, mouths move on the "
           "speaker only, no warping/morphing, no text artifacts, voices sound right."]
    path = reviews / "qa.md"
    path.write_text("\n".join(md) + "\n")
    return {"verdict": verdict, "path": str(path), "fails": fails, "warns": warns}
