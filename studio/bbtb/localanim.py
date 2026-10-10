"""Free local animation built only from Jason's art (EP004, owner 2026-10-07), plus overlays on paid clips.

Shots tagged `fx:<name>` render here instead of the generic animator:
- `worms_play`  the four naughty worms at the landing spot (GRASS_STUMP): bobbing, the blue ball arcing between them;
- `worms_panic` same spot and scale: the ball freezes, drops; they tremble and hop in place (they stay: the count
                needs all four);
- `oak_tilt`    crane up the oak trunk (BG_OAK_TREEHOUSE) to Billy poised by the treehouse (S04's start framing),
                monocle glint, then a comic "WATCH OUT!!!!" burst.
Overlays on paid Kling clips (after fitting, on the shot's own timeline): `bubble:<text>@<t>[@x/y/tail]`,
`numbers:<n>@<t>|...@x<X>/y<Y>/pop<P>`, `ball:stop@<t>`. Every standing figure gets a contact shadow under its soles.
"""
from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import grounding, keyframes

FPS = 24
FONT = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
WORM_H = 0.48 * 0.40                       # worms = 0.40 of standing Billy (continuity board)
WORMS = [("worm_ball_kid", 0.20, 0.75, 1.05), ("worm_bow", 0.40, 0.635, 0.92),
         ("worm_tophat", 0.62, 0.645, 1.02), ("worm_cap", 0.84, 0.635, 0.85)]


def _scaled(art_id: str, h_px: int) -> Image.Image:
    im = keyframes.cutout(art_id)
    return im.resize((max(1, round(im.width * h_px / im.height)), h_px), Image.LANCZOS)


def _shadow_under(canvas: Image.Image, art: Image.Image, x: int, top: int, lift: int = 0) -> None:
    pts = grounding.soles(art, x, top)
    if not pts:
        return
    xs = [p[0] for p in pts]
    w = int(max((max(xs) - min(xs)) * 1.35, art.width * 0.35) * (1 - min(lift, 60) / 120))
    keyframes._shadow(canvas, int(sum(xs) / len(xs)), max(p[1] for p in pts) + 2 + lift, w)


def _encode(frames, size, dst: Path) -> Path:
    W, H = size
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(dst)],
                         stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()
    if p.returncode:
        raise RuntimeError(f"encode failed: {dst}")
    return dst


def _worm_layers(size):
    W, H = size
    return [(_scaled(a, int(WORM_H * s * H)), cx, feet) for a, cx, feet, s in WORMS]


def _ball(size):
    return _scaled("prop_blue_ball", int(0.045 * size[1]))


def worms_play(size, seconds):
    W, H = size
    bg = keyframes.plate("GRASS_STUMP", size).convert("RGBA")
    worms, ball = _worm_layers(size), _ball(size)
    kid, bow = worms[0], worms[1]
    for i in range(round(seconds * FPS)):
        t = i / FPS
        c = bg.copy()
        for k, (art, cx, feet) in enumerate(worms):
            hop = max(0.0, math.sin(2 * math.pi * 1.6 * t + k * 1.3)) * 10        # happy little bounces
            sq = 1 + 0.05 * math.sin(2 * math.pi * 3.2 * t + k)                  # squash and stretch
            a = art.resize((art.width, max(1, int(art.height * sq))), Image.LANCZOS)
            x, top = int(cx * W - a.width / 2), int(feet * H - a.height - hop)
            _shadow_under(c, a, x, top, lift=int(hop))
            c.alpha_composite(a, (x, top))
        p = (t * 0.9) % 1.0                                                     # ball arcs kid <-> bow
        go = int(t * 0.9) % 2 == 0
        x0, x1 = (kid[1], bow[1]) if go else (bow[1], kid[1])
        bx = (x0 + (x1 - x0) * p) * W
        by = (0.56 - 0.13 * math.sin(math.pi * p)) * H
        b = ball.rotate(-360 * p * (1 if go else -1), resample=Image.BICUBIC)
        c.alpha_composite(b, (int(bx - b.width / 2), int(by - b.height / 2)))
        yield c


def worms_panic(size, seconds):
    W, H = size
    bg = keyframes.plate("GRASS_STUMP", size).convert("RGBA")
    worms, ball = _worm_layers(size), _ball(size)
    for i in range(round(seconds * FPS)):
        t = i / FPS
        c = bg.copy()
        for k, (art, cx, feet) in enumerate(worms):
            jit = 4 * math.sin(2 * math.pi * 14 * t + k * 2.1)                   # trembling
            hop = abs(math.sin(2 * math.pi * 2.4 * t + k * 0.9)) * 18 if t > 0.35 else 0.0
            x, top = int(cx * W - art.width / 2 + jit), int(feet * H - art.height - hop)
            _shadow_under(c, art, x, top, lift=int(hop))
            c.alpha_composite(art.rotate(6 * math.sin(2 * math.pi * 5 * t + k), resample=Image.BICUBIC), (x, top))
        if t < 0.35:                                                            # the ball freezes mid-air...
            by = 0.47 * H
        else:                                                                   # ...then drops and bounces
            u = t - 0.35
            by = min(0.75 * H - ball.height / 2, 0.47 * H + 0.5 * 2600 * u * u)
        c.alpha_composite(ball, (int(0.30 * W - ball.width / 2), int(by - ball.height / 2)))
        yield c


def _star(size_px: int, alpha: float) -> Image.Image:
    im = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r = size_px / 2, size_px / 2
    for ang in (0, 90):
        a = math.radians(ang)
        d.polygon([(c + r * math.cos(a), c + r * math.sin(a)), (c + 0.12 * r * math.cos(a + 1.57), c + 0.12 * r * math.sin(a + 1.57)),
                   (c - r * math.cos(a), c - r * math.sin(a)), (c - 0.12 * r * math.cos(a + 1.57), c - 0.12 * r * math.sin(a + 1.57))],
                  fill=(255, 255, 255, int(255 * alpha)))
    return im.filter(ImageFilter.GaussianBlur(0.8))


def burst(size, text: str, scale: float, cy_frac: float = 0.40) -> Image.Image:
    """Comic 'WATCH OUT!!!!' burst (local only: never inside an AI shot)."""
    W, H = size
    s = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    cx, cy, R = W / 2, cy_frac * H, 0.42 * W * scale
    pts = []
    for k in range(28):
        a = 2 * math.pi * k / 28
        rr = R if k % 2 == 0 else R * 0.72
        pts.append((cx + rr * math.cos(a), cy + rr * 0.62 * math.sin(a)))
    d.polygon(pts, fill=(255, 214, 0, 255), outline=(200, 30, 30, 255))
    d.line(pts + pts[:1], fill=(200, 30, 30, 255), width=8)
    f = ImageFont.truetype(FONT, int(0.105 * W * scale))
    d.multiline_text((cx, cy), text.replace(" ", "\n", 1), font=f, fill=(200, 20, 20), anchor="mm", align="center",
                     stroke_width=4, stroke_fill="white")
    return s


def oak_tilt(size, seconds, billy_place: str, burst_at: float, text: str = "WATCH OUT!!!!"):
    """Crane UP the oak trunk to Billy poised by the treehouse; ends EXACTLY on S04's start framing.
    Tilts over the full-resolution book page 12 (BG_OAK_TREEHOUSE is its window x 0-832, y 380-1860), starting
    320 px lower (the door at the bottom edge; the book's painted Snail stays below the frame)."""
    from . import bgplates
    W, H = size
    page = bgplates.book_page("book.bad-billy-the-bird-story", 12).convert("RGBA")
    X0, Y_END, CW, CH = 0, 380, 832, 1480                                       # BG_OAK_TREEHOUSE window
    Y_START = 700
    x, y, h, _ = keyframes.parse_place(billy_place)
    billy = _scaled("billy_tophat_landing_approach1", int(h * CH))
    bx, by = int(X0 + x * CW - billy.width / 2), int(Y_END + y * CH)
    page.alpha_composite(billy, (bx, by))
    mono = (bx + int(0.80 * billy.width), by + int(0.50 * billy.height))         # monocle, LEFT eye (as drawn)
    move = max(0.01, burst_at - 0.65)                                           # the tilt, then the glint, then the burst
    for i in range(round(seconds * FPS)):
        t = i / FPS
        u = min(1.0, t / move)
        e = u * u * (3 - 2 * u)
        z = 1.12 - 0.12 * e
        cw, ch = CW / z, CH / z
        top = Y_START + (Y_END - Y_START) * e + (CH - ch) / 2
        left = X0 + (CW - cw) / 2
        fr = page.crop((int(left), int(top), int(left + cw), int(top + ch))).resize(size, Image.LANCZOS)
        if burst_at - 0.6 <= t < burst_at:                                      # the monocle glints
            k = 1 - abs((t - (burst_at - 0.3)) / 0.3)
            st = _star(int(90 * (0.6 + k)), max(0.0, k))
            mx, my = (mono[0] - left) / cw * W, (mono[1] - top) / ch * H
            fr.alpha_composite(st, (int(mx - st.width / 2), int(my - st.height / 2)))
        if t >= burst_at:
            k = min(1.0, (t - burst_at) / 0.12)
            sc = 1.35 - 0.35 * k + 0.03 * math.sin(2 * math.pi * 3 * (t - burst_at))
            if t < burst_at + 0.06:
                fr.alpha_composite(Image.new("RGBA", size, (255, 255, 255, 120)))
            fr.alpha_composite(burst(size, text, sc, cy_frac=0.64))
        yield fr


def render_fx(shot, size, dst: Path) -> Path:
    tags = shot.fx_args
    if shot.fx == "opening":                    # EP004 S01: worms play at the spot (2.5 s) | cut | oak crane-up (rest)
        import itertools
        part2 = shot.duration - 2.5
        return _encode(itertools.chain(worms_play(size, 2.5),
                                       oak_tilt(size, part2, tags.get("billy", "0.36/0.16/0.24/air"),
                                                float(tags.get("burst", part2 - 0.45)))), size, dst)
    if shot.fx == "worms_play":
        return _encode(worms_play(size, shot.duration), size, dst)
    if shot.fx == "worms_panic":
        return _encode(worms_panic(size, shot.duration), size, dst)
    if shot.fx == "oak_tilt":
        return _encode(oak_tilt(size, shot.duration, tags.get("billy", "0.36/0.16/0.24/air"),
                                float(tags.get("burst", shot.duration - 0.45))), size, dst)
    raise ValueError(f"{shot.id}: unknown fx:{shot.fx}")


# ---------------------------------------------------------------- overlays on fitted paid clips (shot timeline)
def _numbers(spec: str):
    """'1@1.625|2@2.042|3@2.542|4!@2.875@x0.85/y0.66/pop1.4' -> ([(text, t)], x, y, pop)."""
    x, y, pop = 0.85, 0.66, 1.4
    items = []
    for part in spec.split("|"):
        bits = part.split("@")
        items.append((bits[0], float(bits[1])))
        if len(bits) > 2:
            for kv in bits[2].split("/"):
                k, v = kv[0] if not kv.startswith("pop") else "pop", kv[1:] if not kv.startswith("pop") else kv[3:]
                x, y, pop = (float(v), y, pop) if k == "x" else (x, float(v), pop) if k == "y" else (x, y, float(v))
    return items, x, y, pop


def overlay(shot, clip: Path, size, dst: Path) -> Path:
    W, H = size
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    nums = _numbers(shot.fx_args["numbers"]) if "numbers" in shot.fx_args else None
    bub = shot.fx_args.get("bubble")
    ball = shot.fx_args.get("ball")
    ball_img = _ball(size) if ball else None

    def gen():
        for i, f in enumerate(frames):
            t = i / FPS + 1e-6
            im = Image.fromarray(f).convert("RGBA")
            if nums:
                items, nx, ny, pop = nums
                cur = [(n, t0) for n, t0 in items if t >= round(t0 * FPS) / FPS]
                if cur:
                    n, t0 = cur[-1]
                    t0 = round(t0 * FPS) / FPS
                    k = min(1, (t - t0) / 0.12)
                    sc = pop - (pop - 1) * k if k < 1 else 1 + 0.03 * math.sin(2 * math.pi * 2 * (t - t0))
                    lay = Image.new("RGBA", size, (0, 0, 0, 0))
                    ImageDraw.Draw(lay).text((int(nx * W), int(ny * H)), n, font=ImageFont.truetype(FONT, int(0.2 * W * sc)),
                                             fill="white", stroke_width=10, stroke_fill=(214, 60, 120), anchor="mm")
                    im.alpha_composite(lay)
            if bub:
                text, t0, where = _bubble_args(bub)
                if t >= t0:
                    k = min(1, (t - t0) / 0.12)
                    sc = where.get("s", 1.0) * (1.25 - 0.25 * k)
                    im.alpha_composite(bubble(size, text, sc, **{a: v for a, v in where.items() if a != "s"}))
            if ball:
                t_stop = float(ball.split("@")[1])
                fx, feet = 0.40, 0.66                                       # stops just left of Billy's sneakers
                u = min(1.0, t / t_stop)
                e = 1 - (1 - u) ** 2
                bx = (-0.06 + (fx + 0.06) * e) * W
                r = ball_img.width / 2
                rot = -math.degrees((bx + 0.06 * W) / r)
                b = ball_img.rotate(rot, resample=Image.BICUBIC)
                keyframes._shadow(im, int(bx), int(feet * H), int(ball_img.width * 1.1))
                im.alpha_composite(b, (int(bx - b.width / 2), int(feet * H - b.height)))
            yield im
    return _encode(gen(), size, dst)


def _bubble_args(tag: str) -> tuple[str, float, dict]:
    """`<text>@<t>[@x<cx>/y<cy>/s<scale>/tail<tx>/<ty>]` (fractions of the frame). EP004 S02 (owner 2026-10-07): the
    bubble sits left of the Snail's head, clear of his eyes and hat and inside the 4:5 safe area (y 0.15-0.85), its
    tail pointing at his head."""
    text, t0, *rest = tag.split("@")
    where = {}
    if rest:
        spec = rest[0].replace("/tail", " tail").replace("/y", " y").replace("/s", " s")
        for part in re.findall(r"(x|y|s|tail)([0-9.]+(?:/[0-9.]+)?)", spec):
            key, val = part
            if key == "tail":
                where["tail"] = tuple(float(v) for v in val.split("/"))
            else:
                where[key] = float(val.split("/")[0])
    return text, float(t0), where


def bubble(size, text: str, scale: float = 1.0, x: float = 0.62, y: float = 0.30,
           tail: tuple[float, float] = (0.47, 0.47)) -> Image.Image:
    """Book-style speech bubble (p.14 'WATCH OUT!!!!'): white ellipse centred at (x, y), tail toward `tail`; the
    ellipse and tail are one shape with one dark outline (no seam)."""
    W, H = size
    f = ImageFont.truetype(FONT, int(0.085 * W * scale))
    cx, cy = x * W, y * H
    words = text.replace(" ", "\n", 1)
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = probe.multiline_textbbox((cx, cy), words, font=f, anchor="mm", align="center")
    pad = 34 * scale
    l, t, r, b = l - pad, t - pad, r + pad, b + pad
    ax, ay = (r - l) / 2, (b - t) / 2
    tx, ty = tail[0] * W, tail[1] * H
    th = math.atan2((ty - cy) / ay, (tx - cx) / ax)
    base = [(cx + 0.92 * ax * math.cos(th + d), cy + 0.92 * ay * math.sin(th + d)) for d in (-0.22, 0.22)]
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((l, t, r, b), fill=255)
    md.polygon([base[0], base[1], (tx, ty)], fill=255)
    edge = mask.filter(ImageFilter.MaxFilter(7))
    s = Image.new("RGBA", size, (0, 0, 0, 0))
    s.paste((20, 20, 20, 255), (0, 0), edge)
    s.paste((255, 255, 255, 255), (0, 0), mask)
    ImageDraw.Draw(s).multiline_text((cx, cy), words, font=f, fill=(200, 20, 20), anchor="mm", align="center")
    return s
