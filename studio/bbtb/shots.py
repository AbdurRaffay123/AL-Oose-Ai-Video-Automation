"""Turn parsed script events into a shot list (pure logic, no I/O).

Rules (see CLAUDE.md "staging rules"):
  * every dialogue line -> one talking shot, one speaker on screen (shot/reverse-shot);
      pose tag -> medium full-body shot, expression-only tag -> close-up head shot;
      engine: LTX audio-to-video or fal Kling AI Avatar (`talking_engine:` header; the voice drives the mouth).
  * ACTION -> LTX image-to-video shot; characters named in the text are in the first frame,
      characters named in an `end: NAME pose` tag only appear in the last frame.
  * NARRATION before an ACTION rides on that action shot as voice-over; a lone narration
      line holds on the previous shot's keyframe (free local camera move).
  * SFX attaches to the start of the next shot.
  * scene END_CARD -> local end card. A narrator line tagged card:tease or card:book gets its own end-card moment
      (tease: Billy's face + the question; book: cover + CTA); emoji:<e> adds an on-screen emoji (never spoken).
"""
from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field

from .script_parser import Event, Script, name_index

LTX_I2V_DURATIONS = (6, 8, 10)          # ltx-2-3-pro allowed values
A2V_MAX_SECONDS = 20.0                  # ltx-2-3-pro audio-to-video at 720p/1080p
WAN_MAX_SECONDS = 15.0                  # Wan 2.7 image-to-video: duration 2-15 s
SPECIAL_SCENES = {"END_CARD"}
CARDS = {"tease", "book", "title", "versus", "rule"}  # END_CARD moments (tag card:<name>); title = the BBTB title video + text

STYLE = ("2D hand-drawn children's picture-book cartoon animation in exactly the same art style, "
         "colours and line work as the input image. Smooth, gentle, readable cartoon motion.")
LOCK = ("Keep every character's design exactly as in the input image: same costume, colours, "
        "proportions and accessories. No new characters, no text, no logos, no scene change.")


@dataclass
class OnScreen:
    char: str
    variant: str | None
    art: str                 # cut-out id
    framing: str             # wide | medium | closeup
    side: str                # left | right | center
    mirror: bool = False
    role: str = ""           # "with" = silent partner in a talking two-shot (script tag with: <NAME> <pose>)


@dataclass
class Shot:
    id: str
    kind: str                # talk | action | hold | endcard
    engine: str              # ltx_a2v | ltx_i2v | local_still | local_endcard
    scene: str
    cast: list[OnScreen] = field(default_factory=list)
    end_cast: list[OnScreen] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)       # line ids voiced during this shot
    sfx: list[dict] = field(default_factory=list)       # [{"name": "roar", "at": 4.0}]
    prompt: str = ""
    camera: str = "static"
    motion: list[str] = field(default_factory=list)      # local animation: enter-left, shake, pose:<art> ...
    source_line: int = 0
    duration: float = 0.0                                # filled once audio exists
    gen_seconds: float = 0.0                             # seconds billed by LTX / Kling
    prompt_key: str = ""                                 # Kling 3.0 template (library/kling_prompts.yaml)
    acting: str = ""                                     # performance words for Kling 3.0 prompts
    start_cast: list[OnScreen] | None = None             # Kling 3.0 action: first frame cast ([] = empty scene)
    zoom: float = 1.0                                    # camera push-in on the keyframe (tag zoom:<f>; composed sharp)
    min_secs: float = 0.0                                # tag secs:<s>: minimum on-screen seconds (local shots)
    cut: float = 0.0                                     # tag cut:<s>: use the generated clip up to <s>, then hold the
                                                         # drawn end frame (impact shake on the next SFX); free edit
    trim: float = 0.0                                    # seconds cut from the START of the generated clip in the
                                                         # edit (tag trim:<s>; free, never changes the paid request)
    reuse: str = ""                                      # tag reuse:<CLIP_ID>: plays a library clip (library/clips/)
    reuse_from: float = 0.0                              # tag from:<s>: start time inside the reused clip
    line_at: dict = field(default_factory=dict)          # voice-over start times {line id: s} (tag say:<s>)
    fx: str = ""                                         # tag fx:<name>: free local animation (localanim.py)
    fx_args: dict = field(default_factory=dict)          # bubble:/numbers:/ball:/billy:/burst: (localanim overlays)
    out: float = 0.0                                     # tag out:<s>: the shot ENDS at <s> of the source clip (hard cut
                                                         # to the next shot, no held still - owner 2026-10-06)
    place: str = ""                                      # tag pos:<x>/<top>/<h>[/air]: exact first-frame placement
    place_end: str = ""                                  # tag endpos:...: exact last-frame placement (EP004 dive)
    card: str = ""                                       # END_CARD moment: tease | book ("" = classic end card)
    card_text: str = ""                                  # the narrator line, also shown on screen
    emoji: str = ""                                      # on-screen only (tag emoji:<e>)
    backdrop: str = ""                                   # tease card: background plate (the previous scene)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Line:
    id: str
    speaker: str
    text: str
    direction: list[str]
    line_no: int
    source: str = "unmarked"


ENGINE_TAGS = {"local", "ltx", "kling", "kling3", "kling3std", "wan", "o3"}   # o3: Kling O3 on a kling3std action
# Kling 3.0 talking engines: Kling speaks the line, ElevenLabs Voice Changer re-voices it. Turbo, or Standard
# (owner 2026-10-05: Standard adds a negative prompt and an end frame; tag kling3std).
KLING3_TALK_ENGINES = ("kling3_talk", "kling3_talk_std")
KLING3_DURATIONS = range(3, 16)                          # Kling 3.0: 3-15 whole seconds
FX_KEYS = {"fx", "bubble", "numbers", "ball", "billy", "burst", "id", "say", "gen"}    # localanim.py tags (owner 2026-10-07)
MOTION_TAGS = {"enter-left", "enter-right", "shake", "far", "wide", "medium", "pass-left", "pass-right", "noend",
               "parallax", "loop", "creep-left", "creep-right"}


def acting_of(direction: list[str]) -> list[str]:
    """Direction words that describe the performance (engine/motion/framing tags removed)."""
    return [d for d in direction if d not in ENGINE_TAGS | MOTION_TAGS and ">" not in d
            and not d.lower().startswith("end:") and not d.lower().startswith("at ")
            and not d.lower().startswith("prompt:") and not d.lower().startswith("trim:")
            and not d.lower().startswith("with:") and not d.lower().startswith("zoom:")
            and not d.lower().startswith("card:") and not d.lower().startswith("emoji:")
            and not d.lower().startswith("cut:") and not d.lower().startswith("secs:") and d.lower() != "silent"
            and not d.lower().startswith("show:") and not d.lower().startswith("neg:") and d.lower() != "refs"
            and not d.lower().startswith("reuse:") and not d.lower().startswith("from:")
            and not d.lower().startswith("pos:") and not d.lower().startswith("endpos:")
            and not d.lower().startswith("backdrop:") and not d.lower().startswith("out:") and d.lower() != "over"
            and d.lower() != "avatar" and not d.lower().startswith("refvideo:") and not d.lower().startswith("never:")
            and not d.lower().split(":", 1)[0] in FX_KEYS]


def tag_value(direction: list[str], key: str) -> str:
    return next((d.split(":", 1)[1].strip() for d in direction if d.lower().startswith(key + ":")), "")


def prompt_tag(direction: list[str]) -> str:
    return next((d.split(":", 1)[1].strip() for d in direction if d.lower().startswith("prompt:")), "")


def zoom_of(direction: list[str]) -> float:
    return next((float(d.split(":", 1)[1]) for d in direction if d.lower().startswith("zoom:")), 1.0)


def trim_of(direction: list[str]) -> float:
    return next((float(d.split(":", 1)[1]) for d in direction if d.lower().startswith("trim:")), 0.0)


def secs_of(direction: list[str]) -> float:
    return next((float(d.split(":", 1)[1]) for d in direction if d.lower().startswith("secs:")), 0.0)


def cut_of(direction: list[str]) -> float:
    return next((float(d.split(":", 1)[1]) for d in direction if d.lower().startswith("cut:")), 0.0)


def line_id(e: Event) -> str:
    return f"L{e.line_no:03d}_{e.speaker}"


def lines_of(script: Script) -> list[Line]:
    return [Line(line_id(e), e.speaker, e.text, acting_of(e.direction), e.line_no, e.source)
            for e in script.events if e.kind in ("dialogue", "narration") and "silent" not in e.direction
            and not (e.kind == "dialogue" and tag_value(e.direction, "reuse"))]   # a reused talking clip brings its line


def _variant(char: dict, variant: str | None) -> dict:
    return char["variants"].get(variant or char.get("default_variant"), {})


def default_pose(char: dict, variant: str | None) -> str | None:
    poses = _variant(char, variant).get("poses", {})
    for preferred in ("34left", "34right", "front", "holding-scroll", "idle", "front-wave"):
        if preferred in poses:
            return poses[preferred]
    return next(iter(poses.values()), None)


def art_name(char: dict, variant: str | None, art: str) -> str | None:
    v = _variant(char, variant)
    for group in ("poses", "expressions"):
        for name, aid in v.get(group, {}).items():
            if aid == art:
                return name
    return None


def placement(char: dict, variant: str | None, art: str, framing: str) -> tuple[str, bool]:
    """(side, mirror): put a character on the third opposite to the way it faces, so it looks
    into the frame. Characters that may not be mirrored (Billy) are placed by their art."""
    if framing == "closeup":
        return "center", False
    facing = _variant(char, variant).get("facing", {}).get(art_name(char, variant, art), "front")
    if facing == "left":
        return "right", False
    if facing == "right":
        return "left", False
    return "center", False


def partner(words: str, chars: dict, index: dict[str, str], speaker: OnScreen, line_no: int) -> OnScreen:
    """'BILLY 34left' -> a silent partner on the speaker's opposite side (looking at the speaker)."""
    cid, pose_name = parse_end_tag(words, index)
    if cid is None:
        raise ValueError(f"line {line_no}: 'with:' must name a character, e.g. 'with: BILLY 34left'")
    variant = chars[cid].get("default_variant")
    art = _variant(chars[cid], variant).get("poses", {}).get(pose_name) or default_pose(chars[cid], variant)
    if art is None:
        raise ValueError(f"line {line_no}: {chars[cid]['display_name']} has no pose '{pose_name}'")
    side, mirror = placement(chars[cid], variant, art, "medium")
    if side == speaker.side or side == "center":
        side = "right" if speaker.side == "left" else "left"
    return OnScreen(cid, variant, art, speaker.framing, side, mirror, role="with")


def mentioned(text: str, index: dict[str, str]) -> list[str]:
    """Character ids named in free text, in order of appearance (longest names first)."""
    hits = []
    for name in sorted(index, key=len, reverse=True):
        for m in re.finditer(r"\b" + re.escape(name) + r"\b", text.upper()):
            hits.append((m.start(), index[name]))
    seen, out = set(), []
    for _, cid in sorted(hits):
        if cid not in seen and cid != "narrator":
            seen.add(cid)
            out.append(cid)
    return out


def parse_end_tag(words: str, index: dict[str, str]) -> tuple[str | None, str]:
    """'BIG GUY arms-up' -> ('big_guy', 'arms-up')."""
    up = words.strip().upper()
    for name in sorted(index, key=len, reverse=True):
        if up.startswith(name):
            return index[name], words.strip()[len(name):].strip().lower()
    return None, ""


def identity(chars: dict, cast: list[OnScreen]) -> str:
    parts = []
    for o in cast:
        v = _variant(chars[o.char], o.variant)
        if v.get("identity_prompt"):
            parts.append(f"{chars[o.char]['display_name']}: {v['identity_prompt'].strip()}.")
    return " ".join(parts)


def plan(script: Script, chars: dict) -> list[Shot]:
    index = name_index(chars)
    shots: list[Shot] = []
    pending_sfx: list[str] = []
    pending_narration: list[str] = []
    pending_at: dict[str, float] = {}
    def new_shot(**kw) -> Shot:
        s = Shot(id=f"S{len(shots) + 1:02d}", **kw)
        s.sfx, pending_sfx[:] = list(pending_sfx), []
        shots.append(s)
        return s

    def flush_narration(scene: str):
        if not pending_narration:
            return
        prev = next((s for s in reversed(shots) if s.scene == scene), None)
        hold = new_shot(kind="hold", engine="local_still", scene=scene,
                        cast=list(prev.cast) if prev else [], camera="push_in",
                        source_line=0)
        hold.lines, pending_narration[:] = list(pending_narration), []
        hold.zoom = prev.zoom if prev else 1.0          # the held frame keeps the shot's framing

    events = script.events
    for i, e in enumerate(events):
        nxt = next((x for x in events[i + 1:] if x.kind != "sfx"), None)

        if e.kind == "sfx":
            at, vol = 0.0, None
            for d in e.direction:
                m = re.match(r"at\s+([0-9.]+)$", d)
                if m:
                    at = float(m.group(1))
                v = re.match(r"vol\s+([0-9.]+)$", d)          # SFX [at 0.2, vol 0.1]: per-sound level (default 0.8)
                if v:
                    vol = float(v.group(1))
            pending_sfx.append({"name": e.text, "at": at, **({"vol": vol} if vol is not None else {})})
            continue
        if e.kind == "music":
            continue  # music changes are handled by the audio bed

        if e.scene in SPECIAL_SCENES:
            card = tag_value(e.direction, "card") if e.kind in ("narration", "dialogue") else ""
            if card:
                if card not in CARDS:
                    raise ValueError(f"line {e.line_no}: unknown end card '{card}' (use {', '.join(sorted(CARDS))})")
                s = new_shot(kind="endcard", engine="local_endcard", scene=e.scene, source_line=e.line_no)
                s.lines, s.card, s.card_text, s.emoji = [line_id(e)], card, e.text, tag_value(e.direction, "emoji")
                s.card_text = tag_value(e.direction, "show") or e.text   # show:<text> = on screen; the line is spoken
                if "silent" in e.direction:              # on screen only: no voice, so no new recording needed
                    s.lines = []
                s.min_secs = secs_of(e.direction)
                if tag_value(e.direction, "id"):
                    s.id = tag_value(e.direction, "id")
                s.backdrop = tag_value(e.direction, "backdrop") or next(                # tag backdrop:<SCENE>
                    (x.scene for x in reversed(shots) if x.scene not in SPECIAL_SCENES), "")
                continue
            if e.kind == "narration":
                pending_narration.append(line_id(e))
            if nxt is None or nxt.scene != e.scene or tag_value(nxt.direction, "card"):
                s = new_shot(kind="endcard", engine="local_endcard", scene=e.scene, source_line=e.line_no)
                s.lines, pending_narration[:] = list(pending_narration), []
            continue

        clip = tag_value(e.direction, "reuse") if e.kind in ("dialogue", "action") else ""
        if clip:                                         # free: an existing clip from library/clips/clips.yaml
            if e.kind == "dialogue":
                flush_narration(e.scene)
            s = new_shot(kind="talk" if e.kind == "dialogue" else "action",
                         engine="reuse_talk" if e.kind == "dialogue" else "reuse_clip", scene=e.scene, source_line=e.line_no)
            s.reuse = clip
            s.reuse_from = float(tag_value(e.direction, "from") or 0)
            s.min_secs = secs_of(e.direction)
            if e.kind == "dialogue":
                s.lines = [line_id(e)]
            else:
                s.lines, pending_narration[:] = list(pending_narration), []
            s.acting = e.text
            continue

        over = e.kind == "dialogue" and "over" in e.direction    # voice-over on the next action (owner 2026-10-07)
        if e.kind == "narration" or over:
            pending_narration.append(line_id(e))
            if tag_value(e.direction, "say"):
                pending_at[line_id(e)] = float(tag_value(e.direction, "say"))
            ahead = next((x for x in events[i + 1:] if x.kind not in ("sfx", "narration")
                          and not (x.kind == "dialogue" and "over" in x.direction)), None)
            if not (ahead and ahead.kind == "action" and ahead.scene == e.scene):   # several narration lines
                flush_narration(e.scene)                                           # may ride on one action
            continue

        if e.kind == "dialogue":
            flush_narration(e.scene)
            c = chars[e.speaker]
            v = _variant(c, e.variant)
            if e.pose:
                art, framing = v["poses"][e.pose], "medium"
            elif e.expression:
                art, framing = v["expressions"][e.expression], "closeup"
            else:
                art, framing = default_pose(c, e.variant), "medium"
            if art is None:
                raise ValueError(f"line {e.line_no}: {c['display_name']} ({e.variant}) has no art yet")
            side, mirror = placement(c, e.variant, art, framing)
            on = OnScreen(e.speaker, e.variant, art, framing, side, mirror)
            acting = ", ".join(x for x in [e.expression, *acting_of(e.direction)] if x) or "expressive"
            name = c["display_name"]
            prompt = (f"{STYLE} {identity(chars, [on])} {name} talks ({acting}), his mouth/beak opening and "
                      f"closing in time with the speech, with small natural head and body movements while "
                      f"he says: \"{e.text}\" Only {name} is speaking. The camera stays still. {LOCK}")
            engine = ("local_flap" if "local" in e.direction else "kling_avatar" if "kling" in e.direction
                      else "kling3_talk_std" if "kling3std" in e.direction
                      else "kling3_talk" if "kling3" in e.direction else "wan_talk" if "wan" in e.direction
                      else "ltx_a2v" if "ltx" in e.direction else script.meta.get("talking_engine", "ltx_a2v"))
            if engine in KLING3_TALK_ENGINES and framing == "closeup":
                # Kling 3.0 acts with the whole body: start from the full model-sheet pose that faces the same
                # way as the expression head (no pasted-together close-up); the expression goes into the prompt.
                face = v.get("facing", {}).get(e.expression or "", "front")
                body = (v.get("kling_body") or {}).get(face)
                if body:
                    art, framing = body, "medium"
                    side, mirror = placement(c, e.variant, art, framing)
                    on = OnScreen(e.speaker, e.variant, art, framing, side, mirror)
            cast = [on]
            for d in e.direction:                     # two-shot: a silent partner shares the frame
                m = re.match(r"with:\s*(.+)$", d, re.I)
                if m:
                    cast.append(partner(m.group(1), chars, index, on, e.line_no))
            s = new_shot(kind="talk", engine=engine, scene=e.scene, cast=cast, prompt=prompt,
                         source_line=e.line_no, motion=[d for d in e.direction if d in ("shake", "noend")])
            s.lines = [line_id(e)]
            s.acting = acting
            s.prompt_key = prompt_tag(e.direction) or f"talk_{e.speaker}"
            s.trim = trim_of(e.direction)
            s.cut = cut_of(e.direction)
            s.min_secs = secs_of(e.direction)
            s.zoom = zoom_of(e.direction)
            continue

        if e.kind == "action":
            framing = "far" if "far" in e.direction else "wide" if "wide" in e.direction else "medium"
            end_cast = []
            for d in e.direction:
                m = re.match(r"end:\s*(.+)$", d, re.I)
                if m:
                    cid, pose_name = parse_end_tag(m.group(1), index)
                    if cid is None:
                        raise ValueError(f"line {e.line_no}: 'end:' tag must start with a character name")
                    poses = _variant(chars[cid], None).get("poses", {})
                    art = poses.get(pose_name) or default_pose(chars[cid], None)
                    side, mirror = placement(chars[cid], None, art, framing)
                    end_cast.append(OnScreen(cid, None, art, framing, side, mirror))
            end_ids = {o.char for o in end_cast}
            cast = []
            for cid in mentioned(e.text, index):
                if cid in end_ids:
                    continue
                v = _variant(chars[cid], None)
                poses = v.get("poses", {})
                tagged = [d.split(">")[0] for d in e.direction if d.split(">")[0] in poses]
                art = poses[tagged[0]] if tagged else default_pose(chars[cid], None)
                if art:
                    side, mirror = placement(chars[cid], None, art, framing)
                    cast.append(OnScreen(cid, None, art, framing, side, mirror))
            if framing in ("wide", "far") and len(cast) + len(end_cast) == 1:
                for o in cast + end_cast:
                    o.side = "center"
            prompt = f"{STYLE} {identity(chars, cast + end_cast)} {e.text} {LOCK}"
            motion = [d for d in e.direction if d in ("enter-left", "enter-right", "shake", "pass-left", "pass-right",
                                                      "loop", "creep-left", "creep-right")]
            for d in e.direction:                       # pose change "a>b" for the first cast member
                if ">" in d and cast:
                    b = d.split(">", 1)[1].strip()
                    poses = _variant(chars[cast[0].char], cast[0].variant).get("poses", {})
                    if b not in poses:
                        raise ValueError(f"line {e.line_no}: unknown pose '{b}' for {chars[cast[0].char]['display_name']}")
                    motion.append(f"pose:{poses[b]}")
            engine = ("kling_avatar" if "avatar" in e.direction           # EP004 S01b: Avatar driven by a voice-over line
                      else "local_still" if "parallax" in e.direction        # free layered parallax (owner 2026-10-06)
                      else "local_anim" if "local" in e.direction else "kling3_action" if "kling3" in e.direction
                      else "ltx_i2v" if "ltx" in e.direction else script.meta.get("action_engine", "ltx_i2v"))
            if engine == "local_anim" and end_cast:
                raise ValueError(f"line {e.line_no}: 'end:' needs LTX (remove 'local') - local animation can't morph between frames")
            s = new_shot(kind="action", engine=engine, scene=e.scene, cast=cast, end_cast=end_cast,
                         prompt=prompt, source_line=e.line_no, motion=motion)
            s.lines, pending_narration[:] = list(pending_narration), []
            s.prompt_key = prompt_tag(e.direction) or "action"
            s.trim = trim_of(e.direction)
            s.cut = cut_of(e.direction)
            s.min_secs = secs_of(e.direction)
            s.zoom = zoom_of(e.direction)
            s.line_at = {lid: pending_at.pop(lid) for lid in s.lines if lid in pending_at}
            if tag_value(e.direction, "id"):                 # tag id:<ID> pins the shot id (paid clips, approvals)
                s.id = tag_value(e.direction, "id")
            s.place, s.place_end = tag_value(e.direction, "pos"), tag_value(e.direction, "endpos")
            s.out = float(tag_value(e.direction, "out") or 0)
            s.fx = tag_value(e.direction, "fx")
            s.fx_args = {k: tag_value(e.direction, k) for k in FX_KEYS - {"fx"} if tag_value(e.direction, k)}
            s.acting = e.text
            if engine == "kling3_action":
                # first frame -> last frame: an entrance starts on the empty scene and ends with the character
                # on its mark; a pose change "a>b" starts in pose a and ends in pose b.
                pose_to = next((m.split(":", 1)[1] for m in motion if m.startswith("pose:")), None)
                if any(m.startswith("enter-") for m in motion):
                    s.start_cast, s.end_cast = [], list(cast)
                elif pose_to and cast:
                    s.start_cast = list(cast)
                    s.end_cast = [OnScreen(**{**cast[0].__dict__, "art": pose_to})] + cast[1:]
                passing = next((m for m in motion if m.startswith("pass-")), None)
                if passing and s.end_cast:            # travel across the frame: start one side, end the other
                    a, b = ("left", "right") if passing == "pass-right" else ("right", "left")
                    s.start_cast = [OnScreen(**{**(s.start_cast or cast)[0].__dict__, "side": a})]
                    s.end_cast = [OnScreen(**{**s.end_cast[0].__dict__, "side": b})]
            continue

    flush_narration(events[-1].scene if events else "")
    if pending_sfx and shots:
        shots[-1].sfx += pending_sfx
    return shots


def apply_durations(shots: list[Shot], line_seconds: dict[str, float], pad: float = 0.25) -> None:
    """Set each shot's on-screen duration and LTX billable seconds from the voice audio lengths."""
    for s in shots:
        voiced = sum(line_seconds[l] for l in s.lines) + pad * len(s.lines)
        if s.engine in KLING3_TALK_ENGINES:
            s.gen_seconds = float(max(3, min(15, math.ceil(voiced - pad * len(s.lines) - 1e-6))))
            s.duration = round(s.gen_seconds - s.trim, 3)
        elif s.engine == "kling3_action":           # tag secs:<s> = minimum generated length (EP004 S07: a 5 s beat list)
            s.gen_seconds = float(max(3, min(15, math.ceil(max(voiced + pad, s.min_secs) - 1e-6))))
            if s.fx_args.get("gen"):                 # tag gen:<s>: force the generated length (owner: less time to drift)
                s.gen_seconds = float(max(3, min(15, int(float(s.fx_args["gen"])))))
            s.duration = round(s.gen_seconds - s.trim, 3)
            if s.out:                                # tag out:<s>: end the shot there (the paid request is unchanged)
                if not s.trim < s.out <= s.gen_seconds:
                    raise ValueError(f"{s.id}: out:{s.out:g} must be after trim:{s.trim:g} and within {s.gen_seconds:g} s")
                s.duration = round(s.out - s.trim, 3)
        elif s.engine == "wan_talk":                  # Wan 2.7: whole seconds 2-15, driven by the line audio
            s.duration = round(voiced + pad, 2)
            s.gen_seconds = float(max(2, math.ceil(voiced - pad * len(s.lines) - 1e-6)))
            if s.gen_seconds > WAN_MAX_SECONDS:
                raise ValueError(f"{s.id}: line is {s.gen_seconds:.0f}s; Wan 2.7 allows at most "
                                 f"{WAN_MAX_SECONDS:.0f}s. Split the line in the script.")
        elif s.engine == "kling_avatar" and s.kind == "action" and s.line_at:   # driven by a timed voice-over line
            end = max([(s.line_at.get(l, 0.15) + line_seconds[l]) for l in s.lines] + [s.min_secs])
            s.duration = round(end + pad, 2)
            s.gen_seconds = s.duration
        elif s.engine in ("ltx_a2v", "kling_avatar"):
            s.duration = round(voiced + pad, 2)
            s.gen_seconds = s.duration
            if s.gen_seconds > A2V_MAX_SECONDS:
                raise ValueError(f"{s.id}: line is {s.gen_seconds:.1f}s; talking shots allow at most "
                                 f"{A2V_MAX_SECONDS:.0f}s. Split the line in the script.")
        elif s.engine == "ltx_i2v":
            need = max(voiced + pad, 3.0)
            s.gen_seconds = next((d for d in LTX_I2V_DURATIONS if d >= need), LTX_I2V_DURATIONS[-1])
            s.duration = round(min(need, s.gen_seconds) if need <= s.gen_seconds else need, 2)
        elif s.engine == "local_endcard" and s.card and not s.lines:   # silent card: secs:<s>, else reading time
            s.duration = s.min_secs or round(max(2.5, len(s.card_text.split()) / 3.5 + 0.8), 2)
        elif s.engine == "local_endcard" and s.card == "tease":
            s.duration = round(max(voiced + 0.5, 2.0, s.min_secs), 2)
        elif s.engine == "local_endcard":
            s.duration = round(max(voiced + 0.8, 4.0 if s.card else 3.5, s.min_secs), 2)
        elif s.engine == "local_anim":
            s.duration = round(max(voiced + pad, 2.0, s.min_secs), 2)
        elif s.engine in ("reuse_clip", "reuse_talk"):    # pipeline caps this to what the clip offers
            s.duration = round(max(voiced + pad, 1.0, s.min_secs), 2)
        else:
            s.duration = round(max(voiced + pad, 1.5), 2)
        if s.trim and (not s.engine.startswith("kling3") or s.duration < (0.5 if s.out else 1.0)):  # out: = cut on the action
            raise ValueError(f"{s.id}: trim:{s.trim:g} only works on Kling 3.0 shots and must leave at least 1 s")
