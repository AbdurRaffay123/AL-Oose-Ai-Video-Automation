"""Offline tests: fal Kling Avatar client safety, spending caps, prompt templates (fake HTTP, no network)."""
import json
from pathlib import Path

import pytest
import requests

from bbtb import fal, pipeline, shots as sh
from bbtb.ledger import Ledger
from bbtb.paths import LIBRARY
from bbtb.script_parser import ScriptError, load_characters, parse

from test_core import FakeResp

CHARS = load_characters()


class Sess:
    def __init__(self, posts=(), gets=()):
        self.posts, self.gets, self.post_calls, self.post_headers = list(posts), list(gets), 0, []

    def post(self, url, **kw):
        self.post_calls += 1
        self.post_headers.append(kw.get("headers", {}))
        r = self.posts.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def get(self, url, **kw):
        return self.gets.pop(0)


@pytest.fixture
def kjob(tmp_path, monkeypatch):
    monkeypatch.setenv("FAL_AI_API_KEY", "abc:def-test-key-123")
    img, wav = tmp_path / "f.jpg", tmp_path / "v.wav"
    img.write_bytes(b"\xff\xd8fakejpeg")
    wav.write_bytes(b"RIFFfakewav")
    return fal.Job("S04", fal.KLING_AVATAR, "prompt", {"image_url": img, "audio_url": wav}, 1.67,
                   tmp_path / "shots" / "kling_test.mp4")


SUBMITTED = {"request_id": "r1", "status_url": "https://q/s", "response_url": "https://q/r"}


def test_cost_rounds_up_to_whole_seconds(kjob):
    assert kjob.billed_seconds == 2
    assert kjob.cost == pytest.approx(0.1124)
    assert kjob.cost_exact < kjob.cost


def test_no_approval_code_no_submit(kjob, tmp_path):
    c = fal.Client(Ledger(tmp_path / "l.jsonl"), session=Sess(), sleep=lambda s: None)
    with pytest.raises(fal.FalError, match="no approval code"):
        c.submit(kjob)


def test_happy_path_logs_everything_and_never_pays_twice(kjob, tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    sess = Sess([FakeResp(200, SUBMITTED)],
                [FakeResp(200, {"status": "IN_PROGRESS"}), FakeResp(200, {"status": "COMPLETED"}),
                 FakeResp(200, {"video": {"url": "https://cdn/v.mp4"}, "duration": 1.7}),
                 FakeResp(200, content=b"MP4")])
    c = fal.Client(led, session=sess, sleep=lambda s: None, approval_code="ABCD1234")
    assert c.run(kjob).read_bytes() == b"MP4"
    assert sess.post_headers[0]["X-Fal-No-Retry"] == "1"
    rows = led.rows()
    intent = rows[0]
    assert intent["state"] == "intent" and intent["approval_code"] == "ABCD1234"
    assert intent["shot"] == "S04" and intent["model"] == fal.KLING_AVATAR and intent["audio_seconds"] == 1.67
    assert intent["cost_estimate"] == pytest.approx(0.1124) and "ts" in intent
    done = led.find(kjob.request_hash())
    assert done["state"] == "completed" and done["result_url"] == "https://cdn/v.mp4"
    assert kjob.done()
    assert c.run(kjob) == kjob.out_path and sess.post_calls == 1       # reused, not re-bought
    assert led.spent() == pytest.approx(0.1124)


def test_changed_inputs_never_reuse_an_old_clip(kjob, tmp_path):
    kjob.out_path.parent.mkdir(parents=True)
    kjob.out_path.write_bytes(b"old")
    kjob.sidecar.write_text(json.dumps({"request_hash": kjob.request_hash()}))
    assert kjob.done()
    kjob.files["audio_url"].write_bytes(b"RIFFdifferent")
    assert not kjob.done()


def test_no_reply_is_unknown_and_blocks_resubmit(kjob, tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    sess = Sess([requests.Timeout()])
    c = fal.Client(led, session=sess, sleep=lambda s: None, approval_code="X")
    with pytest.raises(fal.FalError, match="NOT be retried"):
        c.submit(kjob)
    with pytest.raises(fal.FalError, match="may have reached fal"):
        c.submit(kjob)
    assert sess.post_calls == 1 and led.find(kjob.request_hash())["state"] == "unknown"


def test_model_error_is_failed_and_not_retried(kjob, tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    sess = Sess([FakeResp(200, SUBMITTED)], [FakeResp(200, {"status": "COMPLETED", "error": "bad face"})])
    c = fal.Client(led, session=sess, sleep=lambda s: None, approval_code="X")
    with pytest.raises(fal.FalError, match="bad face"):
        c.run(kjob)
    assert sess.post_calls == 1 and led.find(kjob.request_hash())["state"] == "failed"


def test_refused_submit_costs_nothing(kjob, tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    c = fal.Client(led, session=Sess([FakeResp(403, {"detail": "balance"})]), sleep=lambda s: None, approval_code="X")
    with pytest.raises(fal.FalError, match="Billing"):
        c.submit(kjob)
    assert led.spent() == 0.0


def test_balance_without_admin_key_is_explained(kjob, tmp_path):
    c = fal.Client(Ledger(tmp_path / "l.jsonl"), session=Sess(gets=[FakeResp(403, {})]))
    bal, note = c.balance()
    assert bal is None and "Admin" in note


def test_talking_engine_header_and_tags():
    s = parse("# T\nformat: 9:16 talking_engine: kling\n## SCENE BIG_WORM_HOLE\n"
              "BILLY [tophat, skeptical]: Silly little worm!\nSAUL [holding-scroll, ltx]: Hi.\n", CHARS)
    shots = sh.plan(s, CHARS)
    assert [x.engine for x in shots] == ["kling_avatar", "ltx_a2v"]
    with pytest.raises(ScriptError, match="talking_engine"):
        parse("# T\ntalking_engine: hedra\n## SCENE BIG_WORM_HOLE\nBILLY [tophat]: Hi.\n", CHARS)


def test_kling_prompt_uses_owner_template_and_art_facing():
    on = sh.OnScreen("bad_billy", "tophat", "billy_tophat_head_skeptical", "closeup", "center")
    p = pipeline.kling_prompt(CHARS, on)
    assert p.startswith("Cartoon bird character with orange beak, black top hat with monocle on left eye, facing right")
    left = sh.OnScreen("bad_billy", "tophat", "billy_tophat_34left", "medium", "right")
    assert "facing left" in pipeline.kling_prompt(CHARS, left)


def test_prompt_templates_are_documented_verbatim():
    import yaml
    cfg = yaml.safe_load((LIBRARY / "kling_prompts.yaml").read_text())
    doc = " ".join((LIBRARY.parent / "docs" / "kling_prompts.md").read_text().split())
    for tpl in cfg["characters"].values():
        assert " ".join(tpl.split()) in doc


def _prod(tmp_path, header):
    s = parse(f"# T\n{header}\n## SCENE BIG_WORM_HOLE\nBILLY [tophat, skeptical]: Hi.\n", CHARS)
    return pipeline.Production(s, tmp_path, CHARS, [], {}, (720, 1280), Ledger(tmp_path / "ledger.jsonl"))


def test_caps_refuse_over_session_episode_and_max_cost(tmp_path):
    prod = _prod(tmp_path, "budget: 10 spend_cap: 4 session_cap: 1")
    assert pipeline.cap_problems(prod, 0.11, 0.20) == []
    assert any("--max-cost" in p for p in pipeline.cap_problems(prod, 0.25, 0.20))
    assert any("session cap" in p for p in pipeline.cap_problems(prod, 1.50, None))
    prod.ledger.write("fal:x", state="completed", kind="fal", cost_estimate=0.95)
    assert any("session cap" in p for p in pipeline.cap_problems(prod, 0.11, None))
    prod.ledger.write("ltx:y", state="completed", kind="ltx", cost_estimate=3.0)
    assert any("episode cap" in p for p in pipeline.cap_problems(prod, 0.11, None))


def test_srt_sidecar_format(tmp_path):
    from bbtb import assemble
    p = assemble.write_srt([("Silly little worm!", 0.15, 1.9), ("Oh POOP!", 61.5, 62.25)], tmp_path / "a.srt")
    assert p.read_text() == ("1\n00:00:00,150 --> 00:00:01,900\nSilly little worm!\n\n"
                             "2\n00:01:01,500 --> 00:01:02,250\nOh POOP!\n")
