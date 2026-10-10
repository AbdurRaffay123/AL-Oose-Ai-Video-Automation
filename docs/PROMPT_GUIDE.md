# Prompt Guide: writing AI video prompts for Bad Billy the Bird

**Who this is for:** anyone (Jason, the owner, a developer or an AI) who writes prompts for the cartoon shots in this
studio.

**What it covers:** why prompts matter, the seven parts of a good prompt, ready templates for each shot type, ideas for
future episodes, mistakes to avoid, and what each video model needs.

**Where prompts live:** the real prompts the tool sends are in `library/kling_prompts.yaml`, quoted word for word in
`docs/kling_prompts.md`. Test results are scored in `docs/model_comparison.md`.

> **Scope.** The model notes in Section 6 come from our own paid tests (EP001 and the Wan 2.7 test on 2026-10-04) and
> from the providers' public pages. Anything we have not tested ourselves is marked **untested**.

---

## Section 1: Why prompts matter so much

The model only knows what the prompt and the first frame tell it. Give the same model the same picture and the same
voice with two different prompts, and you get two different performances. A vague prompt gets the model's safe
default: a character that stands still and moves its mouth a little.

**Our own before/after (EP001 S02, same model, same keyframe, same voice):**

| | Prompt (the movement part) | What happened |
|---|---|---|
| **Before** (Wan 2.7 test 1, `wan_bad_billy_v1`) | "his beak opens and closes in time with the voice, with small natural head and body movements" | The owner's verdict: "Billy just stands and talks". Body movement 4/10, energy 3/10, overall 6/10 |
| **After** (Wan 2.7 test 2, `talk_bad_billy_max_energy`, awaiting approval) | "lunges far forward with his neck stretched out, then whips back upright; his head jabs, tilts and bobs to the rhythm of the words; both wings sweep out wide like a showman's cape and snap back to his sides; he stomps one foot, shifts his weight and bounces on his knees" | To be scored in `docs/model_comparison.md` |

The word "small" in the old prompt asked for small movements, and that's what we got. **Models do what the words say,
not what we meant.** If you want a big performance, the prompt has to describe a big performance, body part by body
part.

**What prompts can and can't fix:**
- The prompt is the cheapest thing to change: rewriting one costs nothing, while switching models means new code and
  new tests.
- Some limits are the model's, not the prompt's. Kling Avatar mostly sways the head whatever you write. Wan test 1 had
  a pose snap at the end.
- So when a result is bad, first ask "did the prompt ask for this?" and only then "can this model do it?"

---

## Section 2: The 7 elements of a great prompt

### 1. Character identity (who they are)
Describe how the character looks **first**, before anything happens. Name every feature that must survive the clip,
with its colour.

- **Monocle position is critical.** Always write "monocle on his LEFT eye". Billy is never mirrored: the art and the
  pre-flight check guarantee the first frame, and the prompt protects the rest of the clip.
- **Colours:** orange beak, feathered yellow wings, black top hat.
- **Accessories:** the "B" badge on the hat (and its crack), the monocle, the moustache curls, the red-and-blue shoes.

> Example: "Cartoon bird villain with an orange beak, a black top hat with a "B" badge, a monocle on his LEFT eye and
> feathered yellow wings"

Add `{facing}` (the tool fills in "facing left" or "facing right" from the art). The model must not "correct" his
direction.

### 2. Personality and energy (how they feel)
- **Generic:** "expressive, natural movement"
- **Better:** "cocky, theatrical, show-off villain"
- **Best:** "every line is a scene-stealing performance: he leans far forward to taunt and rocks back for effect"
- **Rule: match the energy to the CHARACTER, not just the line.** Billy is a show-off even when he is scared: his
  fear is *theatrical* fear. Saul is brave and polite even when he shouts. The line's emotion (from the script's
  acting tag, `{acting}`) sits on top of the character's baseline.

### 3. Body movement (what the body does)
- **Generic:** "natural body movement"
- **Better:** "body leans forward with energy"
- **Best:** "lunges far forward with his neck stretched out, whips back upright, stomps one foot, shifts his weight,
  bounces on his knees"
- **Rule: say WHICH body part moves, and HOW.** Use verbs with force (lunge, whip, jab, stomp, flare, snap), not
  adjectives (dynamic, lively).
- **Order matters:** "first … then …" gives the model a sequence to follow, and sequences read as acting.

### 4. Mouth / beak movement (lip sync quality)
- **Generic:** "mouth moves with words"
- **Better:** "beak opens wide and closes with each word"
- **Best:** "beak flies WIDE open and snaps shut on every word"
- **Rule: for cartoon beaks, say WIDE.** Models default to subtle, realistic mouths, which read as "not talking" on a
  cartoon. Capitals help the word stand out.
- With **Kling 3.0 Turbo** the model speaks the line itself, so quote the line: `says: "{line}"`. With **Wan 2.7** our
  audio drives the beak, so describe the beak and let the audio supply the words.

### 5. What must never change (consistency rules)
Always include these three:
- "Wings stay as feathered bird wings at all times, no human hands, no fingers, no arms". Without it, Kling has turned
  Billy's wings into hands.
- "The top hat and monocle stay on", when there is big motion.
- "Consistent 2D cartoon style" and "No smearing".

**Rule: list what CANNOT change, feature by feature**, not just what should happen. "Maintain the design" is too vague
to help.

On models that accept a **negative prompt** (Kling 3.0 Standard, Wan 2.7), the shared `negative:` list in
`kling_prompts.yaml` adds the "never" list: floating, morphing, smearing, extra limbs, text, watermark, 3D render,
realistic, style change, monocle on the right eye, mirrored character.

### 6. Location and grounding (scene context)
- **Generic:** "outdoor scene"
- **Better:** "standing on rocky ground"
- **Best:** "feet planted on rocky ground, never floating, dust puffing up with each stomp"
- **Rule: grounded characters look solid.** Name the surface the feet touch. Name the scene only in a few words: the
  first frame already shows it, and a long scene description invites the model to repaint it.
- Make sure the location in the prompt **matches the keyframe**. A meadow prompt on a rocky keyframe makes the model
  fight the picture.

### 7. Camera and style (technical rules)
- **Always:** "Static camera". Our shots are composed for the 4:5 safe area, and a moving camera breaks it.
- **Always:** "Consistent 2D cartoon style, exactly the same art style and colours as the image".
- **Always:** "No smearing". Fast motion is where models smear.
- **Often:** "No new characters, no text". Captions and titles are added locally, never by the AI.

---

## Section 3: Prompt templates by shot type

Fill the `[BRACKETS]`. The tool fills `{facing}`, `{acting}`, `{line}` and `{direction}` for you when the template is
saved in `library/kling_prompts.yaml`.

### Template A: villain speaking (Billy talking)
```
[CHARACTER IDENTITY], {facing}, [LOCATION + GROUNDING].
[PERSONALITY]: every line is a performance.
He is {acting} and says: "{line}"
[BEAK MOVEMENT]. [BODY MOVEMENT, in order].
[CONSISTENCY RULES]. [CAMERA/STYLE].
```
**Real example (`talk_bad_billy`, v6):**
> Cartoon bird villain, orange beak, black top hat, monocle on left eye, {facing}, standing on rocky ground. A cocky,
> theatrical show-off: every line is a performance. He is {acting} and says: "{line}" Beak opens WIDE and snaps shut
> with each word. He throws his whole body into the line: leans far forward on the taunts, rocks back on his heels for
> effect, head tilting and bobbing with the rhythm of the words. Wings flare out wide for emphasis, then fold back. Feet
> shift and stomp on the ground, never floating. Big, bold villain personality, never casual. Wings stay as feathered
> bird wings at all times, no human hands, no fingers, no arms. Static camera. Consistent 2D cartoon style. No smearing.

### Template B: character reacting (shock, fear)
```
[CHARACTER IDENTITY], {facing}, [LOCATION].
[WHAT THEY SEE/HEAR]: [what the body does first, then next].
[BEAK MOVEMENT, or "beak frozen open" if silent]. [BODY MOVEMENT].
[CONSISTENCY RULES]. [CAMERA/STYLE].
```
**Real example (`billy_shocked`, v6):**
> Cartoon bird villain, orange beak, black top hat, monocle on left eye, {facing}, on rocky ground. He looks up in total
> shock at something ENORMOUS towering over him and recoils dramatically: his whole body jerks back, wings fly up and out
> wide in panic, mouth drops open. His bravado cracks and he stammers in a trembling voice, beak moving with every word:
> "{line}" Head shakes in disbelief, knees wobble, feet scramble a step backwards. Over-the-top, theatrical fear. Wings
> stay as feathered bird wings at all times, no human hands, no fingers, no arms. Static camera. Consistent 2D cartoon
> style. No smearing.

### Template C: action shot (walking, flying, crashing)
```
[CHARACTER IDENTITY].
[ACTION]: [start] → [middle] → [end], with the physical cause of each move.
[WHAT STAYS CONSISTENT].
[CAMERA/STYLE].
```
- Action shots run on Kling 3.0 Standard with a **start frame and an end frame**. The prompt should describe the
  journey between those two pictures, nothing beyond them.

**Real example (`billy_crash`, EP002 S07):**
> A cartoon bird in a black top hat swoops down to land among the rocks, touches down, slides through the mud, trips on
> a rock and tumbles head over heels, clamping his top hat onto his head with one wing. The top hat stays on his head
> the whole time. Mud splashes where he slides. Real weight and momentum. Feathered bird wings, no hands. Static camera.
> Consistent 2D cartoon style, exactly the same art style and colours as the image.

### Template D: two characters in frame
```
[CHARACTER 1 IDENTITY] and [CHARACTER 2 IDENTITY], [who is where], [LOCATION].
Only [SPEAKER] speaks: "{line}"
[SPEAKER MOUTH MOVEMENT + BODY].
[NON-SPEAKER] stays silent with his [beak/mouth] closed, [what the non-speaker does instead].
[CONSISTENCY RULES]. [CAMERA/STYLE].
```
- **One speaker per talking shot** is a studio rule. Say twice that the other character is silent: models like to
  animate every mouth they see.

**Real example (`saul_brave`, EP002 S01):**
> Small pink cartoon worm character with huge round pale-blue eyes and white cartoon gloves, {facing}, standing up tall
> and brave in front of a much bigger cartoon bird in a black top hat. Only the worm speaks: "{line}" The worm's mouth
> opens wide and moves with each word, one gloved hand raised politely. The bird stays silent with his beak closed,
> leaning over the worm with a suspicious glare. Static camera. Consistent 2D cartoon style. No smearing.

---

## Section 4: Prompt ideas for future episodes

These are starting points: add the identity and consistency rules (Section 2) before using one.

Ideas that need art we don't have yet are marked:
- **The snail** has no cut-outs yet. His recorded design is "an orange-shelled cartoon snail with big googly eyes and a
  tiny top hat" (`library/characters/snail.yaml`). Check the book art (p.14) for gloves and eye colour before adding
  them.
- **The group of worms** has no art beyond Saul.

1. **Billy sneaking** (low energy, suspicious)
   > Cartoon bird villain creeping slowly across the frame, hunched low, beak almost shut, eyes darting side to side,
   > tiptoeing with exaggerated cartoon care, wings folded tight to his body; he freezes mid-step at a sound, one foot
   > still raised, then creeps on.
2. **Billy triumphant** (celebrating a catch)
   > Cartoon bird villain throwing both wings up in victory, hopping on the spot, beak wide open in a villainous laugh,
   > head thrown back, chest puffed out, landing each hop with a stomp.
   - The shared negative prompt contains "feet off the ground". For a jump, use small hops that land, or drop that
     phrase from this shot's negative prompt.
3. **Billy confused** (something went wrong)
   > Cartoon bird villain scratching his head under the hat brim with one wing tip, beak half-open in confusion, head
   > tilting left, then right, one foot tapping, the monocle on his LEFT eye catching the light.
4. **Saul being brave** (standing up to Billy)
   > Small pink cartoon worm standing as tall as he can, chin up, one gloved fist raised, eyes determined, speaking loud
   > and clear despite being tiny next to the huge bird looming over him.
5. **Saul riding** (on Billy's back in flight)
   > Small pink cartoon worm clinging to a flying bird's back, eyes wide with excitement and terror, mouth open in a
   > whoop, tiny gloved hands gripping the feathers, wind pushing his cheeks back, body leaning forward into the wind.
6. **Billy flying** (moving through the air)
   > Cartoon bird villain soaring across the sky, wings beating in a strong, steady rhythm, beak pointed forward with
   > determination, tail feathers streaming behind, one wing tip pressing the top hat down against the wind.
7. **Billy landing** (touchdown)
   > Cartoon bird villain coming in fast, wings spread wide to brake, feet forward for landing; a dust cloud as he touches
   > down, he skids, rights himself, straightens his hat with one wing tip and looks around with a satisfied nod.
8. **Group shot: worms running away** (needs new worm art)
   > Four small cartoon worms scattering in different directions in total panic, each with a different terrified
   > expression, arms flailing, two tumbling over each other, dust puffs at their tails.
9. **Snail reacting**, too slow as always (needs snail art)
   > Small orange-shelled cartoon snail with big googly eyes and a tiny top hat, his mouth dropping open in slow-motion
   > horror, eyes widening gradually, moving at snail pace while the action around him happens instantly.
10. **Billy eating**, off screen, told through sound (needs snail art)
    > Close-up of the snail's horrified face, eyes going wider with each gulp heard off screen, his tiny top hat
    > trembling with each thud, mouth frozen open in a silent scream.
    - Put the gulps and thuds on the SFX track, not in the prompt.

---

## Section 5: What NOT to put in prompts

| Bad | Why it hurts | Write instead |
|---|---|---|
| "realistic animation" | Pushes toward photoreal, away from the book's 2D style | "consistent 2D cartoon style, same art style and colours as the image" |
| "smooth animation" | Says nothing the model can act on | Specific moves: "whips back upright", "wings snap back" |
| "the character speaks naturally" | Too vague, so you get the subtle default | "beak flies WIDE open and snaps shut on every word" |
| "good lip sync" | A wish, not an action | Describe the beak action. With Wan 2.7, supply our audio |
| "maintain character design" | Too vague to check | List each feature: LEFT-eye monocle, B badge, feathered wings… |
| "camera follows the action" | Moving camera breaks the 4:5 safe area and the start/end frames | "Static camera" |
| "realistic feathers" | Same as "realistic": pushes toward photoreal | "feathered yellow cartoon wings" |
| "small / gentle / subtle movements" | You get exactly that (Wan test 1) | Strong verbs and a sequence of moves |
| Text the model should draw ("a sign saying…") | AI text is garbled, and captions are added locally | "no text" |
| A location that doesn't match the keyframe | The model repaints the background | Name the surface the feet touch, the same as in the picture |
| Mirroring words ("flipped", "turns around") | Risks the monocle switching eyes | Keep `{facing}` as the art faces |

---

## Section 6: Model-specific rules

| | Kling 3.0 Turbo | Kling 3.0 Standard | Kling Avatar v2 | Wan 2.7 |
|---|---|---|---|---|
| **Used for** | Short talking lines with full-body acting | Action shots (start → end frame) | Long dialogue lines | Talking (testing) |
| **Price (720p)** | $0.112/s | $0.084/s silent | $0.0562/s | $0.10/s ($0.15 at 1080p, the API default) |
| **Length** | 3–15 whole seconds | 3–15 whole seconds | Length of our audio | 2–15 whole seconds |
| **Voice** | Speaks the line itself; ElevenLabs Voice Changer re-voices it as Billy | Silent | Our ElevenLabs audio | Our ElevenLabs audio drives beak and timing |
| **Prompt rules** | Quote the line: `says: "{line}"`. No negative prompt or end frame | Describe start → middle → end; negative prompt applies; keep it under about 6–7 s | Short character prompt only (`characters:` in the YAML); the audio does the work | Our tool turns prompt expansion OFF and sends 720p explicitly; negative prompt max 500 characters |
| **What we saw** | Best body energy (EP001 S04: body 8/10, beak 8/10), but less consistent (5/10) | Fast motion smears; the end frame keeps the landing on-model | Beak barely opens (EP001 S02: beak 3/10); head and shoulder sway | Stable and on-model, clear beak, but static (test 1: body 4/10) and a pose snap at the end |
| **Known issues** | Wings turn into hands: always add the wing rule. Voice Changer garbles screams and short exclamations | Smearing in fast moves | Low energy; better for calm speakers | Too static with a gentle prompt; test 2 checks if a high-energy prompt fixes it |

**Character references (Jason, 2026-10-05): the biggest lever.**
- **Kling 3.0 Standard** accepts `elements`: per character a frontal image plus 1–3 reference images, named in the
  prompt as `@Element1`, `@Element2`. The price is the same.
- **Our setup:** `productions/<ep>/scene_references/elements/`, built by `./bbtb references`, header `elements: on`. Kling
  then SEES the official sheets instead of only reading words.
- **Turbo takes no references**, so use `kling3std` for every character shot.
- **Wings:** the official sheets say Billy's wings ACT as hands, with long separate feather fingers. Write
  "feather-finger wing tips", not "no hands". What must never appear is smooth human hands or fists (the S02 Turbo
  pilot).

**Not tested yet**
- **PixVerse v6:** $0.045/s silent at 720p; our voice only via a $0.04/s lipsync pass on the finished clip; first+last
  frame via its `transition` endpoint.
- **MiniMax H3 Max:** free sandbox, 5 a day; see `docs/MINIMAX_TEST_INSTRUCTIONS.md`.

**Housekeeping**
- **Changing a template changes the approval code** of every shot that uses it.
- **Never rewrite a template that made a finished clip:** the clip would stop matching its request, and a re-export
  would replace it with a still. Copy the old text to a versioned name (e.g. `billy_shocked_v5`), point the finished
  episode at it, then edit the original.
- **Add a new template to `docs/kling_prompts.md` too.** A test checks that the doc quotes every template word for word.

---

## Section 7: Background selection
The background is the **keyframe**: Kling starts from our composed frame, so the location is already in the picture.
The prompt then only has to name the ground the characters touch.

**Picking one** (see `library/backgrounds/INVENTORY.md`, 21 backgrounds with a 9:16 preview of each):
- Write `## SCENE <name>` for an exact background, or `## SCENE <type>` to let the tool choose the best-rated one.
  It never picks the same background twice in a row.
- **Conversation:** the stump meadow from three angles (GRASS_STUMP, GRASS_FLOWERS, GRASS_SIGN), BG_MEADOW_SIGN_FLOWERS
  and BG_OAK_TREEHOUSE. Alternate them on shot/reverse-shot so each cut feels like a new angle.
- **Flying:** BG_SKY_RAINBOW (pastel, happy), BG_ISLAND_WINDMILL_SKY (lilac, dreamy), BG_SKY_CASTLE (adventure),
  BG_SKY_ISLAND_AIRSHIP (bright blue). Airborne characters need `air_y`, set on every sky plate.
- **Underground / tension:** BG_CAVE_STUDY, BG_CAVE_TUNNEL, TUNNELS. **Danger:** BIG_WORM_HOLE.

**Rules**
- **Match the prompt to the plate:** a meadow prompt on a rocky plate makes Kling repaint the scene (Section 5).
- **Lettering is canon** (the "Look UP in the tree" sign), but only on shots where the camera holds still. Never ask
  the AI to write text.
- **Wide sky plates** (BG_ISLAND_WINDMILL_SKY, BG_SKY_ISLAND_AIRSHIP) show only a part at 9:16. Set `focus` to the
  part you want.
- **Background as an element** (`bg_element: on`) is an experiment. Kling documents elements for characters and
  objects, and the keyframe already carries the location. A/B test it on one cheap shot before relying on it.


---

## Section 8: End card strategy
The full rotation is in `docs/CTA_STRATEGY.md`.
- **Never use the book CTA in two episodes in a row.**
- **Alternate between curiosity, engagement and sales:** at most one sales ending in three episodes.
- **Cliffhanger episodes never end with a sales pitch:** ask a question instead ("Did Saul forget Rule Number One?!").
- **Easy answers get comments:** YES/NO, a name, an emoji. Keep on-screen text to two short lines, drawn locally.
- **Visual-only CTAs** (`silent` / `show:`) can be changed for free after the voices are rendered. Spoken ones need a
  new voice render and approval code.

---

## Section 9: The two things Jason checks first (2026-10-06)
- **Billy's chin:** no white under the beak. Every cut-out passes the red-background test (`./bbtb cutouts`) before it
  goes into a keyframe; pre-flight blocks it otherwise.
- **Saul's eyes:** ENORMOUS and ROUND in every frame. Use `{identity_young_saul}` (it carries the big-eye rule), the
  `saul_eyes` negative set (`negatives: billy_hands,saul_body,saul_eyes`), and references that start with one large face
  close-up. `./bbtb preprod` marks a Saul shot NO-GO without them.

See `docs/CHARACTER_BIBLE.md` and `docs/LESSONS_LEARNED.md`.

## Grounding before prompting (owner, 2026-10-06)
GROUNDING RULE (owner, repeated 5+ times): every standing character's feet must sit on the flat walkable ground defined in ground_zones.yaml. Never on rims, ledges, edges, leaves or dark areas. Pre-flight blocks any keyframe that fails. Check the FEET panel on every approval card before approving.
Kling copies the keyframe: a prompt can't fix feet that the start frame puts on a rim. Fix the keyframe (and pick a
plate with open flat ground) before writing a word of the prompt.
