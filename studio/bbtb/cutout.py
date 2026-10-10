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
from pathlib import Path

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
            erode: int = 1, shadow: bool = False, bg_mode: str = "", erase=()) -> Image.Image:
    return extract_with_offset(sheet, box, tol, holes, min_ratio, erode, shadow, bg_mode, erase)[0]


def extract_with_offset(sheet: Image.Image, box, tol: float = 38.0, holes=(), min_ratio: float = 0.0,
                        erode: int = 1, shadow: bool = False, bg_mode: str = "",
                        erase=()) -> tuple[Image.Image, tuple[int, int]]:
    """extract() plus the sheet position of the cut-out's top-left pixel (to turn cut-out points into sheet seeds)."""
    x0, y0, x1, y1 = box
    crop = sheet.crop((x0, y0, x1, y1)).convert("RGB")
    a = np.asarray(crop).astype(np.int16)
    h, w = a.shape[:2]
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    near_bg = np.sqrt(((a - bg) ** 2).sum(axis=2)) < tol
    if bg_mode == "green":           # a character painted over grass on a book page (EP004 Snail, p.14)
        hsv = np.asarray(crop.convert("HSV")).astype(np.float32)   # float: hue*360 overflows int16
        hue, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
        greenish = (hue >= 55) & (hue <= 175) & (sat >= 0.42)                      # grass and jungle leaves
        bubble = (val >= 0.45) & (sat <= 0.13)                                       # speech-bubble white + grey rim
        darkleaf = (val <= 0.30) & (a[..., 1] >= a[..., 0]) & (sat >= 0.30)          # deep jungle shadow (not black)
        near_bg = greenish | bubble | darkleaf          # (the median border colour is meaningless on a painting)
        green_anywhere = (hue >= 70) & (hue <= 150) & (sat >= 0.5)                # grass between body parts (not cyan lip shine)
    seeds = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
            [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    seeds += [(hx - x0, hy - y0) for hx, hy in holes]
    background = _flood_regions(near_bg, seeds)
    if bg_mode == "green":
        background |= green_anywhere
    if shadow:                       # a soft grey ground shadow touching the bottom edge (Big Pea sheet): drop it
        grey = ((a.max(2) - a.min(2)) <= 28) & (a.mean(2) >= 115) & (a.mean(2) <= 238)
        background |= _flood_regions(grey | near_bg, [(x, h - 1) for x in range(w)])
    fg = ~background
    comps = _components(fg)
    if not comps:
        raise ValueError(f"no foreground found in box {box}")
    largest = int(comps[0].sum())
    keep = np.zeros_like(fg)
    for c in comps:
        if c is comps[0] or (min_ratio and c.sum() >= min_ratio * largest):
            keep |= c

    for poly in erase:               # `erase:` sheet-coordinate polygons: non-character art (e.g. a speech-bubble tail)
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).polygon([(px - x0, py - y0) for px, py in poly], fill=255)
        keep &= ~(np.asarray(m) > 0)
    alpha = Image.fromarray(np.where(keep, 255, 0).astype(np.uint8), "L")
    if erode:
        alpha = alpha.filter(ImageFilter.MinFilter(2 * erode + 1))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.6))
    out = crop.convert("RGBA")
    out.putalpha(alpha)
    out, _ = defringe(out)
    if bg_mode == "green":           # a thin grey speech-bubble tail can survive along the outline: peel grey edges
        o = np.asarray(out).copy()
        for _ in range(4):
            rgb = o[..., :3].astype(np.int16)
            sat_lo = (rgb.max(2) - rgb.min(2)) <= 26
            pad = np.pad(o[..., 3] == 0, 1, constant_values=True)
            touch = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
            kill = (o[..., 3] > 0) & touch & sat_lo & (rgb.mean(2) >= 70)
            if not kill.any():
                break
            o[..., 3][kill] = 0
        out = Image.fromarray(o)
    bbox = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return out.crop(bbox), (x0 + bbox[0], y0 + bbox[1])


# --- red-background white test (Jason 2026-10-06: white under Billy's chin) ---------------------------------------
# Sheet background trapped inside a closed shape (moustache curls, wing/neck gaps) is enclosed on every side, so the
# border flood-fill cannot reach it. Colour alone cannot tell it from drawn white (eye whites, soles, badge rim,
# shirt), so EVERY enclosed white patch must be decided once: `holes:` (sheet points) clears it as background,
# `keep_white:` (cut-out points as fractions) approves it as art. Anything undecided fails the red test.
ISLAND_MIN = 12


def white_islands(img: Image.Image) -> list[dict]:
    """Enclosed near-white patches (not touching transparency): [{mask, size, cx, cy (fractions)}]."""
    a = np.asarray(img.convert("RGBA")).astype(np.int16)
    rgb, A = a[..., :3], a[..., 3]
    white = (rgb.min(2) >= 225) & ((rgb.max(2) - rgb.min(2)) <= 30) & (A > 200)
    pad = np.pad(A < 128, 1, constant_values=True)
    touch = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    out = []
    for c in _components(white):
        if c.sum() >= ISLAND_MIN and not (c & touch).any():
            ys, xs = np.nonzero(c)
            out.append({"mask": c, "size": int(c.sum()), "cx": float(xs.mean() / img.width), "cy": float(ys.mean() / img.height)})
    return out


def _covers(isl: dict, pt) -> bool:
    h, w = isl["mask"].shape
    x, y = int(round(pt[0] * w)), int(round(pt[1] * h))
    r = 3                                            # a point within 3 px of the patch counts
    return bool(isl["mask"][max(y - r, 0):y + r + 1, max(x - r, 0):x + r + 1].any())


def red_test(cut_id: str, img: Image.Image | None = None) -> dict:
    """{'ok', 'edge_white', 'undecided': [(cx, cy, size)], 'kept': n}. ok = no white halo and every enclosed white
    patch approved in cutlist.yaml `keep_white:` (background ones are cleared at build time with `holes:`)."""
    comp = ((yaml.safe_load(CUTLIST.read_text()) or {}).get("composites") or {}).get(cut_id)
    if comp and img is None:                         # a group: each approved part must pass at its own resolution
        if "bust" in comp:
            from .script_parser import load_characters
            v = load_characters()[comp["bust"]["char"]]["variants"][comp["bust"].get("variant") or "tophat"]
            comp = {"parts": [{"cut": comp["bust"]["head"]}, {"cut": v["bust"]["bodies"]["right"]}]}
        parts = [red_test(q["cut"]) for q in comp["parts"]]
        return {"ok": all(r["ok"] for r in parts), "edge_white": sum(r["edge_white"] for r in parts),
                "undecided": [u for r in parts for u in r["undecided"]], "kept": sum(r["kept"] for r in parts)}
    img = img or Image.open(DERIVED / "cutouts" / f"{cut_id}.png")
    keep = (_cut_spec(cut_id) or {}).get("keep_white", [])
    isl = white_islands(img)
    undecided = [(round(i["cx"], 3), round(i["cy"], 3), i["size"]) for i in isl if not any(_covers(i, p) for p in keep)]
    ew = edge_white(img)
    return {"ok": not undecided and ew <= 50, "edge_white": ew, "undecided": undecided, "kept": len(isl) - len(undecided)}


def red_review(cut_id: str, dst: Path) -> Path:
    """The cut-out on solid red with every enclosed white patch boxed and numbered (green = approved art)."""
    img = Image.open(DERIVED / "cutouts" / f"{cut_id}.png").convert("RGBA")
    keep = (_cut_spec(cut_id) or {}).get("keep_white", [])
    red = Image.new("RGBA", img.size, (255, 0, 0, 255))
    red.alpha_composite(img)
    v = red.convert("RGB")
    d = ImageDraw.Draw(v)
    for i, isl in enumerate(white_islands(img)):
        ys, xs = np.nonzero(isl["mask"])
        ok = any(_covers(isl, p) for p in keep)
        d.rectangle((xs.min() - 1, ys.min() - 1, xs.max() + 1, ys.max() + 1), outline=(0, 200, 0) if ok else (0, 0, 255))
        d.text((xs.max() + 2, ys.min() - 2), str(i), fill=(0, 200, 0) if ok else (0, 0, 255))
    s = max(1, 700 // v.height)
    dst.parent.mkdir(parents=True, exist_ok=True)
    v.resize((v.width * s, v.height * s), Image.NEAREST).save(dst)
    return dst


def _cut_spec(cut_id: str) -> dict | None:
    data = yaml.safe_load(CUTLIST.read_text()) or {}
    for spec in data["sheets"].values():
        if cut_id in spec["cuts"]:
            return spec["cuts"][cut_id]
    comp = (data.get("composites") or {}).get(cut_id)
    if comp and "bust" in comp:
        return {"keep_white": []}
    if comp:                                            # keep_white of the parts, mapped into the composite
        keep = []
        for part in comp["parts"]:
            ps = _cut_spec(part["cut"]) or {}
            im = Image.open(DERIVED / "cutouts" / f"{part['cut']}.png")
            h = part["h"] * comp["size"][1]
            w = im.width * h / im.height
            x0, y0 = part["x"] * comp["size"][0] - w / 2, part["feet"] * comp["size"][1] - h
            keep += [[round((x0 + kx * w) / comp["size"][0], 4), round((y0 + ky * h) / comp["size"][1], 4)]
                     for kx, ky in ps.get("keep_white", [])]
        return {"keep_white": keep}
    return None


def composite_members(cut_id: str) -> list[Image.Image]:
    """Each part of a composite on its own full-size canvas (the grounding gate checks every figure's feet)."""
    comp = (yaml.safe_load(CUTLIST.read_text()) or {})["composites"][cut_id]
    W, H = comp["size"]
    out = []
    for part in comp["parts"]:
        if part.get("prop"):                             # a held / dropped prop has no feet to check
            continue
        im = Image.open(DERIVED / "cutouts" / f"{part['cut']}.png").convert("RGBA")
        h = int(part["h"] * H)
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c.alpha_composite(im, (int(part["x"] * W - im.width / 2), int(part["feet"] * H) - h))
        out.append(c)
    return out


def build_composite(cut_id: str) -> Path:
    """A group of approved cut-outs on one transparent canvas (EP004: the four naughty worms at the landing-spot
    layout, so Kling gets them as ONE keyframe figure). Fractions of `size`; no pixel is redrawn."""
    comp = (yaml.safe_load(CUTLIST.read_text()) or {})["composites"][cut_id]
    if "bust" in comp:                                   # an official head on its matching official body
        from . import keyframes
        from .script_parser import load_characters
        import copy
        b = comp["bust"]
        char = copy.deepcopy(load_characters()[b["char"]])
        spec = char["variants"][b.get("variant") or char.get("default_variant")]["bust"]
        spec.update({k: b[k] for k in ("cut", "neck") if k in b})   # per-pose join (EP004: no neck gap)
        img = keyframes.bust(char, b.get("variant"), b["head"])
        dst = DERIVED / "cutouts" / f"{cut_id}.png"
        img.save(dst)
        return dst
    W, H = comp["size"]
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for part in sorted(comp["parts"], key=lambda q: (q.get("prop", False), q["feet"])):   # nearer in front, props last
        im = Image.open(DERIVED / "cutouts" / f"{part['cut']}.png").convert("RGBA")
        h = int(part["h"] * H)
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        canvas.alpha_composite(im, (int(part["x"] * W - im.width / 2), int(part["feet"] * H) - h))
    dst = DERIVED / "cutouts" / f"{cut_id}.png"
    canvas.save(dst)
    return dst


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
        if "@p" in sheet_id:                          # a page of the story PDF: "<pdf asset>@p<N>"
            from .bgplates import book_page
            pdf_id, page = sheet_id.split("@p")
            sheet = book_page(pdf_id, int(page))
        else:
            sheet = Image.open(registry.path_of(sheet_id))
        for cut_id, cut in cuts.items():
            img = extract(sheet, cut["box"], tol=cut.get("tol", spec.get("tol", 38.0)),
                          holes=cut.get("holes", []), min_ratio=cut.get("min_ratio", 0.0),
                          erode=cut.get("erode", 1), shadow=cut.get("shadow", spec.get("shadow", False)),
                          bg_mode=cut.get("bg_mode", spec.get("bg_mode", "")), erase=cut.get("erase", []))
            out = DERIVED / "cutouts" / f"{cut_id}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out)
            manifest[cut_id] = {
                "file": rel(out),
                "parent": sheet_id,
                "parent_sha256": assets[sheet_id.split("@p")[0]]["sha256"],
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
