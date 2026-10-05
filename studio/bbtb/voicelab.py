"""Objective voice measurements (numpy only), so voice quality is not judged on trust.

profile(): pitch (F0) median/range, voiced fraction, spectral brightness, speaking rate.
Used to compare a generated line against the character's original recordings; speaker
similarity and intelligibility (Whisper / Resemblyzer) are measured in voice_eval.py, which
runs in the separate .venv-voice environment.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

SR = 16000


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def f0_track(x: np.ndarray, fmin: float = 70.0, fmax: float = 900.0, frame: int = 1024, hop: int = 160,
             threshold: float = 0.30) -> np.ndarray:
    """YIN pitch per 10 ms frame; NaN where unvoiced/silent."""
    tau_min, tau_max = int(SR / fmax), int(SR / fmin)
    rms_gate = 0.02 * (np.max(np.abs(x)) + 1e-9)
    out = []
    for start in range(0, len(x) - frame - tau_max, hop):
        w = x[start:start + frame + tau_max]
        if np.sqrt(np.mean(w[:frame] ** 2)) < rms_gate:
            out.append(np.nan)
            continue
        d = np.array([np.sum((w[:frame] - w[t:t + frame]) ** 2) for t in range(tau_max + 1)])
        cmnd = np.ones_like(d)
        cmnd[1:] = d[1:] * np.arange(1, len(d)) / (np.cumsum(d[1:]) + 1e-12)
        cand = np.where(cmnd[tau_min:] < threshold)[0]
        if len(cand) == 0:
            out.append(np.nan)
            continue
        t = cand[0] + tau_min
        while t + 1 < len(cmnd) and cmnd[t + 1] < cmnd[t]:
            t += 1
        out.append(SR / t)
    return np.array(out)


def profile(path: Path) -> dict:
    x = load(path)
    f0 = f0_track(x)
    voiced = f0[~np.isnan(f0)]
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) if len(x) else np.zeros(1)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    centroid = float(np.sum(freqs * spec) / (np.sum(spec) + 1e-9))
    active = np.abs(x) > 0.02 * (np.max(np.abs(x)) + 1e-9)
    return {
        "seconds": round(len(x) / SR, 2),
        "f0_median": round(float(np.median(voiced)), 1) if len(voiced) else None,
        "f0_p10": round(float(np.percentile(voiced, 10)), 1) if len(voiced) else None,
        "f0_p90": round(float(np.percentile(voiced, 90)), 1) if len(voiced) else None,
        "voiced_frac": round(len(voiced) / max(len(f0), 1), 2),
        "brightness_hz": round(centroid),
        "active_seconds": round(float(active.sum()) / SR, 2),
    }


def semitones(a: float, b: float) -> float:
    return float(12 * np.log2(a / b))
