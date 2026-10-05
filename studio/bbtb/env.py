"""Read secrets from .env (git-ignored). Values are never printed or logged."""
from __future__ import annotations

import os

from .paths import ENV_FILE


def load() -> dict[str, str]:
    values = {}
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text().splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def get(name: str) -> str | None:
    return os.environ.get(name) or load().get(name)


def require(name: str, purpose: str) -> str:
    value = get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Add it to .env to {purpose} (see .env.example).")
    return value


def redact(text: str) -> str:
    """Remove any known secret values from text before it is shown or logged."""
    for v in load().values():
        if v and len(v) > 6:
            text = text.replace(v, "<redacted>")
    return text
