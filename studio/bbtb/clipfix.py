"""Free clip fixes applied at render time (owner 2026-10-06), recorded in productions/<ep>/clip_fixes.yaml.

`trapped_white`: a clip made from a keyframe whose cut-out still had sheet-white trapped inside a closed shape (Billy's
moustache curls, before the red-background test existed) shows that white in every frame. Instead of paying for a
retake (which changes the performance), the white is replaced by the shot's own background plate:
  - near-white patches inside `box` whose centre is below `below_y` (under the chin; eyes are always above it), or that
    are mostly ringed by the teal moustache, are filled from the plate;
  - a soft light fringe around them is blended away; teal (the curl itself) is never touched;
  - `keep_collar: true` (owner 2026-10-08, EP001 S06; off by default) never fills Billy's white shirt collar;
  - `keep_scroll: true` (owner 2026-10-08, EP001 S05; off by default) never fills or blends the scroll's cream paper.
Only background pixels change. The original paid clip is never modified (a fixed copy goes to _work/).

`hold_frames: [[a, b], ...]` (owner 2026-10-06: "no squinting Saul eyes anywhere"): frames a..b (inclusive, clip frame
numbers) are replaced by frame a-1, i.e. the last good frame is held over a blink or squint.

`feather_white: {box}` (owner 2026-10-08): thin sheet-white slivers between Billy's wing feathers, filled from the plate
(sliver_white_frame). Removed from every EP001 shot (2026-10-09): it hit wing-vest and beak highlights.
`under_white: {box}` (owner 2026-10-10, EP001 S03): the thin sheet-white strip between Young Saul's body outline and
the grass, filled with the grass just below it (under_white_frame). Off unless a shot's YAML sets it.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageFilter

from .cutout import _components


def spec(prod_root: Path) -> dict:
    p = Path(prod_root) / "clip_fixes.yaml"
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


def _grow(m: np.ndarray, k: int) -> np.ndarray:
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k))) > 0


def _flanked(m: np.ndarray, reach: int) -> np.ndarray:
    """True where `m` occurs within `reach` px to the LEFT and within `reach` px to the RIGHT on the same row."""
    left, right = np.zeros_like(m), np.zeros_like(m)
    for d in range(1, reach + 1):
        left[:, d:] |= m[:, :-d]
        right[:, :-d] |= m[:, d:]
    return left & right


def collar_mask(a: np.ndarray, white: np.ndarray, reach: int = 25, near: int = 18, min_px: int = 25):
    """Billy's white shirt collar (owner 2026-10-08, EP001 S06): white within `near` px of the red-orange tie AND
    flanked by the dark-red vest or the tie on both sides of the row (the two collar points inside the vest's V).
    Pieces under `min_px` are specks, not the collar. Returns (collar, vest, tie)."""
    tie = (a[..., 0] > 170) & (a[..., 1] >= 45) & (a[..., 1] <= 80) & (a[..., 2] < 45) & (a[..., 0] - a[..., 1] > 110)
    vest = (a[..., 0] > 40) & (a[..., 0] <= 170) & (a[..., 1] < 60) & (a[..., 2] < 60) & (a[..., 0] - a[..., 1] > 30)
    seed = white & _grow(tie, 2 * near + 1) & _flanked(vest | tie, reach)
    collar = np.zeros_like(white)
    for c in _components(seed):
        if c.sum() >= min_px:
            collar |= c
    return _grow(collar, 3) & white, vest, tie


def paper_mask(a: np.ndarray, mn: np.ndarray, mx: np.ndarray, min_px: int = 2000) -> np.ndarray:
    """The scroll's cream paper (owner 2026-10-08, EP001 S05): light, warm (R-B 20..110), less white than sheet white,
    not Billy's yellow; only big connected areas (the sheet), never the thin cream blend along a white patch's edge."""
    raw = (a[..., 1] > 150) & (a[..., 0] - a[..., 2] >= 20) & (a[..., 0] - a[..., 2] <= 110) & (mn > 110) \
        & (mx - mn > 25) & ~((a[..., 0] > 180) & (a[..., 1] > 140) & (a[..., 2] < 110))
    paper = np.zeros_like(raw)
    for c in _components(raw):
        if c.sum() >= min_px:
            paper |= c
    return paper


def trapped_white_frame(fr: np.ndarray, plate: np.ndarray, box, below_y: int,
                        keep_collar: bool = False, keep_scroll: bool = False) -> tuple[np.ndarray, int]:
    """One RGB frame -> (fixed frame, pixels replaced). `keep_collar` (off by default; EP003 unchanged) never fills
    Billy's white shirt collar, even where the trapped white touches it. `keep_scroll` (off by default) never fills
    or blends the scroll's cream paper."""
    a = fr.astype(int)
    mn, mx = a.min(2), a.max(2)
    white = (mn >= 200) & ((mx - mn) <= 45)
    region = np.zeros_like(white)
    x0, y0, x1, y1 = box
    region[y0:y1, x0:x1] = True
    teal = (a[..., 2] > 110) & (a[..., 1] > 100) & (a[..., 0] < 130) & (a[..., 2] - a[..., 0] > 50)
    yellow = (a[..., 0] > 190) & (a[..., 1] > 150) & (a[..., 2] < 120)
    kill = np.zeros_like(white)
    for c in _components(white & region):
        if c.sum() < 6:
            continue
        ys, _ = np.nonzero(c)
        ring = _grow(c, 7) & ~c
        if ys.mean() >= below_y or (ring.sum() and teal[ring].mean() >= 0.30):
            kill |= c
    keep = np.zeros_like(white)
    if keep_collar:
        collar, vest, tie = collar_mask(a, white)
        kill &= ~collar
        keep = collar | vest | tie
    if keep_scroll:
        paper = paper_mask(a, mn, mx)
        kill &= ~paper
        keep |= paper
    if not kill.any():
        return fr, 0
    fringe = _grow(kill, 7) & ~kill & (mn >= 110) & ~teal & ~yellow & ((mx - mn) <= 80) & ~keep
    hard = kill | fringe
    alpha = np.asarray(Image.fromarray((hard * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))) / 255.0
    alpha = np.maximum(alpha, hard) * ~teal * ~(keep & white)
    if keep_scroll:                                   # as tested on S05: no blending into any kept pixel
        alpha = alpha * ~keep
    alpha = alpha[..., None]
    out = fr.astype(np.float32) * (1 - alpha) + plate.astype(np.float32) * alpha
    return out.clip(0, 255).astype(np.uint8), int(hard.sum())


RINGS = {   # the character colour a sliver must sit inside (EP001: Billy's yellow feathers, Saul's pink body)
    "yellow": lambda a: (a[..., 0] > 180) & (a[..., 1] > 140) & (a[..., 2] < 120),
    "pink": lambda a: (a[..., 0] > 200) & (a[..., 1] > 120) & (a[..., 1] < 215) & (a[..., 2] > 170)
                      & (a[..., 0] - a[..., 1] > 25),
}


def sliver_white_frame(fr: np.ndarray, plate: np.ndarray, box, ring: str = "yellow", min_light: int = 170,
                       max_px: int = 500) -> tuple[np.ndarray, int]:
    """`feather_white` / `outline_white` (owner 2026-10-08, Jason's batch-1 notes): thin light slivers of sheet
    white left between Billy's wing feathers (ring: yellow) or along Saul's body outline (ring: pink) by a cut-out
    made before the red-background test. Inside `box`, a light, thin component (never a solid blob: gloves, eyes,
    sneaker toes and the scroll are blobs) that is mostly surrounded by the character colour or its dark outline is
    replaced by the shot's own plate. The character colour itself is never touched."""
    a = fr.astype(int)
    mn, mx = a.min(2), a.max(2)
    light = (mn >= min_light) & ((mx - mn) <= 60)
    region = np.zeros_like(light)
    x0, y0, x1, y1 = box
    region[y0:y1, x0:x1] = True
    ref = RINGS[ring](a)
    dark = mx < 70
    kill = np.zeros_like(light)
    for c in _components(light & region):
        n = int(c.sum())
        if n < 3 or n > max_px:
            continue
        ys, xs = np.nonzero(c)
        w, h = np.ptp(xs) + 1, np.ptp(ys) + 1
        if n / (w * h) > 0.6 and min(w, h) > 6:          # a solid blob, not a sliver
            continue
        rim = _grow(c, 5) & ~c
        if rim.sum() and (ref[rim] | dark[rim]).mean() >= 0.5 and ref[rim].mean() >= 0.2:
            kill |= c
    if not kill.any():
        return fr, 0
    hard = (_grow(kill, 3) & ~ref & ~dark) | kill        # one pixel of light fringe, never the feather/body or outline
    alpha = np.asarray(Image.fromarray((hard * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))) / 255.0
    alpha = (np.maximum(alpha, hard) * ~ref)[..., None]
    out = fr.astype(np.float32) * (1 - alpha) + plate.astype(np.float32) * alpha
    return out.clip(0, 255).astype(np.uint8), int(hard.sum())


def pink_mask(a: np.ndarray) -> np.ndarray:
    """Young Saul's pink body (EP001 S03 frames)."""
    return (a[..., 0] > 190) & (a[..., 1] > 110) & (a[..., 1] < 215) & (a[..., 2] > 150) & (a[..., 0] - a[..., 1] > 20)


def under_white_frame(fr: np.ndarray, plate: np.ndarray, box, max_thick: float = 4.5, min_px: int = 8,
                      reach: int = 10, up: int = 8) -> tuple[np.ndarray, int]:
    """`under_white: {box}` (owner 2026-10-10, Jason's batch-1 note 5B, EP001 S03): the thin strip of sheet white left
    between Young Saul's body outline and the grass. Inside `box`, a thin neutral-white component (never his pink, never
    a blob: gloves, teeth, eyes) with his body or dark outline within `up` px ABOVE it and grass right BELOW it is
    replaced, pixel by pixel, by the nearest grass pixel below it in the same column (so the ground shading matches)."""
    a = fr.astype(int); p = plate.astype(int)
    mn, mx = a.min(2), a.max(2)
    light = (mn >= 170) & ((mx - mn) <= 60) & (a[..., 0] - a[..., 1] <= 20)
    plate_light = (p.min(2) >= 185) & ((p.max(2) - p.min(2)) <= 60)
    region = np.zeros_like(light)
    x0, y0, x1, y1 = box
    region[y0:y1, x0:x1] = True
    body = pink_mask(a) | (mx < 140)
    grass = (a[..., 1] > a[..., 0]) & (a[..., 1] - a[..., 2] > 50)
    kill = np.zeros_like(light)
    for c in _components(light & region & ~plate_light):
        if int(c.sum()) < min_px:
            continue
        ys, xs = np.nonzero(c)
        if c.sum() / (max(np.ptp(xs), np.ptp(ys)) + 1) > max_thick:   # a blob, not a thin strip
            continue
        above = np.array([body[max(y - up, 0):y, x].any() for y, x in zip(ys, xs)])
        below = np.array([grass[y + 1:y + 4, x].any() for y, x in zip(ys, xs)])
        if above.mean() >= 0.25 and below.mean() >= 0.3:
            kill |= c
    if not kill.any():
        return fr, 0
    hard = kill | (_grow(kill, 3) & ~body & ~grass & (mn >= 140))      # the strip's soft light edge
    out = fr.copy()
    for y, x in zip(*np.nonzero(hard)):
        for d in range(1, reach + 1):
            yy = y + d
            if yy < fr.shape[0] and grass[yy, x] and not hard[yy, x]:
                out[y, x] = fr[yy, x]
                break
        else:
            out[y, x] = plate[y, x]
    return out, int(hard.sum())


def tint_eyes(frames: np.ndarray, t: dict) -> None:
    """`tint_eyes: [{frames: [a, b], box: [x0, y0, x1, y1], color: [r, g, b]}]` (owner 2026-10-06): Kling turns the
    Snail's pale-green eyes white whenever they get big; near-white pixels inside `box` are tinted back to his official
    eye colour (shading kept). Frames a..b inclusive."""
    a, b = t["frames"]
    x0, y0, x1, y1 = t["box"]
    col = np.array(t["color"], float)
    for i in range(a, min(b, len(frames) - 1) + 1):
        reg = frames[i, y0:y1, x0:x1].astype(float)
        m = (reg.min(axis=2) > t.get("min_white", 215)).astype(np.uint8) * 255
        alpha = np.asarray(Image.fromarray(m).filter(ImageFilter.GaussianBlur(1.2))).astype(float)[..., None] / 255
        lum = reg.mean(axis=2, keepdims=True) / 255
        frames[i, y0:y1, x0:x1] = (reg * (1 - alpha) + col * lum * alpha).clip(0, 255).astype(np.uint8)


def edit_frames(frames: np.ndarray, segs: list, fps: int) -> list:
    """`edit: [{from, to, speed, zoom, hold, center: [x, y]}]` (owner 2026-10-06): cut a reaction clip into on-the-beat
    punch-ins that use only its clean moments. Seconds of the source clip; speed < 1 = slower (frames repeated);
    zoom > 1 = closer, around `center`; hold = extra copies of the segment's last frame."""
    H, W = frames.shape[1:3]
    out = []
    for g in segs:
        a, b = round(g["from"] * fps), round(g["to"] * fps)
        src = frames[a:b]
        n = max(1, round(len(src) / g.get("speed", 1.0)))
        picked = [src[min(len(src) - 1, int(k * len(src) / n))] for k in range(n)]
        picked += [picked[-1]] * int(g.get("hold", 0))
        z = float(g.get("zoom", 1.0))
        cx, cy = g.get("center", [W / 2, H / 2])
        for fr in picked:
            if z > 1.001:
                cw, ch = W / z, H / z
                x0 = min(max(cx - cw / 2, 0), W - cw)
                y0 = min(max(cy - ch / 2, 0), H - ch)
                fr = np.asarray(Image.fromarray(fr).crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))
                                .resize((W, H), Image.LANCZOS))
            out.append(fr)
    return out


def edit_seconds(segs: list, fps: int = 24) -> float:
    n = 0
    for g in segs:
        k = round(g["to"] * fps) - round(g["from"] * fps)
        n += max(1, round(k / g.get("speed", 1.0))) + int(g.get("hold", 0))
    return round(n / fps, 3)


def apply(clip: Path, plate: Image.Image, fixes: dict, dst: Path, fps: int | None = None) -> Path:
    """Write a fixed copy of `clip` (video only) to `dst`. `fixes`: {trapped_white: {...}, hold_frames: [[a, b], ...]}."""
    W, H = plate.size
    if fps is None:
        rate = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                               "-of", "csv=p=0", str(clip)], capture_output=True, text=True).stdout.strip()
        n, d = (rate.split("/") + ["1"])[:2]
        fps = round(float(n) / float(d))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).copy()
    for a, b in fixes.get("hold_frames") or []:
        frames[a:b + 1] = frames[max(a - 1, 0)]
    for t in fixes.get("tint_eyes") or []:
        tint_eyes(frames, t)
    if fixes.get("edit"):
        frames = np.stack(edit_frames(frames, fixes["edit"], fps))
    fix = fixes.get("trapped_white")
    slivers = [(fixes["feather_white"], "yellow")] if fixes.get("feather_white") else []
    under = fixes.get("under_white")
    pl = np.asarray(plate.convert("RGB"))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(dst)],
                         stdin=subprocess.PIPE)
    for fr in frames:
        fixed = trapped_white_frame(fr, pl, fix["box"], fix["below_y"], fix.get("keep_collar", False),
                                    fix.get("keep_scroll", False))[0] if fix else fr
        for rule, ring in slivers:
            fixed = sliver_white_frame(fixed, pl, rule["box"], rule.get("ring", ring))[0]
        if under:
            fixed = under_white_frame(fixed, pl, under["box"])[0]
        p.stdin.write(fixed.tobytes())
    p.stdin.close()
    p.wait()
    if p.returncode:
        raise RuntimeError(f"clip fix failed for {clip}")
    return dst
