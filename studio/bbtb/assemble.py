"""Local rendering + final assembly (FFmpeg). Free: nothing here calls a paid API."""
from __future__ import annotations

from pathlib import Path

from . import media
from .shots import Shot

FPS = 24
LEAD = {"ltx_a2v": 0.15, "kling_avatar": 0.15, "kling3_talk": 0.0, "kling3_talk_std": 0.0, "kling3_action": 0.30, "ltx_i2v": 0.30, "local_still": 0.15, "local_endcard": 0.40, "local_flap": 0.15,
        "local_anim": 0.25, "wan_talk": 0.15, "reuse_clip": 0.25, "reuse_talk": 0.0}
GAP = 0.25   # between consecutive lines inside one shot


def line_offsets(shot: Shot, seconds: dict[str, float]) -> list[tuple[str, float]]:
    """Where each voiced line starts, relative to the start of its shot. A trimmed Kling 3.0 talking shot gives a
    negative offset: its re-voiced audio is tied to the clip, so the same seconds are cut from the audio too."""
    t, out = LEAD.get(shot.engine, 0.2) - (shot.trim if shot.engine in ("kling3_talk", "kling3_talk_std") else 0.0), []
    for lid in shot.lines:
        at = (getattr(shot, "line_at", None) or {}).get(lid)     # voice-over with a fixed start (tag say:<s>)
        out.append((lid, at if at is not None else t))
        if at is None:
            t += seconds[lid] + GAP
    return out


def still_clip(image: Path, seconds: float, size: tuple[int, int], dst: Path, push: float = 0.06,
               fade_in: float = 0.0) -> Path:
    """Slow push-in on a still (free camera move), optionally fading in from black."""
    W, H = size
    frames = max(1, round(seconds * FPS))
    zoom = f"1+{push}*on/{frames}"
    fade = f",fade=t=in:st=0:d={fade_in}" if fade_in else ""
    vf = (f"scale={W * 4}:{H * 4},zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={frames}:s={W}x{H}:fps={FPS}{fade},format=yuv420p")
    media.ffmpeg("-loop", "1", "-i", str(image), "-vf", vf, "-frames:v", str(frames),
                 "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(dst))
    return dst


def fit_clip(src: Path, seconds: float, size: tuple[int, int], dst: Path, lead: float = 0.0,
             skip: float = 0.0) -> Path:
    """Generated clip -> exact size, 24 fps, exact duration (trim, or hold last frame), no audio.
    `lead` holds the first frame that long first (a clip made from trimmed speech starts on the first word).
    `skip` cuts that many seconds from the start of the clip (script tag trim:<s>)."""
    W, H = size
    start = f"start_mode=clone:start_duration={lead:.3f}:" if lead > 0 else ""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
          f"tpad={start}stop_mode=clone:stop_duration={seconds},format=yuv420p")
    media.ffmpeg(*(["-ss", f"{skip:.3f}"] if skip > 0 else []), "-i", str(src), "-vf", vf, "-t", f"{seconds:.3f}", "-an",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(dst))
    return dst


def srt_time(t: float) -> str:
    ms = int(round(max(t, 0.0) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(cues: list[tuple[str, float, float]], dst: Path) -> Path:
    """Caption text as an .srt sidecar for CapCut / DaVinci (captions are never burned into the video)."""
    blocks = [f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n" for i, (text, a, b) in enumerate(cues, 1)]
    dst.write_text("\n".join(blocks))
    return dst


def concat(clips: list[Path], dst: Path) -> Path:
    lst = dst.with_suffix(".txt")
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    media.ffmpeg("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dst))
    return dst


def mix(shots: list[Shot], lines: dict[str, dict], sfx: dict[str, Path], music: Path | None,
        total: float, dst: Path) -> Path:
    """Dialogue + SFX + ducked music bed, loudness-normalised to -16 LUFS (owner, 2026-10-04)."""
    inputs, chains, voice_labels, fx_labels = [], [], [], []
    seconds = {k: v["seconds"] for k, v in lines.items()}
    t0 = 0.0
    n = 0
    for s in shots:
        for lid, off in line_offsets(s, seconds):
            inputs += ["-i", lines[lid]["path"]]
            ms = int((t0 + max(off, 0.0)) * 1000)          # a negative offset is cut from the audio instead
            cut = f"atrim=start={-off:.3f},asetpts=PTS-STARTPTS," if off < 0 else ""
            chains.append(f"[{n}:a]{cut}aresample=48000,aformat=channel_layouts=mono,adelay={ms}:all=1[v{n}]")
            voice_labels.append(f"[v{n}]")
            n += 1
        for fx in s.sfx:
            path = sfx.get(fx["name"])
            if path is None:
                continue
            inputs += ["-i", str(path)]
            ms = int((t0 + fx.get("at", 0.0)) * 1000)
            chains.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=mono,volume={fx.get('vol', 0.8)},adelay={ms}:all=1[f{n}]")
            fx_labels.append(f"[f{n}]")
            n += 1
        t0 += s.duration
    if not voice_labels:                                # a silent production (2026-10-08 model test): silent voice bus
        inputs += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=mono"]
        chains.append(f"[{n}:a]anull[vox]")
        n += 1
    else:
        chains.append(f"{''.join(voice_labels)}amix=inputs={len(voice_labels)}:normalize=0,apad=whole_dur={total}[vox]")
    bus = "[vox]"
    if music is not None:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        chains.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=mono,volume=0.32,atrim=0:{total},"
                      f"afade=t=in:d=1,afade=t=out:st={max(total - 2, 0)}:d=2[mus]")
        chains.append("[vox]asplit=2[vox1][vkey]")
        chains.append("[mus][vkey]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[ducked]")
        bus_parts = ["[vox1]", "[ducked]"]
        n += 1
    else:
        bus_parts = [bus]
    all_parts = bus_parts + fx_labels
    chains.append(f"{''.join(all_parts)}amix=inputs={len(all_parts)}:normalize=0,atrim=0:{total}[out]")
    raw = dst.with_suffix(".raw.wav")
    media.ffmpeg(*inputs, "-filter_complex", ";".join(chains), "-map", "[out]", "-ar", "48000",
                 "-c:a", "pcm_s16le", str(raw))
    return normalize(raw, dst, target=-16.0)


def normalize(src: Path, dst: Path, target: float = -14.0, peak_db: float = -3.0) -> Path:
    """Measure, then apply one static gain + a true-peak limiter (speech with pauses fools
    single-pass loudnorm). Two short passes keep it accurate within ~0.5 LU."""
    cur = src
    for i in range(2):
        lufs = media.loudness(cur)["lufs"]
        if lufs is None or abs(lufs - target) < 0.4:
            break
        nxt = dst.with_suffix(f".pass{i}.wav")
        limit = 10 ** (peak_db / 20)
        media.ffmpeg("-i", str(cur), "-af", f"volume={target - lufs:.2f}dB,alimiter=limit={limit:.3f}:level=disabled",
                     "-ar", "48000", "-c:a", "pcm_s16le", str(nxt))
        cur = nxt
    if cur != dst:
        cur.replace(dst)
    for leftover in dst.parent.glob(dst.stem + ".*.wav"):
        leftover.unlink(missing_ok=True)
    return dst


def title_card(video: Path, layers: list[tuple[Path, float]], footage: float, total: float, size: tuple[int, int],
               dst: Path, fade_in: float = 0.4) -> Path:
    """End card from the marketing title video (owner 2026-10-05): its first `footage` seconds, VIDEO ONLY (the
    original's voice and music are never used), centred 4:5 in 9:16 over a blurred copy, the last frame held to
    `total`, a fade in, and text layers (full-frame PNGs) fading in at their times. The original file is only read."""
    W, H = size
    fh = round(W * 1350 / 1080 / 2) * 2
    chain = [f"[0:v]trim=0:{footage:.3f},setpts=PTS-STARTPTS,fps={FPS},tpad=stop_mode=clone:stop_duration={total:.3f},"
             f"trim=0:{total:.3f},split[a][b]",
             f"[a]scale={W}:{fh}[fg]",
             f"[b]scale=-2:{H},crop={W}:{H},boxblur=24:2,eq=brightness=-0.12[bg]",
             f"[bg][fg]overlay=0:(H-h)/2,fade=t=in:st=0:d={fade_in}[v0]"]
    inputs = ["-an", "-i", str(video)]
    for i, (png, t_in) in enumerate(layers, start=1):
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", str(png)]
        chain.append(f"[{i}:v]format=rgba,fade=t=in:st={t_in:.2f}:d=0.35:alpha=1[t{i}]")
        chain.append(f"[v{i - 1}][t{i}]overlay=0:0[v{i}]")
    chain.append(f"[v{len(layers)}]format=yuv420p[out]")
    media.ffmpeg(*inputs, "-filter_complex", ";".join(chain), "-map", "[out]", "-t", f"{total:.3f}",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(dst))
    return dst


def cut_and_hold(clip: Path, cut: float, still: Path, total: float, size: tuple[int, int], dst: Path,
                 shake_at: float | None = None, amp: float = 14.0) -> Path:
    """Free edit (tag cut:<s>): the fitted clip up to `cut` seconds, then the drawn end frame held for the rest of the
    shot, with a short decaying impact shake from `shake_at` (seconds into the shot). Hides a generated clip's broken
    ending (EP002 S07: Billy dissolved mid-tumble) without paying for a retake."""
    W, H = size
    hold = max(total - cut, 1 / FPS)
    s = max((shake_at if shake_at is not None else cut) - cut, 0.0)
    wob = f"if(gte(t,{s:.3f}),{amp}*exp(-(t-{s:.3f})*7)*sin((t-{s:.3f})*{{f}}),0)"
    vf = (f"[0:v]trim=0:{cut:.3f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[a];"
          f"[1:v]scale={round(W * 1.05)}:{round(H * 1.05)},crop={W}:{H}:x='(iw-ow)/2+{wob.format(f=75)}'"
          f":y='(ih-oh)/2+{wob.format(f=58)}',fps={FPS},trim=0:{hold:.3f},setpts=PTS-STARTPTS,format=yuv420p[b];"
          f"[a][b]concat=n=2:v=1:a=0[v]")
    media.ffmpeg("-i", str(clip), "-loop", "1", "-framerate", str(FPS), "-i", str(still), "-filter_complex", vf,
                 "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(dst))
    return dst


def mux(video: Path, audio: Path, dst: Path, crop_4x5: bool = False) -> Path:
    """Video + mix, nothing else: no captions burned in and no subtitle track either (owner 2026-10-04: QuickTime
    showed the animatic's soft track by default). Captions only ever go to the .srt sidecar for CapCut."""
    inputs = ["-i", str(video), "-i", str(audio)]
    chain, last = [], "[0:v]"
    if crop_4x5:
        chain.append(f"{last}crop=iw:iw*5/4,format=yuv420p[vout]")
    else:
        chain.append(f"{last}format=yuv420p[vout]")
    # Written next to dst, then swapped in with one rename: rewriting dst in place corrupted the animatic for a
    # player that still had the previous version open (QuickTime froze from the first changed shot onwards).
    tmp = dst.with_name(dst.stem + ".tmp.mp4")
    media.ffmpeg(*inputs, "-filter_complex", ";".join(chain), "-map", "[vout]", "-map", "1:a", "-sn",
                 "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", "-shortest", str(tmp))
    tmp.replace(dst)
    return dst
