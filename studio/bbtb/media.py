"""Thin FFmpeg/ffprobe helpers. Inputs are never modified; every call writes a new file."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SR = 48000


class MediaError(RuntimeError):
    pass


def run(args: list[str]) -> str:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-6:])
        raise MediaError(f"{Path(args[0]).name} failed:\n{tail}")
    return proc.stdout + proc.stderr


def run_bytes(args: list[str]) -> bytes:
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.decode(errors="replace").strip().splitlines()[-6:])
        raise MediaError(f"{Path(args[0]).name} failed:\n{tail}")
    return proc.stdout


def ffmpeg(*args: str) -> str:
    return run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args])


def duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(out)["format"]["duration"])


def to_wav(src: Path, dst: Path, trim_silence: bool = False, denoise: bool = False) -> Path:
    """Mono 48 kHz 16-bit WAV copy; optionally trim leading/trailing silence and reduce steady background hiss
    (a gentle FFT denoiser + 80 Hz high-pass, for noisy original recordings such as the Snail's)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    af = ["aresample=48000"]
    if trim_silence:
        af = ["silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05",
              "areverse",
              "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.12",
              "areverse", "aresample=48000"]
    if denoise:
        af = ["highpass=f=80", "afftdn=nr=24:nf=-38", "agate=threshold=0.02:ratio=4:attack=5:release=120"] + af
    ffmpeg("-i", str(src), "-ac", "1", "-ar", str(SR), "-af", ",".join(af), "-c:a", "pcm_s16le", str(dst))
    return dst


def to_mp3(src: Path, dst: Path, lead: float = 0.0, tail: float = 0.0) -> Path:
    """MP3 copy for upload (LTX does not accept PCM); optional silence padding in seconds."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    af = f"adelay={int(lead * 1000)}:all=1,apad=pad_dur={tail}"
    ffmpeg("-i", str(src), "-ac", "1", "-ar", "44100", "-af", af, "-c:a", "libmp3lame", "-b:a", "192k", str(dst))
    return dst


def concat_audio(srcs: list[Path], dst: Path, gap: float = 0.3, max_seconds: float = 30.0) -> Path:
    """Join clips with short gaps (for voice-clone references), capped at max_seconds."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    inputs, filt = [], []
    for i, s in enumerate(srcs):
        inputs += ["-i", str(s)]
        filt.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur={gap}[a{i}]")
    joined = "".join(f"[a{i}]" for i in range(len(srcs)))
    filt.append(f"{joined}concat=n={len(srcs)}:v=0:a=1,atrim=0:{max_seconds}[out]")
    ffmpeg(*inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-c:a", "pcm_s16le", str(dst))
    return dst


def loudness(path: Path) -> dict:
    """Integrated loudness (LUFS) and true peak (dBTP) via ebur128."""
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
               "-f", "null", "-"])
    lufs = peak = None
    for line in out.splitlines()[::-1]:
        line = line.strip()
        if lufs is None and line.startswith("I:"):
            lufs = float(line.split()[1])
        if peak is None and line.startswith("Peak:"):
            peak = float(line.split()[1])
    return {"lufs": lufs, "true_peak": peak}
