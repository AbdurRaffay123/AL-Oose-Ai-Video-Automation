"""Compose shot keyframes locally: approved cut-outs on approved background plates.

These frames are the first (and optional last) frame given to LTX, so every shot starts
exactly on-model. Also renders the end card. Pixels of the art are only scaled/positioned.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import yaml
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import registry
from .paths import DERIVED, LIBRARY
from .shots import OnScreen

Image.MAX_IMAGE_PIXELS = None
FONT_ROUNDED = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"

# subject height as a fraction of frame height, by framing
FRAMING_HEIGHT = {"far": 0.24, "wide": 0.40, "medium": 0.65, "closeup": 0.50}   # medium: Billy fills 60-70% (lip sync)
# background zoom (camera "closer") by framing
FRAMING_ZOOM = {"far": 1.0, "wide": 1.0, "medium": 1.22, "closeup": 1.55}
SIDE_X = {"left": 0.30, "center": 0.50, "right": 0.70}
GROUND_FRAC = {"far": 0.78, "wide": 0.80, "medium": 0.84}      # feet line; inside the 4:5 safe area
PARTNER_X = {"left": 0.12, "right": 0.88}         # silent two-shot partner: half out of frame, looming
AIR_CENTER = 0.44                                 # airborne art is centred here (no ground, no shadow)


def out_size(fmt: str, resolution: str) -> tuple[int, int]:
    short = 720 if resolution == "720p" else 1080
    long_ = 1280 if resolution == "720p" else 1920
    return (short, long_) if fmt == "9:16" else (long_, short)


def backgrounds() -> dict:
    return yaml.safe_load((LIBRARY / "backgrounds.yaml").read_text())


def resolve_scene(name: str, previous: str | None = None) -> str:
    """The background for a script scene. An exact name (`## SCENE GRASS_FLOWERS`) is used as written. A scene
    TYPE (`## SCENE flying` or `type:flying`; see library/backgrounds/INVENTORY.md) picks the best-rated
    background of that type that is not the previous shot's. Otherwise the closest name, or a clear error."""
    bgs = backgrounds()
    if name in bgs:
        return name
    key = name.lower().split(":", 1)[-1].strip()
    cands = sorted((k for k, v in bgs.items() if key in (v.get("types") or [])),
                   key=lambda k: (-bgs[k].get("rating", 2), k))
    if cands:
        return next((k for k in cands if k != previous), cands[0])
    import difflib
    close = difflib.get_close_matches(name.upper(), list(bgs), n=1, cutoff=0.6)
    if close:
        return close[0]
    types = sorted({t for v in bgs.values() for t in (v.get("types") or [])})
    raise KeyError(f"unknown scene '{name}'. Use a background name ({', '.join(bgs)}) or a type ({', '.join(types)})")


def cutout(art_id: str) -> Image.Image:
    return Image.open(DERIVED / "cutouts" / f"{art_id}.png").convert("RGBA")


def plate_source(scene: str) -> Image.Image:
    bgs = backgrounds()
    if scene not in bgs:
        raise KeyError(f"unknown scene background '{scene}'. Known: {', '.join(bgs)}")
    spec = bgs[scene]
    if spec.get("file"):                                   # cropped plate (bgplates.build / `bbtb plates`)
        path = LIBRARY / spec["file"]
        if not path.exists():
            raise FileNotFoundError(f"background plate {spec['file']} is missing: run `./bbtb plates` (free)")
        return Image.open(path).convert("RGB")
    return Image.open(registry.path_of(spec["asset"])).convert("RGB")


def plate_window(scene: str, src_size: tuple[int, int], size: tuple[int, int], zoom: float = 1.0,
                 bias_x: float = 0.0) -> tuple[float, float, float, float]:
    """(x0, y0, w, h) in source pixels: the part of the plate that fills a frame of `size` (also used to map
    keyframe points onto ground_zones.yaml, which is in source fractions)."""
    sw, sh = src_size
    W, H = size
    aspect = W / H
    ch = sh / zoom
    cw = ch * aspect
    if cw > sw:
        cw = sw / zoom
        ch = cw / aspect
    fx, fy = backgrounds()[scene].get("focus", [sw / 2, sh / 2])
    fx += bias_x * cw
    x0 = min(max(fx - cw / 2, 0), sw - cw)
    y0 = min(max(fy - ch / 2, 0), sh - ch)
    return x0, y0, cw, ch


def plate(scene: str, size: tuple[int, int], zoom: float = 1.0, bias_x: float = 0.0) -> Image.Image:
    """Crop the scene's background plate to the output aspect around its focus point."""
    src = plate_source(scene)
    x0, y0, cw, ch = plate_window(scene, src.size, size, zoom, bias_x)
    return src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize(size, Image.LANCZOS)


def bust(char: dict, variant: str | None, head_art: str, crop: bool = True,
         facing_override: str | None = None) -> Image.Image | None:
    """Expression head on a matching body (for close-ups). None if the character has no bust spec.
    crop=False returns a fixed-size canvas so two heads (mouth closed/open) stay aligned."""
    v = char["variants"].get(variant or char.get("default_variant"), {})
    spec = v.get("bust")
    if not spec:
        return None
    name = next((n for n, a in v.get("expressions", {}).items() if a == head_art), None)
    facing = facing_override or v.get("facing", {}).get(name, "front")
    body = cutout(spec["bodies"].get(facing, spec["bodies"]["front"]))
    h = body.height
    a = np.asarray(body).copy()
    cols = np.nonzero((a[int(h * 0.05):int(h * 0.35), :, 3] > 20).any(0))[0]
    cx = (cols.min() + cols.max()) / 2
    a[: int(h * spec["cut"]), :, 3] = 0
    body = Image.fromarray(a)
    head = cutout(head_art)
    s = spec["head"] * h / head.height
    head = head.resize((int(head.width * s), int(head.height * s)), Image.LANCZOS)
    pad, top_pad = body.width, h
    canvas = Image.new("RGBA", (body.width + 2 * pad, h + top_pad), (0, 0, 0, 0))
    canvas.alpha_composite(body, (pad, top_pad))
    hx = int(pad + cx - head.width / 2 + spec["dx"].get(facing, 0.0) * head.width)
    canvas.alpha_composite(head, (hx, int(top_pad + spec["neck"] * h - head.height)))
    return canvas.crop(canvas.getbbox()) if crop else canvas


def _scaled(img: Image.Image, target_h: int) -> Image.Image:
    s = target_h / img.height
    out = img.resize((max(1, int(img.width * s)), max(1, target_h)), Image.LANCZOS)
    if s > 1.3:  # upscaled art goes soft; a light unsharp mask restores line crispness
        out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    return out


def _shadow(canvas: Image.Image, cx: int, feet_y: int, width: int) -> None:
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse([cx - width // 2, feet_y - width // 10, cx + width // 2, feet_y + width // 12], fill=(30, 40, 20, 90))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(width / 18)))


def parse_place(text: str) -> tuple[float, float, float, bool] | None:
    """Script tag pos:/endpos: '<centre x>/<top y>/<height>[/air]' as fractions of the frame (EP004: the dive must
    run top-left -> bottom-right, which the automatic ground/air placement can't express)."""
    if not text:
        return None
    parts = [x.strip() for x in text.split("/")]
    x, y, h = (float(v) for v in parts[:3])
    return x, y, h, len(parts) > 3 and parts[3].lower() == "air"


def layout(scene: str, cast: list[OnScreen], chars: dict, size: tuple[int, int],
           art_images: dict[int, Image.Image] | None = None, zoom: float = 1.0,
           place: str = "") -> tuple[Image.Image, list[dict]]:
    """Background plate + where each character goes. art_images overrides the art for cast index i
    (used by the animator for mouth/pose swaps). Returns (background RGBA, placements).
    zoom > 1 is a camera push-in (script tag zoom:<f>): the frame is composed at zoom x the size from the
    originals and a window around the first character's face is cut out, so nothing is upscaled."""
    if zoom > 1.001:
        W, H = size
        big, placed = layout(scene, cast, chars, (round(W * zoom), round(H * zoom)), art_images, place=place)
        p = placed[0] if placed else None
        o = cast[0] if cast else None
        fx, fy = ((chars[o.char]["variants"].get(o.variant or chars[o.char].get("default_variant"), {})
                   .get("face") or {}).get(o.art, (0.5, 0.33)) if o else (0.5, 0.33))
        cx = p["x"] + fx * p["art"].width if p else big.width / 2      # centre the push-in on the face
        cy = p["top"] + fy * p["art"].height if p else big.height / 2
        ox = int(min(max(cx - W / 2, 0), big.width - W))
        oy = cy - 0.40 * H
        if p:                                              # keep the hat top inside the 4:5 safe area if possible
            oy = min(oy, p["top"] - 0.16 * H)
        oy = int(min(max(oy, 0), big.height - H))
        bw = placed[0]["window"] if placed else None
        for q in placed:
            q["x"] -= ox
            q["top"] -= oy
            q["feet"] -= oy
            q["zoomed"] = True
            q["window"] = (bw[0] + ox / big.width * bw[2], bw[1] + oy / big.height * bw[3],
                           W / big.width * bw[2], H / big.height * bw[3])
        return big.crop((ox, oy, ox + W, oy + H)), placed
    W, H = size
    framing = cast[0].framing if cast else "wide"
    bias = 0.0
    if framing != "wide" and cast:
        bias = {"left": -0.12, "right": 0.12, "center": 0.0}[cast[0].side]
    canvas = plate(scene, size, FRAMING_ZOOM[framing], bias).convert("RGBA")
    src_size = plate_source(scene).size
    x0, y0, cw, ch = plate_window(scene, src_size, size, FRAMING_ZOOM[framing], bias)
    window = (x0 / src_size[0], y0 / src_size[1], cw / src_size[0], ch / src_size[1])   # frame -> source fractions
    if framing == "closeup":
        canvas = canvas.filter(ImageFilter.GaussianBlur(3))   # shallow depth of field

    placed = []
    for i, o in enumerate(cast):
        art = None
        if art_images and i in art_images:
            art = art_images[i]
        elif o.framing == "closeup":
            art = bust(chars[o.char], o.variant, o.art)
        is_bust = o.framing == "closeup" and art is not None and (bool(art_images and i in art_images)
                                                                  or chars[o.char]["variants"].get(o.variant or chars[o.char].get("default_variant"), {}).get("bust"))
        art = art if art is not None else cutout(o.art)
        if o.mirror:
            art = art.transpose(Image.FLIP_LEFT_RIGHT)
        rel_h = chars[o.char].get("height", 1.0) or 1.0
        if is_bust:
            h = int(1.0 * H)                      # hat-to-knees fills the frame; larger gets too soft
        elif o.framing in ("wide", "far"):
            h = int(min(FRAMING_HEIGHT[o.framing] * rel_h, 0.78) * H)
        elif o.framing == "closeup":
            h = int(min(FRAMING_HEIGHT["closeup"] * H, 0.86 * W * art.height / art.width))
        else:
            h = int(FRAMING_HEIGHT["medium"] * min(max(rel_h, 0.6), 1.0) * H)
        h = min(h, int(0.92 * W * art.height / art.width)) if not is_bust else h  # never wider than frame
        art = _scaled(art, h)
        partner = getattr(o, "role", "") == "with"
        airborne = o.art in (chars[o.char]["variants"].get(o.variant or chars[o.char].get("default_variant"), {})
                             .get("airborne") or [])
        cx = int((PARTNER_X if partner else SIDE_X)[o.side] * W)
        if is_bust:
            top = int(0.16 * H)                   # hat top inside the 4:5 safe area (y >= 0.148 H)
        elif airborne:
            top = int(backgrounds()[scene].get("air_y", AIR_CENTER) * H) - art.height // 2
        elif o.framing == "closeup":
            top = int(0.80 * H) - art.height
        else:
            top = int((GROUND_FRAC[o.framing] - (0.03 if partner else 0.0)) * H) - art.height
        x = cx - art.width // 2
        if art.width < W and not partner:
            x = min(max(x, 8), W - art.width - 8)  # keep the whole character in frame
        exact = parse_place(place) if i == 0 else None
        if exact:                                  # tag pos:/endpos: overrides the automatic placement
            px, py, ph, in_air = exact
            art = _scaled(cutout(o.art) if not (art_images and i in art_images) else art_images[i], int(ph * H))
            h, airborne = art.height, in_air
            x, top = int(px * W - art.width / 2), int(py * H)
        placed.append({"index": i, "feet": top + art.height, "x": x, "top": top, "art": art,
                       "framing": "closeup" if is_bust else o.framing, "scale": h / max(art.height, 1),
                       "shadow": not airborne, "tagged_air": bool(exact and exact[3]), "window": window,
                       "group": bool(chars[o.char].get("group")),
                       "members": ([m.resize(art.size, Image.LANCZOS) for m in _members(o.art)]
                                   if chars[o.char].get("group") else None)})
    return canvas, placed


def draw(canvas: Image.Image, placed: list[dict], offsets: dict[int, tuple[int, int]] | None = None) -> Image.Image:
    out = canvas.copy()
    for p in sorted(placed, key=lambda p: p["feet"]):          # lower feet = in front
        dx, dy = (offsets or {}).get(p["index"], (0, 0))
        if p["framing"] != "closeup" and p.get("shadow", True):
            from . import grounding                    # contact shadow centred under the soles (owner 2026-10-06)
            if p.get("group"):                         # one shadow under each member of a group figure
                for m in (p.get("members") or grounding.members(p["art"])):
                    mp = grounding.soles(m, p["x"] + dx, p["top"] + dy)
                    if mp:
                        xs = [q[0] for q in mp]
                        _shadow(out, int(sum(xs) / len(xs)), max(q[1] for q in mp) + 2, int(max((max(xs) - min(xs)) * 1.35, 40)))
                out.alpha_composite(p["art"], (p["x"] + dx, p["top"] + dy))
                continue
            pts = grounding.soles(p["art"], p["x"] + dx, p["top"] + dy)
            if pts:
                xs = [q[0] for q in pts]
                span = max(xs) - min(xs)
                _shadow(out, int(sum(xs) / len(xs)), max(q[1] for q in pts) + 2,
                        int(max(span * 1.35, p["art"].width * 0.35)))
            else:
                _shadow(out, p["x"] + dx + p["art"].width // 2, p["feet"] - 4, int(p["art"].width * 0.8))
        out.alpha_composite(p["art"], (p["x"] + dx, p["top"] + dy))
    return out


def _members(art_id: str) -> list[Image.Image]:
    from .cutout import composite_members
    return composite_members(art_id)


def compose(scene: str, cast: list[OnScreen], chars: dict, size: tuple[int, int], zoom: float = 1.0,
            place: str = "") -> Image.Image:
    canvas, placed = layout(scene, cast, chars, size, zoom=zoom, place=place)
    return draw(canvas, placed).convert("RGB")


def end_card(size: tuple[int, int], lines: tuple[str, ...] = ("OUT NOW!", "Paperback | Hardcover | eBook | Audiobook")) -> Image.Image:
    W, H = size
    canvas = Image.new("RGBA", size, (0, 0, 0, 255))
    logo = Image.open(registry.path_of("images.marketing.bbth-title-v2")).convert("RGBA")
    logo = logo.resize((int(W * 0.86), int(W * 0.86 * logo.height / logo.width)), Image.LANCZOS)
    canvas.alpha_composite(logo, ((W - logo.width) // 2, int(H * 0.07)))
    cover = Image.open(registry.path_of("images.marketing.cover")).convert("RGBA")
    cw = int(W * 0.62)
    cover = cover.resize((cw, int(cw * cover.height / cover.width)), Image.LANCZOS).rotate(-4, expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(cover, ((W - cover.width) // 2, int(H * 0.24)))
    d = ImageDraw.Draw(canvas)
    y = int(H * 0.24) + cover.height + int(H * 0.03)
    for i, text in enumerate(lines):
        size_pt = int(W * (0.11 if i == 0 else 0.042))
        font = ImageFont.truetype(FONT_ROUNDED, size_pt)
        tw = d.textlength(text, font=font)
        d.text(((W - tw) / 2, y), text, font=font, fill=(255, 210, 0) if i == 0 else (255, 255, 255))
        y += int(size_pt * 1.35)
    return canvas.convert("RGB")


def tease_frame(L: tuple, t: float, duration: float) -> Image.Image:
    """The tease card at time t: a slow push-in on Billy's face, the question fades up."""
    frames, layer, ty = L
    W, H = frames[0].size
    z = 1 + 0.03 * min(t / max(duration, 0.1), 1.0)
    big = frames[0].resize((round(W * z), round(H * z)), Image.BILINEAR)
    ox, oy = (big.width - W) // 2, int((big.height - H) * 0.3)
    canvas = big.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
    _paste_scaled(canvas, layer, ((W - layer.width) // 2, ty), 1.0, min(1.0, max(t - 0.15, 0) / 0.3))
    return canvas.convert("RGB")


TITLE_VIDEO = "video.1-bbtb-title"     # 4:5 marketing title, 19.2 s; black text cards start at 6.9 s
TITLE_FOOTAGE = 6.0                    # owner 2026-10-05: first 6 s only (the black text cards start at 6.9 s)
TITLE_TIMES = (1.0, 2.5, 4.0)          # when each text line appears (owner 2026-10-05)


def _emoji_split(text: str) -> tuple[str, str]:
    """('text', 'emoji') for a line ending in emoji (drawn with the colour emoji font)."""
    i = len(text)
    while i > 0 and (ord(text[i - 1]) > 0x2600 or text[i - 1] in " \ufe0f"):
        i -= 1
    return text[:i].rstrip(), text[i:].strip()


def outlined_line(size: tuple[int, int], text: str, pt: int) -> Image.Image:
    """One white line with a black outline (and its emoji), cropped; readable over any video."""
    words, emoji = _emoji_split(text)
    layer = text_block(size, [words], pt, (255, 255, 255, 255), stroke=max(4, pt // 6))
    em = emoji_image(emoji, int(pt * 1.1)) if emoji else None
    if em is None:
        return layer
    out = Image.new("RGBA", (layer.width + int(pt * 0.3) + em.width, max(layer.height, em.height)), (0, 0, 0, 0))
    out.alpha_composite(layer, (0, (out.height - layer.height) // 2))
    out.alpha_composite(em, (layer.width + int(pt * 0.3), (out.height - em.height) // 2))
    return out


def title_layers(size: tuple[int, int], text: str) -> list[tuple[Image.Image, int, float]]:
    """Card 'title': the text lines (split on '|') as full-frame transparent layers + when each appears. Placed in
    the bottom of the 4:5 area, under the title video's own 3D letters."""
    W, H = size
    lines = [t.strip() for t in text.split("|") if t.strip()]
    pts = [int(W * 0.066)] * (len(lines) - 1) + [int(W * 0.046)]                # the last line is smaller
    imgs = [outlined_line(size, t, pt) for t, pt in zip(lines, pts)]
    y = int(SAFE_BOTTOM * H) - sum(im.height for im in imgs) - int(H * 0.012) * (len(imgs) - 1)
    out = []
    for i, im in enumerate(imgs):
        full = Image.new("RGBA", size, (0, 0, 0, 0))
        full.alpha_composite(im, ((W - im.width) // 2, y))
        out.append((full, y, TITLE_TIMES[min(i, len(TITLE_TIMES) - 1)]))
        y += im.height + int(H * 0.012)
    return out


def title_background(frame: Image.Image, size: tuple[int, int]) -> Image.Image:
    """A 4:5 frame centred in 9:16 (exactly the 4:5 safe area), the gaps filled with a blurred, darker copy."""
    W, H = size
    fg = frame.convert("RGB").resize((W, round(W * frame.height / frame.width)), Image.LANCZOS)
    bg = frame.convert("RGB").resize((round(H * frame.width / frame.height), H), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(24))
    bg = Image.blend(bg, Image.new("RGB", size, (0, 0, 0)), 0.35)
    bg.paste(fg, (0, (H - fg.height) // 2))
    return bg


VERSUS = {"left": "bigpea_34right", "right": "billy_tophat_34left"}   # versus card cut-outs (both face the middle)


def versus_layers(scene: str, size: tuple[int, int], text: str, left: str = "", right: str = "") -> dict:
    """Card 'versus' (EP004): two characters slam in from the sides, a VS pops, the question builds word by word.
    Text: '<question> | <call to action>' (the second part appears after the question)."""
    W, H = size
    bg = plate(scene, size).convert("RGB").filter(ImageFilter.GaussianBlur(14))
    bg = Image.blend(bg, Image.new("RGB", size, (10, 6, 20)), 0.45)
    over = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    d.polygon([(0, 0), (int(W * 0.62), 0), (int(W * 0.38), H), (0, H)], fill=(255, 120, 20, 70))      # warm side
    d.polygon([(int(W * 0.62), 0), (W, 0), (W, H), (int(W * 0.38), H)], fill=(20, 170, 200, 70))     # cool side
    for k in range(18):                                                                            # burst rays
        a = 2 * math.pi * k / 18
        d.polygon([(W / 2, H * 0.45), (W / 2 + 1400 * math.cos(a), H * 0.45 + 1400 * math.sin(a)),
                   (W / 2 + 1400 * math.cos(a + 0.08), H * 0.45 + 1400 * math.sin(a + 0.08))], fill=(255, 255, 255, 18))
    bg = bg.convert("RGBA")
    bg.alpha_composite(over)
    def fig(cut_id: str, h: int) -> Image.Image:
        im = cutout(cut_id)
        return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    L = fig(left or VERSUS["left"], int(H * 0.30))
    R = fig(right or VERSUS["right"], int(H * 0.40))
    parts = [p.strip() for p in text.split("|")]
    q_words = parts[0].split()
    pt = int(W * 0.078)
    vs = text_block(size, ["VS"], int(W * 0.24), (255, 214, 0, 255), stroke=10)
    cta = text_block(size, [parts[1]], int(W * 0.06), (255, 255, 255, 255), stroke=6) if len(parts) > 1 else None
    return {"bg": bg, "L": L, "R": R, "vs": vs, "cta": cta, "q": q_words, "pt": pt}


def versus_frame(V: dict, t: float, duration: float) -> Image.Image:
    W, H = V["bg"].size
    canvas = V["bg"].copy()
    floor_y = int(H * 0.79)
    shake = 0
    for t0 in (0.25, 0.75):                                     # impact shakes as each one lands
        if t0 <= t < t0 + 0.25:
            shake = int(12 * (1 - (t - t0) / 0.25) * (1 if int(t * 40) % 2 else -1))
    bob = lambda ph: int(4 * math.sin(2 * math.pi * 1.4 * t + ph))
    kl = _ease_back((t - 0.05) / 0.3)                           # left slams in
    xl = int(-V["L"].width + (W * 0.05 + V["L"].width) * min(kl, 1.15))
    canvas.alpha_composite(V["L"], (xl + shake, floor_y - V["L"].height + bob(0)))
    kr = _ease_back((t - 0.55) / 0.3)                           # right slams in
    xr = int(W - (W * 0.05 + V["R"].width) * min(kr, 1.15))
    canvas.alpha_composite(V["R"], (xr + shake, floor_y - V["R"].height + bob(1.5)))
    if t >= 1.0:                                                # VS pops with a flash
        if t < 1.08:
            canvas.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 140)))
        s = 0.6 + 0.4 * _ease_back((t - 1.0) / 0.25) + 0.04 * math.sin(2 * math.pi * 2 * t)
        _paste_scaled(canvas, V["vs"], ((W - V["vs"].width) // 2, int(H * 0.265)), s)
    n = int(max(0.0, t - 1.4) / 0.32) + 1 if t >= 1.4 else 0    # the question, one word every 0.32 s
    if n:
        words = V["q"][:n]
        font = ImageFont.truetype(FONT_ROUNDED, V["pt"])
        probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        lines = _wrap(probe, " ".join(words), font, W * 0.9)
        layer = text_block((W, H), lines, V["pt"], (255, 255, 255, 255), stroke=7)
        _paste_scaled(canvas, layer, ((W - layer.width) // 2, int(H * 0.155)), 1.0)
    t_cta = 1.4 + 0.32 * len(V["q"]) + 0.2
    if V["cta"] is not None and t >= t_cta:
        pulse = 1 + 0.05 * math.sin(2 * math.pi * 1.6 * (t - t_cta))
        _paste_scaled(canvas, V["cta"], ((W - V["cta"].width) // 2, int(H * 0.805)),
                      _ease_back((t - t_cta) / 0.3) * pulse)
    return canvas.convert("RGB")


def card_layers(shot, chars: dict, size: tuple[int, int]):
    if shot.card == "rule":
        return rule_layers(shot.backdrop, size, shot.card_text)
    if shot.card == "versus":
        return versus_layers(shot.backdrop, size, shot.card_text)
    if shot.card == "title":
        return title_layers(size, shot.card_text)
    if shot.card == "tease":
        return tease_layers(chars, shot.backdrop, size, shot.card_text)
    return book_layers(size, shot.card_text, shot.emoji)


def card_frame(shot, L, t: float) -> Image.Image:
    if shot.card == "rule":
        return rule_frame(L, t, shot.duration)
    if shot.card == "versus":
        return versus_frame(L, t, shot.duration)
    if shot.card == "title":                     # keyframe / preview frame (the video itself is built by ffmpeg)
        import subprocess, io
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{min(t, TITLE_FOOTAGE - 0.05):.3f}", "-i",
                              str(registry.path_of(TITLE_VIDEO)), "-an", "-frames:v", "1", "-f", "image2pipe",
                              "-vcodec", "png", "-"], capture_output=True, check=True).stdout
        canvas = title_background(Image.open(io.BytesIO(raw)), L[0][0].size).convert("RGBA")
        for layer, _, t_in in L:
            if t >= t_in:
                canvas.alpha_composite(layer)
        return canvas.convert("RGB")
    return tease_frame(L, t, shot.duration) if shot.card == "tease" else book_frame(L, t)


def save(img: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=93) if path.suffix == ".jpg" else img.save(path)
    return path


# --- END_CARD moments (script tag card:tease / card:book). Local, free; text is drawn here, never in AI shots. ---
FONT_EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
SAFE_TOP, SAFE_BOTTOM = 0.155, 0.845                 # 4:5 safe area of a 9:16 frame


def emoji_image(ch: str, px: int) -> Image.Image | None:
    """A colour emoji as an RGBA image `px` tall (None if the system emoji font is missing)."""
    try:
        font = ImageFont.truetype(FONT_EMOJI, 160)       # the colour bitmaps exist at 160 px only
    except OSError:
        return None
    im = Image.new("RGBA", (420, 220), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((210, 110), ch, font=font, embedded_color=True, anchor="mm")
    box = im.getbbox()
    if not box:
        return None
    im = im.crop(box)
    return im.resize((max(1, round(im.width * px / im.height)), px), Image.LANCZOS)


def _wrap(d: ImageDraw.ImageDraw, text: str, font, max_w: float) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and d.textlength(trial, font=font) > max_w:
            out.append(cur)
            cur = word
        else:
            cur = trial
    return out + ([cur] if cur else [])


def text_block(size: tuple[int, int], lines: list[str], pt: int, fill, stroke: int = 0, gap: float = 1.22,
               panel: bool = False) -> Image.Image:
    """Centred lines of text on a transparent layer cropped to the text (for fades and pops).
    panel=True puts a dark rounded panel behind it (text over busy art)."""
    W, _ = size
    font = ImageFont.truetype(FONT_ROUNDED, pt)
    lh = int(pt * gap)
    layer = Image.new("RGBA", (W, lh * len(lines) + 2 * stroke + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=font)
        d.text(((W - tw) / 2, stroke + i * lh), line, font=font, fill=fill,
               stroke_width=stroke, stroke_fill=(20, 12, 4, 255))
    layer = layer.crop(layer.getbbox())
    if panel:
        pad = int(pt * 0.45)
        back = Image.new("RGBA", (layer.width + 2 * pad, layer.height + 2 * pad), (0, 0, 0, 0))
        ImageDraw.Draw(back).rounded_rectangle((0, 0, back.width - 1, back.height - 1), radius=pad * 2,
                                               fill=(20, 12, 4, 190))
        back.alpha_composite(layer, (pad, pad))
        layer = back
    return layer


def pill(text: str, pt: int, bg, fg, emoji: str = "", pad: float = 0.55) -> Image.Image:
    font = ImageFont.truetype(FONT_ROUNDED, pt)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = probe.textlength(text, font=font)
    em = emoji_image(emoji, int(pt * 1.15)) if emoji else None
    h = int(pt * (1 + 2 * pad))
    w = int(tw + h + (em.width + pt * 0.35 if em else 0))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg)
    d.text((h / 2, h / 2), text, font=font, fill=fg, anchor="lm")
    if em:
        im.alpha_composite(em, (int(h / 2 + tw + pt * 0.35), (h - em.height) // 2))
    return im


def tease_face(chars: dict) -> str:
    """Registry id of the face art for the end-card tease (`tease_face:` in a character variant)."""
    for c in chars.values():
        for v in (c.get("variants") or {}).values():
            if v.get("tease_face"):
                return v["tease_face"]
    raise ValueError("no character defines `tease_face:` for the end-card tease")


def tease_layers(chars: dict, scene: str, size: tuple[int, int], text: str) -> tuple[list[Image.Image], Image.Image, int]:
    """Card 'tease' (owner 2026-10-05: "looks fake" -> simpler): only Billy's face, the official head art shown at most
    at its own size (never enlarged, never pasted onto a body), over the softly blurred previous scene, and the
    question below it in plain outlined text (no box)."""
    W, H = size
    pt = int(W * 0.074)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = ImageFont.truetype(FONT_ROUNDED, pt)
    lines = [ln for part in text.split("|") for ln in _wrap(probe, part.strip(), font, W * 0.88)]   # '|' = line break
    layer = text_block(size, lines, pt, (255, 214, 0, 255), stroke=max(4, pt // 7))
    face = Image.open(registry.path_of(tease_face(chars))).convert("RGBA")
    room = SAFE_BOTTOM * H - SAFE_TOP * H - H * 0.02 - layer.height    # the face shrinks to leave room for the text
    fw = int(min(W * 0.66, face.width, room * face.width / face.height))
    if fw < W * 0.3:
        raise ValueError("tease question is too long for the safe area: shorten the line")
    face = face.resize((fw, round(fw * face.height / face.width)), Image.LANCZOS)
    canvas = plate(scene, size).convert("RGB").filter(ImageFilter.GaussianBlur(8))
    canvas = Image.blend(canvas, Image.new("RGB", size, (0, 0, 0)), 0.25).convert("RGBA")
    top = int(SAFE_TOP * H)
    canvas.alpha_composite(face, ((W - fw) // 2, top))
    ty = top + face.height + int(H * 0.02)
    return [canvas.convert("RGB")], layer, ty


def book_layers(size: tuple[int, int], text: str, emoji: str = "") -> dict:
    """Card 'book': cover + CTA. The sentence with 'link in bio' becomes a pill (with the emoji); a Follow button
    with a tapping hand hints at following. Returns the layers and their resting positions."""
    W, H = size
    cover_src = Image.open(registry.path_of("images.marketing.cover")).convert("RGBA")
    bg = cover_src.convert("RGB").resize((W, int(W * cover_src.height / cover_src.width)), Image.LANCZOS)
    bg = bg.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", size, (0, 0, 0)), 0.62).convert("RGBA")
    logo = Image.open(registry.path_of("images.marketing.bbth-title-v2")).convert("RGBA")
    logo = logo.resize((int(W * 0.58), int(W * 0.58 * logo.height / logo.width)), Image.LANCZOS)
    cw = int(W * 0.42)
    cover = cover_src.resize((cw, int(cw * cover_src.height / cover_src.width)), Image.LANCZOS)
    cover = cover.rotate(-4, expand=True, resample=Image.BICUBIC)

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    link = next((s for s in sentences if "link in bio" in s.lower()), "")
    body = [s for s in sentences if s != link]
    pt = int(W * 0.05)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = ImageFont.truetype(FONT_ROUNDED, pt)
    text_lines = [ln for s in body for ln in _wrap(probe, s, font, W * 0.88)]
    cta = [text_block(size, [ln], pt, (255, 255, 255, 255), stroke=3) for ln in text_lines]
    link_pill = pill(link.upper().rstrip("!").strip() + "!", int(W * 0.05), (255, 214, 0, 255), (40, 20, 0, 255), emoji) if link else None
    follow = pill("+ Follow", int(W * 0.05), (254, 44, 85, 255), (255, 255, 255, 255))
    hand = emoji_image("\U0001F446", int(W * 0.09))

    y = int(SAFE_TOP * H)
    pos = {"logo": ((W - logo.width) // 2, y)}
    y += logo.height + int(H * 0.005)
    pos["cover"] = ((W - cover.width) // 2, y)
    y += cover.height + int(H * 0.012)
    for i, layer in enumerate(cta):
        pos[f"cta{i}"] = ((W - layer.width) // 2, y)
        y += int(pt * 1.25)
    y += int(H * 0.012)
    if link_pill:
        pos["link"] = ((W - link_pill.width) // 2, y)
        y += link_pill.height + int(H * 0.014)
    pos["follow"] = ((W - follow.width) // 2, y)
    if hand:
        pos["hand"] = (pos["follow"][0] + follow.width - hand.width // 3, y + follow.height // 2)
    if y + follow.height > SAFE_BOTTOM * H + 2:
        raise ValueError(f"book card text is too long for the safe area ({len(text_lines)} lines): shorten the CTA")
    return {"bg": bg, "logo": logo, "cover": cover, "cta": cta, "link": link_pill, "follow": follow, "hand": hand,
            "pos": pos}


def _ease_back(t: float) -> float:
    """0 -> 1 with a small overshoot (a 'pop')."""
    t = min(max(t, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def _paste_scaled(canvas: Image.Image, layer: Image.Image, xy: tuple[int, int], scale: float, alpha: float = 1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    w, h = max(1, round(layer.width * scale)), max(1, round(layer.height * scale))
    im = layer.resize((w, h), Image.BILINEAR) if (w, h) != layer.size else layer
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda a: int(a * alpha)))
    canvas.alpha_composite(im, (int(xy[0] + (layer.width - w) / 2), int(xy[1] + (layer.height - h) / 2)))


def book_frame(L: dict, t: float) -> Image.Image:
    """The book card at time t (s): cover pops in, CTA lines fade up one by one, link pill pops, the Follow button
    pops and pulses while a hand taps it."""
    canvas = L["bg"].copy()
    pos = L["pos"]
    canvas.alpha_composite(L["logo"], pos["logo"])
    _paste_scaled(canvas, L["cover"], pos["cover"], 0.6 + 0.4 * _ease_back(t / 0.45), min(1.0, t / 0.2))
    for i, layer in enumerate(L["cta"]):
        k = min(max((t - 0.35 - 0.22 * i) / 0.3, 0.0), 1.0)
        x, y = pos[f"cta{i}"]
        _paste_scaled(canvas, layer, (x, y + int((1 - k) * 18)), 1.0, k)
    t_link = 0.4 + 0.22 * len(L["cta"])
    if L["link"] is not None:
        _paste_scaled(canvas, L["link"], pos["link"], _ease_back((t - t_link) / 0.35))
    t_follow = t_link + 0.35
    tap = 0.0
    if L["hand"] is not None and t > t_follow + 0.4:
        phase = ((t - t_follow - 0.4) % 1.0)                 # one tap per second
        tap = max(0.0, math.sin(math.pi * phase / 0.35)) if phase < 0.35 else 0.0
    pulse = 1 + 0.05 * math.sin(2 * math.pi * 1.6 * max(t - t_follow - 0.35, 0.0)) if t > t_follow + 0.35 else 1.0
    _paste_scaled(canvas, L["follow"], pos["follow"], _ease_back((t - t_follow) / 0.35) * pulse * (1 - 0.06 * tap))
    if L["hand"] is not None and t > t_follow + 0.25:
        hx, hy = pos["hand"]
        _paste_scaled(canvas, L["hand"], (hx, hy + int(14 * (1 - tap)) + 6), 1.0, min(1.0, (t - t_follow - 0.25) / 0.2))
    return canvas.convert("RGB")


RULE_HEAD = "billy_tophat_head_suspicious"           # EP004 end card: Billy's official suspicious head (no redraw)


def rule_layers(scene: str, size: tuple[int, int], text: str) -> dict:
    """Card 'rule' (EP004 v4): 'RULE NUMBER ONE...' slams in word by word, 'LOOK UP! 👆' punches in with a flash and
    spinning rays, Billy's official suspicious head slides up from the bottom, then the share line pops in a panel.
    Text: '<rule> | <punch> | <share>'. The backdrop uses the scene's `wide:` view (GRASS_SIGN_LOW -> GRASS_SIGN)."""
    W, H = size
    spec = backgrounds().get(scene, {})
    bg = plate(spec.get("wide", scene), size).convert("RGB").filter(ImageFilter.GaussianBlur(8))
    bg = Image.blend(bg, Image.new("RGB", size, (16, 8, 30)), 0.28).convert("RGBA")
    parts = [p.strip() for p in text.split("|")] + ["", "", ""]
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    pt = int(W * 0.105)
    font = ImageFont.truetype(FONT_ROUNDED, pt)
    rows, row = [], []                                 # the rule on as few lines as fit 88% of the width
    for w in parts[0].split():
        if row and probe.textlength(" ".join(row + [w]), font=font) > W * 0.88:
            rows.append(row); row = []
        row.append(w)
    rows.append(row)
    gap = int(probe.textlength(" ", font=font))
    words = [[text_block(size, [w], pt, (255, 255, 255, 255), stroke=8) for w in r] for r in rows]
    punch_txt, punch_emo = _emoji_split(parts[1])
    ppt = int(W * 0.18)                                # LOOK UP! + its emoji must fit 90% of the width
    while punch_txt and ppt > 30 and probe.textlength(punch_txt, font=ImageFont.truetype(FONT_ROUNDED, ppt)) + \
            (ppt * 0.9 if punch_emo else 0) > W * 0.86:
        ppt -= 2
    punch = text_block(size, [punch_txt], ppt, (255, 214, 0, 255), stroke=11) if punch_txt else None
    share_txt, share_emo = _emoji_split(parts[2])
    spt = int(W * 0.075)
    share = (text_block(size, _wrap(probe, share_txt, ImageFont.truetype(FONT_ROUNDED, spt), W * 0.82), spt,
                        (255, 255, 255, 255), stroke=5, panel=True) if share_txt else None)
    head = cutout(RULE_HEAD)
    hh = int(H * 0.24)                                 # ~1.5x the official ~200 px head: larger goes soft
    head = head.resize((round(head.width * hh / head.height), hh), Image.LANCZOS)
    rays = Image.new("RGBA", (int(W * 1.6), int(W * 1.6)), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    c = rays.width / 2
    for k in range(16):
        a0 = 2 * math.pi * k / 16
        dr.polygon([(c, c), (c + c * 1.4 * math.cos(a0), c + c * 1.4 * math.sin(a0)),
                    (c + c * 1.4 * math.cos(a0 + 0.14), c + c * 1.4 * math.sin(a0 + 0.14))], fill=(255, 214, 0, 46))
    return {"bg": bg, "words": words, "gap": gap, "pt": pt, "punch": punch,
            "punch_emoji": emoji_image(punch_emo, int(ppt * 0.8)) if punch_emo else None,
            "rule_bottom": int(H * 0.155) + len(rows) * int(pt * 1.12),
            "share": share, "share_emoji": emoji_image(share_emo, int(W * 0.11)) if share_emo else None,
            "head": head, "rays": rays}


RULE_TIMES = {"words": (0.1, 0.18), "punch": 0.7, "head": 1.25, "share": 1.85}   # owner 2026-10-07: 5-6 s card   # SFX in the script hit these


def rule_frame(R: dict, t: float, duration: float) -> Image.Image:
    W, H = R["bg"].size
    canvas = R["bg"].copy()
    t0, step = RULE_TIMES["words"]
    tp = RULE_TIMES["punch"]
    if t >= tp:                                        # slow spinning rays behind LOOK UP!
        k = min(1.0, (t - tp) / 0.3)
        r = R["rays"].rotate(18 * (t - tp), resample=Image.BICUBIC)
        r.putalpha(r.split()[3].point(lambda v: int(v * k)))
        canvas.alpha_composite(r, ((W - r.width) // 2, R["rule_bottom"] + int(H * 0.07) - r.height // 2))
    flat = [w for row in R["words"] for w in row]
    shake = 0
    for k in range(len(flat)):                         # a tiny shake as each word lands
        tk = t0 + k * step
        if tk <= t < tk + 0.12:
            shake = int(9 * (1 - (t - tk) / 0.12) * (1 if int(t * 50) % 2 else -1))
    n = 0
    for ri, row in enumerate(R["words"]):
        total = sum(w.width for w in row) + R["gap"] * (len(row) - 1)
        x = (W - total) // 2
        y = int(H * 0.155) + ri * int(R["pt"] * 1.12)
        for w in row:
            tk = t0 + n * step
            if t >= tk:
                _paste_scaled(canvas, w, (x + shake, y), 1.0 + 0.7 * max(0.0, 1 - (t - tk) / 0.15))
            x += w.width + R["gap"]
            n += 1
    if R["punch"] is not None and t >= tp:
        if t < tp + 0.07:
            canvas.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 130)))
        s = _ease_back((t - tp) / 0.25) + 0.03 * math.sin(2 * math.pi * 1.5 * (t - tp))
        em = R["punch_emoji"]
        px = (W - R["punch"].width - (em.width + 10 if em else 0)) // 2
        py = R["rule_bottom"] + int(H * 0.02)
        _paste_scaled(canvas, R["punch"], (px, py), s)
        if em is not None:                             # the finger keeps pointing UP: a small upward bounce
            bounce = int(14 * abs(math.sin(2 * math.pi * 1.2 * (t - tp))))
            _paste_scaled(canvas, em, (px + R["punch"].width + 10, py - bounce), s)
    th = RULE_TIMES["head"]
    if t >= th:                                        # Billy's head slides up from the bottom and settles
        k = min(_ease_back((t - th) / 0.4), 1.08)
        top = int(H - (H - H * 0.61) * k) + int(4 * math.sin(2 * math.pi * 0.9 * (t - th)))
        head = R["head"].rotate(3 * math.sin(2 * math.pi * 0.6 * (t - th)), resample=Image.BICUBIC, expand=False)
        canvas.alpha_composite(head, ((W - head.width) // 2, top))
    ts = RULE_TIMES["share"]
    if R["share"] is not None and t >= ts:
        pulse = 1 + 0.03 * math.sin(2 * math.pi * 1.4 * (t - ts))
        sx, sy = (W - R["share"].width) // 2, R["rule_bottom"] + int(H * 0.17)
        _paste_scaled(canvas, R["share"], (sx, sy), _ease_back((t - ts) / 0.3) * pulse)
        if R["share_emoji"] is not None and t >= ts + 0.3:   # the worm wiggles at the panel corner
            em = R["share_emoji"].rotate(12 * math.sin(2 * math.pi * 2.0 * (t - ts)), resample=Image.BICUBIC, expand=True)
            canvas.alpha_composite(em, (min(W - em.width - 6, sx + R["share"].width - em.width // 2),
                                        sy + R["share"].height - em.height // 2))
    return canvas.convert("RGB")
