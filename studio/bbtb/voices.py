"""Character voices: original recordings + ONE permanent ElevenLabs clone per character.

Workflow (default for every episode):
  character recordings -> `bbtb voices assess` -> `bbtb voices clone <char> --confirm-rights` (once)
  -> voice ID saved in library/voices.yaml -> scripts reuse it -> `bbtb voices render <script>`
  (paid, approval code) -> cached WAVs drive shot timing and the mouth animation.

Line sources, in priority order:
  original     an original recording whose words match the line exactly - used verbatim, free;
  elevenlabs   the character's saved, OWNER-APPROVED ElevenLabs voice (paid per character, cached).
               All of a character's new lines go out as ONE request (joined with short break tags,
               /with-timestamps) and are sliced back into lines by the returned character timings;
  silent       ONLY with the explicit --placeholder-voices preview flag: silence of the estimated
               length, so timing can be previewed. Never final. (No macOS/Chatterbox voices are ever
               produced for anything the owner hears.)
Credit rules (owner, 2026-10-03): batch per character; one test line per character; never auto-retry
(any failure is logged "unknown" and production stops); a clone must be approved before any render.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import yaml

from . import elevenlabs, media, registry, voicelab
from .ledger import Ledger
from .paths import LIBRARY
from .shots import Line

VOICES_YAML = LIBRARY / "voices.yaml"
REF_DIR = LIBRARY / "derived" / "voice_refs"
VOICE_VENV = LIBRARY.parent / ".venv-voice" / "bin" / "python"
VT = LIBRARY.parent / "studio" / "voicetools" / "vt.py"
BREAK = ' <break time="0.7s" /> '     # official ElevenLabs pause tag between batched lines (~21 chars)
WORDS_PER_SECOND = 2.6                  # silent-placeholder length estimate (relaxed cartoon delivery)
MIN_ACTIVE_SECONDS = 5.0       # below this a clone is refused (unless --allow-short)
GOOD_ACTIVE_SECONDS = 60.0     # ElevenLabs IVC guidance: about 1-2 minutes of clean audio


class VoicesNotReady(RuntimeError):
    """Raised instead of silently substituting a worse voice."""

    def __init__(self, problems: list[str], estimate: dict | None = None):
        self.problems, self.estimate = problems, estimate or {}
        super().__init__("Voices are not ready:\n  " + "\n  ".join(problems))


# ---------------------------------------------------------------------------------- registry

def registry_state() -> dict:
    if VOICES_YAML.exists():
        data = yaml.safe_load(VOICES_YAML.read_text()) or {}
    else:
        data = {}
    data.setdefault("defaults", {"provider": "elevenlabs", "model_id": elevenlabs.DEFAULT_MODEL})
    data.setdefault("characters", {})
    return data


def save_registry(data: dict) -> None:
    VOICES_YAML.write_text(
        "# Character -> voice registry. Written by `bbtb voices ...`; safe to read, edit only `settings`.\n"
        "# voice IDs are not secrets; the API key lives only in .env.\n" + yaml.safe_dump(data, sort_keys=False))


def char_cfg(data: dict, char_id: str) -> dict:
    return data["characters"].setdefault(char_id, {})


def provider_for(char_id: str, data: dict) -> str:
    return "elevenlabs"          # the only provider for anything the owner hears


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower().replace("gunna", "gonna"))


def original_for(char: dict, text: str) -> str | None:
    want = normalize(text)
    for said, asset in (char.get("voice", {}).get("originals") or {}).items():
        if normalize(said) == want:
            return asset
    return None


# ---------------------------------------------------------------------------------- source audio

def source_files(char: dict) -> list[Path]:
    v = char.get("voice", {})
    return [registry.path_of(a) for a in v.get("clone_reference", [])] + \
           [LIBRARY.parent / f for f in v.get("clone_reference_files", [])]


def source_sha(files: list[Path]) -> str:
    return hashlib.sha256("".join(registry.sha256(f) for f in files).encode()).hexdigest()[:16]


def trimmed_sources(char_id: str, files: list[Path]) -> list[Path]:
    """Silence-trimmed derived copies (originals are never modified)."""
    return [media.to_wav(f, REF_DIR / "_parts" / f"{char_id}_{i}.wav", trim_silence=True) for i, f in enumerate(files)]


def reference_wav(char_id: str, char: dict) -> Path | None:
    """All source clips joined (for the optional local Chatterbox clone)."""
    files = source_files(char)
    if not files:
        return None
    dst, stamp = REF_DIR / f"{char_id}.wav", REF_DIR / f"{char_id}.key"
    key = source_sha(files)
    if not (dst.exists() and stamp.exists() and stamp.read_text() == key):
        media.concat_audio(trimmed_sources(char_id, files), dst, gap=0.25, max_seconds=30.0)
        stamp.write_text(key)
    return dst


def assess(char_id: str, char: dict) -> dict:
    """Is this character's audio good enough to clone? Measured, not assumed."""
    files = source_files(char)
    clips, active = [], 0.0
    for f in files:
        x = voicelab.load(f)
        peak = float(abs(x).max()) if len(x) else 0.0
        win = voicelab.SR // 50
        rms = sorted(float((x[i:i + win] ** 2).mean() ** 0.5) for i in range(0, max(len(x) - win, 1), win))
        floor = 20 * math.log10(max(sum(rms[:max(1, len(rms) // 10)]) / max(1, len(rms) // 10), 1e-6))
        p = voicelab.profile(f)
        clipped = int((abs(x) >= 0.999).sum())
        active += float(p["active_seconds"])
        clips.append({"file": f.name, "seconds": p["seconds"], "speech_seconds": p["active_seconds"],
                      "noise_floor_db": round(floor, 1), "clipped_samples": clipped,
                      "pitch_median_hz": p["f0_median"]})
    if not files:
        verdict, note = "none", "no recordings - this character cannot be cloned"
    elif active < MIN_ACTIVE_SECONDS:
        verdict, note = "insufficient", (f"only {active:.1f}s of speech; ElevenLabs advises about 60s. Record 30-60s more "
                                         "of this character (varied lines and emotions, quiet room, no music).")
    elif active < GOOD_ACTIVE_SECONDS:
        verdict, note = "limited", (f"{active:.1f}s of speech (ElevenLabs advises about 60s): the clone may only loosely "
                                    "match. More recordings would improve it.")
    else:
        verdict, note = "good", f"{active:.1f}s of speech"
    noisy = [c["file"] for c in clips if c["noise_floor_db"] > -50]
    if noisy:
        note += f" Noticeable background noise in: {', '.join(noisy)}."
    consistency = same_speaker_check(files)
    for c, score in zip(clips, consistency or []):
        c["same_speaker_score"] = score
    odd = [c["file"] for c in clips if c.get("same_speaker_score") is not None and c["same_speaker_score"] < 0.60]
    if odd:
        note += f" These clips may not match the others (check by ear before cloning): {', '.join(odd)}."
    return {"verdict": verdict, "speech_seconds": round(active, 1), "note": note, "clips": clips,
            "source_sha256": source_sha(files) if files else None}


def same_speaker_check(files: list[Path]) -> list[float] | None:
    """Each clip's speaker similarity to the average of the OTHER clips (Resemblyzer, local, free).
    None if the local toolkit is not installed or there is only one clip."""
    if len(files) < 2 or not VOICE_VENV.exists():
        return None
    scores = []
    for i, f in enumerate(files):
        others = [str(x) for j, x in enumerate(files) if j != i]
        proc = subprocess.run([str(VOICE_VENV), "-W", "ignore", str(VT), "similarity", "--ref", *others, "--test", str(f)],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            return None
        scores.append(float(next(iter(json.loads(proc.stdout).values()))))
    return [round(x, 3) for x in scores]


# ---------------------------------------------------------------------------------- cloning

def clone(char_id: str, char: dict, confirm_rights: bool, client: elevenlabs.Client | None = None,
          allow_short: bool = False) -> tuple[str, bool]:
    """Create the character's ElevenLabs voice ONCE. Returns (voice_id, created_now)."""
    data = registry_state()
    cfg = char_cfg(data, char_id)
    files = source_files(char)
    if not files:
        raise RuntimeError(f"{char['display_name']} has no recordings to clone. Add clips to `voice.clone_reference` "
                           f"in library/characters/{char_id}.yaml, or set an existing voice with `bbtb voices set`.")
    sha = source_sha(files)
    el = cfg.get("elevenlabs") or {}
    if el.get("voice_id") and el.get("source_sha256") == sha:
        return el["voice_id"], False                       # already cloned from the same audio: reuse
    if not confirm_rights:
        raise RuntimeError("Not cloning: add --confirm-rights to confirm the project holds the rights and the "
                           "performer's consent to clone this voice.")
    a = assess(char_id, char)
    if a["verdict"] == "insufficient" and not allow_short:
        raise RuntimeError(f"Not cloning {char['display_name']}: {a['note']} (override with --allow-short).")
    client = client or elevenlabs.Client()
    voice_id = client.clone(f"BBTB {char['display_name']}", trimmed_sources(char_id, files),
                            description=f"Bad Billy the Bird - {char['display_name']} (AL-Oose)")
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    cfg.update({"provider": "elevenlabs", "rights_confirmed": True, "rights_confirmed_at": now, "approved": False,
                "elevenlabs": {"voice_id": voice_id, "source_files": [f.name for f in files], "source_sha256": sha,
                               "cloned_at": now, "settings": el.get("settings") or dict(elevenlabs.DEFAULT_SETTINGS)},
                "assessment": {k: a[k] for k in ("verdict", "speech_seconds", "note")}})
    save_registry(data)
    return voice_id, True


def build_reference(char_id: str, char: dict, ref: Path) -> Path:
    """All clone_reference clips, silence-trimmed and joined; denoised too when the character is marked
    `voice.denoise_originals` (owner 2026-10-07: the Snail's first clone was built from his noisy, undenoised clips)."""
    files = source_files(char)
    denoise = bool(char.get("voice", {}).get("denoise_originals"))
    ref.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:          # trimmed parts are temporary; only the joined ref is kept
        parts = [media.to_wav(f, Path(td) / f"{char_id}_{i}.wav", trim_silence=True, denoise=denoise)
                 for i, f in enumerate(files)]
        media.concat_audio(parts, ref, gap=0.25, max_seconds=120.0)
    return ref


def reclone(char_id: str, char: dict, confirm_rights: bool, client: elevenlabs.Client | None = None) -> dict:
    """Replace a character's clone with a new one made from ALL its current `clone_reference` clips,
    joined into library/derived/voice_refs/<char>_v<N>.wav. Order is safe: the NEW voice is created
    first; the old voice is deleted only after that succeeds. Returns a report dict."""
    if not confirm_rights:
        raise RuntimeError("Not re-cloning: add --confirm-rights (rights and performer consent).")
    data = registry_state()
    cfg = char_cfg(data, char_id)
    el = cfg.get("elevenlabs") or {}
    old_id = el.get("voice_id")
    files = source_files(char)
    if not files:
        raise RuntimeError(f"{char['display_name']} has no clips in voice.clone_reference")
    version = int(el.get("ref_version", 1)) + 1
    ref = REF_DIR / f"{char_id}_v{version}.wav"
    build_reference(char_id, char, ref)
    client = client or elevenlabs.Client()
    new_id = client.clone(f"BBTB {char['display_name']} v{version}", [ref],
                          description=f"Bad Billy the Bird - {char['display_name']} (AL-Oose), reference v{version}")
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    cfg.update({"provider": "elevenlabs", "rights_confirmed": True, "rights_confirmed_at": now, "approved": False,
                "elevenlabs": {"voice_id": new_id, "ref_version": version, "reference_file": str(ref.relative_to(LIBRARY.parent)) if ref.is_relative_to(LIBRARY.parent) else str(ref),
                               "reference_seconds": round(media.duration(ref), 2),
                               "source_files": [f.name for f in files], "source_sha256": source_sha(files),
                               "cloned_at": now, "settings": el.get("settings") or dict(elevenlabs.DEFAULT_SETTINGS),
                               "replaced_voice_id": old_id}})
    save_registry(data)                                    # new id saved before anything is deleted
    deleted = None
    if old_id and old_id != new_id:
        client.delete_voice(old_id)
        deleted = old_id
        cfg["elevenlabs"]["replaced_voice_deleted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        save_registry(data)
    return {"new_voice_id": new_id, "deleted_voice_id": deleted, "reference": ref,
            "reference_seconds": round(media.duration(ref), 2), "files": [f.name for f in files]}


def set_existing(char_id: str, voice_id: str, note: str) -> None:
    """Use a voice that already exists in the ElevenLabs account (e.g. a licensed narrator voice)."""
    data = registry_state()
    cfg = char_cfg(data, char_id)
    cfg.update({"provider": "elevenlabs", "approved": False,
                "elevenlabs": {"voice_id": voice_id, "source_files": [], "source_sha256": None,
                               "settings": dict(elevenlabs.DEFAULT_SETTINGS), "note": note,
                               "set_at": time.strftime("%Y-%m-%dT%H:%M:%S")}})
    save_registry(data)


# ---------------------------------------------------------------------------------- lines

def line_plan(lines: list[Line], chars: dict, data: dict) -> list[dict]:
    """What each line needs, without generating anything."""
    model = data["defaults"].get("model_id", elevenlabs.DEFAULT_MODEL)
    plan = []
    for ln in lines:
        char = chars[ln.speaker]
        orig = original_for(char, ln.text)
        cfg = char_cfg(data, ln.speaker)
        item = {"line": ln, "provider": "original" if orig else "elevenlabs", "asset": orig, "problem": None}
        if orig:
            item["key"] = "orig:" + orig
        else:
            el = cfg.get("elevenlabs") or {}
            settings = {**elevenlabs.DEFAULT_SETTINGS, **(el.get("settings") or {})}
            item.update(voice_id=el.get("voice_id"), model_id=model, settings=settings)
            who = char["display_name"]
            if not el.get("voice_id"):
                item["problem"] = (f"{ln.id}: {who} has no ElevenLabs voice yet. "
                                   + ("Configure the narrator: `bbtb voices set narrator <voice_id>` or "
                                      "`bbtb voices clone narrator --confirm-rights`." if ln.speaker == "narrator"
                                      else f"Run `bbtb voices clone {ln.speaker} --confirm-rights`."))
            elif not cfg.get("approved"):
                item["problem"] = (f"{ln.id}: {who}'s voice is not approved yet. Listen to its test line "
                                   f"(`bbtb voices test {ln.speaker} ...`), then `bbtb voices approve {ln.speaker} "
                                   "--confirm-rights`.")
            item["key"] = elevenlabs.request_hash(el.get("voice_id") or "-", model, settings, ln.text)
        plan.append(item)
    return plan


def group_problems(plan: list[dict]) -> list[str]:
    """One message per problem, listing the affected lines: 'X has no voice yet (L011, L016)'."""
    grouped: dict[str, list[str]] = {}
    for p in plan:
        if p["problem"]:
            lid, msg = p["problem"].split(": ", 1)
            grouped.setdefault(msg, []).append(lid)
    return [f"{msg} (lines {', '.join(ids)})" for msg, ids in grouped.items()]


def batches(pending: list[dict]) -> dict[str, dict]:
    """Group pending ElevenLabs lines into ONE request per character (identical texts sent once)."""
    out: dict[str, dict] = {}
    for p in pending:
        b = out.setdefault(p["line"].speaker, {"voice_id": p["voice_id"], "model_id": p["model_id"],
                                               "settings": p["settings"], "texts": [], "items": []})
        if p["line"].text not in b["texts"]:
            b["texts"].append(p["line"].text)
        b["items"].append(p)
    for sp, b in out.items():
        b["text"] = BREAK.join(b["texts"])
        b["key"] = elevenlabs.request_hash(b["voice_id"], b["model_id"], b["settings"], b["text"])
    return out


def estimate(plan: list[dict], audio_dir: Path, multiplier: float = elevenlabs.FALLBACK_MULTIPLIER) -> dict:
    store = _store(audio_dir)
    todo = [p for p in plan if p["provider"] == "elevenlabs" and not p["problem"] and not _cached(store, p)]
    groups = batches(todo)
    chars = sum(len(b["text"]) for b in groups.values())
    return {"lines": len(todo), "requests": len(groups), "characters": chars, "credits": round(chars * multiplier),
            "per_character": {sp: len(b["text"]) for sp, b in groups.items()},
            "code": hashlib.sha256(json.dumps(sorted(b["key"] for b in groups.values())).encode()).hexdigest()[:8].upper()}


# Production audio layout (owner, 2026-10-03):
#   audio/lines.json          index of every final line (source: elevenlabs | original)
#   audio/lines/<id>.wav      ElevenLabs lines ONLY (paid, real voices) - never a placeholder
#   audio/lines/_by_key/      content-addressed ElevenLabs store (re-numbering never re-bills)
#   audio/lines/_batches/     raw one-request-per-character batches + timings (re-sliced for free)
#   audio/originals/<id>.wav  lines taken from the original book recordings
#   _work/placeholders/       SILENT timing placeholders for previews (never final, never in audio/)

def _index(audio_dir: Path) -> dict:
    p = audio_dir / "lines.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _store(audio_dir: Path) -> Path:
    """Content-addressed ElevenLabs store: <key>.wav, so renumbered or reordered lines are never paid twice."""
    return audio_dir / "lines" / "_by_key"


def _cached(store: Path, p: dict) -> bool:
    return p["provider"] == "original" or (store / f"{p['key'].replace(':', '_')}.wav").exists()


def _locate(chars: list[str], starts: list[float], ends: list[float], texts: list[str]) -> list[tuple[float, float]]:
    """(start, end) seconds of each text inside the batch, from ElevenLabs' character alignment."""
    joined = "".join(chars)
    squash = lambda t: re.sub(r"\s+", " ", t).strip()
    spans, cursor = [], 0
    for t in texts:
        i = joined.find(squash(t), cursor)
        if i < 0:                                   # tolerate small normalisation differences
            head, tail = squash(t)[:12], squash(t)[-12:]
            i = joined.find(head, cursor)
            j = joined.find(tail, max(i, cursor)) if i >= 0 else -1
            if i < 0 or j < 0:
                raise elevenlabs.ElevenLabsError(f"could not find this line in the generated batch: {t[:60]!r}")
            last = j + len(tail) - 1
        else:
            last = i + len(squash(t)) - 1
        spans.append((starts[i], ends[last]))
        cursor = last + 1
    return spans


def _slice_batch(audio: Path, alignment: dict, texts: list[str], workdir: Path) -> dict[str, Path]:
    spans = _locate(alignment["characters"], alignment["character_start_times_seconds"],
                    alignment["character_end_times_seconds"], texts)
    total = media.duration(audio)
    out = {}
    for k, (t, (a, b)) in enumerate(zip(texts, spans)):
        lo = max(0.0, a - 0.06) if k == 0 else max((spans[k - 1][1] + a) / 2, a - 0.06)
        hi = min(total, b + 0.15) if k == len(spans) - 1 else min((b + spans[k + 1][0]) / 2, b + 0.15)
        cut = workdir / f"_cut{k}.wav"
        media.ffmpeg("-ss", f"{lo:.3f}", "-to", f"{hi:.3f}", "-i", str(audio), "-ac", "1", "-ar", str(media.SR),
                     "-c:a", "pcm_s16le", str(cut))
        out[t] = cut
    return out


def render_lines(lines: list[Line], chars: dict, audio_dir: Path, ledger: Ledger, allow_paid: bool = False,
                 placeholder: bool = False, client: elevenlabs.Client | None = None) -> dict[str, dict]:
    """Produce one WAV per line ({line_id: {path, seconds, source, final, ...}}).

    Paid speech only runs with allow_paid=True (`bbtb voices render --approve`), as ONE request per
    character. Anything missing raises VoicesNotReady - unless `placeholder` (explicit preview flag),
    in which case missing lines are SILENT placeholders of estimated length (never final)."""
    lines_dir, orig_dir = audio_dir / "lines", audio_dir / "originals"
    work = audio_dir.parent / "_work" / "placeholders"
    store = _store(audio_dir)
    data = registry_state()
    plan = line_plan(lines, chars, data)
    index = _index(audio_dir)
    problems = group_problems(plan)
    pending = [p for p in plan if p["provider"] == "elevenlabs" and not p["problem"] and not _cached(store, p)]
    if (problems or (pending and not allow_paid)) and not placeholder:
        est = estimate(plan, audio_dir)
        if pending and not allow_paid:
            problems.append(f"{len(pending)} line(s) need ElevenLabs speech: {est['characters']} characters in "
                            f"{est['requests']} request(s), about {est['credits']} credits. Nothing was generated.")
        raise VoicesNotReady(problems, est)

    if pending and allow_paid:                       # ONE request per character, then slice
        client = client or elevenlabs.Client()
        bdir = lines_dir / "_batches"
        bdir.mkdir(parents=True, exist_ok=True)
        store.mkdir(parents=True, exist_ok=True)
        for speaker, b in batches(pending).items():
            stem = bdir / f"{speaker}_{b['key'].replace(':', '_')}"
            mp3, align = stem.with_suffix(".mp3"), stem.with_suffix(".json")
            if not (mp3.exists() and align.exists()):  # a saved batch is re-sliced, never re-bought
                client.tts_with_timestamps(b["voice_id"], b["text"], b["model_id"], b["settings"], mp3, align,
                                           ledger, b["key"], meta={"speaker": speaker, "lines": [p["line"].id for p in b["items"]],
                                                                   "characters": len(b["text"])},
                                           credits_estimate=len(b["text"]))
            cuts = _slice_batch(mp3, json.loads(align.read_text()), b["texts"], bdir)
            for p in b["items"]:
                media.to_wav(cuts[p["line"].text], store / f"{p['key'].replace(':', '_')}.wav", trim_silence=True)
            for c in cuts.values():
                c.unlink(missing_ok=True)

    result = {}
    for p in plan:
        ln = p["line"]
        entry = {"key": p["key"], "source": p["provider"], "speaker": ln.speaker, "text": ln.text,
                 "line_source": ln.source}
        if p["provider"] == "original":
            dst = orig_dir / f"{ln.id}.wav"
            dst.parent.mkdir(parents=True, exist_ok=True)
            media.to_wav(registry.path_of(p["asset"]), dst, trim_silence=True,
                         denoise=bool(chars[ln.speaker].get("voice", {}).get("denoise_originals")))
            entry["asset"] = p["asset"]
        elif _cached(store, p):
            dst = lines_dir / f"{ln.id}.wav"
            shutil.copyfile(store / f"{p['key'].replace(':', '_')}.wav", dst)
            entry.update(voice_id=p["voice_id"], model_id=p["model_id"], settings=p["settings"])
        else:                                          # explicit preview only: silence, never final
            dst = work / f"{ln.id}.wav"
            dst.parent.mkdir(parents=True, exist_ok=True)
            _silent(ln.text, dst, (chars.get(ln.speaker, {}).get("voice") or {}).get("pace_wps", WORDS_PER_SECOND))
            entry.update(source="placeholder", key="placeholder")
        entry["path"] = str(dst)
        entry["seconds"] = round(media.duration(dst), 3)
        if entry["source"] != "placeholder":
            index[ln.id] = dict(entry)
        entry["final"] = is_final(entry, data)
        result[ln.id] = entry
    index = {k: v for k, v in index.items() if v.get("source") in ("elevenlabs", "original")}
    audio_dir.mkdir(parents=True, exist_ok=True)
    (audio_dir / "lines.json").write_text(json.dumps(index, indent=2))
    return result


def is_final(entry: dict, data: dict) -> bool:
    if entry["source"] == "original":
        return True
    if entry["source"] == "elevenlabs":
        cfg = data["characters"].get(entry["speaker"]) or {}
        return bool(cfg.get("approved")) and (cfg.get("elevenlabs") or {}).get("voice_id") == entry.get("voice_id")
    return False


def readiness(lines: dict[str, dict]) -> list[str]:
    names = {"original": "original recording", "elevenlabs": "ElevenLabs clone",
             "placeholder": "SILENT placeholder (timing preview only, never final)"}
    rows = []
    for lid, e in lines.items():
        why = names.get(e["source"], e["source"])          # e.g. "elevenlabs (re-voiced Kling performance)"
        if e["source"] == "elevenlabs" and not e.get("final"):
            why += " - voice not approved"
        rows.append(f"  {lid:<18} {'FINAL' if e.get('final') else 'NOT READY':<10} {why}")
    return rows


# ---------------------------------------------------------------------------------- helpers

def _silent(text: str, dst: Path, wps: float = WORDS_PER_SECOND) -> None:
    """Silence of roughly the time the line would take to say (timing previews only)."""
    seconds = max(0.8, len(text.split()) / wps + 0.3)
    media.ffmpeg("-f", "lavfi", "-i", f"anullsrc=r={media.SR}:cl=mono", "-t", f"{seconds:.2f}",
                 "-c:a", "pcm_s16le", str(dst))
