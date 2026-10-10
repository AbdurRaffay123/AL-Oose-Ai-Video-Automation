"""Scene reference boards and Kling 3.0 "elements" (owner + Jason, 2026-10-05).

Kling 3.0 Standard image-to-video accepts `elements`: per character a frontal image plus 1-3 reference images,
named in the prompt as @Element1, @Element2... Giving Kling the OFFICIAL character sheets as pictures (not only
words) is what keeps the characters on model.

Per production, `references.yaml` lists, for each shot, the characters on screen with:
  frontal: a cut-out id (the exact pose used in the shot) or a crop name from library/sheet_crops.yaml
  refs:    up to 3 groups of crop / cut-out names; each group becomes one clean reference image (no text).
`build()` writes, under productions/<production>/scene_references/:
  S01_reference.jpg                    labelled board for people (never sent to Kling)
  elements/S01_<char>_frontal.png      + S01_<char>_ref<N>.jpg   the images Kling receives
Free and local: only the sheets' pixels are cropped, scaled and laid out.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

from . import registry
from .paths import DERIVED, LIBRARY

CROPS = LIBRARY / "sheet_crops.yaml"
def out_dir(prod_root: Path) -> Path:
    return Path(prod_root) / "scene_references"
FONT = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
MIN_SIDE = 512                      # reference images are upscaled to at least this (Kling rejects tiny images)


def _crops() -> dict:
    return yaml.safe_load(CROPS.read_text())


def art(name: str) -> Image.Image:
    """A crop from an official sheet, or one of our cut-outs, on a plain white background."""
    c = _crops()
    if name in c["crops"]:
        sheet, box = c["crops"][name]
        return Image.open(registry.path_of(c["sheets"][sheet])).convert("RGB").crop(tuple(box))
    cut = Image.open(DERIVED / "cutouts" / f"{name}.png").convert("RGBA")
    if name.endswith("_group"):                      # group composites sit on a full-frame canvas: crop to the figures
        cut = cut.crop(cut.getbbox())
    bg = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    bg.alpha_composite(cut)
    return bg.convert("RGB")


def _fit(im: Image.Image, w: int, h: int) -> Image.Image:
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


ASPECT = (0.4, 2.5)                 # fal / Kling: every element image's width/height must be inside this


def aspect_ok(path_or_image) -> bool:
    im = path_or_image if isinstance(path_or_image, Image.Image) else Image.open(path_or_image)
    return ASPECT[0] <= im.width / im.height <= ASPECT[1]


def grid(names: list[str], cell: int = 512, pad: int = 16, cols: int = 2) -> Image.Image:
    """One clean reference image: the named arts on white, no text, at most `cols` across (wrapping into rows) so
    the image stays inside Kling's aspect-ratio limit (EP003: a 3-across row was rejected by fal)."""
    ims = [_fit(art(n), cell, cell) for n in names]
    cols = min(cols, len(ims))
    rows = -(-len(ims) // cols)
    out = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad) + pad), "white")
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        out.paste(im, (pad + c * (cell + pad) + (cell - im.width) // 2, pad + r * (cell + pad) + (cell - im.height) // 2))
    assert aspect_ok(out), f"reference grid {names} is outside {ASPECT}"
    return out


def frontal(name: str) -> Image.Image:
    im = art(name)
    s = max(1.0, MIN_SIDE / min(im.size))
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    out = Image.new("RGB", (im.width + 64, im.height + 64), "white")
    out.paste(im, (32, 32))
    return out


def spec(prod_root: Path) -> dict:
    p = Path(prod_root) / "references.yaml"
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


def paths(prod_root: Path, shot_id: str) -> list[dict]:
    """[{char, frontal: Path, refs: [Path]}] in element order (@Element1, @Element2 ...) for one shot."""
    d = out_dir(prod_root) / "elements"
    out = []
    for char, s in (spec(prod_root).get(shot_id) or {}).items():
        out.append({"char": char, "frontal": d / f"{shot_id}_{char}_frontal.png",
                    "refs": [d / f"{shot_id}_{char}_ref{i + 1}.jpg" for i in range(len(s.get("refs", [])))]})
    return out


def build(prod_root: Path, chars: dict, only: list[str] | None = None) -> list[Path]:
    """Write every shot's (or only these shots') element images and labelled review boards. Returns the boards."""
    root = out_dir(prod_root)
    (root / "elements").mkdir(parents=True, exist_ok=True)
    boards = []
    for shot_id, cast in spec(prod_root).items():
        if only and shot_id not in only:
            continue
        rows = []
        for char, s in cast.items():
            if len(s.get("refs", [])) > 3:
                raise ValueError(f"{shot_id} {char}: Kling takes at most 3 reference images per element")
            f = frontal(s["frontal"])
            if not aspect_ok(f):
                raise ValueError(f"{shot_id} {char}: frontal {s['frontal']} is outside Kling's aspect limit {ASPECT}")
            f.save(root / "elements" / f"{shot_id}_{char}_frontal.png")
            refs = []
            for i, group in enumerate(s.get("refs", [])):
                g = grid(group)
                g.save(root / "elements" / f"{shot_id}_{char}_ref{i + 1}.jpg", quality=92)
                refs.append((g, group))
            rows.append((chars.get(char, {}).get("display_name", char), s.get("note", ""), f, refs))
        boards.append(_board(shot_id, cast, rows, root / f"{shot_id}_reference.jpg"))
    return boards


def _board(shot_id: str, cast: dict, rows: list, dst: Path) -> Path:
    """Human review board: per character, the frontal pose + each reference image, labelled."""
    W, row_h, head = 1800, 430, 70
    board = Image.new("RGB", (W, head + row_h * len(rows)), "white")
    d = ImageDraw.Draw(board)
    big, small = ImageFont.truetype(FONT, 34), ImageFont.truetype(FONT, 20)
    d.text((24, 16), f"{shot_id}  -  scene reference (official sheets)", font=big, fill=(30, 30, 30))
    for r, (name, note, f, refs) in enumerate(rows):
        y = head + r * row_h
        d.text((24, y + 6), f"{name}{'  -  ' + note if note else ''}", font=small, fill=(180, 40, 40))
        fr = _fit(f, 300, row_h - 70)
        board.paste(fr, (24, y + 40))
        d.text((24, y + row_h - 26), "frontal (pose in the shot)", font=small, fill=(90, 90, 90))
        x = 360
        for i, (g, group) in enumerate(refs):
            gi = _fit(g, (W - 380) // max(len(refs), 1) - 20, row_h - 70)
            board.paste(gi, (x, y + 40))
            d.text((x, y + row_h - 26), f"ref {i + 1}: " + ", ".join(g.replace(group[0].split("_")[0] + "_", "") for g in group)[:34], font=small, fill=(90, 90, 90))
            x += gi.width + 20
        d.line([(0, y + row_h - 2), (W, y + row_h - 2)], fill=(220, 220, 220), width=2)
    board.save(dst, quality=92)
    return dst


# Check B (owner 2026-10-06): references must show each character's face details at a usable size.
FACE_CROPS = {"young_saul": "saul_face_", "bad_billy": "billy_head_"}


def face_ok(prod_root: Path, shot_id: str) -> list[str]:
    """Characters in the shot whose references.yaml lacks a face close-up (Saul: eyes; Billy: head/chin)."""
    bad = []
    for char, s in (spec(prod_root).get(shot_id) or {}).items():
        need = FACE_CROPS.get(char)
        if need and not any(n.startswith(need) for g in s.get("refs", []) for n in g):
            bad.append(char)
    return bad


def build_characters() -> list[Path]:
    """Reusable per-character element sets from library/character_refs.yaml -> library/scene_references/<name>/."""
    sets = yaml.safe_load((LIBRARY / "character_refs.yaml").read_text())
    out = []
    for name, s in sets.items():
        d = LIBRARY / "scene_references" / name
        d.mkdir(parents=True, exist_ok=True)
        frontal(s["frontal"]).save(d / f"{name}_frontal.png")
        refs = []
        for i, group in enumerate(s["refs"]):
            g = grid(group, cell=768 if len(group) == 1 else 512)
            g.save(d / f"{name}_ref{i + 1}.jpg", quality=92)
            refs.append((g, group))
        out.append(_board(name.upper(), {}, [(name, "reusable character set", frontal(s["frontal"]), refs)],
                          d / f"{name.upper()}_reference.jpg"))
    return out

