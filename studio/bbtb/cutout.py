"""Extract transparent character cut-outs from reference sheets.

Method (deterministic, local, no AI):
  1. crop a generous box around one pose on the sheet;
  2. background = "near background colour" pixels connected to the crop border
     (plus optional manual `holes` seeds for enclosed gaps, e.g. between wing and body);
  3. keep the largest foreground component (drops labels, motion lines, neighbours)
     plus any component >= `min_ratio` of it;
  4. erode 1 px + soft edge, trim;
  5. defringe (owner/Jason 2026-10-05): strip the light halo the soft edge leaves - near-white or light
     semi-transparent pixels ON THE SILHOUETTE EDGE, in a few passes. Interior whites (eyes, gloves, soles,
     monocle) are never touched: they are outlined, so they never touch the transparent background.
  Save RGBA PNG.

Only pixels are *removed*; kept pixels are copied unchanged from the original.
Cut definitions live in library/cutlist.yaml so every cut-out is reproducible.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter

from . import registry
from .paths import DERIVED, LIBRARY, rel

CUTLIST = LIBRARY / "cutlist.yaml"
MANIFEST = DERIVED / "manifest.yaml"


def _flood_regions(mask: np.ndarray, seeds) -> np.ndarray:
    """Return the union of mask-connected regions containing any seed (4-connectivity)."""
    # .copy(): fromarray() can share the numpy buffer, and floodfill must write in place.
    img = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L").copy()
    for x, y in seeds:
        if img.getpixel((x, y)) == 255:
            ImageDraw.floodfill(img, (x, y), 128, thresh=0)
    return np.asarray(img) == 128


def _components(mask: np.ndarray) -> list[np.ndarray]:
    """Split a boolean mask into connected components (largest first)."""
    remaining = mask.copy()
    comps = []
    while remaining.any():
        ys, xs = np.nonzero(remaining)
        comp = _flood_regions(remaining, [(int(xs[0]), int(ys[0]))])
        if not comp.any():
            raise RuntimeError("flood fill made no progress")
        comps.append(comp)
        remaining &= ~comp
        if len(comps) > 4000:  # pathological noise guard
            break
    return sorted(comps, key=lambda c: -int(c.sum()))


def edge_white(img: Image.Image) -> int:
    """Near-white pixels touching transparency (the halo a viewer sees as a white edge)."""
    a = np.asarray(img.convert("RGBA")).astype(np.int16)
    rgb, A = a[..., :3], a[..., 3]
    nw = (rgb.min(2) >= 228) & ((rgb.max(2) - rgb.min(2)) <= 25) & (A > 0)
    pad = np.pad(A == 0, 1, constant_values=True)
    touch = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    return int((nw & touch).sum())


def defringe(img: Image.Image, passes: int = 3) -> tuple[Image.Image, int]:
    """Remove the light halo on the silhouette edge. Returns (image, pixels cleared)."""
    a = np.asarray(img.convert("RGBA")).copy()
    cleared = 0
    for _ in range(passes):
        rgb = a[..., :3].astype(np.int16)
        A = a[..., 3]
        mn, mx = rgb.min(2), rgb.max(2)
        light = (mn >= 200) & ((mx - mn) <= 40)                       # white / pale grey (sheet background)
        pad = np.pad(A == 0, 1, constant_values=True)
        touch = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
        kill = (A > 0) & touch & (light | ((A < 160) & (mn >= 170)))
        n = int(kill.sum())
        if not n:
            break
        a[..., 3][kill] = 0
        cleared += n
    return Image.fromarray(a), cleared


def extract(sheet: Image.Image, box, tol: float = 38.0, holes=(), min_ratio: float = 0.0,
            erode: int = 1) -> Image.Image:
    x0, y0, x1, y1 = box
    crop = sheet.crop((x0, y0, x1, y1)).convert("RGB")
    a = np.asarray(crop).astype(np.int16)
    h, w = a.shape[:2]
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    near_bg = np.sqrt(((a - bg) ** 2).sum(axis=2)) < tol

    seeds = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
            [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    seeds += [(hx - x0, hy - y0) for hx, hy in holes]
    background = _flood_regions(near_bg, seeds)

    fg = ~background
    comps = _components(fg)
    if not comps:
        raise ValueError(f"no foreground found in box {box}")
    largest = int(comps[0].sum())
    keep = np.zeros_like(fg)
    for c in comps:
        if c is comps[0] or (min_ratio and c.sum() >= min_ratio * largest):
            keep |= c

    alpha = Image.fromarray(np.where(keep, 255, 0).astype(np.uint8), "L")
    if erode:
        alpha = alpha.filter(ImageFilter.MinFilter(2 * erode + 1))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.6))
    out = crop.convert("RGBA")
    out.putalpha(alpha)
    out, _ = defringe(out)
    bbox = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return out.crop(bbox)


def run(only: str | None = None) -> list[dict]:
    """Build every cut-out in cutlist.yaml (or just those whose id starts with `only`)."""
    with open(CUTLIST) as f:
        cutlist = yaml.safe_load(f)
    manifest = {}
    if MANIFEST.exists():
        manifest = yaml.safe_load(MANIFEST.read_text()) or {}
    assets = registry.load()
    done = []
    for sheet_id, spec in cutlist["sheets"].items():
        cuts = {k: v for k, v in spec["cuts"].items() if not only or k.startswith(only)}
        if not cuts:
            continue
        sheet = Image.open(registry.path_of(sheet_id))
        for cut_id, cut in cuts.items():
            img = extract(sheet, cut["box"], tol=cut.get("tol", spec.get("tol", 38.0)),
                          holes=cut.get("holes", []), min_ratio=cut.get("min_ratio", 0.0),
                          erode=cut.get("erode", 1))
            out = DERIVED / "cutouts" / f"{cut_id}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out)
            manifest[cut_id] = {
                "file": rel(out),
                "parent": sheet_id,
                "parent_sha256": assets[sheet_id]["sha256"],
                "box": cut["box"],
                "method": "cutout.extract (border flood-fill, largest component)",
                "size": list(img.size),
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "status": manifest.get(cut_id, {}).get("status", "draft"),
            }
            done.append({"id": cut_id, "size": img.size})
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w") as f:
        f.write("# GENERATED by `bbtb cutouts`. status: draft -> approved (edit status only).\n")
        yaml.safe_dump(manifest, f, sort_keys=True)
    return done


def contact_sheet(ids: list[str], out: Path, cell: int = 300) -> Path:
    """Preview cut-outs on a dark checkerboard so halos and holes are visible."""
    cols = 6
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (40, 40, 40))
    tile = Image.new("RGB", (16, 16), (70, 70, 70))
    ImageDraw.Draw(tile).rectangle([0, 0, 7, 7], fill=(110, 110, 110))
    ImageDraw.Draw(tile).rectangle([8, 8, 15, 15], fill=(110, 110, 110))
    for i, cid in enumerate(ids):
        im = Image.open(DERIVED / "cutouts" / f"{cid}.png")
        im.thumbnail((cell - 10, cell - 30))
        x, y = (i % cols) * cell, (i // cols) * cell
        for tx in range(x, x + cell, 16):
            for ty in range(y, y + cell, 16):
                sheet.paste(tile, (tx, ty))
        sheet.paste(im, (x + 5, y + 5), im)
        ImageDraw.Draw(sheet).text((x + 6, y + cell - 22), cid, fill=(255, 255, 0))
    sheet.save(out)
    return out
