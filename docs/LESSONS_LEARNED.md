# Lessons learned (short, newest first)

- **Kling 3.0 Turbo is permanently retired** (owner, 2026-10-10). Its record across EP001–EP004: 3 of 8 generations
  rejected (38%: EP001 S04 wrong facing, S08 smiling instead of scared, EP002 S02 take 1), wings turned into fists, Saul's
  eyes drooped for ~5 s (EP002 S01, shipped with the flaw), and its ElevenLabs re-voice step garbled short lines
  ("Oh POOP!" became "Owwooooo H OHP"). It has no negative field to block any of this. Talking shots go to Kling AI
  Avatar; action shots to Kling 3.0 Standard with references, a negative prompt and an end frame.

- **Kling O3 vs Kling 3.0 Standard** (owner, 2026-10-10, `productions/test-o3-ep001`, same keyframe, prompt and Billy
  references, 4 s each, $0.67 in total):
  - **O3** (reference-to-video, EP004 S07 0-3 s as a reference video): more expressive eyes (narrows suspiciously as
    asked), and the reference video helps the acting. But the beak flickered open on alternate frames at 3.0-3.4 s on
    a "beak closed" shot, O3 has no negative field, and it took two refused submits before the third worked (fal: an
    element is images OR a video, never both; the prompt limit is effectively under 2,500 characters, so the guard is
    2,400).
  - **Kling 3.0 Standard:** beak closed throughout, proven pipeline, negative field works. Its eyes closed fully at
    2.5-3.3 s (reads asleep). Both moved very little (motion 2.1 vs 1.6) and both ignored the left-then-right look.
  - **Decision:** keep Kling 3.0 Standard as primary. O3 is reserved for action shots where motion matters more than
    beak control. Test O3 again on a walking or landing shot before EP005.

- **The `feather_white` clip fix causes collateral damage: do not use it on paid clips without a per-frame visual
  check** (owner, 2026-10-09, EP001 fix-ups). Built to remove sheet-white slivers between Billy's wing feathers, it
  instead filled the light highlight where his raised wing meets the vest (EP001 S02: a green gap through his body at
  0.00 s, up to 600 px) and the highlight on the top edge of his beak (S06: up to 193 px in 33 of 148 frames), while
  barely touching the feather tips. Removed from every EP001 shot. The free chin fix (`trapped_white`) also needed two
  guards (`keep_collar` for his white shirt collar, `keep_scroll` for the scroll's cream paper) and was left off S04
  entirely (it marked his grey shirt). Pixel counts missed every one of these problems: only 2-3x crops showed them.

- **Saul's eyes must stay BIG** (Jason, 2026-10-06): add the eye-size rule to every Saul prompt explicitly
  (`{identity_young_saul}`), add the `saul_eyes` negative set, and lead his references with one large face close-up.
- **White under Billy's chin** (Jason, 2026-10-06): sheet background trapped inside the moustache curls survived the
  edge cleanup and was animated into every clip. The red-background test is now mandatory for every cut-out.
  A clip made from a dirty keyframe can't be fixed for free: it has to be re-generated.
- **Finished episodes are locked** (`keyframes: locked`): changing a cut-out, prompt, negative list or reference image
  of a paid shot orphans its clip. Freeze the old text (`*_v1`) before improving a template.
- **fal rejects reference images** outside an aspect ratio of 0.4–2.5 (EP003 run 1). Grids now wrap; the size is
  checked before sending.
- **Renumbered shots must be rekeyed** in references.yaml and prompt_notes.yaml. A Billy shot nearly got Saul's
  references; the tool now refuses references that don't match the characters on screen.
- **Character references plus the keyframe as end frame** keep Billy on model (EP003, about 7.8/10 against 5.4–7.0
  before). Without the end frame, Kling 3.0 Standard redesigned him within half a second (EP002 S02 retake 3).
- **Wing gestures become hands** on engines without a negative prompt (Turbo, Avatar). Keep the wings folded, and use
  Kling 3.0 Standard with `billy_hands`.
- **Check every frame by eye.** Auto-QA scored a melting crash 9.9/10 because it only compares the first and last
  frames.
- **Explain everything to the video API, every time** (owner, 2026-10-06: "we can't afford these kind of mistakes
  again and again"). Write the performance as an ordered list of moves tied to the words. When a take's gestures are
  liked, describe them explicitly in the prompt from then on (Kling can't replay a take). Re-read the prompt and the
  negative prompt together for contradictions before showing the approval code. The clean-chin S01 retake came out
  calmer because the first take's gestures had happened by chance, not by instruction.
- **A retake changes the performance.** When the owner likes a take and only a background artifact is wrong (the white
  under Billy's chin), fix it for free at render time (`clip_fixes.yaml`) instead of re-generating. Two paid retakes of
  EP003 S01 (calm, then overacted) never matched the take the owner liked.
- **Never use Kling Avatar for Saul** (owner, 2026-10-06): it cannot take the saul_eyes negative or reference sheets,
  so his eyes always drift smaller over time. The same goes for Kling 3.0 Turbo (EP002 S01: droopy half-closed eyes for
  ~5 s). Saul shots run on Kling 3.0 Standard with references + `neg:saul_eyes`, and the prompt forbids the exact drift
  (no squinting, no half-closed eyelids, no blinking). Pre-flight fails any other Saul engine.
- **Kling 3.0 Standard did NOT fix talking Saul's eyes** (EP003 S05 retake, 2026-10-06, $0.38): even with references, the
  big-eye identity, `saul_eyes` and an explicit "no squint, no blink" rule, his eyes drooped half-closed in 37% of frames
  (vs about 25% on the Avatar take). Silent Saul shots on Standard hold well (S04, S08). Talking makes Kling animate his
  heavy upper eyelids. Don't pay for more Saul talking retakes until a different approach is tested.
- **Art-based talking Saul rejected** (EP003 S05, 2026-10-06): enlarging the small character sheet faces 6x makes them
  blurry (also floating eyebrows, wrong mouth shape, oversized face). Never use this approach again. It needs high-res
  source art from Jason to work. Until then, use the Avatar take (0.5 s squint only), which is less noticeable than
  Standard's repeated drooping (37% of frames).
- **Hold the last open-eye frame over Saul's blinks/squints** (owner 2026-10-06: "no squinting Saul eyes anywhere, not even
  0.5 s"). `hold_frames` in `productions/<ep>/clip_fixes.yaml` is free and keeps the performance. Measure the eye in every
  frame, cover the eyelid fade (one frame either side), and hold a FULLY open frame. EP003: S04 frames 38–46, S08
  32–37 / 60–70 / 104–107; S05 ends at 0.56 s, before its squint.
- **No stills, reuse first, review every clip** (owner, 2026-10-06, after EP003): narrator shots that zoom into a still
  look like a slideshow. Hold shots with a character now render as parallax; anything without a character must reuse a
  clip. Thirty paid clips ($12.46) already exist (`library/clips/`), and reusing one costs $0. Every generated clip gets
  a 0.5 s frame sheet and the owner's approval before assembly.

## 2026-10-06: EP004 approval cards (found by the free planner, before any spend)
- **The shared negative prompt contradicted airborne shots.** It always contains "floating, sliding, feet off the ground";
  a dive and a skid need exactly those motions. A negative set can now `drop:` shared terms (`billy_dive`).
- **The automatic placement can't express height.** Billy's dive came out going UP (the airborne pose is centred higher
  than a grounded one) and floated with a ground shadow. Tags `pos:`/`endpos:` (`x/top/height[/air]`) place the start and
  end frames exactly; pre-flight checks the same placement.
- **A start frame without the character makes Kling invent him.** S02's Snail was only in the end frame: use a pose range
  (`side>side`) so he is in both.
- **`secs:` was ignored on Kling actions** (a 5 s beat list would have been squeezed into 3 s). Fixed: it's the minimum length.
- **Check reference crops by eye.** `billy_fly_approach2` is a second copy of Approach 1, so the board showed the same pose twice.

## 2026-10-06: GROUNDING (S07 take rejected)
GROUNDING RULE (owner, repeated 5+ times): every standing character's feet must sit on the flat walkable ground defined in ground_zones.yaml. Never on rims, ledges, edges, leaves or dark areas. Pre-flight blocks any keyframe that fails. Check the FEET panel on every approval card before approving.
- **What happened:** S07's keyframe put Billy's sneakers on the stump rim, hanging over its dark front face. Kling copied it,
  so the paid take looked like he was floating ($0.42, archived). It was already visible on the approval card.
- **Root cause:** characters were placed by framing rules only; the tool didn't know where the walkable ground is.
  The same bug caused EP004 v3 Big Pea floating in the cave and the worms on leaves in BG_MEADOW_SIGN_FLOWERS.
- **Fix:** `ground_zones.yaml` per plate, a pre-flight grounding gate (soles inside the ground, never over forbidden
  areas, surface under them not darker or different), contact shadows under the soles, a FEET panel on every card.
- **Plate choice matters:** GRASS_SIGN_LOW's foreground is all stump, so no full-size character can stand there.

## 2026-10-06: LOCATION CONTINUITY
LOCATION CONTINUITY: consecutive shots set in the same place use the same background plate (or plates showing the same landmark from the same side). A character who arrives somewhere stays there in the next shots. Show a continuity board before approval.
- **What happened:** EP004's ground shots jumped between three plates (GRASS_SIGN for the worms and the count, GRASS_STUMP
  for the landing, GRASS_FLOWERS for the burp): Billy would seem to teleport after landing "where the worms were".
- **Fix:** all of them at one spot (GRASS_STUMP), Billy standing exactly where he landed at the same scale (hat width
  matched: touchdown 0.38 H = standing 0.48 H), worms on the same flat grass; continuity board before approval.

## 2026-10-06: EP004 S02 (Snail)
Snail: Kling turns his pale-green eyes white when the stalks stretch. Next time add 'his eyes stay pale green' to the
prompt and 'white eyes' to the negative. Motion smear appears when he snaps back into the shell: keep the used part
before that. (S02 approved with `cut:1.8`, ending on the big open-mouth shout.)

## 2026-10-06: EP004 S05 and the count (owner)
Kling can't do a big fall in 3 s: it smears and face-plants (EP004 S05). Let the previous shot show the fall; the AI shot
only shows the last small move.
Never show eating with art animation: no open-beak body poses exist. Use a reaction cutaway instead.
Never use a floating head on its own over a background.
- Also: GRASS_FLOWERS has no clear sky (flowers fill the top): overlay numbers/text on the open grass in the character's
  eyeline instead.

## 2026-10-06: Snail reactions and direction changes (owner)
Snail: avoid shell in-and-out moves (smear). Use the wide-mouth gasp for big reactions; it's proven (S02).
A reaction cutaway between two shots of the same character hides a direction change.

## 2026-10-06: EP004 S05 v2 (owner)
Kling smears the first frames of a fast arrival. Plan to trim the start; cut from the previous shot into the impact.
Never mix our art-animated character and the Kling character inside one shot: the seam shows.
(S05 v2 approved with `trim:0.79`: f19 at 24 fps is the first frame with a sharp body and wings.)

## 2026-10-06: EP004 S06 Snail cutaway (owner)
Snail has no eyelids in Jason's art: never ask him to squeeze or shut his eyes (Kling turns them into brown blobs).
Kling turns his eyes white whenever they get big: plan the pale-green tint at render time for every Snail gasp.
When the clean moments of a reaction clip are short, cut them together as on-the-beat punch-ins instead of holding
frozen frames.
- Tools: clip_fixes.yaml `tint_eyes:` and `edit:` (segments with speed/zoom/hold); the paid clip is never modified.
- `cut:` holds a drawn still for the rest of the shot; use `out:` to END a shot (hard cut).
- fal's content checker can reject a request (HTTP 422, not charged, never retried): EP004 S04 "dive from the tree".

## 2026-10-07: cutting between shots (owner)
Cut on the action: when the next shot continues a movement, end the first shot while the character is still moving
fast, never on the slow-down or the held end pose. fal's content checker can refuse wording about falling from a
height ('dives down', 'nose down', 'far below'); describe it as flying or swooping.
- EP004 S04 v2 passed the checker; used f31-f50 (trim:1.29, out:2.125): 0-1.29 s he hovered and bobbed UP, from 2.17 s
  he slowed into the end pose. Overlays (numbers) are placed from measured character edges, never by eye.

## 2026-10-07: EP004 build notes
- Speech bubbles and text overlays: never over a character's eyes or hat, and always inside the 4:5 safe area
  (y 0.15-0.85 of the 9:16 frame). Check every frame of the shot AND the 4:5 crop (EP004 S02: the bubble first hid the
  Snail's eyes; moved above his head, it was then cut off in the 4:5 export; it now sits left of his head).
- Never split or insert a shot after paid shots exist: the tool numbers shots in order, so every later shot id (and its
  paid clip folder and approval) would shift. Put several local parts inside ONE shot instead (EP004 S01 `fx:opening`).
- A tilt needs a plate taller than the frame: crane over the full-resolution book page, not a frame-sized crop.
- S04 f34-f38 (the turn into the swoop) were crumpled at full size: always check the first used frame at full size.

## 2026-10-07: EP004 animatic v2 REJECTED (owner)
- Art-animated characters (bobbing cut-outs) read as stills: half the episode looked like a slideshow. Only overlays
  and the end-card background may be art-animated.
- Almost no voices made it lifeless (2 short narrator lines). Every beat needs a voice or a strong sound.
- The comic burst over the tree duplicated the Snail's bubble: one WATCH OUT only.
- I approved pieces one by one and never reviewed the whole animatic with sound before showing it.

## 2026-10-07: voices (owner)
Never give a background character another character's voice or line: viewers will think it IS that character.
- EP004: the four worms giggle / scream as ElevenLabs sound effects; Saul's "Ball time, everybody!" is removed.
- The Snail's first clone was built from his two clips trimmed but NOT denoised (hiss went into the clone). Rebuilds now
  denoise every clip of a character marked `voice.denoise_originals`.
- Billy's growl: only the last ~1.5 s "Arrrr", AFTER the narration, on his eyes narrowing - never under narration.

## 2026-10-07: card review (owner)
- A prop named in the prompt must be in the keyframes (S01a had a ball in the prompt, none in the frames).
- Group motion: keep it small and in place; jumping, scrambling and bumping merge bodies and multiply characters.
- A face reaction (eyes narrow, sly smile) needs a head-and-chest framing; the pose must face where he looks.
- Composite busts: check the neck join on a coloured background (a see-through gap appeared at neck 0.54).

## 2026-10-07: EP004 S01b take 1 (owner)
- Asking Kling for 'a villain who has just spotted his lunch' invited a performance (hip, wing-rub, grin to camera) and
  the style drifted toward semi-realistic. For a reaction shot, say what does NOT move (wings, head, gaze) and block
  camera looks, open beak and wing gestures explicitly.
