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


def test_red_test_fails_undecided_white_and_passes_once_decided(tmp_path, monkeypatch):
    """Jason 2026-10-06: sheet white trapped inside a moustache curl showed under Billy's chin in every clip."""
    from PIL import Image, ImageDraw
    from bbtb import cutout
    im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((5, 5, 95, 95), fill=(240, 200, 0, 255))              # body
    d.ellipse((30, 30, 60, 60), fill=(40, 170, 190, 255))           # a curl...
    d.ellipse((36, 36, 54, 54), fill=(255, 255, 255, 255))          # ...with sheet white trapped inside
    monkeypatch.setattr(cutout, "_cut_spec", lambda cid: {})
    r = cutout.red_test("x", im)
    assert not r["ok"] and len(r["undecided"]) == 1                 # undecided white blocks the cut-out
    monkeypatch.setattr(cutout, "_cut_spec", lambda cid: {"keep_white": [[0.45, 0.45]]})
    assert cutout.red_test("x", im)["ok"]                           # approved as art -> passes


def test_locked_episode_references_cannot_be_rebuilt():
    import subprocess, sys
    from bbtb.paths import LIBRARY
    r = subprocess.run([sys.executable, "-m", "bbtb.cli", "references", str(LIBRARY.parent / "productions/ep003/script.md")],
                       capture_output=True, text=True, cwd=LIBRARY.parent, env={"PYTHONPATH": str(LIBRARY.parent / "studio"), "PATH": "/usr/bin:/bin"})
    assert r.returncode != 0 and "locked" in (r.stderr + r.stdout)


def test_trapped_white_fix_replaces_only_white_below_the_chin_line():
    import numpy as np
    from bbtb import clipfix
    fr = np.full((200, 200, 3), (240, 200, 0), np.uint8)          # yellow bird
    fr[40:60, 80:120] = 255                                        # eye white, above the chin line
    fr[130:150, 80:120] = 252                                      # trapped sheet white, below it
    plate = np.full((200, 200, 3), (90, 60, 30), np.uint8)         # tree trunk
    out, n = clipfix.trapped_white_frame(fr, plate, (0, 0, 200, 200), below_y=100)
    assert n > 0 and (out[140, 100] == plate[140, 100]).all()      # chin white -> background
    assert (out[50, 100] == 255).all()                             # the eye white is untouched


def test_keep_collar_keeps_the_shirt_collar_and_still_removes_the_chin_white():
    """EP001 S06 (owner 2026-10-08): the white collar points between the vest and the tie are Billy's costume."""
    import numpy as np
    from bbtb import clipfix
    fr = np.full((200, 200, 3), (240, 200, 0), np.uint8)          # yellow bird
    fr[120:200, 60:140] = (90, 20, 25)                             # dark-red vest
    fr[120:170, 97:104] = (215, 62, 20)                            # red-orange tie
    fr[120:135, 88:97] = 252                                       # collar point left of the tie
    fr[120:135, 104:113] = 252                                     # collar point right of the tie
    fr[110:140, 20:50] = 252                                       # trapped sheet white beside the neck
    plate = np.full((200, 200, 3), (90, 60, 30), np.uint8)
    out, _ = clipfix.trapped_white_frame(fr, plate, (0, 0, 200, 200), below_y=100, keep_collar=True)
    assert (out[125, 30] == plate[125, 30]).all()                  # chin white -> background
    assert (out[127, 92] >= 245).all() and (out[127, 108] >= 245).all()   # both collar points stay white
    assert (out[150, 100] == (215, 62, 20)).all()                  # the tie is untouched
    old, _ = clipfix.trapped_white_frame(fr, plate, (0, 0, 200, 200), below_y=100)
    assert (old[127, 92] == plate[127, 92]).all()                  # default (EP003) behaviour is unchanged


def test_keep_scroll_keeps_the_cream_paper_and_still_removes_the_chin_white():
    """EP001 S05 (owner 2026-10-08): the open scroll's cream paper touches the trapped white; it must not be blended."""
    import numpy as np
    from bbtb import clipfix
    fr = np.full((200, 200, 3), (240, 200, 0), np.uint8)          # yellow bird
    fr[140:200, 20:120] = (240, 220, 180)                          # big cream scroll paper (6,000 px)
    fr[110:140, 30:80] = 252                                       # trapped sheet white, touching the paper's top edge
    plate = np.full((200, 200, 3), (60, 140, 40), np.uint8)
    out, _ = clipfix.trapped_white_frame(fr, plate, (0, 0, 200, 200), below_y=100, keep_scroll=True)
    assert (out[125, 50] == plate[125, 50]).all()                  # chin white -> background
    assert (out[140:200, 20:120] == fr[140:200, 20:120]).all()     # every paper pixel identical
    old, _ = clipfix.trapped_white_frame(fr, plate, (0, 0, 200, 200), below_y=100)
    assert (old[141, 50] != fr[141, 50]).any()                     # default (EP003/S06) blends the paper edge, as before


YELLOW, WHITE, GREEN = (250, 205, 40), (250, 250, 250), (60, 140, 40)


def _wing(sliver=True, blob=False):
    """Two yellow feathers on green grass, a 2 px sheet-white gap between them (or a solid white blob)."""
    import numpy as np
    fr = np.zeros((120, 120, 3), np.uint8); fr[:] = GREEN
    fr[20:100, 30:50] = YELLOW
    fr[20:100, 52:72] = YELLOW
    if sliver:
        fr[25:95, 50:52] = WHITE
    if blob:
        fr[40:60, 85:105] = WHITE                     # a glove / sneaker toe: a solid blob, must survive
    plate = np.zeros_like(fr); plate[:] = GREEN
    return fr, plate


def test_feather_white_fills_the_sliver_from_the_plate():
    import numpy as np
    from bbtb import clipfix
    fr, plate = _wing()
    out, n = clipfix.sliver_white_frame(fr, plate, (0, 0, 120, 120), "yellow")
    assert n >= 140                                   # the 2 x 70 px sliver
    assert abs(out[25:95, 50:52].astype(int) - np.array(GREEN)).max() < 40
    assert (out[20:100, 30:48] == YELLOW).all()       # the feathers themselves are never touched


def test_feather_white_keeps_solid_white_blobs_and_respects_the_box():
    from bbtb import clipfix
    fr, plate = _wing(sliver=True, blob=True)
    out, _ = clipfix.sliver_white_frame(fr, plate, (0, 0, 120, 120), "yellow")
    assert (out[42:58, 87:103] == WHITE).all()        # a blob is not a sliver
    out2, n2 = clipfix.sliver_white_frame(fr, plate, (80, 0, 120, 120), "yellow")
    assert n2 == 0 and (out2 == fr).all()             # outside the box nothing changes


def test_feather_white_no_op_on_a_clean_frame():
    from bbtb import clipfix
    fr, plate = _wing(sliver=False)
    out, n = clipfix.sliver_white_frame(fr, plate, (0, 0, 120, 120), "yellow")
    assert n == 0 and (out == fr).all()


def test_hold_frames_replaces_a_blink_with_the_last_good_frame(tmp_path):
    import subprocess
    import numpy as np
    from PIL import Image
    from bbtb import clipfix
    W, H = 64, 64
    frames = np.zeros((10, H, W, 3), np.uint8)
    for i in range(10):
        frames[i] = i * 20                                         # every frame different
    src = tmp_path / "c.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24",
                          "-i", "-", "-c:v", "libx264", "-crf", "0", "-pix_fmt", "yuv444p", str(src)], stdin=subprocess.PIPE)
    p.stdin.write(frames.tobytes()); p.stdin.close(); p.wait()
    out = clipfix.apply(src, Image.new("RGB", (W, H)), {"hold_frames": [[4, 6]]}, tmp_path / "o.mp4")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    got = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)[:, 32, 32, 0].astype(int)
    assert len(got) == 10 and abs(got[4] - got[3]) <= 3 and abs(got[6] - got[3]) <= 3 and abs(got[7] - 140) <= 6


REUSE_SCRIPT = """# R
## SCENE BIG_WORM_HOLE
NARRATOR [production]: Then out shot The Big Guy.
ACTION [reuse:EP001_S07, from:2.5]: The Big Guy bursts out.
BILLY [reuse:EP001_S08, canon:p31]: Oh POOP!
"""


def test_reuse_tags_plan_free_shots_and_bring_their_own_line():
    s = parse(REUSE_SCRIPT, characters=CHARS)
    shots = sh.plan(s, CHARS)
    assert [x.engine for x in shots] == ["reuse_clip", "reuse_talk"]
    assert shots[0].reuse == "EP001_S07" and shots[0].reuse_from == 2.5 and len(shots[0].lines) == 1
    assert all("Oh POOP" not in l.text for l in sh.lines_of(s))          # the reused clip brings its own audio
    from bbtb import cliplib
    e = cliplib.entry("EP001_S08")
    with pytest.raises(ValueError, match="same words"):
        cliplib.talk_audio(e, "Oh no!")
    assert cliplib.talk_audio(e, "Oh POOP!")[0].exists()
    with pytest.raises(ValueError, match="marked 'no'"):
        cliplib.entry("WANTEST2_S01")


def test_review_gate_blocks_unapproved_takes(tmp_path):
    from bbtb import review
    assert not review.approved(tmp_path, "S01", "fal:abc")
    review.approve(tmp_path, "S01", "fal:abc", "ok")
    assert review.approved(tmp_path, "S01", "fal:abc") and not review.approved(tmp_path, "S01", "fal:new-take")


def test_parallax_moves_the_character_and_the_background(tmp_path):
    import subprocess
    import numpy as np
    from bbtb import animate
    s = parse("# P\n## SCENE BIG_WORM_HOLE\nBILLY [tophat, 34left, suspicious, local]: Hi.\nNARRATOR: Billy waited.\n",
              characters=CHARS)
    hold = sh.plan(s, CHARS)[-1]
    assert hold.engine == "local_still" and hold.cast
    hold.duration = 1.0
    out = animate.render_parallax(hold, CHARS, (180, 320), tmp_path / "p.mp4")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 320, 180, 3).astype(int)
    assert len(f) == 24 and np.abs(f[-1] - f[0]).mean() > 2                # it really moves (not a still)


# ---------------------------------------------------------------- under_white (EP001 S03, owner 2026-10-10)
import numpy as np

from bbtb.clipfix import under_white_frame

U_PINK, U_OUTLINE, U_WHITE, U_GRASS = (240, 170, 210), (60, 20, 40), (245, 245, 240), (90, 170, 40)


def _saul(strip=True, glove=False, lone=False):
    fr = np.zeros((120, 120, 3), np.uint8); fr[:] = U_GRASS
    fr[20:60, 20:100] = U_PINK                          # Saul's body
    fr[60:62, 20:100] = U_OUTLINE                       # his dark outline
    if strip:
        fr[62:64, 30:90] = U_WHITE                      # sheet-white strip between the outline and the grass
    if glove:
        fr[40:60, 100:120] = U_WHITE                    # a white glove: a solid blob, must survive
    if lone:
        fr[90:92, 30:90] = U_WHITE                      # a white line on open grass, nothing above it
    plate = np.zeros_like(fr); plate[:] = U_GRASS
    return fr, plate


def test_under_white_fills_the_strip_with_grass_and_keeps_saul_and_his_glove():
    fr, plate = _saul(glove=True)
    out, n = under_white_frame(fr, plate, (0, 0, 120, 120))
    assert n >= 120 and (out[62:64, 30:90] == U_GRASS).all()       # strip -> grass
    assert (out[20:60, 20:100] == U_PINK).all() and (out[60:62, 20:100] == U_OUTLINE).all()
    assert (out[40:60, 100:120] == U_WHITE).all()                   # the glove is a blob, not a strip


def test_under_white_ignores_white_with_no_body_above_and_respects_the_box():
    fr, plate = _saul(strip=False, lone=True)
    out, n = under_white_frame(fr, plate, (0, 0, 120, 120))
    assert n == 0 and (out == fr).all()
    fr, plate = _saul()
    out, n = under_white_frame(fr, plate, (0, 0, 120, 50))       # box above the strip
    assert n == 0 and (out == fr).all()
