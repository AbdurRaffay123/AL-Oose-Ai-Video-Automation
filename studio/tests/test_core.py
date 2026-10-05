"""Offline tests: script parsing, shot planning, and LTX spend safety (fake HTTP, no network)."""
from pathlib import Path

import pytest
import requests

from bbtb import ltx, pipeline, shots as sh
from bbtb.ledger import Ledger
from bbtb.script_parser import ScriptError, load_characters, parse

CHARS = load_characters()

SCRIPT = """# T
format: 9:16  resolution: 720p  budget: 5
## SCENE BIG_WORM_HOLE
ACTION [wide]: Bad Billy looks around.
BILLY [tophat, suspicious]: Where is the worm?
SAUL [holding-scroll]: Right here.
SFX [at 1.5]: roar
NARRATOR: Then out shot The Big Guy.
ACTION [wide, end: BIG GUY arms-up]: The Big Guy bursts out.
"""


def test_parse_classifies_tags():
    s = parse(SCRIPT, characters=CHARS)
    assert s.meta["budget"] == 5.0
    d = [e for e in s.events if e.kind == "dialogue"]
    assert (d[0].speaker, d[0].variant, d[0].expression) == ("bad_billy", "tophat", "suspicious")
    assert (d[1].speaker, d[1].pose) == ("young_saul", "holding-scroll")


def test_parse_errors_are_plain():
    with pytest.raises(ScriptError, match="unknown character 'GERALD'"):
        parse("## SCENE BIG_WORM_HOLE\nGERALD: hi", characters=CHARS)
    with pytest.raises(ScriptError, match="SCENE"):
        parse("BILLY: hi", characters=CHARS)


def test_plan_one_speaker_per_talk_shot_and_narration_on_action():
    s = parse(SCRIPT, characters=CHARS)
    shots = sh.plan(s, CHARS)
    talk = [x for x in shots if x.kind == "talk"]
    assert all(len(x.cast) == 1 and x.engine == "ltx_a2v" for x in talk)
    assert talk[0].cast[0].framing == "closeup"           # expression-only tag
    assert talk[1].cast[0].framing == "medium"            # pose tag
    erupt = shots[-1]
    assert erupt.engine == "ltx_i2v" and erupt.cast == [] and erupt.end_cast[0].char == "big_guy"
    assert erupt.lines and erupt.lines[0].endswith("narrator")
    assert erupt.sfx == [{"name": "roar", "at": 1.5}]


def test_billy_is_never_mirrored():
    s = parse(SCRIPT, characters=CHARS)
    for x in sh.plan(s, CHARS):
        for o in x.cast + x.end_cast:
            if o.char == "bad_billy":
                assert o.mirror is False


def test_durations_follow_audio_and_i2v_rounds_up():
    s = parse(SCRIPT, characters=CHARS)
    shots = sh.plan(s, CHARS)
    secs = {l.id: 2.0 for l in sh.lines_of(s)}
    sh.apply_durations(shots, secs)
    talk = [x for x in shots if x.engine == "ltx_a2v"][0]
    assert talk.gen_seconds == pytest.approx(2.5)     # 2.0 s line + 0.25 s padding each side
    assert all(x.gen_seconds in (6, 8, 10) for x in shots if x.engine == "ltx_i2v")


def test_a2v_line_too_long_is_rejected():
    s = parse(SCRIPT, characters=CHARS)
    shots = sh.plan(s, CHARS)
    with pytest.raises(ValueError, match="Split the line"):
        sh.apply_durations(shots, {l.id: 25.0 for l in sh.lines_of(s)})


# ---------------------------------------------------------------- LTX safety (fake HTTP)

class FakeResp:
    def __init__(self, status=200, body=None, headers=None, content=b"video"):
        self.status_code, self._body, self.headers, self.content = status, body or {}, headers or {}, content
        self.text = str(body)

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(self.status_code)

    def iter_content(self, n):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeSession:
    def __init__(self, post_responses, get_responses):
        self.posts, self.gets = list(post_responses), list(get_responses)
        self.post_calls = 0

    def post(self, url, **kw):
        self.post_calls += 1
        r = self.posts.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def get(self, url, **kw):
        return self.gets.pop(0)


@pytest.fixture
def job(tmp_path, monkeypatch):
    monkeypatch.setenv("LTX_API_KEY", "test-key-123456")
    img = tmp_path / "f.jpg"
    img.write_bytes(b"\xff\xd8fakejpeg")
    return ltx.Job("S01", "image-to-video", {"prompt": "p", "model": "ltx-2-3-pro", "duration": 6,
                   "resolution": "720x1280"}, {"image_uri": img}, 6, "720p", tmp_path / "out" / "ltx.mp4")


def test_cost_matches_published_price(job):
    assert job.cost == pytest.approx(0.24)


def test_full_happy_path_and_no_double_submit(job, tmp_path):
    led = Ledger(tmp_path / "ledger.jsonl")
    sess = FakeSession([FakeResp(202, {"id": "job1"})],
                       [FakeResp(200, {"status": "processing"}),
                        FakeResp(200, {"status": "completed", "result": {"video_url": "https://x/v.mp4"}}),
                        FakeResp(200, content=b"MP4DATA")])
    c = ltx.Client(led, session=sess, sleep=lambda s: None)
    out = c.run(job)
    assert out.read_bytes() == b"MP4DATA"
    assert led.find(job.request_hash())["state"] == "completed"
    assert c.submit(job) == "job1" and sess.post_calls == 1      # never paid twice
    assert led.spent() == pytest.approx(0.24)


def test_timeout_after_post_is_unknown_and_blocks_resubmit(job, tmp_path):
    led = Ledger(tmp_path / "ledger.jsonl")
    sess = FakeSession([requests.Timeout()], [])
    c = ltx.Client(led, session=sess, sleep=lambda s: None)
    with pytest.raises(ltx.LtxError, match="NOT be retried"):
        c.submit(job)
    assert led.find(job.request_hash())["state"] == "unknown"
    with pytest.raises(ltx.LtxError, match="Check the LTX console"):
        c.submit(job)
    assert sess.post_calls == 1


def test_out_of_credits_is_plain_and_not_counted(job, tmp_path):
    led = Ledger(tmp_path / "ledger.jsonl")
    c = ltx.Client(led, session=FakeSession([FakeResp(402, {"error": {}})], []), sleep=lambda s: None)
    with pytest.raises(ltx.LtxError, match="out of credits"):
        c.submit(job)
    assert led.spent() == 0.0


def test_failed_job_can_be_resubmitted(job, tmp_path):
    led = Ledger(tmp_path / "ledger.jsonl")
    sess = FakeSession([FakeResp(202, {"id": "j1"}), FakeResp(202, {"id": "j2"})],
                       [FakeResp(200, {"status": "failed", "error": {"message": "boom"}})])
    c = ltx.Client(led, session=sess, sleep=lambda s: None)
    with pytest.raises(ltx.LtxError, match="boom"):
        c.run(job)
    assert c.submit(job) == "j2"


def test_approval_code_changes_with_jobs_or_budget(job, tmp_path):
    a = pipeline.approval_code([job], 10)
    assert a == pipeline.approval_code([job], 10)
    assert a != pipeline.approval_code([job], 12)
    job.payload["prompt"] = "different"
    assert a != pipeline.approval_code([job], 10)


def test_secrets_redacted(monkeypatch, tmp_path):
    from bbtb import env
    monkeypatch.setattr(env, "ENV_FILE", tmp_path / ".env")
    (tmp_path / ".env").write_text("LTX_API_KEY=supersecretvalue\n")
    assert "supersecretvalue" not in env.redact("token supersecretvalue leaked")


# ---------------------------------------------------------------- v2: sources, local engines, voice gate

V2 = """# T
## SCENE BIG_WORM_HOLE
ACTION [wide, local, enter-right]: Bad Billy hops in.
BILLY [tophat, skeptical, local, canon:p29 speech bubble]: Silly little worm!
ACTION [medium, local, scroll-pickup>scroll-reading]: Billy unrolls the scroll.
SAUL [holding-scroll, adapted:p28]: Don't sweat.
"""


def test_source_tags_are_recorded_and_not_acting():
    s = parse(V2, characters=CHARS)
    d = [e for e in s.events if e.kind == "dialogue"]
    assert d[0].source == "canon:p29 speech bubble" and d[1].source == "adapted:p28"
    lines = sh.lines_of(s)
    assert all("canon" not in " ".join(l.direction) and "local" not in l.direction for l in lines)


def test_local_tags_select_free_engines_and_motions():
    shots = sh.plan(parse(V2, characters=CHARS), CHARS)
    assert [x.engine for x in shots] == ["local_anim", "local_flap", "local_anim", "ltx_a2v"]
    assert shots[0].motion == ["enter-right"]
    assert shots[2].cast[0].art == "billy_tophat_scroll_pickup"
    assert shots[2].motion == ["pose:billy_tophat_scroll_reading"]


def test_local_action_cannot_use_end_frame():
    with pytest.raises(ValueError, match="needs LTX"):
        sh.plan(parse("## SCENE BIG_WORM_HOLE\nACTION [wide, local, end: BIG GUY arms-up]: The Big Guy bursts out.",
                      characters=CHARS), CHARS)


def test_mouth_pairs_only_where_art_matches():
    from bbtb import animate
    b = CHARS["bad_billy"]
    assert animate.mouth_pair(b, "tophat", "billy_tophat_head_skeptical") == ("billy_tophat_head_skeptical", "billy_tophat_head_talking")
    assert animate.mouth_pair(b, "tophat", "billy_tophat_head_shock") is None          # no partner
    assert animate.mouth_pair(b, "tophat", "billy_tophat_scroll_reading") is None      # no head swap on scroll poses
    assert animate.mouth_pair(CHARS["young_saul"], None, "saul_talking_scroll") is None


def test_voice_gate_blocks_talking_shots_with_unready_voices(tmp_path, job):
    from bbtb import pipeline
    talk = sh.Shot(id="S01", kind="talk", engine="ltx_a2v", scene="X", lines=["L1"])
    prod = pipeline.Production(script=None, root=tmp_path, chars=CHARS, shots=[talk],
                               lines={"L1": {"source": "elevenlabs", "final": False}}, size=(720, 1280),
                               ledger=Ledger(tmp_path / "l.jsonl"))
    a2v = ltx.Job("S01", "audio-to-video", {"model": "ltx-2-3-pro"}, {}, 2.0, "720p", tmp_path / "S01.mp4")
    assert pipeline.voice_blockers(prod, [a2v]) == ["S01 (L1: elevenlabs)"]
    prod.lines["L1"] = {"source": "original", "final": True}
    assert pipeline.voice_blockers(prod, [a2v]) == []




def test_talking_shot_without_final_voice_cannot_be_submitted(tmp_path, monkeypatch):
    monkeypatch.setenv("LTX_API_KEY", "test-key-123456")
    img = tmp_path / "f.jpg"
    img.write_bytes(b"\xff\xd8x")
    j = ltx.Job("S02", "audio-to-video", {"prompt": "p", "model": "ltx-2-3-pro"}, {"image_uri": img}, 3.0, "720p",
                tmp_path / "S02" / "ltx.mp4")
    assert j.ready is False and j.cost == pytest.approx(0.18)          # still priced for the estimate
    sess = FakeSession([], [])
    with pytest.raises(ltx.LtxError, match="voice is not final"):
        ltx.Client(Ledger(tmp_path / "l.jsonl"), session=sess, sleep=lambda s: None).submit(j)
    assert sess.post_calls == 0


def test_audio_bed_reads_either_key_name_without_calling_any_api(tmp_path, monkeypatch):
    from bbtb import audio_bed
    monkeypatch.setattr(env_mod := __import__("bbtb.env", fromlist=["x"]), "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_LABS_API_KEY", raising=False)
    (tmp_path / ".env").write_text("ELEVEN_LABS_API_KEY=abc123456789\n")
    assert audio_bed._key() == "abc123456789"
    (tmp_path / ".env").write_text("")
    assert audio_bed._key() is None and audio_bed.estimate(["rumble"], "playful-adventure", 40) == 0.0


def test_mux_replaces_the_animatic_instead_of_rewriting_it(tmp_path, monkeypatch):
    """A player holding the old animatic open must never see a half-rewritten file (QuickTime froze, 2026-10-04)."""
    from bbtb import assemble, media
    monkeypatch.setattr(media, "ffmpeg", lambda *a: Path(a[-1]).write_bytes(b"new"))
    dst = tmp_path / "animatic.mp4"
    dst.write_bytes(b"old")
    before = dst.stat().st_ino
    assemble.mux(tmp_path / "video.mp4", tmp_path / "mix.wav", dst)
    assert dst.read_bytes() == b"new" and dst.stat().st_ino != before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["animatic.mp4"]


def test_mux_never_adds_captions_or_a_subtitle_track(tmp_path, monkeypatch):
    """Captions live only in the .srt sidecar (owner adds them in CapCut): no subtitles, no text filters."""
    from bbtb import assemble, media
    calls = []
    monkeypatch.setattr(media, "ffmpeg", lambda *a: (calls.append(a), Path(a[-1]).write_bytes(b"x")))
    assemble.mux(tmp_path / "video.mp4", tmp_path / "mix.wav", tmp_path / "animatic.mp4")
    assemble.mux(tmp_path / "video.mp4", tmp_path / "mix.wav", tmp_path / "x_4x5.mp4", crop_4x5=True)
    for args in calls:
        joined = " ".join(args)
        assert "-sn" in args and ".srt" not in joined and "mov_text" not in joined
        assert not any(f in joined for f in ("subtitles=", "drawtext", "ass="))


CARD_SCRIPT = SCRIPT + """## SCENE END_CARD
NARRATOR [production, card:tease]: Did a tiny worm just outsmart the baddest bird around?
NARRATOR [production, card:book, emoji:🐛]: Bedtime just got WAY more fun. Link in bio!
"""


def test_end_card_moments_split_into_tease_and_book():
    shots = sh.plan(parse(CARD_SCRIPT, characters=CHARS), CHARS)
    tease, book = shots[-2:]
    assert (tease.card, book.card) == ("tease", "book")
    assert tease.engine == book.engine == "local_endcard" and len(tease.lines) == len(book.lines) == 1
    assert tease.backdrop == "BIG_WORM_HOLE" and book.emoji == "🐛"
    assert book.card_text == "Bedtime just got WAY more fun. Link in bio!"
    lines = {l.id: l for l in sh.lines_of(parse(CARD_SCRIPT, characters=CHARS))}
    assert lines[book.lines[0]].direction == []           # card/emoji tags never reach the voice
    sh.apply_durations(shots, {l: 2.0 for s in shots for l in s.lines})
    assert tease.duration == 2.75 and book.duration == 4.0    # 2.0 s + 0.25 s line pad + 0.5 s; book: 4 s minimum


def test_end_card_without_card_tag_is_unchanged_and_unknown_card_fails():
    old = sh.plan(parse(SCRIPT + "## SCENE END_CARD\nNARRATOR: Follow!\nNARRATOR: Now!\n", characters=CHARS), CHARS)
    assert old[-1].card == "" and len(old[-1].lines) == 2
    with pytest.raises(ValueError, match="unknown end card 'promo'"):
        sh.plan(parse(SCRIPT + "## SCENE END_CARD\nNARRATOR [card:promo]: Buy!\n", characters=CHARS), CHARS)


def test_book_card_fits_the_safe_area_and_ep002_cta_renders():
    from bbtb import keyframes
    text = "Bedtime just got WAY more fun. Bad Billy the Bird — grab your copy! Link in bio!"
    L = keyframes.book_layers((720, 1280), text, "🐛")
    assert L["link"] is not None and len(L["cta"]) == 2
    assert keyframes.book_frame(L, 4.0).size == (720, 1280)
    with pytest.raises(ValueError, match="safe area"):
        keyframes.book_layers((720, 1280), " ".join(["A long line that keeps going."] * 6) + " Link in bio!")


def test_silent_card_needs_no_voice_and_lasts_its_reading_time():
    script = parse(SCRIPT + "## SCENE END_CARD\nNARRATOR [production, card:tease, silent]: one two three four five six seven\n",
                   characters=CHARS)
    assert all("one two" not in l.text for l in sh.lines_of(script))        # nothing to record
    shots = sh.plan(script, CHARS)
    sh.apply_durations(shots, {l: 1.0 for s in shots for l in s.lines})
    assert shots[-1].lines == [] and shots[-1].card_text.startswith("one two") and shots[-1].duration == 2.8


def test_secs_tag_sets_a_minimum_length_for_a_local_shot():
    script = parse("# T\n## SCENE BIG_WORM_HOLE\nNARRATOR: Short.\n"
                   "ACTION [wide, local, pass-right, landing-approach>landing-touchdown, secs:3.5]: Bad Billy glides in.\n",
                   characters=CHARS)
    shot = sh.plan(script, CHARS)[0]
    sh.apply_durations([shot], {shot.lines[0]: 1.0})
    assert shot.engine == "local_anim" and "pass-right" in shot.motion and shot.duration == 3.5
    assert "secs:3.5" not in shot.acting


def test_title_card_is_silent_timed_text_in_the_4x5_area():
    from bbtb import keyframes
    script = parse(SCRIPT + "## SCENE END_CARD\nNARRATOR [production, card:title, silent, secs:9.5]: "
                   "What did Saul do to Bad Billy? | Find out in the book! 📖 | Bad Billy the Bird — Link in bio\n",
                   characters=CHARS)
    shots = sh.plan(script, CHARS)
    sh.apply_durations(shots, {l: 1.0 for s in shots for l in s.lines})
    card = shots[-1]
    assert card.card == "title" and card.lines == [] and card.duration == 9.5
    layers = keyframes.title_layers((720, 1280), card.card_text)
    assert [t for _, _, t in layers] == [1.0, 2.5, 4.0]
    for layer, y, _ in layers:                      # every line inside the 4:5 safe area
        box = layer.getbbox()
        assert box[1] >= 0.148 * 1280 and box[3] <= 0.852 * 1280
    assert keyframes._emoji_split("Find out in the book! 📖") == ("Find out in the book!", "📖")


def test_defringe_clears_the_white_halo_but_keeps_outlined_whites():
    """Jason 2026-10-05: no white left around cut-outs; eyes/gloves (outlined) must survive."""
    import numpy as np
    from PIL import Image, ImageDraw
    from bbtb import cutout
    im = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((8, 8, 72, 72), fill=(250, 250, 250, 255))         # sheet-white halo ring...
    d.ellipse((10, 10, 70, 70), fill=(240, 200, 0, 255))         # ...around a yellow body (2 px halo, as real)
    d.ellipse((28, 28, 52, 52), fill=(0, 0, 0, 255))             # an eye: black outline
    d.ellipse((31, 31, 49, 49), fill=(255, 255, 255, 255))       # with a white eye inside
    assert cutout.edge_white(im) > 0
    out, cleared = cutout.defringe(im)
    a = np.asarray(out)
    assert cutout.edge_white(out) == 0 and cleared > 0
    assert (a[40, 40, :3] == 255).all() and a[40, 40, 3] == 255         # the eye white is untouched
    assert (a[20, 40, :3] == (240, 200, 0)).all() and a[20, 40, 3] == 255  # the body is untouched


def test_references_are_capped_at_three_per_character(tmp_path):
    from bbtb import references
    (tmp_path / "references.yaml").write_text("S01:\n  bad_billy:\n    frontal: billy_head_neutral\n"
                                              "    refs: [[billy_head_neutral], [billy_head_angry], [billy_head_wink], [billy_head_talking]]\n")
    with pytest.raises(ValueError, match="at most 3 reference images"):
        references.build(tmp_path, CHARS)


def test_music_library_analyses_tracks_and_never_repeats_the_last_one(tmp_path, monkeypatch):
    import subprocess
    from bbtb import music_lib
    monkeypatch.setattr(music_lib, "DIR", tmp_path)
    monkeypatch.setattr(music_lib, "INV", tmp_path / "music_inventory.yaml")
    for name, freq in (("bouncy.wav", 2600), ("calm.wav", 220)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration=12:sample_rate=22050",
                        str(tmp_path / name)], check=True)
    inv = music_lib.scan()
    assert set(inv["tracks"]) == {"bouncy.wav", "calm.wav"}
    t = inv["tracks"]["bouncy.wav"]
    assert abs(t["duration"] - 12) < 0.2 and t["mood"] and t["energy"] in ("high", "medium", "low")
    first = music_lib.pick("playful", 10, record=True)
    second = music_lib.pick("playful", 10, record=True)
    assert first != second                                           # never the previous episode's track
    assert "MUSIC_INVENTORY.md" in [p.name for p in tmp_path.iterdir()]


def test_empty_music_library_falls_back(tmp_path, monkeypatch):
    from bbtb import music_lib
    monkeypatch.setattr(music_lib, "DIR", tmp_path)
    monkeypatch.setattr(music_lib, "INV", tmp_path / "music_inventory.yaml")
    assert music_lib.pick("playful", 30) is None


def test_reference_grids_stay_inside_klings_aspect_limit():
    """EP003: 3- and 4-across reference rows (ratio 2.9-3.9) were rejected by fal (limit 0.4-2.5)."""
    from bbtb import references
    for names in (["billy_head_neutral"] * n for n in (1, 2, 3, 4)):
        g = references.grid(names)
        assert references.aspect_ok(g), (len(names), g.size)
