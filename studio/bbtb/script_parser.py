"""Parse the owner's script.md into structured events.

Format:
    # EP001 Title
    format: 9:16   resolution: 720p   music: playful-adventure   budget: 10
    ## SCENE BIG_WORM_HOLE
    ACTION: Billy hops in from the left.
    BILLY [tophat, scroll-reading]: (muttering) Silly little worm!
    NARRATOR: Then deep from below came a great rumbling sound...
    SFX: rumble
    MUSIC: tense

Speaker names resolve to character ids through each character's id, display_name and aliases.
Tags in [...] are classified per character as variant / pose / expression; anything else is
kept as acting direction. A leading (parenthetical) is also acting direction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .paths import CHARACTERS

HEADER_KEYS = {"format", "resolution", "music", "budget", "fps", "captions", "model", "talking_engine", "negatives", "keyframes", "elements", "bg_element", "shot_cap",
               "action_engine", "spend_cap", "session_cap"}
TALKING_ENGINES = {"ltx": "ltx_a2v", "ltx_a2v": "ltx_a2v", "kling": "kling_avatar", "kling_avatar": "kling_avatar",
                   "kling3": "kling3_talk", "kling3_talk": "kling3_talk",
                   "kling3std": "kling3_talk_std", "kling3_talk_std": "kling3_talk_std", "wan": "wan_talk", "wan_talk": "wan_talk"}
ACTION_ENGINES = {"ltx": "ltx_i2v", "ltx_i2v": "ltx_i2v", "kling3": "kling3_action", "kling3_action": "kling3_action"}
DEFAULTS = {"format": "9:16", "resolution": "720p", "music": None, "budget": 10.0, "fps": 24,
            "captions": "off", "model": "ltx-2-3-pro", "talking_engine": "ltx_a2v",
            "action_engine": "ltx_i2v", "spend_cap": None, "session_cap": 1.0, "negatives": None, "keyframes": None, "elements": None, "bg_element": None, "shot_cap": None}


class ScriptError(ValueError):
    """A problem in the script, reported with its line number in plain language."""


@dataclass
class Event:
    kind: str                      # dialogue | narration | action | sfx | music
    line_no: int
    scene: str
    text: str
    speaker: str | None = None     # character id
    variant: str | None = None
    pose: str | None = None
    expression: str | None = None
    direction: list[str] = field(default_factory=list)
    source: str = "unmarked"       # canon:<page> | adapted:<page> | production | unmarked


SOURCE_RE = re.compile(r"^(canon|adapted|production)(:\s*\S.*)?$", re.I)


@dataclass
class Script:
    title: str
    meta: dict
    events: list[Event]
    path: Path | None = None

    @property
    def scenes(self) -> list[str]:
        seen = []
        for e in self.events:
            if e.scene not in seen:
                seen.append(e.scene)
        return seen


def load_characters() -> dict[str, dict]:
    return {p.stem: yaml.safe_load(p.read_text()) for p in sorted(CHARACTERS.glob("*.yaml"))}


def name_index(characters: dict[str, dict]) -> dict[str, str]:
    idx = {}
    for cid, c in characters.items():
        names = [cid, cid.replace("_", " "), c.get("display_name", "")] + c.get("aliases", [])
        for n in names:
            if n:
                idx[n.upper()] = cid
    return idx


def classify_tags(char: dict, tags: list[str]) -> tuple[str, str | None, str | None, list[str]]:
    variant = char.get("default_variant")
    variants = char.get("variants", {})
    for t in tags:
        if t in variants:
            variant = t
    v = variants.get(variant, {})
    pose = expression = None
    direction = []
    for t in tags:
        if t in variants:
            continue
        if t in v.get("poses", {}):
            pose = t
        elif t in v.get("expressions", {}):
            expression = t
        else:
            direction.append(t)
    return variant, pose, expression, direction


LINE_RE = re.compile(r"^(?P<name>[A-Z][A-Z0-9 _'.-]*?)\s*(?:\[(?P<tags>[^\]]*)\])?\s*:\s*(?P<text>.*)$")


def parse(text: str, path: Path | None = None, characters: dict | None = None) -> Script:
    characters = characters if characters is not None else load_characters()
    names = name_index(characters)
    title, meta, events, scene = "Untitled", dict(DEFAULTS), [], None

    for no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("<!--") or line.startswith("//"):
            continue
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            continue
        if line.upper().startswith("## SCENE"):
            scene = line[len("## SCENE"):].strip().strip(":").strip()
            if not scene:
                raise ScriptError(f"line {no}: '## SCENE' needs a background name, e.g. '## SCENE BIG_WORM_HOLE'")
            continue
        header = dict(re.findall(r"(\w+):\s*([^\s]+)", line))
        if header and set(header) <= HEADER_KEYS and scene is None:
            meta.update(header)
            continue

        m = LINE_RE.match(line)
        if not m:
            raise ScriptError(f"line {no}: can't read this line. Expected 'NAME: text', 'ACTION: ...' or 'SFX: ...'.\n  > {raw}")
        if scene is None:
            raise ScriptError(f"line {no}: put a '## SCENE <BACKGROUND>' heading before the first line of the story")
        name, tags_s, body = m["name"].strip().upper(), m["tags"] or "", m["text"].strip()
        tags = [t.strip() for t in tags_s.split(",") if t.strip()]
        source = next((t for t in tags if SOURCE_RE.match(t)), "unmarked").lower()
        tags = [t for t in tags if not SOURCE_RE.match(t)]
        direction = []
        pm = re.match(r"^\(([^)]*)\)\s*(.*)$", body)
        if pm:
            direction.append(pm.group(1).strip())
            body = pm.group(2).strip()
        if not body:
            raise ScriptError(f"line {no}: '{name}' has no text after the colon")

        if name in ("ACTION", "SFX", "MUSIC"):
            events.append(Event(kind=name.lower(), line_no=no, scene=scene, text=body, direction=tags + direction,
                                source=source))
            continue
        cid = names.get(name)
        if cid is None:
            known = ", ".join(sorted({c.get('display_name', k).upper() for k, c in characters.items()}))
            raise ScriptError(f"line {no}: unknown character '{name}'. Known: {known}")
        variant, pose, expression, extra = classify_tags(characters[cid], tags)
        kind = "narration" if cid == "narrator" else "dialogue"
        events.append(Event(kind=kind, line_no=no, scene=scene, text=body, speaker=cid, variant=variant,
                            pose=pose, expression=expression, direction=extra + direction, source=source))

    try:
        meta["budget"] = float(meta["budget"])
        meta["fps"] = int(meta["fps"])
        meta["session_cap"] = float(meta["session_cap"])
        if meta["spend_cap"] is not None:
            meta["spend_cap"] = float(meta["spend_cap"])
        if meta["shot_cap"] is not None:
            meta["shot_cap"] = float(meta["shot_cap"])
    except ValueError as exc:
        raise ScriptError(f"header: budget must be a number of dollars and fps a whole number ({exc})") from None
    if meta["format"] not in ("9:16", "16:9"):
        raise ScriptError("header: format must be 9:16 or 16:9 (the only shapes LTX can generate)")
    if str(meta["talking_engine"]) not in TALKING_ENGINES:
        raise ScriptError("header: talking_engine must be ltx, kling or kling3")
    meta["talking_engine"] = TALKING_ENGINES[str(meta["talking_engine"])]
    if str(meta["action_engine"]) not in ACTION_ENGINES:
        raise ScriptError("header: action_engine must be ltx or kling3")
    meta["action_engine"] = ACTION_ENGINES[str(meta["action_engine"])]
    if meta["resolution"] not in ("720p", "1080p"):
        raise ScriptError("header: resolution must be 720p or 1080p")
    if not events:
        raise ScriptError("the script has no lines")
    return Script(title=title, meta=meta, events=events, path=path)


def parse_file(path: Path) -> Script:
    return parse(Path(path).read_text(), path=Path(path))
