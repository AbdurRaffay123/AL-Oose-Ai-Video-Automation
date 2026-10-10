"""Grounding gate (owner rule, repeated 5+ times): feet on the flat walkable ground, or pre-flight FAILs."""
from bbtb import grounding, keyframes, shots as sh
from bbtb.script_parser import load_characters, parse

CHARS = load_characters()
SIZE = (720, 1280)


def _gate(scene: str, action: str):
    s = parse(f"# T\nformat: 9:16 action_engine: kling3\n## SCENE {scene}\n{action}\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    bg, placed = keyframes.layout(shot.scene, shot.cast, CHARS, SIZE, place=shot.place)
    return grounding.check(shot.scene, placed, bg)


def test_every_background_has_a_ground_zone():
    assert set(keyframes.backgrounds()) <= set(grounding.zones())


def test_point_in_polygon():
    sq = [[0, 0], [1, 0], [1, 1], [0, 1]]
    assert grounding.inside((0.5, 0.5), sq) and not grounding.inside((1.5, 0.5), sq)


def test_rejected_ep004_s07_feet_on_the_stump_rim_fail():
    """The owner-rejected S07 keyframe: Billy auto-placed on GRASS_SIGN_LOW, sneakers on the stump rim."""
    res = _gate("GRASS_SIGN_LOW", "ACTION [medium, kling3std, 34left>34left, loop]: Bad Billy stands.")
    assert res[0][1] == "FAIL", res


def test_feet_on_flat_grass_pass():
    res = _gate("GRASS_FLOWERS", "ACTION [medium, kling3std, 34left>34left, pos:0.6/0.21/0.63, loop]: Bad Billy stands.")
    assert res[0][1] == "PASS", res


def test_feet_on_leaves_or_cut_off_or_no_floor_fail():
    leaves = _gate("BG_MEADOW_SIGN_FLOWERS", "ACTION [medium, kling3std, 34left>34left, loop]: Bad Billy stands.")
    cut = _gate("GRASS_FLOWERS", "ACTION [medium, kling3std, 34left>34left, pos:0.6/0.5/0.63, loop]: Bad Billy stands.")
    assert leaves[0][1] == "FAIL" and "no walkable ground" in leaves[0][2]
    assert cut[0][1] == "FAIL" and "cut off" in cut[0][2]


def test_only_script_tagged_airborne_poses_are_exempt():
    air = _gate("BG_OAK_TREEHOUSE", "ACTION [wide, kling3std, landing-approach1>landing-approach, "
                                    "pos:0.36/0.16/0.24/air]: Bad Billy dives.")
    untagged = _gate("BG_OAK_TREEHOUSE", "ACTION [wide, kling3std, landing-approach1>landing-approach, "
                                         "pos:0.36/0.16/0.24]: Bad Billy dives.")
    assert air[0][1] == "PASS" and untagged[0][1] == "FAIL"


def test_contact_shadow_sits_under_the_soles():
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_FLOWERS\n"
              "ACTION [medium, kling3std, 34left>34left, pos:0.6/0.21/0.63, loop]: Bad Billy stands.\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    bg, placed = keyframes.layout(shot.scene, shot.cast, CHARS, SIZE, place=shot.place)
    with_shadow = keyframes.draw(bg, placed)
    feet_y = max(y for _, y in grounding.soles(placed[0]["art"], placed[0]["x"], placed[0]["top"]))
    a, b = bg.convert("RGB").crop((0, feet_y + 2, SIZE[0], feet_y + 6)), with_shadow.convert("RGB").crop((0, feet_y + 2, SIZE[0], feet_y + 6))
    assert a.tobytes() != b.tobytes()                       # the ground just under the soles is darkened


def test_group_figure_checks_every_member_and_props_are_exempt():
    from bbtb import cutout
    members = cutout.composite_members("worms_group_ball")
    assert len(members) == 4                                  # the ball (a prop) is not a figure with feet
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE GRASS_STUMP\n"
              "ACTION [wide, kling3std, group-ball>group-ball, pos:0.5/0.0/1.0, loop]: The worms play.\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    bg, placed = keyframes.layout(shot.scene, shot.cast, CHARS, SIZE, place=shot.place)
    res = grounding.check(shot.scene, placed, bg)
    assert res[0][1] == "PASS" and "4 figures" in res[0][2]


def test_head_and_chest_pushin_has_no_feet_to_check():
    s = parse("# T\nformat: 9:16 action_engine: kling3\n## SCENE BG_OAK_TREEHOUSE\n"
              "ACTION [medium, kling3std, watch-down>watch-down, zoom:1.55, pos:0.30/0.32/0.62, loop]: Bad Billy watches.\n", CHARS)
    shot = sh.plan(s, CHARS)[0]
    bg, placed = keyframes.layout(shot.scene, shot.cast, CHARS, SIZE, zoom=shot.zoom, place=shot.place)
    res = grounding.check(shot.scene, placed, bg)
    assert res[0][1] == "PASS" and "feet out of frame" in res[0][2]
