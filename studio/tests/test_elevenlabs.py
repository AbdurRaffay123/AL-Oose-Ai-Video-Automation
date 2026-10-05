"""ElevenLabs voice workflow - fully offline (fake HTTP session, temporary registry).

Covers the owner's credit rules: one request per character (batched + sliced by timestamps),
content-keyed cache (renumbering never re-bills), any failure -> 'unknown' + stop, unapproved
voices never rendered, silent (never audible) placeholders, clone once.
"""
import base64
import json
import subprocess

import pytest
import requests

from bbtb import elevenlabs, env, media, voices
from bbtb.ledger import Ledger
from bbtb.script_parser import load_characters
from bbtb.shots import Line

CHARS = load_characters()


def tone_mp3(tmp_path, seconds: float) -> bytes:
    out = tmp_path / f"tone{seconds}.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=300:duration={seconds}",
                    "-c:a", "libmp3lame", str(out)], check=True)
    return out.read_bytes()


def batch_response(tmp_path, text: str) -> "Resp":
    """What /with-timestamps returns: audio + one start/end time per character (evenly spread)."""
    secs = max(1.0, len(text) * 0.05)
    step = secs / len(text)
    align = {"characters": list(text),
             "character_start_times_seconds": [round(i * step, 3) for i in range(len(text))],
             "character_end_times_seconds": [round((i + 1) * step, 3) for i in range(len(text))]}
    return Resp(200, body={"audio_base64": base64.b64encode(tone_mp3(tmp_path, secs)).decode(), "alignment": align})


@pytest.fixture
def registry_file(tmp_path, monkeypatch):
    monkeypatch.setattr(voices, "VOICES_YAML", tmp_path / "voices.yaml")
    monkeypatch.setattr(voices, "VOICE_VENV", tmp_path / "no-venv")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    data = voices.registry_state()
    data["characters"]["bad_billy"] = {"approved": True, "elevenlabs": {"voice_id": "VOICE_BILLY", "source_sha256": "x"}}
    data["characters"]["young_saul"] = {"approved": True, "elevenlabs": {"voice_id": "VOICE_SAUL", "source_sha256": "y"}}
    voices.save_registry(data)
    return tmp_path / "voices.yaml"


class Resp:
    def __init__(self, status=200, content=b"", body=None, headers=None):
        self.status_code, self.content, self._body, self.headers = status, content, body or {}, headers or {}
        self.ok = status < 400
        self.text = json.dumps(body) if body else ""

    def json(self):
        return self._body


class Session:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r if not callable(r) else r(kw)

    get = post


LINES = [Line("L001_bad_billy", "bad_billy", "Well, where is the worm?", [], 1),
         Line("L002_young_saul", "young_saul", "Don't sweat.", [], 2),
         Line("L003_bad_billy", "bad_billy", "Silly little worm!", [], 3),            # original recording
         Line("L004_bad_billy", "bad_billy", "Oh POOP!", [], 4)]


def responder(tmp_path):
    return lambda kw: batch_response(tmp_path, kw["json"]["text"])


def test_key_is_read_from_either_name_and_never_printed(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_LABS_API_KEY", raising=False)
    (tmp_path / ".env").write_text("ELEVEN_LABS_API_KEY=sk_secret_value_123\n")
    assert elevenlabs.api_key() == "sk_secret_value_123"
    assert "sk_secret_value_123" not in env.redact("leak sk_secret_value_123")
    (tmp_path / ".env").write_text("")
    with pytest.raises(elevenlabs.ElevenLabsError, match="No ElevenLabs API key"):
        elevenlabs.api_key()


def test_no_paid_call_without_approval_and_nothing_substituted(registry_file, tmp_path):
    sess = Session([])
    with pytest.raises(voices.VoicesNotReady) as ei:
        voices.render_lines(LINES, CHARS, tmp_path / "ep" / "audio", Ledger(tmp_path / "l.jsonl"),
                            client=elevenlabs.Client(session=sess))
    assert sess.calls == []
    assert ei.value.estimate["requests"] == 2                       # one per character, not one per line
    assert "2 request(s)" in str(ei.value)
    assert not list((tmp_path / "ep" / "audio").glob("L*.wav"))


def test_one_request_per_character_sliced_and_mapped_to_own_voice(registry_file, tmp_path):
    sess = Session([responder(tmp_path), responder(tmp_path)])
    out_dir = tmp_path / "ep" / "audio"
    out = voices.render_lines(LINES, CHARS, out_dir, Ledger(tmp_path / "l.jsonl"), allow_paid=True,
                              client=elevenlabs.Client(session=sess))
    urls = [c[0] for c in sess.calls]
    assert urls == ["https://api.elevenlabs.io/v1/text-to-speech/VOICE_BILLY/with-timestamps",
                    "https://api.elevenlabs.io/v1/text-to-speech/VOICE_SAUL/with-timestamps"]
    billy_text = sess.calls[0][1]["json"]["text"]
    assert billy_text == "Well, where is the worm?" + voices.BREAK + "Oh POOP!"   # batched; original line not sent
    assert out["L003_bad_billy"]["source"] == "original"
    assert all(out[l]["final"] for l in out)                                    # approved voices
    assert 0.2 < out["L004_bad_billy"]["seconds"] < out["L001_bad_billy"]["seconds"]   # sliced, not the whole batch
    assert out["L001_bad_billy"]["path"].endswith("/audio/lines/L001_bad_billy.wav")      # ElevenLabs -> lines/
    assert out["L003_bad_billy"]["path"].endswith("/audio/originals/L003_bad_billy.wav")  # original -> originals/
    saved = list((tmp_path / "ep" / "audio" / "lines" / "_batches").glob("bad_billy_*.json"))
    assert saved and json.loads(saved[0].read_text())["text"] == billy_text      # batch kept for free re-slicing


def test_cache_is_by_content_so_renumbering_costs_nothing(registry_file, tmp_path):
    out_dir = tmp_path / "ep" / "audio"
    voices.render_lines(LINES, CHARS, out_dir, Ledger(tmp_path / "l.jsonl"), allow_paid=True,
                        client=elevenlabs.Client(session=Session([responder(tmp_path), responder(tmp_path)])))
    renumbered = [Line(f"L1{i}_{l.speaker}", l.speaker, l.text, [], 10 + i) for i, l in enumerate(LINES)]
    sess = Session([])
    out = voices.render_lines(renumbered, CHARS, out_dir, Ledger(tmp_path / "l.jsonl"),
                              client=elevenlabs.Client(session=sess))
    assert sess.calls == [] and all(e["source"] in ("original", "elevenlabs") for e in out.values())


def test_any_failure_is_logged_unknown_and_blocks_retry(registry_file, tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    quota = Resp(401, body={"detail": {"status": "quota_exceeded", "message": "This request exceeds your quota"}})
    sess = Session([quota])
    with pytest.raises(elevenlabs.ElevenLabsError, match="Not enough ElevenLabs credits"):
        voices.render_lines(LINES[:1], CHARS, tmp_path / "ep" / "audio", led, allow_paid=True,
                            client=elevenlabs.Client(session=sess))
    assert list(led.latest().values())[0]["state"] == "unknown"
    with pytest.raises(elevenlabs.ElevenLabsError, match="Not retried"):
        voices.render_lines(LINES[:1], CHARS, tmp_path / "ep" / "audio", led, allow_paid=True,
                            client=elevenlabs.Client(session=sess))
    assert len(sess.calls) == 1


def test_timeout_is_unknown_and_not_retried(registry_file, tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    sess = Session([requests.Timeout()])
    with pytest.raises(elevenlabs.ElevenLabsError, match="NOT retried"):
        voices.render_lines(LINES[:1], CHARS, tmp_path / "ep" / "audio", led, allow_paid=True,
                            client=elevenlabs.Client(session=sess))
    assert list(led.latest().values())[0]["state"] == "unknown" and len(sess.calls) == 1


def test_unapproved_voice_is_never_rendered(registry_file, tmp_path):
    data = voices.registry_state()
    data["characters"]["young_saul"]["approved"] = False
    voices.save_registry(data)
    sess = Session([])
    with pytest.raises(voices.VoicesNotReady, match="not approved yet"):
        voices.render_lines(LINES, CHARS, tmp_path / "ep" / "audio", Ledger(tmp_path / "l.jsonl"),
                            allow_paid=True, client=elevenlabs.Client(session=sess))
    assert sess.calls == []


def test_missing_permission_is_explained(registry_file):
    r = Resp(401, body={"detail": {"status": "missing_permissions",
                                   "message": "The API key you used is missing the permission user_read to execute this operation."}})
    with pytest.raises(elevenlabs.ElevenLabsError, match="missing permission 'user_read'"):
        elevenlabs.Client(session=Session([r])).subscription()


def test_narrator_without_voice_is_reported_not_substituted(registry_file, tmp_path):
    with pytest.raises(voices.VoicesNotReady, match="Configure the narrator"):
        voices.render_lines([Line("L009_narrator", "narrator", "Then deep from below...", [], 9)], CHARS,
                            tmp_path / "ep" / "audio", Ledger(tmp_path / "l.jsonl"), allow_paid=True,
                            client=elevenlabs.Client(session=Session([])))


def test_preview_placeholders_are_silent_and_never_final(registry_file, tmp_path):
    out = voices.render_lines([LINES[0], LINES[1]], CHARS, tmp_path / "ep" / "audio",
                              Ledger(tmp_path / "l.jsonl"), placeholder=True)
    for e in out.values():
        assert e["source"] == "placeholder" and e["final"] is False
        assert "/_work/placeholders/" in e["path"]                     # never inside audio/
        assert media.loudness(e["path"])["lufs"] is None or media.loudness(e["path"])["lufs"] < -60   # silence
    assert not list((tmp_path / "ep" / "audio").rglob("*.wav"))         # audio/ holds no placeholders


def test_clone_once_then_reuse(tmp_path, monkeypatch):
    monkeypatch.setattr(voices, "VOICES_YAML", tmp_path / "voices.yaml")
    monkeypatch.setattr(voices, "VOICE_VENV", tmp_path / "no-venv")
    monkeypatch.setattr(voices, "REF_DIR", tmp_path / "refs")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    billy = CHARS["bad_billy"]
    with pytest.raises(RuntimeError, match="--confirm-rights"):
        voices.clone("bad_billy", billy, confirm_rights=False, client=elevenlabs.Client(session=Session([])))
    sess = Session([Resp(200, body={"voice_id": "NEW_ID", "requires_verification": False})])
    vid, created = voices.clone("bad_billy", billy, confirm_rights=True, client=elevenlabs.Client(session=sess))
    assert (vid, created) == ("NEW_ID", True)
    assert sess.calls[0][0].endswith("/v1/voices/add")
    assert len(sess.calls[0][1]["files"]) == len(billy["voice"]["clone_reference"])
    vid2, created2 = voices.clone("bad_billy", billy, confirm_rights=True, client=elevenlabs.Client(session=Session([])))
    assert (vid2, created2) == ("NEW_ID", False)
    assert voices.registry_state()["characters"]["bad_billy"]["approved"] is False


def test_too_little_audio_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(voices, "VOICES_YAML", tmp_path / "voices.yaml")
    monkeypatch.setattr(voices, "VOICE_VENV", tmp_path / "no-venv")
    with pytest.raises(RuntimeError, match="Not cloning Young Saul"):
        voices.clone("young_saul", CHARS["young_saul"], confirm_rights=True, client=elevenlabs.Client(session=Session([])))


def test_reclone_creates_new_before_deleting_old(tmp_path, monkeypatch):
    monkeypatch.setattr(voices, "VOICES_YAML", tmp_path / "voices.yaml")
    monkeypatch.setattr(voices, "REF_DIR", tmp_path / "refs")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    data = voices.registry_state()
    data["characters"]["bad_billy"] = {"approved": True, "elevenlabs": {"voice_id": "OLD", "source_sha256": "x"}}
    voices.save_registry(data)
    order = []

    class S(Session):
        def post(self, url, **kw):
            order.append("create")
            return Resp(200, body={"voice_id": "NEW", "requires_verification": False})

        def delete(self, url, **kw):
            order.append(("delete", url.rsplit("/", 1)[-1]))
            return Resp(200, body={})

    r = voices.reclone("bad_billy", CHARS["bad_billy"], confirm_rights=True, client=elevenlabs.Client(session=S([])))
    assert order == ["create", ("delete", "OLD")]                      # new first, old deleted after
    cfg = voices.registry_state()["characters"]["bad_billy"]
    assert cfg["elevenlabs"]["voice_id"] == "NEW" and cfg["approved"] is False
    assert cfg["elevenlabs"]["replaced_voice_id"] == "OLD" and r["reference"].exists()


def test_approve_moves_test_from_pending_to_approved(tmp_path, monkeypatch):
    import argparse
    from bbtb import voice_cli
    monkeypatch.setattr(voices, "VOICES_YAML", tmp_path / "voices.yaml")
    pending = tmp_path / "voice_test" / "elevenlabs" / "pending"
    pending.mkdir(parents=True)
    f = pending / "young_saul_test_v1.wav"
    f.write_bytes(b"RIFF")
    data = voices.registry_state()
    data["characters"]["young_saul"] = {"approved": False, "elevenlabs": {
        "voice_id": "V", "test": {"voice_id": "V", "file": str(f), "text": "hi"}}}
    voices.save_registry(data)
    with pytest.raises(SystemExit):                                   # rights must be confirmed
        voice_cli.approve(argparse.Namespace(character="young_saul", confirm_rights=False))
    voice_cli.approve(argparse.Namespace(character="young_saul", confirm_rights=True))
    cfg = voices.registry_state()["characters"]["young_saul"]
    moved = tmp_path / "voice_test" / "elevenlabs" / "approved" / "young_saul_test_v1.wav"
    assert cfg["approved"] is True and moved.exists() and not f.exists()
    assert cfg["elevenlabs"]["test"]["file"] == str(moved) == cfg["approved_after_test"]
