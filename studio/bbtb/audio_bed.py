"""Background music and sound effects.

Lookup order for each item:
  1. local library:  library/audio/music/<mood>.(mp3|wav|m4a)  and  library/audio/sfx/<name>.(mp3|wav)
     (drop royalty-free files there; no API needed);
  2. ElevenLabs Music / Sound Effects API if ELEVENLABS_API_KEY is set AND the run is approved
     (paid, cached forever in library/audio/elevenlabs/ so each prompt is paid for once);
  3. SFX only: a free synthesized cartoon effect (rumble, roar, whoosh, pop, scroll) in
     library/audio/generated/ (free synth ONLY lives there);
  4. otherwise nothing -> the video still renders; QA reports the missing music.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import requests

from . import env
from .ledger import Ledger
from .paths import LIBRARY

AUDIO = LIBRARY / "audio"
EXTS = (".mp3", ".wav", ".m4a", ".ogg")
SFX_URL = "https://api.elevenlabs.io/v1/sound-generation"
MUSIC_URL = "https://api.elevenlabs.io/v1/music"
SFX_COST, MUSIC_COST_PER_MIN = 0.12, 0.15    # API-price equivalent in USD; on our subscription these are paid
                                             # in ElevenLabs credits, so they never count toward fal/LTX dollars

MUSIC_PROMPTS = {
    "playful-adventure": "Playful, bouncy orchestral children's cartoon underscore with pizzicato strings, "
                         "light woodwinds, xylophone and soft percussion; curious and mischievous; instrumental.",
    "tense": "Comic suspense cartoon underscore, tiptoeing pizzicato and low bassoon, building tension; instrumental.",
}
SFX_PROMPTS = {
    "rumble": "deep cartoon ground rumble building up, rocks rattling",
    "roar": "big goofy friendly cartoon monster roar, playful not scary",
    "whoosh": "quick cartoon whoosh",
    "crash": "cartoon crash and thud with a comedic bounce",
    "pop": "cartoon pop",
    "scroll": "old paper scroll unrolling",
    "tummy": "funny cartoon stomach growl, a long hungry gurgle",
    # EP004 (owner 2026-10-07)
    "gulp": "single big comedic cartoon gulp swallow, one wet throat gulp, kid-friendly, no voice, no music",
    "burp": "one short funny cartoon burp from a small bird, satisfied, kid-friendly, no words, no music",
    "alarm": "short cartoon alarm siren whoop, urgent warning, comedic, no voice, no music",
    "giggles": "a few tiny cartoon worms giggling and squeaking happily while playing ball, high-pitched, kid-friendly, no words, no music",
    "aaah": "a short group scream of tiny cartoon worms, high-pitched 'aaah!', comedic panic, kid-friendly, no words, no music",
}
SFX_SECONDS = {"gulp": 1.0, "burp": 1.0, "alarm": 1.5, "giggles": 2.0, "aaah": 1.0}   # fixed length = predictable ElevenLabs credits
SFX_CREDITS_PER_SECOND = 40                               # ElevenLabs sound effects pricing (set length)


def _key() -> str | None:
    """Same key lookup as the voice client (ELEVENLABS_API_KEY or ELEVEN_LABS_API_KEY)."""
    return env.get("ELEVENLABS_API_KEY") or env.get("ELEVEN_LABS_API_KEY")


def _local(folder: str, name: str) -> Path | None:
    for ext in EXTS:
        p = AUDIO / folder / f"{name}{ext}"
        if p.exists():
            return p
    return None


def _eleven(url: str, body: dict, dst: Path, ledger: Ledger, cost: float, label: str) -> Path:
    key = _key()
    rh = "eleven:" + hashlib.sha256(repr(sorted(body.items())).encode()).hexdigest()[:16]
    ledger.write(rh, state="intent", kind="audio", provider="elevenlabs", item=label, cost_estimate=0.0,
                 usd_equivalent=cost)
    r = requests.post(url, headers={"xi-api-key": key, "Content-Type": "application/json"},
                      params={"output_format": "mp3_44100_128"}, json=body, timeout=300)
    if r.status_code >= 300:
        ledger.write(rh, state="failed", error=env.redact(r.text[:300]), cost_estimate=0.0)
        raise RuntimeError(f"ElevenLabs {label} failed ({r.status_code}): {env.redact(r.text[:300])}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(r.content)
    ledger.write(rh, state="completed")
    return dst


def sfx_body(name: str, prompt: str) -> dict:
    body = {"text": prompt, "prompt_influence": 0.5}
    if name in SFX_SECONDS:
        body["duration_seconds"] = SFX_SECONDS[name]
    return body


def sfx_plan(names: list[str]) -> list[dict]:
    """What `bbtb sfx` would buy: only sounds with no local file and no cached ElevenLabs file."""
    out = []
    for n in names:
        prompt = SFX_PROMPTS.get(n, f"cartoon sound effect: {n}")
        dst = AUDIO / "elevenlabs" / f"sfx_{hashlib.sha256(prompt.encode()).hexdigest()[:10]}.mp3"
        if _local("sfx", n) or dst.exists():
            continue
        secs = SFX_SECONDS.get(n)
        out.append({"name": n, "prompt": prompt, "seconds": secs, "dst": dst,
                    "credits": round(secs * SFX_CREDITS_PER_SECOND) if secs else 200})
    return out


def sfx(name: str, ledger: Ledger, allow_paid: bool) -> Path | None:
    local = _local("sfx", name)
    if local:
        return local
    prompt = SFX_PROMPTS.get(name, f"cartoon sound effect: {name}")
    dst = AUDIO / "elevenlabs" / f"sfx_{hashlib.sha256(prompt.encode()).hexdigest()[:10]}.mp3"
    if dst.exists():
        return dst
    if allow_paid and _key():
        return _eleven(SFX_URL, sfx_body(name, prompt), dst, ledger, SFX_COST, f"sfx {name}")
    return synth_sfx(name)


def synth_sfx(name: str) -> Path | None:
    """Free, deterministic cartoon SFX made from noise and tones (numpy)."""
    import wave

    import numpy as np
    sr = 48000
    rng = np.random.default_rng(3)

    def lowpass(x, k):
        return np.convolve(x, np.ones(k) / k, mode="same")

    if name == "rumble":
        n = int(sr * 3.5)
        x = lowpass(lowpass(rng.standard_normal(n), 400), 200)
        x *= (0.6 + 0.4 * np.sin(2 * np.pi * 7 * np.arange(n) / sr)) * np.linspace(0.2, 1.0, n) ** 1.5
        x *= np.minimum(1, (n - np.arange(n)) / (0.4 * sr))
    elif name == "roar":
        n = int(sr * 1.6)
        t = np.arange(n) / sr
        f = 95 + 25 * np.sin(2 * np.pi * 5.5 * t) - 30 * t
        saw = 2 * ((np.cumsum(f) / sr) % 1) - 1
        x = lowpass(saw + 0.6 * lowpass(rng.standard_normal(n), 8), 6)
        x *= np.minimum(1, t / 0.12) * np.minimum(1, (1.6 - t) / 0.6)
    elif name == "whoosh":
        n = int(sr * 0.6)
        t = np.arange(n) / sr
        x = lowpass(rng.standard_normal(n), 12) * np.sin(np.pi * t / 0.6) ** 2
    elif name == "pop":
        n = int(sr * 0.15)
        t = np.arange(n) / sr
        x = np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t / 0.03)
    elif name == "scroll":
        n = int(sr * 0.9)
        t = np.arange(n) / sr
        x = (rng.standard_normal(n) * (rng.random(n) > 0.97)) * np.sin(np.pi * t / 0.9)
        x = lowpass(x, 3)
    elif name == "chomp":                       # two quick beak clacks
        n = int(sr * 0.45)
        t = np.arange(n) / sr
        x = np.zeros(n)
        for t0 in (0.0, 0.16):
            k = t >= t0
            d = t[k] - t0
            x[k] += (np.sin(2 * np.pi * 1800 * d) * 0.6 + lowpass(rng.standard_normal(k.sum()), 2)) * np.exp(-d / 0.018)
            x[k] += np.sin(2 * np.pi * 140 * d) * np.exp(-d / 0.05) * 0.8
    elif name == "crash":                       # debris burst: noise with bouncing clicks
        n = int(sr * 1.1)
        t = np.arange(n) / sr
        x = lowpass(rng.standard_normal(n), 3) * np.exp(-t / 0.25)
        for t0 in (0.08, 0.19, 0.33, 0.5):
            k = t >= t0
            x[k] += rng.standard_normal(k.sum()) * np.exp(-(t[k] - t0) / 0.02) * 0.7
    elif name == "thud":                        # low body drop
        n = int(sr * 0.6)
        t = np.arange(n) / sr
        x = np.sin(2 * np.pi * (75 - 40 * t) * t) * np.exp(-t / 0.12) + lowpass(rng.standard_normal(n), 30) * np.exp(-t / 0.05)
    else:
        return None
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.7
    dst = AUDIO / "generated" / f"synth_{name}.wav"
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    return dst


def music(mood: str | None, seconds: float, ledger: Ledger, allow_paid: bool) -> Path | None:
    if not mood:
        return None
    if mood == "auto" or mood.startswith("auto:"):        # Jason's library (bbtb music); else the cached bed
        from . import music_lib
        track = music_lib.pick(mood.split(":", 1)[1] if ":" in mood else "playful", seconds, record=allow_paid)
        if track:
            return track
        mood = "playful-adventure"
    local = _local("music", mood)
    if local:
        return local
    prompt = MUSIC_PROMPTS.get(mood, f"{mood} children's cartoon underscore, instrumental")
    length_ms = int(min(max(seconds + 3, 10), 300) * 1000)
    dst = AUDIO / "elevenlabs" / f"music_{hashlib.sha256(f'{prompt}{length_ms}'.encode()).hexdigest()[:10]}.mp3"
    if dst.exists():
        return dst
    longer = cached_music(prompt, length_ms)       # the mix trims the bed, so a longer paid track is reused
    if longer:
        return longer
    if allow_paid and _key():
        body = {"prompt": prompt, "music_length_ms": length_ms, "force_instrumental": True}
        out = _eleven(MUSIC_URL, body, dst, ledger, round(MUSIC_COST_PER_MIN * length_ms / 60000, 3), f"music {mood}")
        dst.with_suffix(".json").write_text(json.dumps({"prompt": prompt, "length_ms": length_ms}))
        return out
    return None


def cached_music(prompt: str, length_ms: int) -> Path | None:
    """A cached ElevenLabs track for the same prompt that is at least `length_ms` long (from its .json sidecar)."""
    best = None
    for side in sorted((AUDIO / "elevenlabs").glob("music_*.json")):
        try:
            info = json.loads(side.read_text())
        except (OSError, ValueError):
            continue
        mp3 = side.with_suffix(".mp3")
        if info.get("prompt") == prompt and info.get("length_ms", 0) >= length_ms and mp3.exists():
            if best is None or info["length_ms"] < best[0]:
                best = (info["length_ms"], mp3)
    return best[1] if best else None


def estimate(names: list[str], mood: str | None, seconds: float) -> float:
    """Cost of what would be generated in the approved run (local, cached and synthesized SFX are
    free; ElevenLabs is only used when ELEVENLABS_API_KEY is set)."""
    if not _key():
        return 0.0
    cost = 0.0
    for n in set(names):
        prompt = SFX_PROMPTS.get(n, f"cartoon sound effect: {n}")
        cached = AUDIO / "elevenlabs" / f"sfx_{hashlib.sha256(prompt.encode()).hexdigest()[:10]}.mp3"
        if not _local("sfx", n) and not cached.exists():
            cost += SFX_COST
    if mood and not _local("music", mood):
        cost += MUSIC_COST_PER_MIN * (seconds + 3) / 60
    return round(cost, 3)
