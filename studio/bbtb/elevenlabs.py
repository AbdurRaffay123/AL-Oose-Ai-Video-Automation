"""ElevenLabs API client: instant voice cloning, text-to-speech, free account checks.

Official endpoints (https://elevenlabs.io/docs/api-reference):
  POST /v1/voices/add                     instant voice clone (multipart: name, files[], remove_background_noise)
  GET  /v1/voices/{voice_id}              voice exists? (free)
  POST /v1/text-to-speech/{voice_id}      speech; billed in credits per character (voice tests)
  POST /v1/text-to-speech/{voice_id}/with-timestamps
                                          batched speech + per-character timings (script renders)
  GET  /v1/user/subscription              plan, credits used/limit, IVC allowed, voice slots (free)
  GET  /v1/models                         model ids + character_cost_multiplier (free)
  POST /v1/speech-to-speech/{voice_id}    Voice Changer: re-voice a performance, keeping its timing
                                          (billed per minute of audio; ~1000 credits / $0.12 per minute)
Key: ELEVENLABS_API_KEY (ELEVEN_LABS_API_KEY also accepted). Never printed; error text is redacted.
Safety (owner rule): every paid request is written to the ledger before it is sent. ANY failure -
timeout or error response - is logged "unknown", production stops, and the same request is refused
until the owner checks ElevenLabs > History and clears it (`bbtb voices forget <hash>`). Never retried.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import requests

from . import env

API = "https://api.elevenlabs.io"
DEFAULT_MODEL = "eleven_multilingual_v2"     # ElevenLabs recommends it for animation; IVC-compatible
DEFAULT_SETTINGS = {"stability": 0.45, "similarity_boost": 0.85, "style": 0.3, "use_speaker_boost": True, "speed": 1.0}
FALLBACK_MULTIPLIER = 1.0                     # credits per character if /v1/models can't be read
KEY_NAMES = ("ELEVENLABS_API_KEY", "ELEVEN_LABS_API_KEY")
PERMISSIONS_NEEDED = {
    "text_to_speech": "generate speech",
    "voices_read": "verify saved voice IDs",
    "voices_write": "create voice clones",
    "user_read": "check remaining credits before spending",
    "models_read": "read each model's credit rate",
}


class ElevenLabsError(RuntimeError):
    pass


def api_key() -> str:
    for name in KEY_NAMES:
        value = env.get(name)
        if value:
            return value
    raise ElevenLabsError("No ElevenLabs API key found. Add ELEVENLABS_API_KEY=... to .env (it is git-ignored).")


def plain_error(r: requests.Response, action: str) -> str:
    try:
        detail = r.json().get("detail", {})
    except ValueError:
        detail = {}
    if isinstance(detail, str):
        detail = {"message": detail}
    status = (detail.get("status") or detail.get("code") or "").lower()
    msg = env.redact(str(detail.get("message", r.text[:200])))
    if status == "missing_permissions" or "missing the permission" in msg:
        perm = msg.split("permission")[-1].split()[0] if "permission" in msg else "?"
        return (f"Your ElevenLabs API key is not allowed to {action} (missing permission '{perm}'). In ElevenLabs "
                f"> Developers > API keys, edit the key and enable: " + ", ".join(PERMISSIONS_NEEDED) + ".")
    if status in ("invalid_api_key", "unauthorized") or r.status_code == 401 and "quota" not in status:
        return "ElevenLabs rejected the API key (invalid or revoked). Check ELEVENLABS_API_KEY in .env."
    if status == "quota_exceeded" or "quota" in msg.lower() or r.status_code == 402:
        return "Not enough ElevenLabs credits for this request. Nothing was generated. Top up or wait for the monthly reset."
    if status == "voice_not_found" or r.status_code == 404:
        return "ElevenLabs can't find that voice ID (deleted, or from another account). Re-run `bbtb voices verify`."
    if r.status_code == 429 or status in ("too_many_concurrent_requests", "system_busy"):
        return "ElevenLabs is busy or rate-limiting (429). Nothing was generated; wait a minute and re-run."
    return f"ElevenLabs could not {action} (HTTP {r.status_code}: {msg})."


class Client:
    def __init__(self, session: requests.Session | None = None, api: str = API):
        self.http = session or requests.Session()
        self.api = api

    def _h(self, json_body: bool = True) -> dict:
        h = {"xi-api-key": api_key()}
        if json_body:
            h["Content-Type"] = "application/json"
        return h

    # ---- free checks ------------------------------------------------------------------
    def subscription(self) -> dict:
        r = self.http.get(f"{self.api}/v1/user/subscription", headers=self._h(False), timeout=30)
        if not r.ok:
            raise ElevenLabsError(plain_error(r, "read your plan and credits"))
        return r.json()

    def cost_multiplier(self, model_id: str) -> float | None:
        r = self.http.get(f"{self.api}/v1/models", headers=self._h(False), timeout=30)
        if not r.ok:
            return None
        for m in r.json():
            if m.get("model_id") == model_id:
                return float((m.get("model_rates") or {}).get("character_cost_multiplier", 1.0))
        return None

    def voice_exists(self, voice_id: str) -> dict:
        r = self.http.get(f"{self.api}/v1/voices/{voice_id}", headers=self._h(False), timeout=30)
        if not r.ok:
            raise ElevenLabsError(plain_error(r, "read that voice"))
        d = r.json()
        return {"voice_id": d.get("voice_id"), "name": d.get("name"), "category": d.get("category")}

    # ---- cloning (uses a voice slot) --------------------------------------------------
    def clone(self, name: str, files: list[Path], description: str = "", remove_noise: bool = False) -> str:
        handles = [("files", (Path(f).name, open(f, "rb"), "audio/wav")) for f in files]
        try:
            r = self.http.post(f"{self.api}/v1/voices/add", headers=self._h(False),
                               data={"name": name, "description": description,
                                     "remove_background_noise": str(remove_noise).lower()},
                               files=handles, timeout=180)
        finally:
            for _, (_, fh, _) in handles:
                fh.close()
        if not r.ok:
            raise ElevenLabsError(plain_error(r, "create a voice clone"))
        d = r.json()
        if d.get("requires_verification"):
            raise ElevenLabsError(f"ElevenLabs created voice {d.get('voice_id')} but requires verification before use. "
                                  "Finish verification in the ElevenLabs app, then run `bbtb voices verify`.")
        return d["voice_id"]

    def delete_voice(self, voice_id: str) -> None:
        """Permanently remove a voice from the account (frees its slot). Cannot be undone."""
        r = self.http.delete(f"{self.api}/v1/voices/{voice_id}", headers=self._h(False), timeout=60)
        if not r.ok:
            raise ElevenLabsError(plain_error(r, "delete that voice"))

    # ---- speech (paid) ----------------------------------------------------------------
    def _guard(self, ledger, request_hash: str) -> None:
        prev = ledger.find(request_hash)
        if prev and prev.get("state") in ("intent", "unknown"):
            raise ElevenLabsError(f"An earlier attempt at this exact request ended without a confirmed result "
                                  f"(state '{prev['state']}'; {prev.get('error', 'no detail')}). It may have been charged. "
                                  f"Check ElevenLabs > History, then clear it with `bbtb voices forget {request_hash}`. "
                                  "Not retried.")

    def _post_paid(self, url: str, body: dict, ledger, request_hash: str, meta: dict, credits_estimate: float):
        self._guard(ledger, request_hash)
        ledger.write(request_hash, state="intent", kind="tts", provider="elevenlabs", credits_estimate=credits_estimate,
                     cost_estimate=0.0, **meta)
        try:
            r = self.http.post(url, headers=self._h(), params={"output_format": "mp3_44100_128"}, json=body, timeout=180)
        except (requests.Timeout, requests.ConnectionError) as exc:
            ledger.write(request_hash, state="unknown", error=f"no response: {type(exc).__name__}")
            raise ElevenLabsError("ElevenLabs did not answer, so this may or may not have been charged. Logged as "
                                  "'unknown' and NOT retried. Check ElevenLabs > History.") from None
        if not r.ok:
            msg = plain_error(r, "generate speech")
            ledger.write(request_hash, state="unknown", http=r.status_code, error=env.redact(msg)[:300])
            raise ElevenLabsError(msg + " Logged as 'unknown'; not retried.")
        return r

    def tts(self, voice_id: str, text: str, model_id: str, settings: dict, dst: Path, ledger, request_hash: str,
            meta: dict, credits_estimate: float) -> Path:
        """One short line (voice tests)."""
        body = {"text": text, "model_id": model_id, "voice_settings": settings}
        r = self._post_paid(f"{self.api}/v1/text-to-speech/{voice_id}", body, ledger, request_hash,
                            {"voice_id": voice_id, "model": model_id, **meta}, credits_estimate)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(r.content)
        ledger.write(request_hash, state="completed", bytes=len(r.content), request_id=r.headers.get("request-id"),
                     output_sha256=hashlib.sha256(r.content).hexdigest())
        return dst

    def tts_with_timestamps(self, voice_id: str, text: str, model_id: str, settings: dict, dst_audio: Path,
                            dst_alignment: Path, ledger, request_hash: str, meta: dict, credits_estimate: float) -> Path:
        """A whole batch of lines in ONE request; saves the audio and the character alignment."""
        body = {"text": text, "model_id": model_id, "voice_settings": settings}
        r = self._post_paid(f"{self.api}/v1/text-to-speech/{voice_id}/with-timestamps", body, ledger, request_hash,
                            {"voice_id": voice_id, "model": model_id, **meta}, credits_estimate)
        d = r.json()
        align = d.get("alignment") or d.get("normalized_alignment")
        if not d.get("audio_base64") or not align:
            ledger.write(request_hash, state="unknown", error="response had no audio or alignment")
            raise ElevenLabsError("ElevenLabs answered without audio/timings (probably charged). Logged as 'unknown'.")
        audio = base64.b64decode(d["audio_base64"])
        dst_audio.parent.mkdir(parents=True, exist_ok=True)
        dst_audio.write_bytes(audio)
        dst_alignment.write_text(json.dumps({"text": text, **align}))
        ledger.write(request_hash, state="completed", bytes=len(audio), request_id=r.headers.get("request-id"),
                     output_sha256=hashlib.sha256(audio).hexdigest())
        return dst_audio


    def speech_to_speech(self, voice_id: str, audio: Path, model_id: str, settings: dict, dst: Path, ledger,
                         request_hash: str, meta: dict, credits_estimate: float) -> Path:
        """Re-voice `audio` as `voice_id` (same words and timing). Same safety as speech: logged first,
        any failure is 'unknown', never retried."""
        self._guard(ledger, request_hash)
        ledger.write(request_hash, state="intent", kind="sts", provider="elevenlabs", voice_id=voice_id,
                     model=model_id, credits_estimate=credits_estimate, cost_estimate=0.0, **meta)
        try:
            with open(audio, "rb") as fh:
                r = self.http.post(f"{self.api}/v1/speech-to-speech/{voice_id}", headers=self._h(False),
                                   params={"output_format": "mp3_44100_128"},
                                   data={"model_id": model_id, "voice_settings": json.dumps(settings),
                                         "remove_background_noise": "true"},
                                   files={"audio": (Path(audio).name, fh, "audio/wav")}, timeout=180)
        except (requests.Timeout, requests.ConnectionError) as exc:
            ledger.write(request_hash, state="unknown", error=f"no response: {type(exc).__name__}")
            raise ElevenLabsError("ElevenLabs did not answer, so this may or may not have been charged. Logged as "
                                  "'unknown' and NOT retried. Check ElevenLabs > History.") from None
        if not r.ok:
            msg = plain_error(r, "re-voice the line")
            ledger.write(request_hash, state="unknown", http=r.status_code, error=env.redact(msg)[:300])
            raise ElevenLabsError(msg + " Logged as 'unknown'; not retried.")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(r.content)
        ledger.write(request_hash, state="completed", bytes=len(r.content), request_id=r.headers.get("request-id"),
                     output_sha256=hashlib.sha256(r.content).hexdigest())
        return dst


def request_hash(voice_id: str, model_id: str, settings: dict, text: str) -> str:
    blob = json.dumps({"v": voice_id, "m": model_id, "s": settings, "t": text}, sort_keys=True)
    return "el:" + hashlib.sha256(blob.encode()).hexdigest()[:20]
