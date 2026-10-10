"""Grounding gate (owner, repeated 5+ times, 2026-10-06): every standing character's feet must sit on the flat
walkable ground of its background, never on rims, ledges, edges, leaves or dark areas.

library/backgrounds/ground_zones.yaml defines, per plate, the `ground` polygons where soles may stand and the
`forbidden` polygons they may never touch (fractions of the plate's source image). For each placed character the
gate finds the soles (the lowest opaque pixels of the cut-out) and FAILs when they are outside the ground, over a
forbidden area, cut off by the frame, or when the surface right under them is darker or a different colour than
the ground around them. Only characters the script tags airborne (pos:.../air) and close-up busts are exempt.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

from .paths import LIBRARY

ZONES = LIBRARY / "backgrounds" / "ground_zones.yaml"
OVERLAYS = LIBRARY / "backgrounds" / "ground_overlays"
DARKER = 0.72          # surface under the soles darker than 72% of the nearby ground = a rim, hole or shadowed face
DIFFERENT = 70.0       # RGB distance from the nearby ground colour = a different material (wood, rock, sky)


def zones() -> dict:
    return yaml.safe_load(ZONES.read_text()) if ZONES.exists() else {}


def inside(pt: tuple[float, float], poly: list) -> bool:
    x, y = pt
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def soles(art: Image.Image, x: int, top: int, tol: float = 0.02) -> list[tuple[int, int]]:
    """Frame points of the soles: per column, the lowest opaque pixel, kept where it is within `tol` of the art
    height from the very lowest one (both feet of a standing pose)."""
    a = np.asarray(art.convert("RGBA"))[..., 3] > 128
    if not a.any():
        return []
    rows = np.where(a.any(axis=1))[0]
    low = rows.max()
    keep = max(2, int(tol * a.shape[0]))
    pts = []
    for c in np.where(a.any(axis=0))[0]:
        b = np.where(a[:, c])[0].max()
        if b >= low - keep:
            pts.append((int(x + c), int(top + b)))
    return pts


def members(art: Image.Image, min_frac: float = 0.15) -> list[Image.Image]:
    """Each separate figure of a group art (same canvas size, others cleared)."""
    from .cutout import _components
    a = np.asarray(art.convert("RGBA"))
    comps = _components(a[..., 3] > 128)
    if not comps:
        return [art]
    big = max(c.sum() for c in comps)
    out = []
    for c in comps:
        if c.sum() >= min_frac * big:
            m = a.copy()
            m[..., 3] = np.where(c, a[..., 3], 0)
            out.append(Image.fromarray(m, "RGBA"))
    return out


def _src(pt, window, size) -> tuple[float, float]:
    W, H = size
    return window[0] + pt[0] / W * window[2], window[1] + pt[1] / H * window[3]


def _ground_ref(bg: np.ndarray, zone: dict, window, size, near_y: int) -> np.ndarray | None:
    """Median colour of ground-zone pixels in a band around the soles' height (lighting changes with depth)."""
    H, W = bg.shape[:2]
    for band in (0.08, 0.2, 1.0):
        lo, hi = max(0, near_y - int(band * H)), min(H, near_y + int(band * H))
        pix = [bg[y, x] for y in range(lo, hi, 6) for x in range(0, W, 6)
               if any(inside(_src((x, y), window, size), g) for g in zone.get("ground") or [])
               and not any(inside(_src((x, y), window, size), f) for f in zone.get("forbidden") or [])]
        if len(pix) >= 20:
            return np.median(np.array(pix, float), axis=0)
    return None


def check(scene: str, placed: list[dict], bg: Image.Image) -> list[tuple[int, str, str]]:
    """[(cast index, PASS/FAIL, detail)] for every placed character."""
    zone = zones().get(scene)
    size = bg.size
    W, H = size
    arr = np.asarray(bg.convert("RGB")).astype(float)
    out = []
    for p in placed:
        i = p["index"]
        if p.get("tagged_air"):
            out.append((i, "PASS", "airborne (tagged pos:.../air in the script): no ground needed"))
            continue
        if p.get("framing") == "closeup":
            out.append((i, "PASS", "close-up bust: no feet in frame"))
            continue
        if zone is None:
            out.append((i, "FAIL", f"{scene} has no ground zone in ground_zones.yaml: define it before using the plate"))
            continue
        if p.get("group"):                        # several figures in one art (EP004 worms): check each one
            res = [check(scene, [dict(p, art=m, group=False, index=i)], bg)[0]
                   for m in (p.get("members") or members(p["art"]))]
            bad = [r for r in res if r[1] == "FAIL"]
            out.append((i, "FAIL" if bad else "PASS", f"{len(res)} figures: " + ("; ".join(r[2] for r in bad) if bad
                                                                                  else "all soles on the walkable ground")))
            continue
        pts = soles(p["art"], p["x"], p["top"])
        if not pts:
            out.append((i, "FAIL", "no opaque pixels: can't find the soles"))
            continue
        if p.get("zoomed") and min(q[1] for q in pts) >= H - 1:
            out.append((i, "PASS", "camera push-in: feet out of frame (head-and-chest shot)"))
            continue
        if max(q[1] for q in pts) >= H - 1:
            out.append((i, "FAIL", "feet cut off by the bottom of the frame"))
            continue
        if not zone.get("ground"):
            out.append((i, "FAIL", f"{scene} has no walkable ground ({zone.get('note', '')}): tag the pose airborne "
                                   f"or use another background"))
            continue
        src = [_src(q, p["window"], size) for q in pts]
        bad_zone = [q for q in src if any(inside(q, f) for f in zone.get("forbidden") or [])]
        off = [q for q in src if not any(inside(q, g) for g in zone["ground"])]
        sy = max(q[1] for q in pts)
        if bad_zone:
            out.append((i, "FAIL", f"{len(bad_zone)}/{len(src)} sole pixels over a forbidden area "
                                   f"({zone.get('note', '')}) at y {sy / H:.2f}"))
            continue
        if off:
            out.append((i, "FAIL", f"{len(off)}/{len(src)} sole pixels outside the walkable ground at y {sy / H:.2f}"))
            continue
        under = np.array([arr[min(H - 1, y + d), min(W - 1, max(0, x))] for x, y in pts for d in (3, 6, 9)], float)
        ref = _ground_ref(arr, zone, p["window"], size, sy)
        if ref is not None:
            lum = lambda c: 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]
            ratio = float(lum(under.mean(axis=0)) / max(lum(ref), 1.0))
            dist = float(np.linalg.norm(under.mean(axis=0) - ref))
            if ratio < DARKER:
                out.append((i, "FAIL", f"surface under the soles is darker than the ground ({ratio:.0%}): a rim, "
                                       f"hole or shadowed face"))
                continue
            if dist > DIFFERENT:
                out.append((i, "FAIL", f"surface under the soles is a different colour from the ground "
                                       f"(distance {dist:.0f}): not the grass/floor"))
                continue
        out.append((i, "PASS", f"soles on the walkable ground at y {sy / H:.2f} ({len(pts)} sole pixels)"))
    return out


def overlay(scene: str, max_side: int = 900) -> Image.Image:
    """The plate with its ground zone (green) and forbidden areas (red) drawn over it."""
    from . import keyframes
    src = keyframes.plate_source(scene)
    src.thumbnail((max_side, max_side))
    W, H = src.size
    zone = zones().get(scene) or {}
    layer = Image.new("RGBA", src.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for poly in zone.get("ground") or []:
        d.polygon([(x * W, y * H) for x, y in poly], fill=(40, 220, 60, 95), outline=(20, 160, 30, 255))
    for poly in zone.get("forbidden") or []:
        d.polygon([(x * W, y * H) for x, y in poly], fill=(230, 30, 30, 95), outline=(170, 0, 0, 255))
    out = src.convert("RGBA")
    out.alpha_composite(layer)
    return out.convert("RGB")


def build_overlays(only: str | None = None) -> list[Path]:
    from . import keyframes
    OVERLAYS.mkdir(parents=True, exist_ok=True)
    paths = []
    for scene in keyframes.backgrounds():
        if only and not scene.startswith(only):
            continue
        p = OVERLAYS / f"{scene}.jpg"
        overlay(scene).save(p, quality=88)
        paths.append(p)
    return paths
