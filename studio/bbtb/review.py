"""Owner frame review (owner 2026-10-06: "no video approved without visual verification first").

After a clip is generated, a contact sheet of every 0.5 s is written to productions/<ep>/reviews/<shot>_frames.jpg.
The final video is only assembled from generated clips the owner has approved for exactly that take:
  ./bbtb review <script>              sheets + approval status of every generated clip
  ./bbtb approve-clip <script> S01,S04  records the owner's approval (productions/<ep>/clip_approvals.yaml)
`--auto-approve` (make/export) skips the gate: for tests only.
"""
from __future__ import annotations

import datetime
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

STEP = 0.5


def sheet(clip: Path, dst: Path, title: str = "") -> Path:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(clip)], capture_output=True, text=True).stdout)
    n = max(1, int(dur / STEP + 1e-6))
    tiles = []
    for k in range(n):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{k * STEP + 0.02:.2f}", "-i", str(clip), "-frames:v", "1",
                              "-vf", "scale=180:320", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True).stdout
        if len(raw) == 180 * 320 * 3:
            tiles.append(Image.frombytes("RGB", (180, 320), raw))
    cols = min(8, max(1, len(tiles)))
    rows = -(-len(tiles) // cols)
    g = Image.new("RGB", (cols * 184, rows * 340 + 24), "white")
    d = ImageDraw.Draw(g)
    d.text((4, 4), f"{title}  {clip.name}  {dur:.2f}s  (every {STEP}s)", fill=(0, 0, 0))
    for i, t in enumerate(tiles):
        x, y = (i % cols) * 184, 24 + (i // cols) * 340
        g.paste(t, (x, y + 16))
        d.text((x + 2, y + 2), f"{i * STEP:.1f}s", fill=(200, 0, 0))
    dst.parent.mkdir(parents=True, exist_ok=True)
    g.save(dst, quality=88)
    return dst


def _file(prod_root: Path) -> Path:
    return Path(prod_root) / "clip_approvals.yaml"


def approvals(prod_root: Path) -> dict:
    p = _file(prod_root)
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


def approve(prod_root: Path, shot: str, request_hash: str, note: str = "") -> None:
    data = approvals(prod_root)
    data[shot] = {"request_hash": request_hash, "approved": datetime.date.today().isoformat(), "note": note}
    _file(prod_root).write_text("# Owner-approved generated clips (`bbtb approve-clip`). A new take needs a new approval.\n"
                                + yaml.safe_dump(data, sort_keys=True))


def approved(prod_root: Path, shot: str, request_hash: str) -> bool:
    return approvals(prod_root).get(shot, {}).get("request_hash") == request_hash
