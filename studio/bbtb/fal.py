"""fal.ai client for Kling AI Avatar v2 Standard (talking shots), with the same spend safety as ltx.py.

Docs: https://fal.ai/docs/model-apis/model-endpoints/queue
  POST https://queue.fal.run/<model-id>        -> {request_id, status_url, response_url}
  GET  <status_url>                             -> {status: IN_QUEUE | IN_PROGRESS | COMPLETED, error?}
  GET  <response_url>                           -> {video: {url}, duration}
  Header `Authorization: Key <FAL key>`; `X-Fal-No-Retry: 1` stops fal re-running a failed request.
Models: Kling AI Avatar v2 Standard (talking head synced to OUR audio), Kling 3.0 Turbo Standard i2v (talking
shots: full-body acting + Kling's own voice, re-voiced later with ElevenLabs) and Kling 3.0 Standard i2v (action
shots, silent, start + end frame); Wan 2.7 i2v (talking shots driven by OUR audio: lip sync + action timing, owner
test 2026-10-04). Billing granularity is not documented, so estimates round UP to whole seconds.
Safety (owner rules): ledger row BEFORE the POST; no automatic retries ever; a POST without a reply is
"unknown" and blocks a resubmit; results are downloaded immediately; every row carries the approval code.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import mimetypes
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from . import env
from .ledger import Ledger

QUEUE = "https://queue.fal.run"
PLATFORM = "https://api.fal.ai/v1"
KLING_AVATAR = "fal-ai/kling-video/ai-avatar/v2/standard"
KLING3_TURBO = "fal-ai/kling-video/v3/turbo/standard/image-to-video"   # 720p, native audio always on
KLING3_STD = "fal-ai/kling-video/v3/standard/image-to-video"           # start+end frame, audio switchable
WAN27 = "fal-ai/wan/v2.7/image-to-video"   # audio_url = driving audio (lip sync); resolution MUST be sent (default 1080p)
KLING_O3_R2V = "fal-ai/kling-video/o3/standard/reference-to-video"   # start+end frame, elements (+ ONE element video
                                                                     # 3-10.05 s), NO negative prompt field (2026-10-08)
PRICES = {KLING_AVATAR: 0.0562, KLING3_TURBO: 0.112, KLING3_STD: 0.084,   # USD per output second (verified
          WAN27: 0.10, KLING_O3_R2V: 0.084}                               # 2026-10-04, GET /v1/models/pricing;
KLING3_STD_AUDIO = 0.126                                                 # Wan 2.7: model page, 720p; 1080p is 0.15)
KLING_O3_AUDIO = 0.112                                                   # O3: model page 2026-10-08 (audio off 0.084)
KEY_NAMES = ("FAL_KEY", "FAL_AI_API_KEY")
DATA_URI_LIMIT = 10_000_000
POLL_MIN, POLL_MAX_WAIT = 5.0, 30 * 60

PLAIN_ERRORS = {
    400: "fal rejected the request parameters. Nothing was generated.",
    401: "The fal key in .env was refused (check FAL_AI_API_KEY).",
    403: "fal refused this request: the key is not allowed to do it, or the account balance is empty. "
         "Check fal.ai > Billing.",
    404: "fal does not know this model id.",
    422: "fal could not use the inputs (image or audio).",
}


class FalError(RuntimeError):
    pass


def api_key() -> str | None:
    return next((v for v in (env.get(n) for n in KEY_NAMES) if v), None)


def billed_seconds(audio_seconds: float) -> int:
    """Conservative: whole seconds, rounded up (fal does not document sub-second billing)."""
    return max(1, math.ceil(audio_seconds - 1e-6))


@dataclass
class Job:
    shot_id: str
    model: str
    prompt: str
    files: dict                       # {"image_url": Path, "audio_url": Path}
    audio_seconds: float              # trimmed speech length = expected output length
    out_path: Path
    head_trim: float = 0.0            # silence removed from the start of the line (for alignment)
    endpoint: str = "kling-avatar"
    extra: dict = field(default_factory=dict)       # extra request fields (duration, negative_prompt ...)
    info: dict = field(default_factory=dict)        # pre-flight audio stats (never sent)
    required: tuple = ("image_url", "audio_url")    # file fields that must exist before submitting
    elements: list = field(default_factory=list)    # Kling 3.0 / O3 character references: image elements
                                                    # {"frontal": Path, "refs": [Path]}; O3 also takes ONE video element
                                                    # {"video": Path} (fal: an element is images OR a video, never both)

    @property
    def billed_seconds(self) -> int:
        return billed_seconds(self.audio_seconds)

    @property
    def rate(self) -> float:
        if self.model == KLING3_STD and self.extra.get("generate_audio", True):
            return KLING3_STD_AUDIO
        if self.model == KLING_O3_R2V and self.extra.get("generate_audio", False):
            return KLING_O3_AUDIO
        return PRICES[self.model]

    @property
    def cost(self) -> float:
        return round(self.rate * self.billed_seconds, 4)

    @property
    def cost_exact(self) -> float:
        return round(self.rate * self.audio_seconds, 4)

    @property
    def ready(self) -> bool:
        return (all(k in self.files and Path(self.files[k]).exists() for k in self.required)
                and all(Path(p).exists() for e in self.elements for p in element_files(e)))

    def request_hash(self) -> str:
        files = {k: hashlib.sha256(Path(p).read_bytes()).hexdigest() for k, p in sorted(self.files.items())
                 if Path(p).exists()}
        spec = {"model": self.model, "prompt": self.prompt, "files": files}
        if self.extra:
            spec["extra"] = self.extra
        if self.elements:                              # only present when used, so older requests keep their hash
            spec["elements"] = [[hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in element_files(e)]
                                for e in self.elements]          # a video is hashed only when present
        blob = json.dumps(spec, sort_keys=True)
        return "fal:" + hashlib.sha256(blob.encode()).hexdigest()[:24]

    @property
    def sidecar(self) -> Path:
        return self.out_path.with_suffix(".json")

    def done(self) -> bool:
        """The clip exists AND was made from exactly these inputs (a changed keyframe, line or prompt
        never silently reuses an old clip)."""
        if not (self.out_path.exists() and self.sidecar.exists()):
            return False
        try:
            return json.loads(self.sidecar.read_text()).get("request_hash") == self.request_hash()
        except (ValueError, OSError):
            return False


def element_files(e: dict) -> list:
    """Every file of one element: front view + reference images (image element) or the clip (O3 video element)."""
    return [e["video"]] if "video" in e else [e["frontal"], *e["refs"]]


def element_body(e: dict) -> dict:
    """One element as fal expects it: images OR a video (fal 422 otherwise, 2026-10-10)."""
    if "video" in e:
        return {"video_url": data_uri(e["video"])}
    return {"frontal_image_url": data_uri(e["frontal"]), "reference_image_urls": [data_uri(r) for r in e["refs"]]}


def data_uri(path: Path) -> str:
    raw = Path(path).read_bytes()
    if len(raw) > DATA_URI_LIMIT:
        raise FalError(f"{Path(path).name} is {len(raw) / 1e6:.1f} MB; keep inputs under {DATA_URI_LIMIT / 1e6:.0f} MB")
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


class Client:
    def __init__(self, ledger: Ledger, session: requests.Session | None = None, sleep=time.sleep,
                 approval_code: str = ""):
        self.ledger = ledger
        self.http = session or requests.Session()
        self.sleep = sleep
        self.approval_code = approval_code

    def _headers(self) -> dict:
        key = api_key()
        if not key:
            raise FalError("No fal key in .env (FAL_KEY or FAL_AI_API_KEY).")
        return {"Authorization": f"Key {key}", "Content-Type": "application/json"}

    # -- free account calls ---------------------------------------------------------------
    def balance(self) -> tuple[float | None, str]:
        """(USD balance, note). Needs an ADMIN-scope key; an ordinary key gets (None, reason)."""
        try:
            r = self.http.get(f"{PLATFORM}/account/billing", params={"expand": "credits"},
                              headers=self._headers(), timeout=30)
        except requests.RequestException as exc:
            return None, f"balance check failed ({type(exc).__name__})"
        if r.status_code == 200:
            c = (r.json() or {}).get("credits") or {}
            return c.get("current_balance"), c.get("currency", "USD")
        if r.status_code == 403:
            return None, "this key can't read the balance (needs an Admin-scope key); see fal.ai > Billing"
        return None, f"balance check returned HTTP {r.status_code}"

    def price(self, model: str) -> float | None:
        r = self.http.get(f"{PLATFORM}/models/pricing", params={"endpoint_id": model},
                          headers=self._headers(), timeout=30)
        if r.status_code != 200:
            return None
        prices = (r.json() or {}).get("prices") or []
        return prices[0]["unit_price"] if prices and prices[0].get("unit") == "seconds" else None

    # -- paid ----------------------------------------------------------------------------
    def submit(self, job: Job) -> dict:
        """Submit once (paid). Returns the ledger row with request_id/status_url/response_url."""
        if not job.ready:
            raise FalError(f"{job.shot_id}: missing input file(s) {', '.join(job.required)}. Nothing submitted.")
        if not self.approval_code:
            raise FalError(f"{job.shot_id}: no approval code. Nothing submitted.")
        rh = job.request_hash()
        prev = self.ledger.find(rh)
        if prev and prev.get("state") in ("submitted", "completed"):
            return prev
        if prev and prev.get("state") in ("intent", "unknown"):
            raise FalError(f"{job.shot_id}: an earlier submit of this exact shot may have reached fal "
                           f"(ledger state '{prev['state']}'). Check fal.ai > Requests before anything else; "
                           f"use `bbtb ltx forget {rh}` only if it is not there.")
        body = {**({"prompt": job.prompt} if job.prompt else {}), **job.extra}
        for name, path in job.files.items():
            body[name] = data_uri(path)
        if job.elements:
            body["elements"] = [element_body(e) for e in job.elements]
        self.ledger.write(rh, state="intent", kind="fal", provider="fal.ai", shot=job.shot_id, model=job.model,
                          audio_seconds=round(job.audio_seconds, 3), billed_seconds=job.billed_seconds,
                          cost_estimate=job.cost, approval_code=self.approval_code,
                          prompt=job.prompt[:2000], out=str(job.out_path))
        headers = {**self._headers(), "X-Fal-No-Retry": "1"}
        try:
            r = self.http.post(f"{QUEUE}/{job.model}", headers=headers, json=body, timeout=120)
        except (requests.Timeout, requests.ConnectionError) as exc:
            self.ledger.write(rh, state="unknown", error=f"no response to submit: {type(exc).__name__}")
            raise FalError(f"{job.shot_id}: the submit got no response, so it may or may not have been accepted. "
                           f"It will NOT be retried automatically - check fal.ai > Requests.") from None
        if r.status_code not in (200, 201, 202):
            msg = PLAIN_ERRORS.get(r.status_code) or f"fal returned HTTP {r.status_code}"
            self.ledger.write(rh, state="failed", http=r.status_code, error=env.redact(r.text[:400]), cost_estimate=0.0)
            raise FalError(f"{job.shot_id}: {msg} ({env.redact(r.text[:200])})")
        data = r.json()
        return self.ledger.write(rh, state="submitted", request_id=data.get("request_id"),
                                 status_url=data.get("status_url"), response_url=data.get("response_url"))

    def wait(self, job: Job, row: dict, max_wait: float = POLL_MAX_WAIT) -> Path:
        """Poll (free) until done, then download. Never resubmits."""
        rh = job.request_hash()
        start, backoff = time.monotonic(), POLL_MIN
        while True:
            try:
                r = self.http.get(row["status_url"], headers=self._headers(), timeout=60)
            except (requests.Timeout, requests.ConnectionError):
                r = None
            if r is not None and r.status_code in (200, 202):
                st = r.json()
                if st.get("status") == "COMPLETED":
                    if st.get("error"):
                        self.ledger.write(rh, state="failed", error=str(st.get("error"))[:400],
                                          error_type=st.get("error_type"))
                        raise FalError(f"{job.shot_id}: fal reported an error: {st.get('error')}")
                    return self._finish(job, row)
                backoff = POLL_MIN
            else:
                backoff = min(backoff * 2, 60.0)
            if time.monotonic() - start > max_wait:
                raise FalError(f"{job.shot_id}: still running after {max_wait / 60:.0f} min. "
                               f"Run `bbtb resume` later; it re-checks without resubmitting.")
            self.sleep(backoff + random.uniform(0, 1.0))

    def _finish(self, job: Job, row: dict) -> Path:
        rh = job.request_hash()
        r = self.http.get(row["response_url"], headers=self._headers(), timeout=60)
        if r.status_code != 200:
            self.ledger.write(rh, state="failed", http=r.status_code, error=env.redact(r.text[:400]))
            raise FalError(f"{job.shot_id}: fal finished with HTTP {r.status_code}: {env.redact(r.text[:200])}")
        data = r.json()
        url = (data.get("video") or {}).get("url")
        if not url:
            self.ledger.write(rh, state="failed", error=f"no video url: {str(data)[:300]}")
            raise FalError(f"{job.shot_id}: fal finished but returned no video.")
        self._download(url, job.out_path)
        sha = hashlib.sha256(job.out_path.read_bytes()).hexdigest()
        self.ledger.write(rh, state="completed", request_id=row.get("request_id"), result_url=url,
                          output_seconds=data.get("duration"), output_sha256=sha)
        job.sidecar.write_text(json.dumps({"request_hash": rh, "request_id": row.get("request_id"),
                                           "model": job.model, "result_url": url, "head_trim": job.head_trim,
                                           "audio_seconds": job.audio_seconds, "output_seconds": data.get("duration"),
                                           "cost_estimate": job.cost,
                                           "approval_code": row.get("approval_code") or self.approval_code},
                                          indent=2))
        return job.out_path

    def _download(self, url: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(4):                       # downloading is free; only the generation is paid
            try:
                with self.http.get(url, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    tmp = dst.with_suffix(".part")
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(1 << 20):
                            f.write(chunk)
                    tmp.rename(dst)
                    return
            except requests.RequestException:
                self.sleep(2 ** attempt)
        raise FalError(f"could not download {dst.name}; run `bbtb resume` soon (the link lasts about 7 days).")

    def run(self, job: Job) -> Path:
        if job.done():
            return job.out_path
        return self.wait(job, self.submit(job))
