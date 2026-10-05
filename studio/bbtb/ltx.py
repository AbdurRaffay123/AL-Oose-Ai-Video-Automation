"""LTX API (V2, async) client with spend safety.

Docs: https://docs.ltx.io  (V1 sync endpoints are deprecated after 2026-10-26; V2 only here.)
  POST /v2/image-to-video | /v2/audio-to-video  -> 202 {id}
  GET  /v2/<endpoint>/<id> -> {status: pending|processing|completed|failed, result, error}
Safety:
  * cost estimate per job from the published per-second prices;
  * ledger row written BEFORE the POST (no idempotency key exists) -> a repeat with the same
    request hash is refused unless the earlier one failed;
  * a POST that times out is marked "unknown" and is never retried automatically;
  * 402/422 stop immediately; 429/5xx on polling back off; polling >= 5 s with jitter;
  * outputs are downloaded immediately (result URLs expire).
"""
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import random
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from . import env
from .ledger import Ledger

API = "https://api.ltx.io"
PRICES = {  # USD per second, verified 2026-10-03 at https://docs.ltx.io/pricing
    ("image-to-video", "ltx-2-3-pro"): {"720p": 0.04, "1080p": 0.08},
    ("image-to-video", "ltx-2-3-fast"): {"720p": 0.03, "1080p": 0.06},
    ("audio-to-video", "ltx-2-3-pro"): {"720p": 0.06, "1080p": 0.10},
}
RESOLUTION = {("9:16", "720p"): "720x1280", ("9:16", "1080p"): "1080x1920",
              ("16:9", "720p"): "1280x720", ("16:9", "1080p"): "1920x1080"}
DATA_URI_LIMIT = {"image": 7_000_000, "audio": 15_000_000}
POLL_MIN, POLL_MAX_WAIT = 5.0, 30 * 60

PLAIN_ERRORS = {
    400: "LTX rejected the request parameters (invalid_request_error). Nothing was generated.",
    401: "The LTX API key in .env was refused (authentication_error).",
    402: "Your LTX account is out of credits (insufficient_funds_error). Top up in the LTX console, then re-run.",
    403: "This LTX key isn't allowed to use that model/endpoint (permission_error).",
    422: "LTX's safety filter rejected this shot (content_filtered_error). Rephrase the ACTION/prompt.",
}


class LtxError(RuntimeError):
    pass


@dataclass
class Job:
    shot_id: str
    endpoint: str                  # image-to-video | audio-to-video
    payload: dict                  # JSON fields except the *_uri file references
    files: dict                    # {"image_uri": Path, "last_frame_uri": Path, "audio_uri": Path}
    billed_seconds: float
    resolution_tier: str           # 720p | 1080p
    out_path: Path

    @property
    def cost(self) -> float:
        rate = PRICES[(self.endpoint, self.payload["model"])][self.resolution_tier]
        return round(rate * self.billed_seconds, 4)

    @property
    def ready(self) -> bool:
        """An audio-to-video job is only submittable once its real (final) voice file exists."""
        return self.endpoint != "audio-to-video" or "audio_uri" in self.files

    def request_hash(self) -> str:
        files = {k: hashlib.sha256(Path(p).read_bytes()).hexdigest() for k, p in sorted(self.files.items())}
        if not self.ready:
            files["audio_uri"] = "pending-final-voice"
        blob = json.dumps({"endpoint": self.endpoint, "payload": self.payload, "files": files}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:24]


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    raw = Path(path).read_bytes()
    kind = mime.split("/")[0]
    limit = DATA_URI_LIMIT.get(kind)
    if limit and len(raw) > limit:
        raise LtxError(f"{Path(path).name} is {len(raw) / 1e6:.1f} MB; LTX data URIs allow {limit / 1e6:.0f} MB for {kind}")
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


class Client:
    def __init__(self, ledger: Ledger, session: requests.Session | None = None, api: str = API,
                 sleep=time.sleep):
        self.ledger = ledger
        self.http = session or requests.Session()
        self.api = api
        self.sleep = sleep

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {env.require('LTX_API_KEY', 'generate video with LTX')}",
                "Content-Type": "application/json"}

    # -- submit -------------------------------------------------------------------------
    def submit(self, job: Job) -> str:
        """Submit once. Returns the LTX job id. Refuses duplicates of an active request."""
        if not job.ready:
            raise LtxError(f"{job.shot_id}: its voice is not final yet, so there is no audio to send. Nothing submitted.")
        rh = job.request_hash()
        prev = self.ledger.find(rh)
        if prev and prev.get("state") in ("submitted", "completed"):
            return prev["job_id"]
        if prev and prev.get("state") in ("intent", "unknown"):
            raise LtxError(f"{job.shot_id}: an earlier submit of this exact shot may have reached LTX "
                           f"(ledger state '{prev['state']}'). Check the LTX console before retrying; "
                           f"use `bbtb ltx forget {rh}` only if you are sure it was not billed.")
        body = dict(job.payload)
        for field, path in job.files.items():
            body[field] = data_uri(path)
        self.ledger.write(rh, state="intent", kind="ltx", shot=job.shot_id, endpoint=job.endpoint,
                          model=job.payload["model"], billed_seconds=job.billed_seconds,
                          cost_estimate=job.cost, params={k: v for k, v in job.payload.items() if k != "prompt"},
                          prompt=job.payload.get("prompt", "")[:2000], out=str(job.out_path))
        try:
            r = self.http.post(f"{self.api}/v2/{job.endpoint}", headers=self._headers(), json=body, timeout=120)
        except (requests.Timeout, requests.ConnectionError) as exc:
            self.ledger.write(rh, state="unknown", error=f"no response to submit: {type(exc).__name__}")
            raise LtxError(f"{job.shot_id}: the submit got no response, so it may or may not have been "
                           f"accepted. It will NOT be retried automatically - check the LTX console.") from None
        if r.status_code != 202 and r.status_code != 200:
            msg = PLAIN_ERRORS.get(r.status_code) or f"LTX returned HTTP {r.status_code}"
            self.ledger.write(rh, state="failed", http=r.status_code, error=env.redact(r.text[:400]), cost_estimate=0.0)
            if r.status_code == 429:
                msg = f"LTX queue is full (429). Wait {r.headers.get('Retry-After', 'a minute')} s and re-run; nothing was billed."
            raise LtxError(f"{job.shot_id}: {msg}")
        job_id = r.json()["id"]
        self.ledger.write(rh, state="submitted", job_id=job_id)
        return job_id

    # -- poll + download ----------------------------------------------------------------
    def wait(self, job: Job, job_id: str, max_wait: float = POLL_MAX_WAIT) -> Path:
        rh = job.request_hash()
        start, backoff = time.monotonic(), POLL_MIN
        while True:
            try:
                r = self.http.get(f"{self.api}/v2/{job.endpoint}/{job_id}", headers=self._headers(), timeout=60)
            except (requests.Timeout, requests.ConnectionError):
                r = None
            if r is not None and r.status_code == 404:
                self.ledger.write(rh, state="expired", error="job status no longer available (24 h)")
                raise LtxError(f"{job.shot_id}: LTX no longer has this job (status expires after 24 h).")
            if r is not None and r.status_code == 200:
                data = r.json()
                status = data.get("status")
                if status == "completed":
                    url = (data.get("result") or {}).get("video_url") or _first_url(data.get("result"))
                    self._download(url, job.out_path)
                    sha = hashlib.sha256(job.out_path.read_bytes()).hexdigest()
                    self.ledger.write(rh, state="completed", job_id=job_id, output_sha256=sha)
                    return job.out_path
                if status == "failed":
                    err = data.get("error") or {}
                    self.ledger.write(rh, state="failed", job_id=job_id, error=json.dumps(err)[:400])
                    raise LtxError(f"{job.shot_id}: LTX reported the job failed: {err.get('message', err)}")
                backoff = POLL_MIN
            else:
                retry_after = r.headers.get("Retry-After") if r is not None else None
                backoff = min(float(retry_after) if retry_after else backoff * 2, 60.0)
            if time.monotonic() - start > max_wait:
                raise LtxError(f"{job.shot_id}: still running after {max_wait / 60:.0f} min. "
                               f"Run `bbtb resume` later; it re-checks without resubmitting.")
            self.sleep(backoff + random.uniform(0, 1.0))

    def _download(self, url: str, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(4):
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
        raise LtxError(f"could not download the finished video for {dst.name}; run `bbtb resume` soon "
                       f"(the result link expires).")

    def run(self, job: Job) -> Path:
        if job.out_path.exists():
            return job.out_path
        return self.wait(job, self.submit(job))


def _first_url(result) -> str:
    if isinstance(result, dict):
        for v in result.values():
            if isinstance(v, str) and v.startswith("http"):
                return v
    raise LtxError(f"LTX finished but returned no video URL: {result!r}"[:300])
