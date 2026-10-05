"""Kling 3.0 talking shots, step 2: Kling's own voice -> the character's approved ElevenLabs voice.

Kling 3.0 Turbo acts the line with its own (generic) voice and moves the beak/mouth to THAT voice. To keep
the lip sync and still use our voices, the performance is re-voiced, not replaced:
  1. extract the clip's audio (free)
  2. Whisper checks Kling said the script line (free, local) - a wrong line stops here, before any credits
  3. ElevenLabs Voice Changer turns it into the character's approved voice, same words and timing (paid
     ElevenLabs credits; part of the shot's approval; logged first, never retried)
  4. Whisper again on the result (free) + speech start/end for captions
  5. If the re-voiced words are not the script's (e.g. "Ahh POOP" for "Oh POOP"), or Kling said the wrong line,
     the character's APPROVED ElevenLabs line (already paid) is placed word by word on Kling's word timings
     instead (free). The script's words are then guaranteed; the Voice Changer result is kept for reference.
Output: shots/Sxx/voice_revoiced.wav and voice_revoiced.json (tied to the exact Kling clip).
"""
from __future__ import annotations

import difflib
import hashlib
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

from . import elevenlabs, media, voices
from .ledger import Ledger
from .paths import LIBRARY

STS_MODEL = "eleven_multilingual_sts_v2"
CREDITS_PER_MINUTE = 1000            # ElevenLabs Voice Changer (~$0.12/min on API billing); verify in History
SR = 44100
MIN_MATCH = 0.6                      # share of script words Whisper must hear before re-voicing
VT = LIBRARY.parent / "studio" / "voicetools" / "vt.py"
VOICE_PY = LIBRARY.parent / ".venv-voice" / "bin" / "python"


class RevoiceError(RuntimeError):
    pass


def credits_estimate(seconds: float) -> int:
    return math.ceil(seconds * CREDITS_PER_MINUTE / 60)


def voice_for(char_id: str) -> tuple[str | None, dict, str | None]:
    """(voice_id, settings, problem). Only owner-approved voices are ever used."""
    data = voices.registry_state()
    cfg = voices.char_cfg(data, char_id)
    el = cfg.get("elevenlabs") or {}
    if not el.get("voice_id"):
        return None, {}, f"{char_id} has no ElevenLabs voice"
    if not cfg.get("approved"):
        return None, {}, f"{char_id}'s voice is not approved by the owner yet"
    s = el.get("settings") or {}
    return el["voice_id"], {"stability": s.get("stability", 0.45), "similarity_boost": s.get("similarity_boost", 0.85)}, None


def paths(shot_dir: Path) -> dict:
    return {"raw": shot_dir / "kling_audio.wav", "mp3": shot_dir / "voice_revoiced.mp3",
            "wav": shot_dir / "voice_revoiced.wav", "meta": shot_dir / "voice_revoiced.json"}


def done(shot_dir: Path, kling_hash: str) -> dict | None:
    p = paths(shot_dir)
    if p["wav"].exists() and p["meta"].exists():
        info = json.loads(p["meta"].read_text())
        if info.get("kling_request_hash") == kling_hash:
            return info
    return None


def transcribe(audio: Path) -> dict:
    """Local Whisper (free). Returns {"text", "words": [{w, start, end}]} or {} if the tool is missing."""
    if not VOICE_PY.exists():
        return {}
    out = subprocess.run([str(VOICE_PY), str(VT), "transcribe", str(audio)], capture_output=True, text=True)
    if out.returncode != 0:
        return {}
    try:
        return next(iter(json.loads(out.stdout).values()))
    except (ValueError, StopIteration):
        return {}


def words_of(text: str) -> list[str]:
    return [w for w in (voices.normalize(x) for x in text.replace("-", " ").split()) if w]


def match(heard: str, line: str) -> float:
    """Share of matching words (word by word; punctuation and case ignored)."""
    a, b = words_of(heard), words_of(line)
    return round(difflib.SequenceMatcher(None, a, b).ratio(), 2) if b else 0.0


def words_ok(heard: str, line: str) -> bool:
    """Short lines (<= 4 words) must match exactly; longer ones may differ by Whisper noise (>= 0.85)."""
    return match(heard, line) >= (1.0 if len(words_of(line)) <= 4 else 0.85)


def _pcm(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32)


def onsets(words: list[dict], pcm: np.ndarray, frac: float = 0.15) -> list[dict]:
    """Whisper's word starts can be early (it often starts the first word at 0.0). Move each start to where the
    sound actually begins inside that word (10 ms RMS above `frac` of the loudest frame)."""
    hop = int(0.01 * SR)
    rms = np.sqrt(np.array([np.mean(pcm[i:i + hop] ** 2) for i in range(0, max(len(pcm) - hop, 1), hop)]) + 1e-9)
    thr = frac * rms.max()
    out = []
    for w in words:
        a, b = int(w["start"] / 0.01), max(int(w["end"] / 0.01), int(w["start"] / 0.01) + 1)
        hit = next((i for i in range(a, min(b, len(rms))) if rms[i] > thr), None)
        out.append({**w, "start": hit * 0.01 if hit is not None else w["start"]})
    return out


def aligned_line(approved: Path, kling_words: list[dict], seconds: float, dst: Path,
                 kling_audio: Path | None = None) -> str:
    """Free: the approved line's words placed at Kling's word start times, so the beak still matches.
    Word by word when both have the same number of words, else the whole line on Kling's first word."""
    tts = _pcm(approved)
    tw = transcribe(approved).get("words") or []          # clean studio line: Whisper's boundaries are fine
    if kling_audio is not None:                           # Kling's take: snap to the real sound, keep consonants
        kling_words = [{**w, "start": max(w["start"] - 0.05, 0.0)} for w in onsets(kling_words, _pcm(kling_audio), 0.25)]
    out = np.zeros(int(seconds * SR) + 1, np.float32)
    if tw and kling_words and len(tw) == len(kling_words):
        mode = "word by word"
        bounds = [w["start"] for w in tw[1:]] + [len(tts) / SR]
        for w, end, k in zip(tw, bounds, kling_words):
            a, b = int(max(w["start"] - 0.03, 0) * SR), int(end * SR)
            seg = tts[a:b].copy()
            fade = min(len(seg), int(0.01 * SR))
            if fade:
                seg[:fade] *= np.linspace(0, 1, fade)
                seg[-fade:] *= np.linspace(1, 0, fade)
            at = int(max(k["start"] - 0.03, 0) * SR)
            seg = seg[: max(len(out) - at, 0)]
            out[at:at + len(seg)] += seg
    else:
        mode = "whole line"
        lead = (tw[0]["start"] if tw else 0.0)
        at = max((kling_words[0]["start"] if kling_words else 0.0) - lead, 0.0)
        seg = tts[: max(len(out) - int(at * SR), 0)]
        out[int(at * SR):int(at * SR) + len(seg)] += seg
    np.clip(out, -32768, 32767, out=out)
    with wave.open(str(dst), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes(out.astype(np.int16).tobytes())
    return mode


def run(clip: Path, kling_hash: str, char_id: str, line: str, shot_id: str, ledger: Ledger,
        approval_code: str, client: elevenlabs.Client | None = None, fallback: Path | None = None) -> dict:
    """`fallback`: the character's approved ElevenLabs/original line for this script line (free safety net)."""
    shot_dir = clip.parent
    prev = done(shot_dir, kling_hash)
    if prev:
        return prev
    voice_id, settings, problem = voice_for(char_id)
    if problem:
        raise RevoiceError(f"{shot_id}: {problem}. Nothing re-voiced.")
    p = paths(shot_dir)
    try:
        media.ffmpeg("-i", str(clip), "-vn", "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(p["raw"]))
    except media.MediaError:
        raise RevoiceError(f"{shot_id}: the Kling clip has no audio track, so there is no performance to re-voice.") from None
    seconds = media.duration(p["raw"])
    heard = transcribe(p["raw"])
    m = match(heard.get("text", ""), line) if heard else None
    if m is not None and m < MIN_MATCH and fallback is not None:
        mode = aligned_line(fallback, heard.get("words") or [], seconds, p["wav"], p["raw"])      # no credits spent
        return _save(p, {"kling_request_hash": kling_hash, "method": f"approved line, {mode} (Kling said "
                         f"the wrong line)", "seconds": round(media.duration(p["wav"]), 3),
                         "speech": _speech(p["wav"], seconds), "kling_heard": heard.get("text"), "kling_match": m})
    if m is not None and m < MIN_MATCH:
        raise RevoiceError(f"{shot_id}: Kling did not say the script line (Whisper heard \"{heard.get('text', '')}\", "
                           f"match {m:.0%}). Not re-voiced (no credits spent); the shot needs a retake.")
    sha = hashlib.sha256(p["raw"].read_bytes()).hexdigest()
    rh = "sts:" + hashlib.sha256(json.dumps({"v": voice_id, "m": STS_MODEL, "s": settings, "a": sha},
                                            sort_keys=True).encode()).hexdigest()[:20]
    client = client or elevenlabs.Client()
    client.speech_to_speech(voice_id, p["raw"], STS_MODEL, settings, p["mp3"], ledger, rh,
                            {"shot": shot_id, "approval_code": approval_code, "seconds": round(seconds, 2)},
                            credits_estimate(seconds))
    media.to_wav(p["mp3"], p["wav"])
    after = transcribe(p["wav"])
    words = after.get("words") or []
    speech = [words[0]["start"], words[-1]["end"]] if words else [0.0, seconds]
    info = {"kling_request_hash": kling_hash, "sts_request_hash": rh, "voice_id": voice_id, "model": STS_MODEL,
            "method": "voice changer", "seconds": round(media.duration(p["wav"]), 3), "speech": speech,
            "kling_heard": heard.get("text"), "kling_match": m,
            "revoiced_heard": after.get("text"), "revoiced_match": match(after.get("text", ""), line) if after else None}
    if after and not words_ok(after.get("text", ""), line) and fallback is not None:
        p["mp3"].rename(shot_dir / "voice_sts_rejected.mp3")          # paid result kept for reference, not used
        mode = aligned_line(fallback, heard.get("words") or [], seconds, p["wav"], p["raw"])
        info.update(method=f"approved line, {mode} (the Voice Changer said \"{after.get('text')}\")",
                    seconds=round(media.duration(p["wav"]), 3), speech=_speech(p["wav"], seconds))
    return _save(p, info)


def _speech(wav: Path, seconds: float) -> list[float]:
    words = transcribe(wav).get("words") or []
    return [words[0]["start"], words[-1]["end"]] if words else [0.0, seconds]


def _save(p: dict, info: dict) -> dict:
    p["meta"].write_text(json.dumps(info, indent=2))
    return info
