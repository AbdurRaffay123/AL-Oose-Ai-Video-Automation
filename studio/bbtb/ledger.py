"""Append-only spend ledger (productions/<ep>/ledger.jsonl).

Every paid call is recorded BEFORE the request is sent (state "intent"), because the LTX API
has no idempotency key: if the network drops after a POST, the intent row is what stops us from
paying twice. States: intent -> submitted -> completed | failed | unknown | expired.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ACTIVE = {"intent", "submitted", "completed", "unknown"}


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def latest(self) -> dict[str, dict]:
        """Most recent row per request hash."""
        out = {}
        for r in self.rows():
            out[r["request_hash"]] = {**out.get(r["request_hash"], {}), **r}
        return out

    def find(self, request_hash: str) -> dict | None:
        return self.latest().get(request_hash)

    def write(self, request_hash: str, **fields) -> dict:
        row = {"request_hash": request_hash, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **fields}
        with open(self.path, "a") as f:
            f.write(json.dumps(row) + "\n")
        return row

    def spent(self) -> float:
        """Committed spend: everything not known to have failed before billing."""
        return round(sum(r.get("cost_estimate", 0.0) for r in self.latest().values()
                         if r.get("state") in ACTIVE), 4)
