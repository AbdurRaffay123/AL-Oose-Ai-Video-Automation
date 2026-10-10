"""Offline tests: Kling 3.0 engines, prompt templates, ElevenLabs re-voice safety (fake HTTP, no network)."""
import json
import wave
from pathlib import Path

import numpy as np
import pytest
import requests

from bbtb import elevenlabs, fal, pipeline, revoice, shots as sh
from bbtb.ledger import Ledger
from bbtb.script_parser import ScriptError, load_characters, parse

from test_core import FakeResp

CHARS = load_characters()
SCRIPT = """# T
format: 9:16  talking_engine: kling3  action_engine: kling3  budget: 5
## SCENE BIG_WORM_HOLE
ACTION [wide, enter-right, prompt:billy_walk]: Bad Billy walks in.
BILLY [tophat, skeptical]: Silly little worm!
ACTION [medium, scroll-pickup>scroll-reading, prompt:billy_scroll]: Billy unrolls the scroll.
ACTION [wide, end: BIG GUY arms-up, prompt:big_guy_erupt]: The Big Guy bursts up.
"""


def _shots():
    return sh.plan(parse(SCRIPT, CHARS), CHARS)


def test_engines_frames_and_full_body_talk():
    walk, talk, scroll, erupt = _shots()
    assert [s.engine for s in (walk, talk, scroll, erupt)] == ["kling3_action", "kling3_talk", "kling3_action", "kling3_action"]
    assert walk.start_cast == [] and walk.end_cast[0].char == "bad_billy"          # enters: empty -> on his mark
    assert scroll.start_cast[0].art == "billy_tophat_scroll_pickup"
    assert scroll.end_cast[0].art == "billy_tophat_scroll_reading"                  # pose a -> pose b
    assert erupt.end_cast[0].char == "big_guy"
    assert talk.cast[0].art == "billy_tophat_34right" and talk.cast[0].framing == "medium"   # no pasted close-up
    assert not talk.cast[0].mirror and talk.acting == "skeptical" and talk.prompt_key == "talk_bad_billy"


def test_kling3_durations_are_whole_seconds_3_to_15():
    shots = _shots()
    sh.apply_durations(shots, {shots[1].lines[0]: 1.746})
    assert shots[1].gen_seconds == 3 and shots[0].gen_seconds == 3
    shots[1].lines = ["x"]
    sh.apply_durations([shots[1]], {"x": 9.83})
    assert shots[1].gen_seconds == 10


def test_header_rejects_unknown_engines():
    with pytest.raises(ScriptError, match="action_engine"):
        parse("# T\naction_engine: sora\n## SCENE BIG_WORM_HOLE\nBILLY [tophat]: Hi.\n", CHARS)


def _prod(tmp_path):
    shots = _shots()
    lines = {shots[1].lines[0]: {"text": "Silly little worm!", "seconds": 1.746, "speaker": "bad_billy"}}
    sh.apply_durations(shots, {shots[1].lines[0]: 1.746})
    prod = pipeline.Production(parse(SCRIPT, CHARS), tmp_path, CHARS, shots, lines, (720, 1280),
                               Ledger(tmp_path / "ledger.jsonl"))
    (tmp_path / "keyframes").mkdir()
    for s in shots:
        for p in pipeline.frame_paths(prod, s):
            p.write_bytes(b"\xff\xd8" + s.id.encode())
    return prod


def test_talk_prompt_has_owner_template_line_facing_and_acting(tmp_path):
    prod = _prod(tmp_path)
    prompt, _ = pipeline.kling3_prompt(prod, prod.shots[1])
    assert prompt.startswith("Cartoon bird villain, orange beak, black top hat, monocle on left eye, facing right,")
    assert 'He is skeptical and says: "Silly little worm!"' in prompt and "{" not in prompt


def test_walk_prompt_uses_script_direction(tmp_path):
    prod = _prod(tmp_path)
    prompt, negative = pipeline.kling3_prompt(prod, prod.shots[0])
    assert "Walks confidently from the right into frame" in prompt
    assert "floating" in negative and "mirrored character" in negative


def test_kling3_jobs_models_fields_and_cost(tmp_path):
    prod = _prod(tmp_path)
    walk, talk, scroll, erupt = (pipeline.kling3_job(prod, s) for s in prod.shots)
    assert talk.model == fal.KLING3_TURBO and talk.extra == {"duration": "3"} and set(talk.files) == {"image_url"}
    assert talk.cost == pytest.approx(0.336)
    assert walk.model == fal.KLING3_STD and walk.extra["generate_audio"] is False
    assert set(walk.files) == {"start_image_url", "end_image_url"} and walk.cost == pytest.approx(0.252)
    assert erupt.extra["duration"] == "3" and "negative_prompt" in erupt.extra
    talk.extra["generate_audio"] = True
    assert talk.rate == fal.PRICES[fal.KLING3_TURBO]                    # Turbo: one price, audio always on
    walk.extra["generate_audio"] = True
    assert walk.rate == fal.KLING3_STD_AUDIO                            # Standard with audio costs more


def test_kling3_body_sends_extra_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("FAL_AI_API_KEY", "abc:def-test-key-123")
    prod = _prod(tmp_path)
    job = pipeline.kling3_job(prod, prod.shots[0])
    sent = {}

    class S:
        def post(self, url, **kw):
            sent.update(kw["json"], url=url)
            return FakeResp(200, {"request_id": "r", "status_url": "s", "response_url": "r"})
    fal.Client(prod.ledger, session=S(), approval_code="CODE").submit(job)
    assert sent["url"].endswith(fal.KLING3_STD)
    assert sent["duration"] == "3" and sent["generate_audio"] is False
    assert sent["start_image_url"].startswith("data:image/jpeg;base64,") and "end_image_url" in sent


# ---------------------------------------------------------------- re-voice (ElevenLabs Voice Changer)

def _clip_with_audio(path: Path):
    import subprocess
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=green:s=72x128:d=1",
                    "-f", "lavfi", "-i", "sine=frequency=300:duration=1", "-shortest", "-c:v", "libx264",
                    "-c:a", "aac", str(path)], check=True)


class StsSession:
    def __init__(self, resp):
        self.resp, self.calls = resp, 0

    def post(self, url, **kw):
        self.calls += 1
        if isinstance(self.resp, Exception):
            raise self.resp
        return self.resp


def _mp3(tmp_path):
    import subprocess
    p = tmp_path / "out.mp3"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    "sine=frequency=200:duration=1", str(p)], check=True)
    return p.read_bytes()


def test_revoice_stops_before_paying_if_kling_said_the_wrong_line(tmp_path, monkeypatch):
    clip = tmp_path / "S04" / "kling3.mp4"
    clip.parent.mkdir()
    _clip_with_audio(clip)
    monkeypatch.setattr(revoice, "transcribe", lambda p: {"text": "banana pancakes forever", "words": []})
    sess = StsSession(FakeResp(200))
    with pytest.raises(revoice.RevoiceError, match="did not say the script line"):
        revoice.run(clip, "fal:h", "bad_billy", "Silly little worm!", "S04", Ledger(tmp_path / "l.jsonl"), "C",
                    client=elevenlabs.Client(session=sess))
    assert sess.calls == 0


def test_revoice_logs_first_and_never_retries(tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test-key-123456")
    clip = tmp_path / "S04" / "kling3.mp4"
    clip.parent.mkdir()
    _clip_with_audio(clip)
    monkeypatch.setattr(revoice, "transcribe", lambda p: {"text": "Silly little worm!",
                                                          "words": [{"w": "Silly", "start": 0.1, "end": 0.3},
                                                                    {"w": "worm", "start": 0.6, "end": 0.9}]})
    led = Ledger(tmp_path / "l.jsonl")
    sess = StsSession(requests.Timeout())
    with pytest.raises(elevenlabs.ElevenLabsError, match="NOT retried"):
        revoice.run(clip, "fal:h", "bad_billy", "Silly little worm!", "S04", led, "C", client=elevenlabs.Client(session=sess))
    row = led.rows()[-1]
    assert row["state"] == "unknown" and led.rows()[0]["kind"] == "sts" and led.rows()[0]["approval_code"] == "C"
    with pytest.raises(elevenlabs.ElevenLabsError, match="Not retried"):
        revoice.run(clip, "fal:h", "bad_billy", "Silly little worm!", "S04", led, "C", client=elevenlabs.Client(session=sess))
    assert sess.calls == 1


def test_revoice_success_is_tied_to_the_exact_clip(tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test-key-123456")
    clip = tmp_path / "S04" / "kling3.mp4"
    clip.parent.mkdir()
    _clip_with_audio(clip)
    monkeypatch.setattr(revoice, "transcribe", lambda p: {"text": "Silly little worm!",
                                                          "words": [{"w": "Silly", "start": 0.1, "end": 0.3},
                                                                    {"w": "worm", "start": 0.6, "end": 0.9}]})
    ok = FakeResp(200, content=_mp3(tmp_path))
    ok.ok = True
    sess = StsSession(ok)
    led = Ledger(tmp_path / "l.jsonl")
    info = revoice.run(clip, "fal:h", "bad_billy", "Silly little worm!", "S04", led, "C",
                       client=elevenlabs.Client(session=sess))
    assert info["speech"] == [0.1, 0.9] and info["kling_match"] == 1.0 and sess.calls == 1
    assert revoice.done(clip.parent, "fal:h") and not revoice.done(clip.parent, "fal:other")
    assert led.find(info["sts_request_hash"])["state"] == "completed"
    revoice.run(clip, "fal:h", "bad_billy", "Silly little worm!", "S04", led, "C", client=elevenlabs.Client(session=sess))
    assert sess.calls == 1                                              # cached, never paid twice


def test_unapproved_voice_is_never_used(monkeypatch):
    from bbtb import voices
    monkeypatch.setattr(voices, "registry_state", lambda: {"characters": {"snail": {"elevenlabs": {"voice_id": "v"}}}})
    vid, _, problem = revoice.voice_for("snail")
    assert vid is None and "not approved" in problem


def test_ep001_uses_the_hybrid_engine_plan():
    from bbtb.paths import LIBRARY
    script = (LIBRARY.parent / "productions" / "ep001-big-guy" / "script.md").read_text()
    engines = {s.id: s.engine for s in sh.plan(parse(script, CHARS), CHARS)}
    assert engines == {"S01": "kling3_action", "S02": "kling_avatar", "S03": "kling_avatar", "S04": "kling3_talk",
                       "S05": "kling3_action", "S06": "kling_avatar", "S07": "kling3_action", "S08": "kling3_talk",
                       "S09": "kling3_talk", "S10": "local_endcard"}


def test_kling3_templates_are_documented_verbatim():
    import yaml
    from bbtb.paths import LIBRARY
    cfg = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    doc = " ".join((LIBRARY.parent / "docs" / "kling_prompts.md").read_text().split())
    for tpl in cfg["templates"].values():
        assert " ".join(tpl.split()) in doc


def test_avatar_clips_are_saved_as_kling_avatar(tmp_path):
    s = parse("# T\nformat: 9:16 talking_engine: kling\n## SCENE BIG_WORM_HOLE\nBILLY [tophat, skeptical]: Hi.\n", CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {shots[0].lines[0]: 1.0})
    prod = pipeline.Production(s, tmp_path, CHARS, shots, {shots[0].lines[0]: {"text": "Hi.", "seconds": 1.0}},
                               (720, 1280), Ledger(tmp_path / "l.jsonl"))
    first = tmp_path / "f.jpg"
    first.write_bytes(b"\xff\xd8x")
    assert pipeline.kling_job(prod, shots[0], first).out_path.name == "kling_avatar.mp4"
    assert pipeline.kling_job(prod, shots[0], first, test=True).out_path.name == "kling_test.mp4"


# ---------------------------------------------------------------- 2026-10-04: trims, word check, fallback, takes

def test_trim_shortens_the_edit_but_never_changes_the_paid_request(tmp_path):
    plain, trimmed = _prod(tmp_path / "a"), None
    script = SCRIPT.replace("BILLY [tophat, skeptical]", "BILLY [tophat, skeptical, trim:0.6]")
    shots = sh.plan(parse(script, CHARS), CHARS)
    sh.apply_durations(shots, {shots[1].lines[0]: 1.746})
    talk = shots[1]
    assert talk.trim == 0.6 and talk.duration == pytest.approx(2.4) and talk.gen_seconds == 3
    assert "trim" not in talk.acting
    from bbtb import assemble
    assert assemble.line_offsets(talk, {talk.lines[0]: 3.0}) == [(talk.lines[0], pytest.approx(-0.6))]
    trimmed = pipeline.Production(parse(script, CHARS), tmp_path / "b", CHARS, shots, plain.lines, (720, 1280),
                                  Ledger(tmp_path / "b.jsonl"))
    assert pipeline.kling3_prompt(trimmed, talk) == pipeline.kling3_prompt(plain, plain.shots[1])
    with pytest.raises(ValueError, match="at least 1 s"):
        bad = sh.plan(parse(SCRIPT.replace("BILLY [tophat, skeptical]", "BILLY [tophat, skeptical, trim:2.5]"),
                            CHARS), CHARS)
        sh.apply_durations(bad, {bad[1].lines[0]: 1.7})


def test_word_check_is_word_by_word():
    assert revoice.match("Ahh! Poop!", "Oh POOP!") == 0.5
    assert not revoice.words_ok("Ahh! Poop!", "Oh POOP!")
    assert revoice.words_ok("Oh poop!", "Oh POOP!")
    assert revoice.words_ok("This worm is a worm of super duper size.", "This worm is a worm of super-duper size!")


def _wav(path: Path, seconds=1.0):
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=250:duration={seconds}",
                    "-ac", "1", "-ar", "44100", str(path)], check=True)
    return path


def _fake_whisper(revoiced_text):
    words = {"kling_audio": ("Oh! Poop!", [{"w": "Oh!", "start": 0.4, "end": 0.6}, {"w": "Poop!", "start": 1.2, "end": 1.6}]),
             "line": ("Oh poop!", [{"w": "Oh", "start": 0.0, "end": 0.3}, {"w": "poop!", "start": 0.3, "end": 0.7}]),
             "voice_revoiced": (revoiced_text, [{"w": "x", "start": 0.4, "end": 1.6}])}
    return lambda p: dict(zip(("text", "words"), words[Path(p).stem]))


def test_voice_changer_word_slip_falls_back_to_the_approved_line(tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test-key-123456")
    clip = tmp_path / "S08" / "kling3.mp4"
    clip.parent.mkdir()
    _clip_with_audio(clip)
    monkeypatch.setattr(revoice, "transcribe", _fake_whisper("Ahh! Poop!"))
    ok = FakeResp(200, content=_mp3(tmp_path))
    ok.ok = True
    sess = StsSession(ok)
    info = revoice.run(clip, "fal:h", "bad_billy", "Oh POOP!", "S08", Ledger(tmp_path / "l.jsonl"), "C",
                       client=elevenlabs.Client(session=sess), fallback=_wav(tmp_path / "line.wav", 0.8))
    assert sess.calls == 1 and info["method"].startswith("approved line, word by word")
    assert (clip.parent / "voice_sts_rejected.mp3").exists() and revoice.done(clip.parent, "fal:h")


def test_kling_wrong_line_uses_the_approved_line_without_paying(tmp_path, monkeypatch):
    clip = tmp_path / "S08" / "kling3.mp4"
    clip.parent.mkdir()
    _clip_with_audio(clip)
    monkeypatch.setattr(revoice, "transcribe", lambda p: {"text": "banana pancakes", "words": []}
                        if Path(p).stem == "kling_audio" else _fake_whisper("Oh poop")(p))
    sess = StsSession(FakeResp(200))
    info = revoice.run(clip, "fal:h", "bad_billy", "Oh POOP!", "S08", Ledger(tmp_path / "l.jsonl"), "C",
                       client=elevenlabs.Client(session=sess), fallback=_wav(tmp_path / "line.wav", 0.8))
    assert sess.calls == 0 and "Kling said the wrong line" in info["method"]


def test_a_retake_moves_the_old_paid_take_aside(tmp_path):
    prod = _prod(tmp_path)
    job = pipeline.kling3_job(prod, prod.shots[1])
    d = job.out_path.parent
    d.mkdir(parents=True)
    for n in ("kling3.mp4", "kling3_qa.jpg", "voice_revoiced.wav", "voice_revoiced.json"):
        (d / n).write_bytes(b"old")
    job.sidecar.write_text(json.dumps({"request_hash": "fal:0123456789abcdef"}))
    dst = pipeline.archive_take(job)
    assert dst.name == "kling3_01234567" and not job.out_path.exists()
    assert sorted(p.name for p in dst.iterdir()) == ["kling3.json", "kling3.mp4", "kling3_qa.jpg",
                                                     "voice_revoiced.json", "voice_revoiced.wav"]


def test_a_longer_cached_music_track_is_reused(tmp_path, monkeypatch):
    from bbtb import audio_bed
    monkeypatch.setattr(audio_bed, "AUDIO", tmp_path)
    (tmp_path / "elevenlabs").mkdir()
    (tmp_path / "elevenlabs" / "music_x.mp3").write_bytes(b"mp3")
    (tmp_path / "elevenlabs" / "music_x.json").write_text(json.dumps({"prompt": "p", "length_ms": 50910}))
    assert audio_bed.cached_music("p", 48900).name == "music_x.mp3"
    assert audio_bed.cached_music("p", 60000) is None and audio_bed.cached_music("q", 1000) is None


def test_trimmed_talk_audio_is_cut_not_moved_earlier(tmp_path):
    import subprocess
    from bbtb import assemble
    line = tmp_path / "line.wav"                       # 0.5 s silence, then 0.5 s of "speech"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono:d=0.5",
                    "-f", "lavfi", "-i", "sine=frequency=300:duration=0.5:sample_rate=48000",
                    "-filter_complex", "[0][1]concat=n=2:v=0:a=1", str(line)], check=True)
    blip = tmp_path / "blip.wav"                       # narration at the very start, like a real episode
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=500:duration=0.1:sample_rate=48000",
                    str(blip)], check=True)
    a = sh.Shot("S01", "action", "kling3_action", "X", lines=["N"], duration=1.0)
    b = sh.Shot("S02", "talk", "kling3_talk", "X", lines=["L"], duration=1.0, trim=0.5)
    out = assemble.mix([a, b], {"N": {"path": str(blip), "seconds": 0.1}, "L": {"path": str(line), "seconds": 1.0}},
                       {}, None, 2.0, tmp_path / "mix.wav")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float)
    rms = lambda t0, t1: np.sqrt((x[int(t0 * 8000):int(t1 * 8000)] ** 2).mean())
    assert rms(0.5, 0.95) < 50 and rms(1.05, 1.45) > 500   # the tone starts exactly at the cut into S02


def test_word_starts_snap_to_the_real_sound():
    sr = revoice.SR
    pcm = np.zeros(sr * 2, np.float32)
    pcm[int(0.8 * sr):int(1.2 * sr)] = 8000                    # the word is really at 0.8 s
    w = revoice.onsets([{"w": "Oh", "start": 0.0, "end": 1.3}], pcm)
    assert w[0]["start"] == pytest.approx(0.8, abs=0.02)


def _wan_prod(tmp_path, final=True, seconds=4.74):
    s = parse("# T\nformat: 9:16\n## SCENE BIG_WORM_HOLE\nBILLY [tophat, 34left, suspicious, wan]: Where is the worm?\n", CHARS)
    shots = sh.plan(s, CHARS)
    lid = shots[0].lines[0]
    sh.apply_durations(shots, {lid: seconds})
    wav = tmp_path / "line.wav"
    wav.write_bytes(b"RIFF")
    lines = {lid: {"text": "Where is the worm?", "seconds": seconds, "path": str(wav), "final": final,
                   "source": "elevenlabs" if final else "placeholder"}}
    return pipeline.Production(s, tmp_path, CHARS, shots, lines, (720, 1280), Ledger(tmp_path / "l.jsonl")), shots[0]


def test_wan_tag_plans_a_wan_talking_shot_in_whole_seconds():
    s = parse("# T\n## SCENE BIG_WORM_HOLE\nBILLY [tophat, 34left, wan]: Hi.\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    assert shot.engine == "wan_talk" and "wan" not in sh.acting_of(["wan", "suspicious"])
    sh.apply_durations([shot], {shot.lines[0]: 4.74})
    assert shot.gen_seconds == 5.0
    with pytest.raises(ValueError, match="Wan 2.7 allows at most 15s"):
        sh.apply_durations([shot], {shot.lines[0]: 15.5})


def test_wan_job_sends_our_audio_at_720p_without_prompt_rewrite(tmp_path, monkeypatch):
    prod, shot = _wan_prod(tmp_path)

    def fake_upload(src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"wav")
        return {"prepared": {"seconds": 4.74}, "head_trim": 0.0}
    monkeypatch.setattr(pipeline, "upload_audio", fake_upload)
    first = tmp_path / "f.jpg"
    first.write_bytes(b"\xff\xd8x")
    j = pipeline.wan_job(prod, shot, first)
    assert j.model == fal.WAN27 == "fal-ai/wan/v2.7/image-to-video" and j.endpoint == "wan-talk"
    assert set(j.files) == {"image_url", "audio_url"} and j.out_path.name == "wan.mp4"
    assert j.extra["resolution"] == "720p"                      # the API default is 1080p ($0.15/s)
    assert j.extra["duration"] == 5 and isinstance(j.extra["duration"], int)
    assert j.extra["enable_prompt_expansion"] is False and len(j.extra["negative_prompt"]) <= 500
    assert "monocle on his LEFT eye" in j.prompt and "facing left" in j.prompt and "suspicious" in j.prompt
    assert "Where is the worm?" not in j.prompt                 # the audio carries the line
    assert j.cost == 0.5


def test_wan_never_runs_on_a_voice_that_is_not_final(tmp_path):
    prod, shot = _wan_prod(tmp_path, final=False)
    first = tmp_path / "f.jpg"
    first.write_bytes(b"\xff\xd8x")
    j = pipeline.wan_job(prod, shot, first)
    assert "audio_url" not in j.files and not j.ready         # nothing to upload, so it can't be submitted
    assert pipeline.voice_blockers(prod, [j]) == [f"S01 ({shot.lines[0]}: placeholder)"]


def test_wan_prompts_are_quoted_in_the_prompt_doc():
    import yaml
    from bbtb.paths import LIBRARY
    cfg = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    doc = " ".join((LIBRARY.parent / "docs" / "kling_prompts.md").read_text().split())
    for tpl in cfg["wan_characters"].values():
        assert " ".join(tpl.split()) in doc


def test_finished_ep001_points_at_frozen_prompt_texts():
    """Rewriting a template must never orphan a paid clip: EP001's clips use frozen, versioned texts."""
    import yaml
    from bbtb.paths import LIBRARY
    ep001 = (LIBRARY.parent / "productions" / "ep001-big-guy" / "script.md").read_text()
    assert "prompt:billy_shocked_v5" in ep001 and "prompt:billy_shocked," not in ep001
    t = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())["templates"]
    assert "Body shrinks back slightly" in t["billy_shocked_v5"] and "wan_bad_billy_v1" in t


def test_wan_prompt_tag_uses_the_shared_template_with_the_line(tmp_path, monkeypatch):
    s = parse("# T\n## SCENE BIG_WORM_HOLE\nBILLY [tophat, 34left, suspicious, wan, prompt:talk_bad_billy_max_energy]: Hi.\n", CHARS)
    shots = sh.plan(s, CHARS)
    lid = shots[0].lines[0]
    sh.apply_durations(shots, {lid: 2.0})
    prod = pipeline.Production(s, tmp_path, CHARS, shots, {lid: {"text": "Hi.", "seconds": 2.0}}, (720, 1280),
                               Ledger(tmp_path / "l.jsonl"))
    prompt, negative = pipeline.wan_prompt(prod, shots[0])
    assert "MAXIMUM energy" in prompt and '"Hi."' in prompt and "facing left" in prompt and "{" not in prompt
    assert negative and len(negative) <= 500


EP002_V7 = ("saul_brave", "billy_outraged", "billy_menace", "billy_flight", "saul_riding", "billy_crash")


def test_ep002_v7_billy_prompts_carry_the_owner_protection_sentences():
    import yaml
    from bbtb.paths import LIBRARY
    t = {k: " ".join(v.split()) for k, v in yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())["templates"].items()}
    monocle = ("The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER "
               "disappears, NEVER changes size. Check the monocle position in every frame.")
    wings = ("His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. "
             "Only feathered wings that gesture and fold.")
    style = ("The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style "
             "drift. Same colors, same line weight, same character proportions from first to last frame.")
    folded = ("His wings stay folded flat and tight against his sides throughout the entire clip. The wings do not "
              "spread, do not gesture, do not move away from his body.")
    for k in EP002_V7:
        assert monocle in t[k] and t[k].endswith(style), k
        if k == "billy_outraged":                    # v8: no wing gestures at all (the Turbo pilot grew fists)
            assert folded in t[k] and "gesture and fold" not in t[k] and "wings spread" not in t[k]
            assert "No human hands appear. No fingers. No arms." in t[k]
        else:
            assert wings in t[k], k
        assert "silver badge with a red letter B" in t[k] and "curly blue moustache" in t[k], k
        assert len(t[k].replace("{line}", "x" * 120)) <= 2500, k        # Kling prompt limit, with the line filled in
    assert t["saul_pitch"].endswith(style) and "monocle" not in t["saul_pitch"]   # Saul alone: no Billy in the frame


def test_avatar_shot_uses_its_prompt_tag_and_untagged_keeps_the_character_prompt(tmp_path):
    for tag, expect in (("prompt:billy_menace, ", "Cold, controlled menace"), ("", "beak animates to match speech audio")):
        s = parse(f"# T\nformat: 9:16 talking_engine: kling\n## SCENE GRASS_FLOWERS\nBILLY [tophat, 34left, {tag}suspicious]: Okay.\n", CHARS)
        shots = sh.plan(s, CHARS)
        sh.apply_durations(shots, {shots[0].lines[0]: 2.0})
        prod = pipeline.Production(s, tmp_path, CHARS, shots, {shots[0].lines[0]: {"text": "Okay.", "seconds": 2.0}},
                                   (720, 1280), Ledger(tmp_path / "l.jsonl"))
        first = tmp_path / "f.jpg"
        first.write_bytes(b"\xff\xd8x")
        assert expect in pipeline.kling_job(prod, shots[0], first).prompt


def test_kling3_standard_talk_job_blocks_hands_and_returns_to_the_keyframe(tmp_path):
    s = parse("# T\nformat: 9:16 negatives: billy_hands\n## SCENE GRASS_FLOWERS\n"
              "BILLY [tophat, 34left, surprised, kling3std, prompt:billy_outraged]: REALLY?! Who dares talk to me?\n", CHARS)
    shots = sh.plan(s, CHARS)
    lid = shots[0].lines[0]
    assert shots[0].engine == "kling3_talk_std" and "kling3std" not in sh.acting_of(["kling3std"])
    sh.apply_durations(shots, {lid: 3.43})
    prod = pipeline.Production(s, tmp_path, CHARS, shots, {lid: {"text": "REALLY?! Who dares talk to me?", "seconds": 3.43}},
                               (720, 1280), Ledger(tmp_path / "l.jsonl"))
    (tmp_path / "keyframes").mkdir()
    j = pipeline.kling3_job(prod, shots[0])
    assert j.model == fal.KLING3_STD and j.endpoint == "kling3-talk"          # re-voiced like Turbo
    assert j.files["start_image_url"] == j.files["end_image_url"]               # back to the start pose
    assert j.extra["generate_audio"] is True and j.extra["duration"] == "4"
    assert "human fingers, fists, clenched hands" in j.extra["negative_prompt"]
    assert "monocle on the right eye" in j.extra["negative_prompt"]             # the shared list is kept
    assert j.cost == round(0.126 * 4, 4)


def test_negative_sets_are_opt_in_so_finished_episodes_keep_their_requests(tmp_path):
    s = parse("# T\nformat: 9:16\n## SCENE BIG_WORM_HOLE\nACTION [wide, enter-right, prompt:billy_walk]: Bad Billy walks in.\n", CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {})
    prod = pipeline.Production(s, tmp_path, CHARS, shots, {}, (720, 1280), Ledger(tmp_path / "l.jsonl"))
    (tmp_path / "keyframes").mkdir()
    assert "fists" not in pipeline.kling3_job(prod, shots[0]).extra["negative_prompt"]


def test_negative_set_drop_removes_contradicting_shared_terms(tmp_path, monkeypatch):
    """A dive is airborne and the landing skids: the shared "floating, sliding" must not contradict the prompt."""
    import yaml
    from bbtb.paths import LIBRARY
    real = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    real["negative_sets"]["t_dive"] = {"character": "bad_billy", "text": "hat flying off", "drop": ["floating", "sliding"]}
    monkeypatch.setattr(pipeline.yaml, "safe_load", lambda text, _r=real: _r)
    s = parse("# T\nformat: 9:16\n## SCENE BIG_WORM_HOLE\n"
              "ACTION [wide, enter-right, prompt:billy_walk, neg:t_dive]: Bad Billy walks in.\n", CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {})
    prod = pipeline.Production(s, tmp_path, CHARS, shots, {}, (720, 1280), Ledger(tmp_path / "l.jsonl"))
    neg = pipeline.shot_negative(prod, shots[0], "floating, hovering, sliding, text")
    assert neg == "hovering, text, hat flying off"


def test_kling3_standard_talk_noend_drops_only_the_end_frame(tmp_path):
    s = parse("# T\nformat: 9:16 negatives: billy_hands\n## SCENE GRASS_FLOWERS\n"
              "BILLY [tophat, 34left, surprised, kling3std, noend, prompt:billy_outraged]: REALLY?! Who dares talk to me?\n", CHARS)
    shots = sh.plan(s, CHARS)
    lid = shots[0].lines[0]
    assert "noend" not in sh.acting_of(shots[0].motion + ["surprised"])
    sh.apply_durations(shots, {lid: 3.43})
    prod = pipeline.Production(s, tmp_path, CHARS, shots, {lid: {"text": "REALLY?! Who dares talk to me?", "seconds": 3.43}},
                               (720, 1280), Ledger(tmp_path / "l.jsonl"))
    (tmp_path / "keyframes").mkdir()
    j = pipeline.kling3_job(prod, shots[0])
    assert set(j.files) == {"start_image_url"} and "fists" in j.extra["negative_prompt"] and j.cost == round(0.126 * 4, 4)


def _std_prod(tmp_path, header):
    s = parse(f"# T\nformat: 9:16 negatives: billy_hands {header}\n## SCENE GRASS_FLOWERS\n"
              "BILLY [tophat, 34left, surprised, kling3std, prompt:billy_outraged]: REALLY?!\n", CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {shots[0].lines[0]: 2.0})
    root = tmp_path / "ep_test"
    (root / "keyframes").mkdir(parents=True, exist_ok=True)
    return pipeline.Production(s, root, CHARS, shots, {shots[0].lines[0]: {"text": "REALLY?!", "seconds": 2.0}},
                               (720, 1280), Ledger(root / "l.jsonl")), shots[0]


def test_elements_are_opt_in_and_named_in_the_prompt(tmp_path, monkeypatch):
    from bbtb import references
    prod, shot = _std_prod(tmp_path, "")
    plain = pipeline.kling3_job(prod, shot)
    assert plain.elements == [] and "@Element" not in plain.prompt              # finished episodes unchanged
    prod, shot = _std_prod(tmp_path, "elements: on")
    from PIL import Image
    f, r = tmp_path / "f.png", tmp_path / "r.jpg"
    Image.new("RGB", (600, 600), "white").save(f); Image.new("RGB", (800, 500), "white").save(r)
    monkeypatch.setattr(references, "paths", lambda root, sid: [{"char": "bad_billy", "frontal": f, "refs": [r]}])
    j = pipeline.kling3_job(prod, shot)
    assert j.elements == [{"frontal": f, "refs": [r]}] and "@Element1 is Bad Billy" in j.prompt
    assert j.request_hash() != plain.request_hash()                          # references are part of the request


def test_official_identity_placeholders_fill_from_the_sheets(tmp_path):
    prod, shot = _std_prod(tmp_path, "")
    shot.prompt_key = "billy_outraged"
    import yaml
    from bbtb.paths import LIBRARY
    cfg = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    assert "red script letter B" in cfg["official_identity"]["bad_billy"]
    assert "never human hands or fingers, never fists" in cfg["official_identity"]["bad_billy"]
    assert "white cartoon gloves" in cfg["official_identity"]["young_saul"]


def test_background_element_is_opt_in_on_top_of_character_elements(tmp_path, monkeypatch):
    from bbtb import references
    from PIL import Image
    f, r = tmp_path / "f.png", tmp_path / "r.jpg"
    Image.new("RGB", (600, 600), "white").save(f); Image.new("RGB", (800, 500), "white").save(r)
    monkeypatch.setattr(references, "paths", lambda root, sid: [{"char": "bad_billy", "frontal": f, "refs": [r]}])
    prod, shot = _std_prod(tmp_path, "elements: on")
    assert len(pipeline.kling3_job(prod, shot).elements) == 1                      # characters only by default
    prod, shot = _std_prod(tmp_path, "elements: on bg_element: on")
    j = pipeline.kling3_job(prod, shot)
    assert len(j.elements) == 2 and "@Element2 is the location" in j.prompt
    assert j.elements[1]["frontal"].exists() and j.elements[1]["refs"][0].exists()


def test_scene_types_pick_the_best_background_never_twice_in_a_row():
    from bbtb import keyframes
    assert keyframes.resolve_scene("GRASS_FLOWERS") == "GRASS_FLOWERS"            # exact names are untouched
    a = keyframes.resolve_scene("flying")
    b = keyframes.resolve_scene("type:flying", previous=a)
    assert a != b and "flying" in keyframes.backgrounds()[a]["types"] and "flying" in keyframes.backgrounds()[b]["types"]
    assert keyframes.resolve_scene("underground") in ("TUNNELS", "BG_CAVE_STUDY", "BG_CAVE_TUNNEL")
    with pytest.raises(KeyError, match="Use a background name"):
        keyframes.resolve_scene("SPACESHIP_BRIDGE")


def test_shot_cap_refuses_any_single_expensive_shot_and_risk_order(tmp_path):
    prod, shot = _std_prod(tmp_path, "shot_cap: 0.30")
    j = pipeline.kling3_job(prod, shot)                        # 2 s talking, Standard with speech = $0.25... 3 s min
    assert j.cost > 0.30
    assert any("shot cap" in p for p in pipeline.cap_problems(prod, j.cost, None, [j]))
    a = fal.Job("S09", fal.KLING_AVATAR, "", {}, 2.0, tmp_path / "a.mp4", endpoint="kling-avatar")
    b = fal.Job("S01", fal.KLING3_STD, "", {}, 3.0, tmp_path / "b.mp4", endpoint="kling3-talk")
    c = fal.Job("S05", fal.KLING3_STD, "", {}, 3.0, tmp_path / "c.mp4", endpoint="kling3-action")
    assert [x.shot_id for x in sorted([b, c, a], key=pipeline.risk_rank)] == ["S09", "S05", "S01"]


def test_references_for_the_wrong_character_are_refused(tmp_path, monkeypatch):
    """Renumbered shots once pointed a Billy shot at Saul's references (EP003, caught in pre-production)."""
    from bbtb import references
    from PIL import Image
    f, r = tmp_path / "f.png", tmp_path / "r.jpg"
    Image.new("RGB", (600, 600), "white").save(f); Image.new("RGB", (800, 500), "white").save(r)
    monkeypatch.setattr(references, "paths", lambda root, sid: [{"char": "young_saul", "frontal": f, "refs": [r]}])
    prod, shot = _std_prod(tmp_path, "elements: on")
    with pytest.raises(RuntimeError, match="references.yaml lists"):
        pipeline.kling3_job(prod, shot)


def test_saul_identity_carries_the_big_eye_rule_and_the_eye_negative_exists():
    import yaml
    from bbtb.paths import LIBRARY
    c = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    saul = " ".join(c["official_identity"]["young_saul"].split())
    assert "ENORMOUS ROUND EYES" in saul and "LARGE and ROUND" in saul and "never flat" in saul
    assert "ball" not in saul.lower()                    # the ball is per-shot, or Kling adds it everywhere
    assert "beady eyes" in c["negative_sets"]["saul_eyes"]["text"]


def test_kling3_action_honours_secs_as_minimum_length():
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\n"
              "ACTION [medium, kling3std, 34left>34left, loop, secs:5]: Bad Billy pats his tummy.\n", CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {})
    assert shots[0].engine == "kling3_action" and shots[0].gen_seconds == 5.0
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\nACTION [medium, kling3std, 34left>34left, loop]: Bad Billy pats.\n", CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {})
    assert shots[0].gen_seconds == 3.0                       # unchanged without the tag


def test_pos_tags_place_start_and_end_frames_exactly():
    from bbtb import keyframes
    assert keyframes.parse_place("0.36/0.16/0.24/air") == (0.36, 0.16, 0.24, True)
    assert keyframes.parse_place("") is None
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\n"
              "ACTION [wide, kling3std, landing-approach1>landing-approach, pos:0.36/0.16/0.24/air, "
              "endpos:0.62/0.52/0.30/air]: Bad Billy dives.\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    assert (shot.place, shot.place_end) == ("0.36/0.16/0.24/air", "0.62/0.52/0.30/air")
    assert "pos:0.36/0.16/0.24/air" not in sh.acting_of(s.events[0].direction)
    _, start = keyframes.layout(shot.scene, shot.cast, CHARS, (720, 1280), place=shot.place)
    _, end = keyframes.layout(shot.scene, shot.end_cast, CHARS, (720, 1280), place=shot.place_end)
    assert start[0]["top"] == int(0.16 * 1280) and not start[0]["shadow"]
    assert end[0]["top"] > start[0]["top"] and end[0]["x"] > start[0]["x"]     # top-left -> bottom-right


def test_rule_end_card_is_dynamic_and_planned():
    from bbtb import keyframes
    s = parse("# T\nformat: 9:16\n## SCENE GRASS_SIGN_LOW\nACTION [wide, local]: Bad Billy stands.\n## SCENE END_CARD\n"
              "NARRATOR [production, card:rule, silent, show:RULE NUMBER ONE... | LOOK UP! 👆 | Tag a friend, secs:12]: x\n", CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {})
    card = shots[-1]
    assert card.card == "rule" and card.lines == [] and card.duration == 12 and card.backdrop == "GRASS_SIGN_LOW"
    R = keyframes.card_layers(card, CHARS, (720, 1280))
    early, late = (keyframes.card_frame(card, R, t) for t in (0.1, 5.0))
    assert early.size == (720, 1280) and early.tobytes() != late.tobytes()     # it moves, never a still


def test_retimed_line_replaces_audio_by_exact_text(tmp_path):
    import wave
    (tmp_path / "audio" / "retimed").mkdir(parents=True)
    w = wave.open(str(tmp_path / "audio" / "retimed" / "x.wav"), "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(b"\0\0" * 48000 * 2); w.close()
    (tmp_path / "audio" / "retimed.yaml").write_text('"One, two.": retimed/x.wav\n')
    lines = {"L1": {"text": "One, two.", "path": "orig.wav", "seconds": 0.6, "final": True},
             "L2": {"text": "Other.", "path": "o2.wav", "seconds": 1.0, "final": True}}
    pipeline.apply_retimed(tmp_path, lines)
    assert lines["L1"]["seconds"] == 2.0 and lines["L1"]["retimed_from"] == "orig.wav" and lines["L2"]["path"] == "o2.wav"


def test_out_tag_ends_the_shot_without_changing_the_paid_request(tmp_path):
    base = ("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\n"
            "ACTION [medium, kling3std, 34left>34left, loop, secs:5{tags}]: Bad Billy burps.\n")
    plain, cut = (sh.plan(parse(base.format(tags=t), CHARS), CHARS)[0] for t in ("", ", trim:0.5, out:4.375"))
    for s in (plain, cut):
        sh.apply_durations([s], {})
    assert plain.duration == 5.0 and cut.duration == 3.875 and cut.gen_seconds == plain.gen_seconds == 5.0
    assert "out:4.375" not in sh.acting_of(parse(base.format(tags=", out:4.375"), CHARS).events[0].direction)


def test_clipfix_edit_and_eye_tint():
    from bbtb import clipfix
    fr = np.zeros((48, 64, 32, 3), np.uint8)
    for i in range(48):
        fr[i] = i                                           # frame i is filled with value i
    fr[10:20, 10:20, 5:15] = 250                            # a "white eye" in frames 10-19
    clipfix.tint_eyes(fr, {"frames": [10, 19], "box": [5, 10, 15, 20], "color": [205, 254, 194]})
    assert fr[12, 15, 10, 1] > fr[12, 15, 10, 0] and fr[12, 15, 10, 0] < 230          # white -> pale green
    segs = [{"from": 0.0, "to": 0.5, "speed": 0.75}, {"from": 1.0, "to": 1.25, "hold": 3, "zoom": 1.3}]
    out = clipfix.edit_frames(fr, segs, 24)
    assert len(out) == 16 + 6 + 3 and clipfix.edit_seconds(segs) == round(25 / 24, 3)
    assert out[0][0, 0, 0] == 0 and out[16][0, 0, 0] == 24                            # second slice starts at 1.0 s


def test_localanim_numbers_spec_and_grounded_worms():
    from bbtb import grounding, keyframes, localanim
    items, x, y, pop = localanim._numbers("1@1.625|2@2.042|4!@2.875@x0.85/y0.66/pop1.4")
    assert items == [("1", 1.625), ("2", 2.042), ("4!", 2.875)] and (x, y, pop) == (0.85, 0.66, 1.4)
    size = (360, 640)
    bg = keyframes.plate("GRASS_STUMP", size).convert("RGBA")
    src = keyframes.plate_source("GRASS_STUMP").size
    x0, y0, cw, ch = keyframes.plate_window("GRASS_STUMP", src, size)
    win = (x0 / src[0], y0 / src[1], cw / src[0], ch / src[1])
    placed = [{"index": i, "art": a, "x": int(cx * size[0] - a.width / 2), "top": int(feet * size[1]) - a.height,
               "framing": "medium", "window": win} for i, (a, cx, feet) in enumerate(localanim._worm_layers(size))]
    assert all(s == "PASS" for _, s, _ in grounding.check("GRASS_STUMP", placed, bg))     # worms on the flat grass
    assert len(list(localanim.worms_play(size, 0.25))) == 6


def test_voiceover_say_and_pinned_ids():
    from bbtb import assemble
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\n"
              "NARRATOR [production]: Hello there.\n"
              "BILLY [tophat, over, say:2.5, production]: Arrrr!\n"
              "ACTION [medium, kling3std, id:S01b, 34left>34left, loop]: Bad Billy watches.\n", CHARS)
    shots = sh.plan(s, CHARS)
    assert len(shots) == 1 and shots[0].id == "S01b" and shots[0].engine == "kling3_action"
    narr, growl = shots[0].lines
    assert shots[0].line_at == {growl: 2.5}
    offs = dict(assemble.line_offsets(shots[0], {narr: 1.0, growl: 1.3}))
    assert offs[growl] == 2.5 and offs[narr] == assemble.LEAD["kling3_action"]


def test_only_matches_pinned_ids_case_insensitively(tmp_path, monkeypatch):
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\n"
              "ACTION [medium, kling3std, id:S01b, 34left>34left, loop]: Bad Billy watches.\n", CHARS)
    shots = sh.plan(s, CHARS)
    assert shots[0].id == "S01b" and shots[0].id.upper() in {x.strip().upper() for x in ["s01b"]}


def test_avatar_action_is_driven_by_the_on_screen_line_only(tmp_path):
    s = parse("# T\nformat: 9:16\n## SCENE GRASS_FLOWERS\n"
              "NARRATOR [production]: Hello there.\n"
              "BILLY [tophat, over, say:3.95, production]: Arrrr!\n"
              "ACTION [medium, avatar, id:S01b, 34left>34left]: Bad Billy watches.\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    narr, growl = shot.lines
    sh.apply_durations([shot], {narr: 3.56, growl: 1.35})
    assert shot.engine == "kling_avatar" and shot.kind == "action" and shot.duration == round(3.95 + 1.35 + 0.25, 2)
    prod = pipeline.Production(s, tmp_path, CHARS, [shot],
                               {narr: {"text": "Hello there.", "speaker": "narrator", "seconds": 3.56},
                                growl: {"text": "Arrrr!", "speaker": "bad_billy", "seconds": 1.35}},
                               (720, 1280), Ledger(tmp_path / "l.jsonl"))
    assert pipeline.avatar_driver(prod, shot) == (growl, 3.95)      # never the narrator


def test_sfx_vol_tag_sets_the_level():
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\n"
              "SFX [at 0.2, vol 0.1]: giggles\nSFX [at 1.0]: pop\n"
              "ACTION [medium, kling3std, 34left>34left, loop]: Bad Billy watches.\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    assert shot.sfx == [{"name": "giggles", "at": 0.2, "vol": 0.1}, {"name": "pop", "at": 1.0}]


# ---------------------------------------------------------------- Kling O3 reference-to-video (owner 2026-10-08)

def _o3_prod(tmp_path, monkeypatch, video_secs=3.0, tags="o3, refvideo:refs/billy.mp4", n_refs=2):
    from bbtb import media, references
    from PIL import Image
    s = parse("# T\nformat: 9:16 action_engine: kling3 negatives: billy_hands elements: on\n## SCENE BIG_WORM_HOLE\n"
              f"ACTION [medium, kling3std, refs, {tags}, prompt:billy_full_v3, 34left>34left, zoom:1.55, loop, gen:4]: "
              "Bad Billy looks around.\n".replace(", , ", ", "), CHARS)
    shots = sh.plan(s, CHARS)
    sh.apply_durations(shots, {})
    root = tmp_path / "test_o3"
    (root / "keyframes").mkdir(parents=True)
    (root / "refs").mkdir()
    (root / "refs" / "billy.mp4").write_bytes(b"fake mp4")
    f, r = tmp_path / "f.png", tmp_path / "r.jpg"
    Image.new("RGB", (600, 600), "white").save(f); Image.new("RGB", (800, 500), "white").save(r)
    monkeypatch.setattr(references, "paths", lambda root_, sid: [{"char": "bad_billy", "frontal": f, "refs": [r] * n_refs}])
    monkeypatch.setattr(media, "duration", lambda p: video_secs)
    return pipeline.Production(s, root, CHARS, shots, {}, (720, 1280), Ledger(root / "l.jsonl")), shots[0]


def test_o3_job_same_keyframes_no_negative_field_and_reference_video(tmp_path, monkeypatch):
    prod, shot = _o3_prod(tmp_path, monkeypatch)
    j = pipeline.kling3_job(prod, shot)
    assert j.model == fal.KLING_O3_R2V and "negative_prompt" not in j.extra
    assert j.extra == {"duration": "4", "aspect_ratio": "9:16", "generate_audio": False}
    assert "Never: " in j.prompt and "@Element1 is Bad Billy" in j.prompt     # blocking list folded into the prompt
    assert set(j.files) == {"start_image_url", "end_image_url"}               # same start/end keyframe as Kling 3.0
    assert len(j.elements) == 2 and len(j.elements[0]["refs"]) == 2
    assert j.cost == round(0.084 * 4, 4)


def test_o3_reference_video_must_be_3_to_10_seconds(tmp_path, monkeypatch):
    prod, shot = _o3_prod(tmp_path, monkeypatch, video_secs=2.5)
    with pytest.raises(RuntimeError, match="3-10.05 s"):
        pipeline.kling3_job(prod, shot)


def test_o3_body_sends_the_element_video_and_the_control_shot_is_unchanged(tmp_path, monkeypatch):
    from PIL import Image
    monkeypatch.setenv("FAL_AI_API_KEY", "abc:def-test-key-123")
    prod, shot = _o3_prod(tmp_path, monkeypatch)
    j = pipeline.kling3_job(prod, shot)
    for p in j.files.values():
        Path(p).parent.mkdir(parents=True, exist_ok=True); Image.new("RGB", (720, 1280), "white").save(p)
    sent = {}

    class S:
        def post(self, url, **kw):
            sent.update(kw["json"], url=url)
            return FakeResp(200, {"request_id": "r", "status_url": "s", "response_url": "r"})
    fal.Client(prod.ledger, session=S(), approval_code="CODE").submit(j)
    assert sent["url"].endswith(fal.KLING_O3_R2V) and "negative_prompt" not in sent
    assert set(sent["elements"][0]) == {"frontal_image_url", "reference_image_urls"}      # image element: no video
    assert set(sent["elements"][1]) == {"video_url"}                                      # video element: video only
    assert sent["elements"][1]["video_url"].startswith("data:video/mp4;base64,")
    control_prod, control_shot = _o3_prod(tmp_path / "c", monkeypatch, tags="")
    c = pipeline.kling3_job(control_prod, control_shot)
    assert c.model == fal.KLING3_STD and "negative_prompt" in c.extra and "video" not in c.elements[0]


def test_o3_prompt_over_the_2500_character_limit_is_refused_before_sending(tmp_path, monkeypatch):
    prod, shot = _o3_prod(tmp_path, monkeypatch)
    shot.prompt_key = "billy_full_v3"
    monkeypatch.setattr(pipeline, "O3_PROMPT_MAX", 500)
    with pytest.raises(RuntimeError, match="limit 500"):
        pipeline.kling3_job(prod, shot)


def test_o3_never_tag_uses_the_short_o3_list_instead_of_the_full_negative(tmp_path, monkeypatch):
    prod, shot = _o3_prod(tmp_path, monkeypatch, tags="o3, refvideo:refs/billy.mp4, never:o3_never_billy")
    monkeypatch.setattr(pipeline, "O3_PROMPT_MAX", 10_000)          # this stand-in template is longer than the test one
    j = pipeline.kling3_job(prod, shot)
    assert "Never: human hands or fingers, fists" in j.prompt and "feet off the ground" not in j.prompt
    assert j.prompt.endswith(". @Element1 is Bad Billy; @Element2 is a video of him.")


def test_o3_reference_video_is_its_own_element_and_the_4_item_limit_holds(tmp_path, monkeypatch):
    """fal 422 (2026-10-10): an element is images OR a video. @Element1 = Billy's images, @Element2 = the clip."""
    prod, shot = _o3_prod(tmp_path, monkeypatch)
    j = pipeline.kling3_job(prod, shot)
    assert "video" not in j.elements[0] and set(j.elements[1]) == {"video"}
    assert fal.element_files(j.elements[1]) == [prod.root / "refs" / "billy.mp4"]
    assert j.prompt.endswith(". @Element1 is Bad Billy; @Element2 is a video of him.")
    assert pipeline.O3_PROMPT_MAX == 2400                                       # 100 spare under fal's 2500
    prod, shot = _o3_prod(tmp_path / "b", monkeypatch, n_refs=3)                 # 2 elements + 3 refs = 5 > 4
    with pytest.raises(RuntimeError, match="at most 4"):
        pipeline.kling3_job(prod, shot)
