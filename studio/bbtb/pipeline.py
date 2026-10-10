"""`bbtb make <script>`: script -> finished video, with ONE approval before any paid generation.

Run 1 (free):  parse -> voices -> keyframes -> pre-flight -> cost table + approval code -> storyboard animatic.
Run 2:         `--approve CODE` -> Kling 3.0 / LTX shots -> re-voice Kling talking shots (ElevenLabs Voice
               Changer) -> music/SFX -> assemble -> QA -> exports (+ captions .srt, never burned in).
The approval code is a hash of the exact jobs and budget, so any change to the script, art or
settings produces a new code (old approvals can never authorise different spend).
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from . import animate, assemble, localanim, audio_bed, clip_qa, clipfix, cliplib, review, elevenlabs, fal, keyframes, ltx, media, preflight, qa, references, revoice, voices
from .ledger import ACTIVE, Ledger
from .paths import DERIVED, LIBRARY, PRODUCTIONS
DERIVED_CUTOUTS = DERIVED / "cutouts"
from .script_parser import Script, load_characters, parse_file
from . import shots as shots_mod
from .shots import SPECIAL_SCENES, Shot, apply_durations, lines_of, plan


@dataclass
class Production:
    script: Script
    root: Path
    chars: dict
    shots: list[Shot]
    lines: dict
    size: tuple[int, int]
    ledger: Ledger

    @property
    def total(self) -> float:
        return round(sum(s.duration for s in self.shots), 3)


def apply_retimed(root: Path, lines: dict) -> None:
    """audio/retimed.yaml {exact line text: wav}: a free re-timing of an approved recording (slices of the same audio
    with pauses added, e.g. EP004's count so each CHOMP gets its own number). The original slice stays untouched."""
    cfg = root / "audio" / "retimed.yaml"
    if not cfg.exists():
        return
    table = yaml.safe_load(cfg.read_text()) or {}
    for lid, e in lines.items():
        wav = table.get(e.get("text", ""))
        if wav and e.get("final") and (root / "audio" / wav).exists():
            p = root / "audio" / wav
            lines[lid] = {**e, "path": str(p), "seconds": media.duration(p), "retimed_from": e.get("path")}


def prepare(script_path: Path, placeholder_voices: bool = False) -> Production:
    """Free: never calls a paid API. Raises voices.VoicesNotReady if speech still has to be generated
    (unless placeholder_voices - an explicit, never-final timing preview)."""
    script = parse_file(script_path)
    root = Path(script_path).resolve().parent
    chars = load_characters()
    led = Ledger(root / "ledger.jsonl")
    lines = voices.render_lines(lines_of(script), chars, root / "audio", led,
                                allow_paid=False, placeholder=placeholder_voices)
    apply_retimed(root, lines)
    shots = plan(script, chars)
    previous = None
    for s in shots:                                    # scene types -> a concrete background (never twice in a row)
        if s.scene not in SPECIAL_SCENES:
            s.scene = keyframes.resolve_scene(s.scene, previous)
            previous = s.scene
    for s in shots:                                    # reused talking clips bring their own approved line audio
        if s.engine == "reuse_talk":
            e = cliplib.entry(s.reuse)
            ev = next(x for x in script.events if x.line_no == s.source_line)
            audio, lead = cliplib.talk_audio(e, ev.text)
            dst = root / "audio" / "reused" / f"{s.lines[0]}.wav"
            dst.parent.mkdir(parents=True, exist_ok=True)
            ms = int(lead * 1000)
            media.ffmpeg("-i", str(audio), "-af", f"adelay={ms}|{ms}", "-ac", "1", "-ar", "48000", str(dst))
            lines[s.lines[0]] = {"path": str(dst), "seconds": media.duration(dst), "text": ev.text, "final": True,
                                 "speaker": ev.speaker, "source": f"reused clip audio ({s.reuse})",
                                 "line_source": ev.source}
    apply_durations(shots, {k: v["seconds"] for k, v in lines.items()})
    edits = clipfix.spec(root)                         # clip_fixes.yaml `edit:` sets the shot's on-screen length
    for s_ in shots:
        if (edits.get(s_.id) or {}).get("edit"):
            s_.duration = clipfix.edit_seconds(edits[s_.id]["edit"])
    for s in shots:                                    # a reused clip can't run longer than its usable window
        if s.engine in ("reuse_clip", "reuse_talk"):
            e = cliplib.entry(s.reuse)
            a, b = cliplib.window(e, s.reuse_from)
            if s.engine == "reuse_talk":
                s.duration = round(min(lines[s.lines[0]]["seconds"] + 0.2, b - a), 2)
            elif s.duration > (b - a) * cliplib.MAX_SLOW + 1e-6:
                raise ValueError(f"{s.id}: {s.reuse} offers {b - a:.1f}s (up to {(b - a) * cliplib.MAX_SLOW:.1f}s slowed) "
                                 f"but the narration needs {s.duration:.1f}s: split the narration or pick a longer clip")
    size = keyframes.out_size(script.meta["format"], script.meta["resolution"])
    prod = Production(script, root, chars, shots, lines, size, led)
    locked = script.meta.get("keyframes") == "locked"   # finished episode: keep the exact frames its paid clips used
    for s in shots:
        first, last = frame_paths(prod, s)
        if locked and first.exists() and (not s.end_cast or last.exists()) and s.engine != "local_endcard":
            continue
        if s.engine in ("reuse_clip", "reuse_talk"):
            cliplib.frame(cliplib.entry(s.reuse), cliplib.window(cliplib.entry(s.reuse), s.reuse_from)[0], first)
        elif s.engine == "local_endcard" and s.card:      # moment: the keyframe is its last (complete) frame
            keyframes.save(keyframes.card_frame(s, keyframes.card_layers(s, chars, size), s.duration), first)
        elif s.engine == "local_endcard":
            keyframes.save(keyframes.end_card(size), first)
        else:
            start = s.start_cast if s.start_cast is not None else s.cast     # [] = the empty scene
            keyframes.save(keyframes.compose(s.scene, start, chars, size, s.zoom, place=s.place), first)
            if s.end_cast:
                keyframes.save(keyframes.compose(s.scene, s.end_cast, chars, size, s.zoom, place=s.place_end), last)
    return prod


def frame_paths(prod: Production, s: Shot) -> tuple[Path, Path]:
    d = prod.root / "keyframes"
    return d / f"{s.id}_first.jpg", d / f"{s.id}_last.jpg"


def kling_prompt(chars: dict, on) -> str:
    """The owner's fixed prompt template for this character (library/kling_prompts.yaml)."""
    cfg = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    tpl = (cfg.get("characters") or {}).get(on.char)
    if not tpl:
        raise RuntimeError(f"no Kling prompt template for {on.char}: add one to library/kling_prompts.yaml")
    face = preflight.facing_of(chars[on.char], on)
    return " ".join(tpl.split()).replace("{facing}", cfg["facing_words"][face])


def upload_audio(src: Path, dst: Path, keep_lead: bool = False) -> dict:
    """Trimmed, -16 LUFS upload copy of a line (cached by the source's hash). keep_lead: a timed driver track whose
    leading silence is intentional (Avatar action shots)."""
    meta = dst.with_suffix(".json")
    sha = hashlib.sha256(src.read_bytes()).hexdigest() + (":lead" if keep_lead else "")
    if dst.exists() and meta.exists():
        info = json.loads(meta.read_text())
        if info.get("source_sha256") == sha:
            return info
    info = {**preflight.prepare_audio(src, dst, keep_lead=keep_lead), "source_sha256": sha, "source_path": str(src)}
    meta.write_text(json.dumps(info, indent=2))
    return info


def avatar_driver(prod: Production, s: Shot) -> tuple[str, float] | None:
    """An ACTION shot on Avatar is driven by the ON-SCREEN character's own timed voice-over line only (never the
    narrator: Avatar moves the mouth to whatever audio it gets). Returns (line id, start in the shot)."""
    if s.kind != "action" or not s.cast:
        return None
    for lid, at in (s.line_at or {}).items():
        if prod.lines[lid].get("speaker") == s.cast[0].char:
            return lid, at
    return None


def kling_job(prod: Production, s: Shot, first: Path, test: bool = False) -> fal.Job:
    drv = avatar_driver(prod, s)
    lid = drv[0] if drv else s.lines[0]
    e = prod.lines[lid]
    d = prod.root / "shots" / s.id
    files, info, seconds, head = {"image_url": first}, {}, e["seconds"], 0.0
    if e.get("final") and drv:             # silence up to the line's start, then the line (lead kept, not trimmed)
        lead = assemble.LEAD["kling_avatar"]
        src = d / "kling_driver_src.wav"
        d.mkdir(parents=True, exist_ok=True)
        media.ffmpeg("-f", "lavfi", "-t", f"{max(drv[1] - lead, 0.0):.3f}", "-i", "anullsrc=r=48000:cl=mono",
                     "-i", str(e["path"]), "-filter_complex", "[1:a]aresample=48000,aformat=channel_layouts=mono[b];[0:a][b]concat=n=2:v=0:a=1",
                     "-c:a", "pcm_s16le", str(src))
        audio = d / "kling_voice.wav"
        info = upload_audio(src, audio, keep_lead=True)
        info["driver"] = {"line": lid, "start": drv[1]}
        files["audio_url"] = audio
        seconds, head = info["prepared"]["seconds"], 0.0
    elif e.get("final"):                   # only real (original / approved ElevenLabs) audio is ever uploaded
        audio = d / "kling_voice.wav"
        info = upload_audio(Path(e["path"]), audio)
        files["audio_url"] = audio
        seconds, head = info["prepared"]["seconds"], info["head_trim"]
    # A prompt:<name> tag picks a shared template (EP002 S03/S04); without one, the character's Avatar prompt.
    explicit = s.prompt_key != f"talk_{s.cast[0].char}"
    prompt = kling3_prompt(prod, s)[0] if explicit else kling_prompt(prod.chars, s.cast[0])
    job = fal.Job(s.id, fal.KLING_AVATAR, prompt, files, seconds,
                  d / ("kling_test.mp4" if test else "kling_avatar.mp4"), head_trim=head, info=info)
    for name in AVATAR_CLIPS:                           # reuse a clip only if made from these exact inputs
        cand = replace(job, out_path=d / name)
        if cand.done():
            return cand
    return job


AVATAR_CLIPS = ("kling_avatar.mp4", "kling.mp4", "kling_test.mp4")


def wan_prompt(prod: Production, s: Shot) -> tuple[str, str]:
    """(prompt, negative prompt) for a Wan 2.7 talking shot. Default: the character's template under
    `wan_characters:` in library/kling_prompts.yaml (Wan hears the line in the audio, so it is not quoted).
    A `prompt:<name>` tag picks a shared template instead (filled like a Kling 3.0 prompt)."""
    cfg = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    on = s.cast[0]
    if s.prompt_key != f"talk_{on.char}":                  # explicit prompt:<name> tag
        text, negative = kling3_prompt(prod, s)
    else:
        tpl = (cfg.get("wan_characters") or {}).get(on.char)
        if not tpl:
            raise RuntimeError(f"{s.id}: no Wan 2.7 prompt for {on.char}: add one under wan_characters: in "
                               f"library/kling_prompts.yaml")
        face = preflight.facing_of(prod.chars[on.char], on)
        text = " ".join(tpl.split()).replace("{facing}", cfg["facing_words"][face]).replace("{acting}", s.acting or "expressive")
        negative = " ".join((cfg.get("negative") or "").split())
    if len(negative) > 500:
        raise RuntimeError("the negative prompt is over Wan 2.7's 500-character limit: shorten `negative:`")
    return text, negative


def wan_job(prod: Production, s: Shot, first: Path) -> fal.Job:
    """Wan 2.7 image-to-video, 720p, driven by the shot's approved line (lip sync + timing). Our prompt is sent as
    written (prompt expansion off: a rewrite could drop the on-model rules)."""
    e = prod.lines[s.lines[0]]
    d = prod.root / "shots" / s.id
    files, info, seconds, head = {"image_url": first}, {}, e["seconds"], 0.0
    if e.get("final"):                     # only real (original / approved ElevenLabs) audio is ever uploaded
        info = upload_audio(Path(e["path"]), d / "wan_voice.wav")
        files["audio_url"] = d / "wan_voice.wav"
        seconds, head = info["prepared"]["seconds"], info["head_trim"]
    secs = max(2, math.ceil(seconds - 1e-6))
    prompt, negative = wan_prompt(prod, s)
    return fal.Job(s.id, fal.WAN27, prompt, files, float(secs), d / "wan.mp4", head_trim=head, info=info,
                   endpoint="wan-talk", extra={"resolution": "720p", "duration": secs, "negative_prompt": negative,
                                               "enable_prompt_expansion": False})


def kling3_prompt(prod: Production, s: Shot) -> tuple[str, str]:
    """(prompt, negative prompt) from the owner's templates in library/kling_prompts.yaml."""
    cfg = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    tpl = (cfg.get("templates") or {}).get(s.prompt_key)
    if not tpl:
        raise RuntimeError(f"{s.id}: no Kling 3.0 template '{s.prompt_key}' in library/kling_prompts.yaml "
                           f"(set one with the script tag prompt:<name>)")
    on = next(iter(s.cast or s.end_cast or []), None)
    face = preflight.facing_of(prod.chars[on.char], on) if on else "front"
    fill = {"{facing}": cfg["facing_words"][face],
            "{line}": prod.lines[s.lines[0]]["text"] if s.kind == "talk" and s.lines else "",
            "{acting}": s.acting or "expressive",
            "{direction}": next((cfg["direction_words"][m] for m in s.motion if m in cfg["direction_words"]), "")}
    for cid, text in (cfg.get("official_identity") or {}).items():
        fill["{identity_" + cid + "}"] = " ".join(text.split())
    text = " ".join(tpl.split())
    for k, v in fill.items():
        text = text.replace(k, v)
    return text, " ".join((cfg.get("negative") or "").split())


def shot_tags(prod: Production, s: Shot) -> list[str]:
    line = next((e for e in prod.script.events if e.line_no == s.source_line), None)
    return line.direction if line else []


def shot_negative(prod: Production, s: Shot, base: str) -> str:
    """The shared negative prompt, plus the script's opt-in sets (header `negatives: <set>[,<set>]`, defined under
    negative_sets: in library/kling_prompts.yaml) for every shot with that set's character on screen. Opt-in, so
    finished episodes keep their exact requests."""
    names = [n.strip() for n in (prod.script.meta.get("negatives") or "").split(",") if n.strip()]
    line = next((e for e in prod.script.events if e.line_no == s.source_line), None)   # per-shot tag neg:<set>[+<set>]
    names += [n.strip() for n in shots_mod.tag_value(line.direction, "neg").split("+") if n.strip()] if line else []
    if not names:
        return base
    sets = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text()).get("negative_sets") or {}
    on = {o.char for o in (s.cast or []) + (s.end_cast or []) + (s.start_cast or [])}
    extra, drop = [], set()
    for n in names:
        if n not in sets:
            raise RuntimeError(f"unknown negative set '{n}' (script header negatives:); see negative_sets: in kling_prompts.yaml")
        if sets[n]["character"] in on:
            if " ".join((sets[n].get("text") or "").split()):          # a set may only drop shared terms
                extra.append(" ".join(sets[n]["text"].split()))
            drop |= {d.strip() for d in sets[n].get("drop") or []}
    if drop:      # a set may remove shared terms its shot needs (EP004 dive: airborne + skid vs "floating, sliding")
        base = ", ".join(t for t in (x.strip() for x in base.split(",")) if t and t not in drop)
    return ", ".join([base, *extra]) if extra else base


def with_elements(prod: Production, s: Shot, job: fal.Job) -> fal.Job:
    """Header `elements: on`: attach the shot's character references (references.yaml, built by `bbtb references`)
    to a Kling 3.0 Standard job and name them in the prompt as @Element1, @Element2 ..."""
    if job.model not in (fal.KLING3_STD, fal.KLING_O3_R2V) or (prod.script.meta.get("elements") != "on"
                                                              and "refs" not in shot_tags(prod, s)):
        return job                                    # header elements: on, or per shot with the tag `refs`
    els = references.paths(prod.root, s.id)
    if not els:
        return job
    on_screen = {o.char for o in (s.cast or []) + (s.end_cast or [])}
    if not on_screen <= {e["char"] for e in els}:        # stale references.yaml (e.g. shots renumbered)
        raise RuntimeError(f"{s.id}: references.yaml lists {sorted(e['char'] for e in els)} but the shot shows "
                           f"{sorted(on_screen)}: fix the shot ids in references.yaml, then `bbtb references`")
    names = ", ".join(f"@Element{i + 1} is {prod.chars[e['char']]['display_name']}" for i, e in enumerate(els))
    job.prompt = (f"{job.prompt} Character references: {names}. Keep every character exactly as in their reference "
                  f"images: same design, colours, proportions and details.")
    bad = [Path(p).name for e in els for p in [e["frontal"], *e["refs"]] if Path(p).exists() and not references.aspect_ok(p)]
    if bad:                                               # fal rejects these after queueing (HTTP 422)
        raise RuntimeError(f"{s.id}: reference image(s) outside Kling's aspect limit {references.ASPECT}: "
                           f"{', '.join(bad)} - rebuild with `bbtb references`")
    job.elements = [{"frontal": e["frontal"], "refs": e["refs"]} for e in els]
    if prod.script.meta.get("bg_element") == "on" and s.scene not in SPECIAL_SCENES:
        # Opt-in experiment (owner 2026-10-05): the location as one more element. The keyframe already shows it,
        # and Kling documents elements for characters/objects, so A/B test this before relying on it.
        d = references.out_dir(prod.root) / "elements"
        d.mkdir(parents=True, exist_ok=True)
        view = d / f"{s.id}_background.jpg"
        keyframes.plate(s.scene, prod.size).save(view, quality=92)
        spec = keyframes.backgrounds()[s.scene]
        full = LIBRARY / spec["file"] if spec.get("file") else registry_path(spec["asset"])
        job.elements.append({"frontal": view, "refs": [full]})
        job.prompt += (f" @Element{len(job.elements)} is the location: keep this background exactly as it is; "
                       f"it is scenery, not a character.")
    return job


def registry_path(asset_id: str) -> Path:
    from . import registry
    return registry.path_of(asset_id)


def kling3_job(prod: Production, s: Shot) -> fal.Job:
    """Talking: Kling 3.0 Turbo from the first frame (it speaks the line itself; re-voiced afterwards).
    Action: Kling 3.0 Standard, silent, first frame -> last frame."""
    d = prod.root / "shots" / s.id
    first, last = frame_paths(prod, s)
    prompt, negative = kling3_prompt(prod, s)
    secs = int(s.gen_seconds)
    if s.engine == "kling3_talk":
        return fal.Job(s.id, fal.KLING3_TURBO, prompt, {"image_url": first}, float(secs), d / "kling3.mp4",
                       endpoint="kling3-talk", extra={"duration": str(secs)}, required=("image_url",))
    negative = shot_negative(prod, s, negative)
    if s.engine == "kling3_talk_std":
        # Kling 3.0 Standard speaks the line itself (no audio input exists; re-voiced like Turbo), but it takes a
        # negative prompt, and the keyframe as END frame brings the character back to the start pose. Tag `noend`
        # drops the end frame (owner 2026-10-05: the round trip flattened the S02 performance).
        files = {"start_image_url": first} if "noend" in s.motion else {"start_image_url": first, "end_image_url": first}
        return with_elements(prod, s, fal.Job(s.id, fal.KLING3_STD, prompt, files, float(secs),
                       d / "kling3.mp4", endpoint="kling3-talk", required=("start_image_url",),
                       extra={"duration": str(secs), "generate_audio": True, "negative_prompt": negative}))
    files = {"start_image_url": first}
    if s.end_cast:
        files["end_image_url"] = last
    elif "loop" in s.motion:                          # tag loop: end on the start frame (keeps characters on model)
        files["end_image_url"] = first
    job = fal.Job(s.id, fal.KLING3_STD, prompt, files, float(secs), d / "kling3.mp4", endpoint="kling3-action",
                  extra={"duration": str(secs), "generate_audio": False, "negative_prompt": negative},
                  required=("start_image_url",))
    if "o3" in shot_tags(prod, s):
        return o3_job(prod, s, job, negative)
    return with_elements(prod, s, job)


O3_VIDEO_SECONDS = (3.0, 10.05)                       # fal limits for an element video (2026-10-08 schema)
O3_PROMPT_MAX = 2400                                  # fal's limit is 2500, but fal refused a 2,493-character prompt
                                                      # (2026-10-10; it seems to expand the @Element tags): keep 100 spare
O3_VIDEO_ITEMS = 4                                    # fal: with a video, at most 4 elements + reference images


def o3_job(prod: Production, s: Shot, job: fal.Job, negative: str) -> fal.Job:
    """Script tag `o3` on a kling3std action (owner 2026-10-08 model test): the same keyframes, prompt and character
    references on Kling O3 reference-to-video. O3 has no negative-prompt field, so the shot's blocking list is
    appended to the prompt as "Never: ...". Tag `refvideo:<path>` (relative to the production) adds a 3-10 s clip of
    the character as its OWN element: @Element1 = the character's images, @Element2 = the video (owner 2026-10-10: fal
    refuses an element with both). With a video, fal allows at most 4 items (elements + reference images)."""
    job.model, job.endpoint = fal.KLING_O3_R2V, "kling-o3"
    job.extra = {"duration": job.extra["duration"], "aspect_ratio": "9:16", "generate_audio": False}
    never = shots_mod.tag_value(shot_tags(prod, s), "never")      # tag never:<set>: a short O3-only list (owner
    if never:                                                       # 2026-10-08) instead of the full negative
        sets = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text()).get("negative_sets") or {}
        if never not in sets:
            raise RuntimeError(f"{s.id}: never:{never} is not a negative set in library/kling_prompts.yaml")
        negative = " ".join(sets[never]["text"].split())
    base = f"{job.prompt} Never: {negative}."
    job.prompt = base
    job = with_elements(prod, s, job)
    ref = shots_mod.tag_value(shot_tags(prod, s), "refvideo")
    if ref:
        video = prod.root / ref
        if not video.exists():
            raise RuntimeError(f"{s.id}: reference video {ref} not found in {prod.root}")
        if len(job.elements) != 1:
            raise RuntimeError(f"{s.id}: refvideo needs exactly one character with references (header elements: on, "
                               f"or tag refs); found {len(job.elements)}")
        secs = media.duration(video)
        lo, hi = O3_VIDEO_SECONDS
        if not lo <= secs <= hi:
            raise RuntimeError(f"{s.id}: reference video is {secs:.2f} s; Kling O3 needs {lo:g}-{hi:g} s")
        job.elements = [job.elements[0], {"video": video}]
        items = len(job.elements) + len(job.elements[0]["refs"])
        if items > O3_VIDEO_ITEMS:
            raise RuntimeError(f"{s.id}: {items} items (elements + reference images); with a video Kling O3 takes at "
                               f"most {O3_VIDEO_ITEMS}: list fewer refs for this shot in references.yaml")
        name = prod.chars[(s.cast or s.end_cast)[0].char]["display_name"]
        job.prompt = f"{base} @Element1 is {name}; @Element2 is a video of him."
    if len(job.prompt) > O3_PROMPT_MAX:
        raise RuntimeError(f"{s.id}: the Kling O3 prompt is {len(job.prompt)} characters (limit {O3_PROMPT_MAX}: fal's "
                           f"2500 minus a safety margin; the blocking list is part of it): shorten the template or the neg: sets. Nothing was sent.")
    return job


def use_revoiced(prod: Production, job_list: list) -> None:
    """Talking shots that have been re-voiced play that audio (it is in sync with the Kling beak)."""
    for j in job_list:
        if getattr(j, "endpoint", "") != "kling3-talk" or not j.done():
            continue
        info = revoice.done(j.out_path.parent, j.request_hash())
        s = next(x for x in prod.shots if x.id == j.shot_id)
        if info and s.lines:
            e = prod.lines[s.lines[0]]
            prod.lines[s.lines[0]] = {**e, "path": str(revoice.paths(j.out_path.parent)["wav"]),
                                      "seconds": info["seconds"], "speech": info["speech"],
                                      "source": "elevenlabs (re-voiced Kling performance)"}


def revoice_credits(job_list: list) -> int:
    return sum(revoice.credits_estimate(j.audio_seconds) for j in job_list
               if getattr(j, "endpoint", "") == "kling3-talk"
               and not (j.done() and revoice.done(j.out_path.parent, j.request_hash())))


def is_done(j) -> bool:
    return j.done() if isinstance(j, fal.Job) else j.out_path.exists()


def jobs(prod: Production, test: bool = False) -> list:
    meta = prod.script.meta
    res = ltx.RESOLUTION[(meta["format"], meta["resolution"])]
    out = []
    for s in prod.shots:
        first, last = frame_paths(prod, s)
        raw = prod.root / "shots" / s.id / "ltx.mp4"
        if s.engine == "kling_avatar":
            out.append(kling_job(prod, s, first, test))
        elif s.engine.startswith("kling3"):
            out.append(kling3_job(prod, s))
        elif s.engine == "wan_talk":
            out.append(wan_job(prod, s, first))
        elif s.engine == "ltx_a2v":
            lid = s.lines[0]
            sec = prod.lines[lid]["seconds"]
            lead = assemble.LEAD["ltx_a2v"]
            payload = {"prompt": s.prompt, "model": meta["model"], "resolution": res, "fps": meta["fps"],
                       "camera_motion": "static"}
            files = {"image_uri": first}
            if prod.lines[lid].get("final"):      # voice.mp3 is only ever made from real audio (ElevenLabs/original)
                files["audio_uri"] = media.to_mp3(Path(prod.lines[lid]["path"]), prod.root / "shots" / s.id / "voice.mp3",
                                                  lead=lead, tail=max(s.duration - sec - lead, 0.05))
            out.append(ltx.Job(s.id, "audio-to-video", payload, files,
                               billed_seconds=s.duration, resolution_tier=meta["resolution"], out_path=raw))
        elif s.engine == "ltx_i2v":
            payload = {"prompt": s.prompt, "model": meta["model"], "duration": int(s.gen_seconds),
                       "resolution": res, "fps": meta["fps"], "generate_audio": False,
                       "camera_motion": "static"}
            files = {"image_uri": first}
            if s.end_cast:
                files["last_frame_uri"] = last
            out.append(ltx.Job(s.id, "image-to-video", payload, files, billed_seconds=s.gen_seconds,
                               resolution_tier=meta["resolution"], out_path=raw))
    return out


def approval_code(job_list: list[ltx.Job], budget: float) -> str:
    blob = json.dumps({"jobs": sorted(j.request_hash() for j in job_list), "budget": budget})
    return hashlib.sha256(blob.encode()).hexdigest()[:8].upper()


def cost_table(prod: Production, job_list: list[ltx.Job], include_audio: bool = True) -> tuple[str, float]:
    rows, total = [], 0.0
    pending = [j for j in job_list if not is_done(j)]
    for s in prod.shots:
        j = next((x for x in job_list if x.shot_id == s.id), None)
        if j is None and s.engine.startswith(("kling", "ltx")):
            rows.append(f"  {s.id}  {s.engine:<14} {s.duration:5.1f}s   not in this run (storyboard still)")
        elif j is None and s.engine.startswith("reuse"):
            rows.append(f"  {s.id}  {s.engine:<14} {s.duration:5.1f}s   free (reuses {s.reuse})")
        elif j is None:
            rows.append(f"  {s.id}  {s.engine:<14} {s.duration:5.1f}s   free (local)")
        elif is_done(j):
            rows.append(f"  {s.id}  {s.engine:<14} {s.duration:5.1f}s   done (already paid)")
        else:
            rows.append(f"  {s.id}  {s.engine:<14} {s.duration:5.1f}s   ${j.cost:.2f}  ({j.billed_seconds:g}s billed)")
            total += j.cost
    names = [fx["name"] for s in prod.shots for fx in s.sfx]
    audio_cost = audio_bed.estimate(names, prod.script.meta.get("music"), prod.total) if include_audio else 0.0
    if audio_cost:
        rows.append(f"  music/SFX generation      ElevenLabs credits (~${audio_cost:.2f} API-equivalent; not fal/LTX $)")
    credits = revoice_credits(job_list)
    if credits:
        rows.append(f"  re-voice talking shots    ElevenLabs Voice Changer, ~{credits} credits")
    return "\n".join(rows), round(total, 2) if pending else 0.0


def session_spent(ledger: Ledger, hours: float = 12.0) -> float:
    """Paid video spend whose request was first sent in the last `hours` (the per-session cap)."""
    first_ts: dict[str, str] = {}
    for r in ledger.rows():
        first_ts.setdefault(r["request_hash"], r["ts"])
    cutoff = time.time() - hours * 3600
    total = 0.0
    for rh, row in ledger.latest().items():
        if row.get("kind") in ("ltx", "fal") and row.get("state") in ACTIVE:
            if time.mktime(time.strptime(first_ts[rh], "%Y-%m-%dT%H:%M:%S")) >= cutoff:
                total += row.get("cost_estimate", 0.0)
    return round(total, 4)


RISK = {"kling-avatar": 0, "audio-to-video": 0, "kling3-action": 1, "image-to-video": 1, "wan-talk": 2, "kling3-talk": 2}


def risk_rank(j) -> tuple[int, str]:
    """LOW (Avatar: our audio, consistent) < MEDIUM (Kling 3.0 action) < HIGH (Kling talking: can drift)."""
    return RISK.get(getattr(j, "endpoint", ""), 1), j.shot_id


def cap_problems(prod: Production, new_cost: float, max_cost: float | None, job_list: list | None = None) -> list[str]:
    """Owner hard limits. Any problem = no paid call at all."""
    meta, out = prod.script.meta, []
    if meta.get("shot_cap") is not None:                # owner 2026-10-05: no single shot above this
        for j in job_list or []:
            if not is_done(j) and j.cost > meta["shot_cap"] + 1e-9:
                out.append(f"shot cap: {j.shot_id} costs ${j.cost:.2f} > ${meta['shot_cap']:.2f} (shot_cap) - shorten it")
    spent = prod.ledger.spent()
    if meta.get("spend_cap") is not None and spent + new_cost > meta["spend_cap"] + 1e-9:
        out.append(f"episode cap: ${spent:.2f} spent + ${new_cost:.2f} new > ${meta['spend_cap']:.2f} (spend_cap)")
    sess = session_spent(prod.ledger)
    if sess + new_cost > meta["session_cap"] + 1e-9:
        out.append(f"session cap: ${sess:.2f} in the last 12 h + ${new_cost:.2f} new > ${meta['session_cap']:.2f} "
                   f"(session_cap) - needs a new owner approval for a higher cap")
    if max_cost is not None and new_cost > max_cost + 1e-9:
        out.append(f"this run: ${new_cost:.2f} > --max-cost ${max_cost:.2f}")
    return out


def preflight_report(prod: Production, job_list: list) -> dict[str, list]:
    by_shot = {s.id: s for s in prod.shots}
    out = {}
    for j in job_list:
        s = by_shot[j.shot_id]
        if is_done(j) or not (s.kind == "talk" or s.engine in ("kling3_action", "kling_avatar")):
            continue
        first, last = frame_paths(prod, s)
        if s.engine == "kling3_action":
            checks = []
            if s.start_cast == [] or not s.cast:
                checks.append(preflight.Check("first frame", "PASS" if first.exists() else "FAIL",
                                              f"{first.name}: the empty scene (the character enters)"))
            else:
                checks += preflight.keyframe_checks(prod, s)
            if s.end_cast:
                checks += [preflight.Check(f"end {c.name}", c.status, c.detail)
                           for c in preflight.keyframe_checks(prod, s, frame=last, cast=s.end_cast)]
        else:
            checks = preflight.keyframe_checks(prod, s)
            if any(o.char == "young_saul" for o in s.cast) and s.engine in ("kling3_talk", "wan_talk"):
                checks.append(preflight.Check("Saul engine", "FAIL", "No Turbo/Wan for Saul: his eyes droop for most of the "
                                              "clip (EP002 S01). Talking Saul: Kling Avatar (least drift so far)"))
            elif any(o.char == "young_saul" for o in s.cast) and s.kind == "talk":
                checks.append(preflight.Check("Saul engine", "WARN", "Talking Saul drifts on every Kling model (Avatar: "
                                              "short squint; Standard: 37% droopy frames). Check his eyes frame by frame; "
                                              "the real fix is high-res expression art from Jason"))
            if s.engine == "kling3_talk" and prod.script.meta.get("elements") == "on":
                checks.append(preflight.Check("character references", "FAIL",
                                              "Kling 3.0 Turbo takes no reference images: tag the line kling3std"))
            if s.engine in ("kling3_talk", "kling3_talk_std"):
                _, _, problem = revoice.voice_for(s.cast[0].char)
                checks.append(preflight.Check("voice for re-voice", "FAIL" if problem else "PASS",
                                              problem or f"{s.cast[0].char}: approved ElevenLabs voice"))
                checks.append(preflight.Check("script line in prompt", "PASS",
                                              f"\"{prod.lines[s.lines[0]]['text']}\" ({j.audio_seconds:g}s clip)"))
            else:
                checks += preflight.audio_checks(prod, s, j.info if isinstance(j, fal.Job) and j.info else None)
        out[s.id] = checks
    return out


def unreviewed(prod: Production, job_list: list) -> list:
    """Generated clips the owner has not approved yet (review gate)."""
    return [j for j in job_list if isinstance(j, fal.Job) and j.done()
            and not review.approved(prod.root, j.shot_id, j.request_hash())]


def review_sheets(prod: Production, job_list: list) -> list[Path]:
    out = []
    for j in job_list:
        if isinstance(j, fal.Job) and j.done():
            out.append(review.sheet(j.out_path, prod.root / "reviews" / f"{j.shot_id}_frames.jpg",
                                    f"{prod.script.title} {j.shot_id}"))
    return out


def make(script_path: Path, approve: str | None = None, only: list[str] | None = None,
         placeholder_voices: bool = False, max_cost: float | None = None, assemble: bool = True,
         auto_approve: bool = False) -> dict:
    """`only`: generate just these shot ids (e.g. a cheap test); everything else stays local."""
    if approve and placeholder_voices:
        raise RuntimeError("--placeholder-voices is for free previews only; it can't be combined with --approve.")
    # With --only, lines outside the selected shots are not generated, so they may stand in as
    # (never-final) timing placeholders; the selected talking shots must still have FINAL voices.
    prod = prepare(script_path, placeholder_voices=placeholder_voices or bool(only))
    meta = prod.script.meta
    all_jobs = jobs(prod, test=bool(only))
    use_revoiced(prod, all_jobs)
    job_list = list(all_jobs)
    if only:
        wanted = {x.strip().upper() for x in only}      # case-insensitive: pinned ids like S01b (owner 2026-10-07)
        unknown = wanted - {s.id.upper() for s in prod.shots}
        if unknown:
            raise RuntimeError(f"no such shot(s): {', '.join(sorted(unknown))}")
        job_list = [j for j in job_list if j.shot_id.upper() in wanted]
    table, new_cost = cost_table(prod, job_list, include_audio=not only)
    spent = prod.ledger.spent()
    code = approval_code(job_list, meta["budget"])
    write_plan(prod, job_list, code, new_cost)
    animatic = render(prod, final=False, job_list=all_jobs)

    blocked = voice_blockers(prod, job_list)
    pre = preflight_report(prod, job_list)
    caps = cap_problems(prod, new_cost, max_cost, job_list)
    summary = {"title": prod.script.title, "duration": prod.total, "shots": len(prod.shots),
               "new_cost": new_cost, "spent": spent, "budget": meta["budget"], "code": code,
               "animatic": str(animatic), "table": table, "voices": voices.readiness(prod.lines),
               "voice_blockers": blocked, "preflight": pre, "caps": caps,
               "session_spent": session_spent(prod.ledger), "jobs": job_list,
               "revoice_credits": revoice_credits(job_list)}
    if approve is None:
        flag = f" --only {','.join(only)}" if only else ""
        flag += f" --max-cost {max_cost:.2f}" if max_cost is not None else ""
        summary["next"] = (f"Review {animatic.relative_to(prod.root.parent.parent)} then run:\n"
                           f"  ./bbtb make {script_path}{flag} --approve {code}")
        return summary
    if approve.strip().upper() != code:
        raise RuntimeError(f"Approval code {approve} does not match the current plan ({code}). The script, art or "
                           f"settings changed since you approved; review the new cost table and use the new code.")
    if blocked:
        raise RuntimeError("Not generating: these talking shots would be animated to voices that are not final "
                           "(LTX moves the mouth to the exact audio, so changing the voice later means paying again):\n  "
                           + "\n  ".join(blocked) + "\nApprove the voices after listening (`bbtb voices approve`) "
                           "or use `--only` for shots whose voices are ready.")
    if spent + new_cost > meta["budget"] + 1e-9:
        raise RuntimeError(f"Over budget: ${spent:.2f} already spent + ${new_cost:.2f} new > ${meta['budget']:.2f}. "
                           f"Raise `budget:` in the script header or switch to `resolution: 720p`.")
    bad = [sid for sid, checks in pre.items() if preflight.worst(checks) == "FAIL"]
    if bad:
        raise RuntimeError("Pre-flight failed, nothing sent: " + "; ".join(
            f"{sid}: " + ", ".join(f"{c.name} ({c.detail})" for c in pre[sid] if c.status == "FAIL") for sid in bad))
    if caps:
        raise RuntimeError("Spending limit reached, nothing sent:\n  " + "\n  ".join(caps))

    job_list = sorted(job_list, key=risk_rank)        # owner 2026-10-05: cheap, reliable shots first
    ltx_client = ltx.Client(prod.ledger)
    fal_client = fal.Client(prod.ledger, approval_code=code)
    by_shot = {s.id: s for s in prod.shots}
    failures, made = [], []
    for j in job_list:
        try:
            if isinstance(j, fal.Job):
                if not is_done(j):
                    archive_take(j)
                    fal_client.run(j)
                    made.append(j)
                if j.endpoint == "kling3-talk" and not revoice.done(j.out_path.parent, j.request_hash()):
                    s = by_shot[j.shot_id]
                    e = prod.lines[s.lines[0]]
                    revoice.run(j.out_path, j.request_hash(), s.cast[0].char, e["text"], s.id, prod.ledger, code,
                                fallback=Path(e["path"]) if e.get("final") else None)
                    if j not in made:
                        made.append(j)
            elif not is_done(j):
                ltx_client.run(j)
        except (ltx.LtxError, fal.FalError, revoice.RevoiceError) as exc:
            failures.append(f"{j.shot_id}: {exc}")     # owner 2026-10-04: skip the shot (never retried), it falls
            continue                                   # back to local animation; the batch goes on
        except elevenlabs.ElevenLabsError as exc:
            failures.append(f"{j.shot_id}: {exc}")
            break                                    # CLAUDE.md credit rule 4: a failed ElevenLabs call stops production
    use_revoiced(prod, all_jobs)
    summary["clip_qa"] = [clip_qa.check(prod, by_shot[j.shot_id], j) for j in made if j.done()]
    if made or any(isinstance(j, fal.Job) for j in job_list):
        summary["balance"] = fal_client.balance()
    summary["spent_after"] = prod.ledger.spent()
    summary["review_sheets"] = [str(p) for p in review_sheets(prod, made)]
    pending = [] if auto_approve else unreviewed(prod, all_jobs)
    if not assemble or pending:                        # owner reviews the new clip(s) before anything is assembled
        summary.update({"final": None, "failures": failures, "unreviewed": [j.shot_id for j in pending]})
        return summary
    final = render(prod, final=True, paid_audio=not only, job_list=all_jobs)
    if not only:
        final = copy_finals(prod, final)
    report = qa.check(prod, final, failures)
    summary.update({"final": str(final), "qa": report["verdict"], "qa_report": report["path"], "failures": failures})
    return summary


def copy_finals(prod: Production, final: Path, suffix: str = "") -> Path:
    """Rename the export to the owner's delivery names (exports/ holds only the _FINAL_ files; owner 2026-10-04).
    `suffix` "_nomusic" names the no-music delivery copy. Returns the FINAL 9:16 path."""
    for tag in ("9x16", "4x5"):
        src = final.with_name(final.name.replace("_9x16", f"_{tag}"))
        if src.exists():
            src.replace(final.with_name(f"{prod.root.name}_FINAL_{tag}{suffix}.mp4"))
    return final.with_name(f"{prod.root.name}_FINAL_9x16{suffix}.mp4")


def archive_take(j: fal.Job) -> Path | None:
    """Before a retake overwrites a shot's paid clip, move that take (clip, sidecar, QA, re-voice) to
    shots/Sxx/takes/<clip>_<hash>/ so the owner can still compare or go back. Nothing paid is ever deleted."""
    d, stem = j.out_path.parent, j.out_path.stem
    if not j.out_path.exists() or j.done():
        return None
    try:
        old = json.loads(j.sidecar.read_text()).get("request_hash", "unknown")
    except (OSError, ValueError):
        old = "unknown"
    dst = d / "takes" / f"{stem}_{old.split(':')[-1][:8]}"
    dst.mkdir(parents=True, exist_ok=True)
    names = [j.out_path.name, j.sidecar.name, f"{stem}_qa.jpg", f"{stem}_qa.json"]
    if j.endpoint == "kling3-talk":
        names += [p.name for p in revoice.paths(d).values()] + ["voice_sts_rejected.mp3"]
    for n in names:
        if (d / n).exists():
            (d / n).rename(dst / n)
    return dst


def export(script_path: Path, auto_approve: bool = False, no_music: bool = False) -> dict:
    """Free re-export from the clips already made (after an edit such as trim:<s>). Never calls a paid API:
    music/SFX come from the cache or are synthesized; shots without a clip use free local animation.
    `no_music` (owner 2026-10-10, Jason's delivery format): voices + SFX only, saved as `_FINAL_<fmt>_nomusic.mp4`
    next to the finals with music (which are never overwritten by it)."""
    prod = prepare(script_path)
    if no_music:
        prod.script.meta["music"] = "off"
    all_jobs = jobs(prod)
    use_revoiced(prod, all_jobs)
    pending = [] if auto_approve else unreviewed(prod, all_jobs)
    if pending:
        sheets = review_sheets(prod, pending)
        raise RuntimeError("Not assembled: the owner has not approved these clips yet (review gate):\n  "
                           + "\n  ".join(f"{j.shot_id}: {p}" for j, p in zip(pending, sheets))
                           + f"\nAfter the owner approves: ./bbtb approve-clip {script_path} "
                           + ",".join(j.shot_id for j in pending))
    missing = [j.shot_id for j in all_jobs if not is_done(j)]
    final = render(prod, final=True, paid_audio=False, job_list=all_jobs)
    final = copy_finals(prod, final, suffix="_nomusic" if no_music else "")
    report = qa.check(prod, final, [f"{sid}: no generated clip (local stand-in)" for sid in missing])
    return {"final": final, "duration": prod.total, "missing": missing, "qa": report["verdict"],
            "qa_report": report["path"]}


def voice_blockers(prod: Production, job_list: list[ltx.Job]) -> list[str]:
    """Talking shots whose line audio is not final (placeholder or unapproved clone)."""
    by_shot = {s.id: s for s in prod.shots}
    out = []
    for j in job_list:
        if j.endpoint == "kling3-talk":
            _, _, problem = revoice.voice_for(by_shot[j.shot_id].cast[0].char)
            if problem:
                out.append(f"{j.shot_id} ({problem})")
            continue
        if j.endpoint not in ("audio-to-video", "kling-avatar", "wan-talk") or is_done(j):
            continue
        for lid in by_shot[j.shot_id].lines:
            e = prod.lines[lid]
            if not e.get("final"):
                out.append(f"{j.shot_id} ({lid}: {e['source']})")
    return out


def write_plan(prod: Production, job_list: list[ltx.Job], code: str, cost: float) -> None:
    data = {"title": prod.script.title, "meta": prod.script.meta, "approval_code": code, "new_cost": cost,
            "shots": [s.to_dict() for s in prod.shots],
            "jobs": [{"shot": j.shot_id, "endpoint": j.endpoint, "cost": j.cost,
                      "request_hash": j.request_hash()} for j in job_list]}
    (prod.root / "plan.json").write_text(json.dumps(data, indent=2))


def render(prod: Production, final: bool, paid_audio: bool = True, job_list: list | None = None) -> Path:
    """Build the video. Generated shots (Kling 3.0 / LTX / Avatar) use their clips in the final. Kling 3.0
    shots without a clip yet are shown as storyboard stills (never puppet animation); older engines fall back
    to local animation. Intermediates go to _work/ (never shipped)."""
    work = prod.root / "_work" / ("final" if final else "preview")
    work.mkdir(parents=True, exist_ok=True)
    seconds = {k: v["seconds"] for k, v in prod.lines.items()}
    clips = []
    kling = {j.shot_id: j for j in (job_list or []) if isinstance(j, fal.Job)}
    for s in prod.shots:
        first, _ = frame_paths(prod, s)
        shot_dir = prod.root / "shots" / s.id
        shot_dir.mkdir(parents=True, exist_ok=True)
        raw = shot_dir / "ltx.mp4"
        dst = shot_dir / "local.mp4"
        kj = kling.get(s.id)
        if s.engine.startswith("kling3"):
            _, last = frame_paths(prod, s)
            ready = kj is not None and kj.done() and (s.engine not in ("kling3_talk", "kling3_talk_std")
                                                      or revoice.done(kj.out_path.parent, kj.request_hash()))
            if final and ready:
                dst = work / f"{s.id}_kling3_fitted.mp4"
                src = kj.out_path
                fixes = clipfix.spec(prod.root).get(s.id)
                if fixes:                              # free render-time fixes (clip_fixes.yaml); the paid clip is untouched
                    bg, _ = keyframes.layout(s.scene, s.cast, prod.chars, prod.size, zoom=s.zoom)
                    src = clipfix.apply(kj.out_path, bg, fixes, work / f"{s.id}_clipfix.mp4")
                assemble.fit_clip(src, s.duration, prod.size, dst, skip=s.trim)
                if s.fx_args:                          # localanim overlays: bubble / numbers / ball (owner 2026-10-07)
                    dst = localanim.overlay(s, dst, prod.size, work / f"{s.id}_overlay.mp4")
                if s.cut and last.exists():            # tag cut:<s> (owner 2026-10-05: S07 meltdown hidden, free)
                    thud = next((fx["at"] for fx in sorted(s.sfx, key=lambda x: x["at"]) if fx["at"] >= s.cut), s.cut)
                    dst = assemble.cut_and_hold(dst, s.cut, last, s.duration, prod.size,
                                                work / f"{s.id}_kling3_cut.mp4", shake_at=thud)
            elif final:                                # skipped / failed shot: free local animation (owner 2026-10-04)
                dst = work / f"{s.id}_local_fallback.mp4"
                stand_in = replace(s, cast=list(s.cast or s.end_cast))
                animate.render(stand_in, prod.chars, prod.size, dst, prod.lines,
                               [(lid, max(off, 0.0)) for lid, off in assemble.line_offsets(s, seconds)])
            else:                                      # storyboard: start frame, then the end frame halfway
                dst = work / f"{s.id}_storyboard.mp4"
                if s.end_cast and last.exists():
                    half = round(s.duration / 2, 3)
                    a_clip = assemble.still_clip(first, half, prod.size, work / f"{s.id}_board_a.mp4", push=0.03)
                    b_clip = assemble.still_clip(last, s.duration - half, prod.size, work / f"{s.id}_board_b.mp4", push=0.03)
                    assemble.concat([a_clip, b_clip], dst)
                else:
                    assemble.still_clip(first, s.duration, prod.size, dst, push=0.03)
        elif final and kj is not None and kj.done():
            dst = work / f"{s.id}_kling_fitted.mp4"
            src = kj.out_path
            fixes = clipfix.spec(prod.root).get(s.id)
            if fixes:                                  # free render-time fixes for Avatar clips too (EP001 S02/S03/S06)
                bg, _ = keyframes.layout(s.scene, s.cast, prod.chars, prod.size, zoom=s.zoom)
                src = clipfix.apply(src, bg, fixes, work / f"{s.id}_clipfix.mp4")
            if s.cut:                                  # tag cut:<s>: use the clip up to <s>, hold that frame (free)
                cut_src = work / f"{s.id}_cut_src.mp4"
                media.ffmpeg("-i", str(src), "-t", f"{s.cut:.3f}", "-an", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "16", str(cut_src))   # cut the fixed copy, not the raw clip
                src = cut_src
            assemble.fit_clip(src, s.duration, prod.size, dst,
                              lead=assemble.LEAD.get(s.engine, assemble.LEAD["kling_avatar"]) + kj.head_trim)
        elif final and raw.exists() and s.engine.startswith("ltx"):
            dst = work / f"{s.id}_ltx_fitted.mp4"
            assemble.fit_clip(raw, s.duration, prod.size, dst)
        elif s.engine == "local_endcard" and s.card:
            animate.render_card(s, prod.chars, prod.size, dst)
        elif s.engine == "local_endcard":
            assemble.still_clip(first, s.duration, prod.size, dst, push=0.04, fade_in=0.3)
        elif s.engine in ("reuse_clip", "reuse_talk"):    # free: a library clip (cliplib), with its known fixes
            e = cliplib.entry(s.reuse)
            fixes = clipfix.spec(prod.root).get(s.id) or {}
            tw = (fixes.get("trapped_white") or (e.get("fixes") or {}).get("trapped_white"))
            plate = keyframes.plate(e["scene"], prod.size, float(tw.get("plate_zoom", 1.0))) if tw else None
            dst = cliplib.fitted(e, s.reuse_from, s.duration, prod.size, work / f"{s.id}_reuse.mp4", fixes, plate)
        elif s.engine == "local_still" and s.cast:     # owner 2026-10-06: never a flat zoom - layered parallax
            animate.render_parallax(s, prod.chars, prod.size, dst)
        elif s.engine == "local_still" or (s.engine == "ltx_i2v" and not s.cast):
            animate.render_parallax(s, prod.chars, prod.size, dst)
        elif s.fx:                                     # free local animation from Jason's art (localanim.py)
            localanim.render_fx(s, prod.size, dst)
        else:
            animate.render(s, prod.chars, prod.size, dst, prod.lines, assemble.line_offsets(s, seconds))
        clips.append(dst)
    video = assemble.concat(clips, work / "video.mp4")

    led = prod.ledger
    sfx_paths = {}
    for name in {fx["name"] for s in prod.shots for fx in s.sfx}:
        p = audio_bed.sfx(name, led, allow_paid=final and paid_audio)
        if p:
            sfx_paths[name] = p
    music = audio_bed.music(prod.script.meta.get("music"), prod.total, led, allow_paid=final and paid_audio)
    audio = assemble.mix(prod.shots, prod.lines, sfx_paths, music, prod.total, work / "mix.wav")

    cues = caption_cues(prod)

    out_dir = prod.root / ("exports" if final else "preview")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = prod.root.name
    if not final:
        assemble.write_srt(cues, out_dir / "animatic.srt")              # sidecar only, never inside the video
        return assemble.mux(video, audio, out_dir / "animatic.mp4")
    version = 1 + len(list(out_dir.glob(f"{stem}_v*_9x16.mp4")))
    master = assemble.mux(video, audio, out_dir / f"{stem}_v{version}_9x16.mp4")
    assemble.write_srt(cues, out_dir / f"{stem.split('-')[0]}_captions.srt")   # for CapCut; same for the 4:5 crop
    if prod.script.meta["format"] == "9:16":
        assemble.mux(video, audio, out_dir / f"{stem}_v{version}_4x5.mp4", crop_4x5=True)
    return master


def caption_cues(prod: Production) -> list[tuple[str, float, float]]:
    """Every spoken line with its exact start/end in the edit (for the owner's captions in CapCut/DaVinci)."""
    seconds = {k: v["seconds"] for k, v in prod.lines.items()}
    cues, t0 = [], 0.0
    for s in prod.shots:
        for lid, off in assemble.line_offsets(s, seconds):
            a, b = prod.lines[lid].get("speech") or (0.0, seconds[lid])
            cues.append((prod.lines[lid]["text"], max(t0, t0 + off + a), min(t0 + s.duration, t0 + off + b)))
        t0 += s.duration
    return cues


# --- pre-production quality sheet (owner 2026-10-05: "maximum preparation -> one take") -------------------------
EDGE_WHITE_MAX = 50          # edge-white pixels allowed on a cut-out (after defringe they are ~0-30)


def free_shot_verdict(prod: Production, s: Shot) -> tuple[str, str]:
    """Owner 2026-10-06: no static images anywhere; reused clips must carry their fixes; end cards must be dynamic."""
    if s.engine in ("reuse_clip", "reuse_talk"):
        e = cliplib.entry(s.reuse)
        fixes = clipfix.spec(prod.root).get(s.id) or {}
        if e.get("chin_white") and not (fixes.get("trapped_white") or (e.get("fixes") or {}).get("trapped_white")):
            return f"**NO-GO**: {s.reuse} has Billy's chin white - set a trapped_white clip fix", f"reuse {s.reuse}"
        if e.get("reusable") == "C":
            return f"**NO-GO**: {s.reuse} is rated C ({e.get('notes')})", f"reuse {s.reuse}"
        return "GO (free reuse)", f"reuse {s.reuse}"
    if s.engine == "local_still":
        return ("GO (free, parallax)" if s.cast else
                "**NO-GO**: static still with no character (rule 2) - reuse a clip"), "parallax" if s.cast else "still"
    if s.engine == "local_endcard" and s.card == "tease":
        return "**NO-GO**: static end card (owner rejected) - use a dynamic end card", "end card"
    return "GO (free)", s.engine


def preprod(script_path: Path) -> Path:
    """Free: write PRE_PRODUCTION.md (GO/NO-GO per paid shot, risk order, min/max cost) and PROMPTS.md (the exact
    prompts that would be sent, with the rationale from prompt_notes.yaml). Never calls a paid API."""
    from . import cutout
    from PIL import Image
    prod = prepare(script_path, placeholder_voices=True)
    all_jobs = jobs(prod)
    notes = yaml.safe_load((prod.root / "prompt_notes.yaml").read_text()) if (prod.root / "prompt_notes.yaml").exists() else {}
    pre = preflight_report(prod, all_jobs)
    meta = prod.script.meta
    cap = meta.get("shot_cap")
    rows, gos, plan_rows, gos_free = [], 0, [], []
    for s in prod.shots:
        j = next((x for x in all_jobs if x.shot_id == s.id), None)
        who = ", ".join(prod.chars[o.char]["display_name"] for o in (s.cast or s.end_cast or [])) or "-"
        if j is None:
            verdict, engine = free_shot_verdict(prod, s)
            gos_free.append(verdict.startswith("GO"))
            rows.append(f"| {s.id} | {s.scene} | {who} | - | {engine} | {s.duration:.1f}s | free | - | - | - | - | {verdict} |")
            continue
        checks = pre.get(s.id, [])
        pf = preflight.worst(checks) if checks else "PASS"
        voice_ok = all(prod.lines[l].get("final") for l in s.lines) or s.kind != "talk"
        refs_needed = isinstance(j, fal.Job) and j.model in (fal.KLING3_STD, fal.KLING_O3_R2V) and (meta.get("elements") == "on"
                                                                                 or "refs" in shot_tags(prod, s))
        refs = references.paths(prod.root, s.id)
        on_screen = {o.char for o in (s.cast or []) + (s.end_cast or [])}
        refs_ok = (not refs_needed) or (bool(refs) and on_screen <= {e["char"] for e in refs}
                                         and all(Path(p).exists() and references.aspect_ok(p)
                                                 for e in refs for p in [e["frontal"], *e["refs"]]))
        arts = {o.art for o in (s.cast or []) + (s.end_cast or [])}
        reds = {a: cutout.red_test(a) for a in arts}
        white = sum(len(r["undecided"]) for r in reds.values()) + sum(r["edge_white"] > EDGE_WHITE_MAX for r in reds.values())
        facing = next((c.status for c in checks if c.name == "facing"), "PASS")
        n = notes.get(s.id, {})
        reviewed = bool(n.get("reviewed"))
        cost_ok = cap is None or j.cost <= cap + 1e-9
        bg_ok = s.scene in keyframes.backgrounds()
        faces_missing = references.face_ok(prod.root, s.id) if refs_needed else []
        saul_on = "young_saul" in on_screen and isinstance(j, fal.Job) and j.model in (fal.KLING3_STD, fal.KLING3_TURBO, fal.WAN27)
        big_eyes = (not saul_on) or ("LARGE and ROUND" in j.prompt and "beady eyes" in j.extra.get("negative_prompt", ""))
        go = all([pf != "FAIL", voice_ok, refs_ok, white == 0, facing != "FAIL", reviewed, cost_ok, bg_ok,
                  not faces_missing, big_eyes])
        gos += go
        why = [w for w, ok in (("pre-flight", pf != "FAIL"), ("voice not final", voice_ok), ("references", refs_ok),
                                ("red test (white)", white == 0), ("facing", facing != "FAIL"),
                                ("prompt review", reviewed), (f"> shot cap ${cap}", cost_ok), ("background", bg_ok),
                                (f"no face close-up in references ({', '.join(faces_missing)})", not faces_missing),
                                ("Saul big-eye rule / saul_eyes negative missing", big_eyes)) if not ok]
        if is_done(j):                                 # already paid and made: shown for the record, not re-judged
            go, why = True, ["done (paid clip kept)"]
        expr = n.get("emotion", "-").split(" (")[0]
        label = {fal.KLING3_STD: "Kling 3.0 Std", fal.KLING3_TURBO: "Kling 3.0 Turbo", fal.KLING_AVATAR: "Kling Avatar",
                 fal.WAN27: "Wan 2.7", fal.KLING_O3_R2V: "Kling O3"}.get(getattr(j, "model", ""), s.engine)
        rows.append(f"| {s.id} | {s.scene} | {who} | {expr} | {label} "
                    f"{'(+refs)' if refs_needed else ''} | {j.billed_seconds}s | ${j.cost:.2f} | {'yes' if refs_ok else 'NO'} "
                    f"| {pf} | {'yes' if reviewed else 'NO'}{' (owner: ' + ('ok' if n.get('owner_ok') else 'pending') + ')'} "
                    f"| {'PASS' if white == 0 else 'FAIL'} | **{'GO' if go else 'NO-GO'}**{(': ' + ', '.join(why)) if why else ''} |")
        plan_rows.append((risk_rank(j)[0], s.id, j))
    paid = [p for p in plan_rows]
    lo = round(sum(j.cost for _, _, j in paid), 2)
    hi = round(lo * 2, 2)
    order = [f"{i + 1}. {sid} - {['LOW', 'MEDIUM', 'HIGH'][r]} risk - ${j.cost:.2f}" for i, (r, sid, j) in enumerate(sorted(paid, key=lambda x: (x[0], x[1])))]
    md = f"""# {prod.script.title}: pre-production quality sheet
Generated by `./bbtb preprod {script_path}` (free; rerun after every change). Only shots marked **GO** may be generated.

| Shot | Scene | Character | Expression | Engine | Seconds | Cost | Reference ready? | Pre-flight | Prompt reviewed? | Red test (white) | GO/NO-GO |
|---|---|---|---|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + f"""

**{gos} of {len(paid)} paid shots and {sum(gos_free)} of {len(gos_free)} free shots are GO.** Facing is checked by pre-flight (art as drawn, never mirrored); backgrounds are
all assigned plates (`library/backgrounds/INVENTORY.md`).

## Cost plan (fal.ai)
- **Minimum** (every shot right first time): **${lo:.2f}**
- **Maximum** (one retake of every paid shot): **${hi:.2f}**
- **Target** (minimum + 20%): **${lo * 1.2:.2f}**
- Limits in the script: session ${meta['session_cap']:.2f}, episode ${meta['spend_cap'] or 0:.2f}, any single shot ${cap or 0:.2f}.
- ElevenLabs credits on top: voices (`./bbtb voices render`), re-voice of Kling talking shots, new SFX.

## Generation order (lowest risk first; `make` runs them in this order)
""" + "\n".join(order) + "\n"
    out = prod.root / "PRE_PRODUCTION.md"
    out.write_text(md)
    _prompts_md(prod, all_jobs, notes)
    return out


def _prompts_md(prod: Production, all_jobs: list, notes: dict) -> Path:
    parts = [f"# {prod.script.title}: prompts per shot\nExactly what each paid request sends (free to regenerate with "
             f"`./bbtb preprod`). Talking lines show the script text; Kling 3.0 speaks it, then ElevenLabs re-voices it.\n"]
    for j in all_jobs:
        n = notes.get(j.shot_id, {})
        els = ", ".join(f"@Element{i + 1}: {Path(e['frontal']).name} + {len(e['refs'])} sheet images"
                        for i, e in enumerate(getattr(j, "elements", []) or [])) or "none (engine takes no references)"
        parts.append(f"""## {j.shot_id} ({j.model}, {j.billed_seconds}s, ${j.cost:.2f})
- **Emotion:** {n.get('emotion', '-')}
- **Action:** {n.get('action', '-')}
- **Background:** {n.get('background', '-')}
- **Must not happen:** {n.get('avoid', '-')}
- **Must be preserved:** {n.get('preserve', '-')}
- **Visual inputs:** {', '.join(f'{k}: {Path(v).name}' for k, v in j.files.items())}; elements: {els}
- **Reviewed:** {n.get('reviewed', 'NO')}; owner sign-off: {'yes' if n.get('owner_ok') else 'pending'}

**Prompt ({len(j.prompt)} chars):**
> {j.prompt}

**Negative prompt:** {j.extra.get('negative_prompt', '(engine takes none)')}
""")
    out = prod.root / "PROMPTS.md"
    out.write_text("\n".join(parts))
    return out

