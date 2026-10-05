"""Offline tests: EP002 staging (two-shots, passes, far shots, camera zoom, plates, narration, placeholder pace)."""
import pytest

from bbtb import keyframes, shots as sh
from bbtb.script_parser import load_characters, parse

CHARS = load_characters()
SCRIPT = """# T
format: 9:16  talking_engine: kling3  action_engine: kling3  budget: 5
## SCENE BIG_WORM_HOLE
SAUL [standing-tall, zoom:1.15, with: BILLY 34left]: Excuse me, Bad Billy.
NARRATOR: Then off the two jumped into the vast open sky.
NARRATOR: They flew, and they flew.
ACTION [far, pass-right, fly-saul-down>fly-saul-up]: Bad Billy glides across the sky.
"""


def _plan():
    return sh.plan(parse(SCRIPT, CHARS), CHARS)


def test_two_shot_partner_and_zoom():
    talk = _plan()[0]
    speaker, partner = talk.cast
    assert speaker.char == "young_saul" and speaker.side == "left"
    assert partner.char == "bad_billy" and partner.role == "with" and partner.side == "right" and not partner.mirror
    assert talk.zoom == 1.15 and "with" not in talk.acting and "zoom" not in talk.acting


def test_two_narration_lines_ride_on_one_action_and_pass_travels():
    shots = _plan()
    assert len(shots) == 2
    fly = shots[1]
    assert fly.lines and len(fly.lines) == 2 and fly.engine == "kling3_action"
    assert fly.start_cast[0].side == "left" and fly.end_cast[0].side == "right"
    assert fly.start_cast[0].framing == "far" and fly.end_cast[0].art == "billy_tophat_fly_saul_up"


def test_zoomed_layout_is_composed_sharp_and_keeps_the_face_in_frame():
    talk = _plan()[0]
    size = (720, 1280)
    plain, p0 = keyframes.layout(talk.scene, talk.cast, CHARS, size)
    zoomed, p1 = keyframes.layout(talk.scene, talk.cast, CHARS, size, zoom=1.15)
    assert zoomed.size == size and p1[0].get("zoomed")
    assert p1[0]["art"].height > p0[0]["art"].height                       # drawn bigger from the original art
    face_y = p1[0]["top"] + 0.33 * p1[0]["art"].height
    assert 0.2 * size[1] < face_y < 0.6 * size[1]


def test_far_figures_are_small_and_airborne_has_no_ground():
    fly = _plan()[1]
    _, placed = keyframes.layout(fly.scene, fly.start_cast, CHARS, (720, 1280))
    assert placed[0]["art"].height <= 0.25 * 1280 and placed[0]["shadow"] is False


def test_plate_crop_must_stay_inside_the_original(monkeypatch, tmp_path):
    from bbtb import bgplates
    monkeypatch.setattr(bgplates, "specs", lambda: {"X": {"parent": "images.backgrounds.bg", "crop": [0, 0, 99999, 10],
                                                          "file": "backgrounds/X.png"}})
    monkeypatch.setattr(bgplates, "MANIFEST", tmp_path / "m.yaml")
    with pytest.raises(ValueError, match="outside"):
        bgplates.build()


def test_placeholder_pace_follows_the_character(tmp_path):
    from bbtb import media, voices
    voices._silent("one two three four five six seven eight nine", tmp_path / "a.wav", 4.5)
    voices._silent("one two three four five six seven eight nine", tmp_path / "b.wav", 2.3)
    assert media.duration(tmp_path / "a.wav") < media.duration(tmp_path / "b.wav")
