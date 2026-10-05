# Kling prompt templates

**v1 (Avatar)**: long dialogue shots S02, S03, S06. **v3/v4 (Kling 3.0)**: every other generated shot. EP001 was made with this hybrid on 2026-10-04. Source of truth: `library/kling_prompts.yaml`.

## v1: Kling AI Avatar v2

Used for the long dialogue shots (script tag `kling`) made with fal **Kling AI Avatar v2 Standard** (`fal-ai/kling-video/ai-avatar/v2/standard`, $0.0562 per output second).

- **Source of truth:** `library/kling_prompts.yaml`. The code reads it, and a test checks that this page quotes it word for word.
- **Changing a prompt** changes the approval code of every affected shot. An old approval can never pay for a new prompt.
- **What Kling receives:** the prompt, the shot's keyframe (`keyframes/Sxx_first.jpg`) and the trimmed, −16 LUFS line audio (`shots/Sxx/kling_voice.wav`).

## Bad Billy

> Cartoon bird character with orange beak, black top hat with monocle on left eye, {facing}, beak animates to match speech audio, consistent style throughout, no style drift, character stays on model

`{facing}` is taken from the art as drawn; the art is never mirrored:

| Shot | Art | Facing | Words used |
|---|---|---|---|
| S02 | `34left` | left | facing left |
| S06 | `scroll-reading` | left | facing left |

**Two changes from the owner's wording (2026-10-03), both factual:**
1. **"yellow beak" became "orange beak".** Billy's beak is orange on every model sheet (`library/characters/bad_billy.yaml`). Telling the model "yellow" invites it to recolour the beak, which is style drift.
2. **"facing right" became `{facing}`.** S02 and S06 use art where Billy faces left; that's correct shot/reverse-shot staging with Saul. Mirroring the art to make him face right is forbidden (the monocle must stay on his LEFT eye), so the prompt names the direction the art actually faces.

To use the exact original wording anyway, edit `library/kling_prompts.yaml`; the free run then prints new codes.

## Young Saul

> Small pink cartoon worm character with huge round pale-blue eyes, brown eyebrows, two buck teeth and white cartoon gloves, {facing}, mouth animates to match speech audio, consistent style throughout, no style drift, character stays on model

S03 uses `holding-scroll`, which faces right, so the prompt says "facing right". The description comes from `library/characters/young_saul.yaml`.

## Narrator
The narrator is voice-over only; it never appears on screen and has no Kling shot. Its lines ride on these shots:
- S05: Billy unrolls the scroll (Kling 3.0 Standard).
- S07: the Big Guy bursts out (Kling 3.0 Standard).
- S10: the end card (local).

## Results log

### Tests
| Date | Shot | Prompt version | Beak moved? | Owner verdict | Cost | Notes |
|---|---|---|---|---|---|---|
| 2026-10-03 | S04 | v1 Avatar | yes, but small | **rejected** for short lines: floaty, beak not clearly visible | $0.11 | Kling adds ~0.46 s after the speech. Clip deleted 2026-10-04 |
| 2026-10-04 | S04 | v3 Kling 3.0 Turbo + re-voice | **yes, wide and clear** | **approved as-is**; it is the S04 in the final | $0.34 + 51 EL credits | Full-body acting with dust puffs. Whisper heard the exact line before and after the re-voice. **Drift:** the wings became arms with hands, which led to the v4 fix |

### EP001 final shots (approval code 27C34623, 2026-10-04; owner: EP001 complete)
| Shot | Engine / prompt | Auto-QA | Notes |
|---|---|---|---|
| S01 | Kling 3.0 Std, `billy_walk` v3 | WARN: frames 10/10, motion 1.4 (low) | **Known issue:** the empty scene holds ~1.7 s, then Billy pops up from behind the rocks; there's no walking strut |
| S02 | Avatar v1 + our audio | consistency 1.3/10* | on-model; lip sync to our audio |
| S03 | Avatar v1 + our audio | consistency 0/10* | on-model; lip sync to our audio |
| S04 | Kling 3.0 Turbo, `billy_taunt` v5 (retake, B30A4EEA) | 0/10*, "mirrored"* | on the right facing Saul, feathered wings, beak wide open; take 1 (v3) is in `shots/S04/takes/` |
| S05 | Kling 3.0 Std, `billy_scroll` | PASS 10/10 | scroll unroll |
| S06 | Avatar v1 + our audio | consistency 0/10* | scroll-reading pose; beak partly side-on |
| S07 | Kling 3.0 Std, `big_guy_erupt` v3 | PASS 10/10 | the Big Guy rises from the hole |
| S08 | Kling 3.0 Turbo, `billy_terrified` v5 (retake, 61261DC2) | PASS beak, 0/10*, "mirrored"* | terrified, not smiling. The Voice Changer was rejected ("Owwooooo H OHP!"); the final plays the approved line on Kling's timing. Take 1 (v4, grinning) is in `shots/S08/takes/` |
| S09 | Kling 3.0 Turbo, `billy_shocked` v4 + re-voice | 0/10*, "mirrored"* | wings on hips, no fingers; Whisper heard the exact line after the re-voice |

\* **False alarms.** The consistency metric compares pixels against the first frame, so any turn or big movement scores about 0. "Mirrored" fires when Billy turns to three-quarters view; the monocle stays on his LEFT eye.

### Final cost summary (EP001)
| Item | Cost |
|---|---|
| Kling 3.0 Standard (S01, S05, S07) | $0.92 |
| Kling AI Avatar (S02, S03, S06) | $1.18 |
| Kling 3.0 Turbo (S04 $0.34, S08 $0.34, S09 $0.67) | $1.34 |
| Avatar test (S04 v1, rejected) | $0.11 |
| Retakes S04 + S08 (v5) | $0.67 |
| **fal.ai total** | **$4.23** (ledger) |
| ElevenLabs re-voice (S04, S08, S09) | ~203 credits |

Full episode record: [`EPISODE_LOG.md`](EPISODE_LOG.md).

## Hybrid engine plan (owner, 2026-10-04)
| Shot | Engine | Template |
|---|---|---|
| S01 walk-in | Kling 3.0 Standard, silent | `billy_walk` |
| S02, S03, S06 long dialogue | Kling AI Avatar v2 + our ElevenLabs audio (script tag `kling`) | v1 `characters` |
| S04, S08 short Billy lines | Kling 3.0 Turbo + ElevenLabs re-voice | S04 `talk_bad_billy_v3` (approved), S08 `talk_bad_billy` |
| S09 | Kling 3.0 Turbo + ElevenLabs re-voice | `billy_shocked` |
| S05 scroll | Kling 3.0 Standard, silent | `billy_scroll` |
| S07 Big Guy erupts | Kling 3.0 Standard, silent | `big_guy_erupt` |
| S10 end card | local (free) | – |

`talk_bad_billy`, `billy_walk` and `big_guy_erupt` were replaced with the owner's natural-motion prompts (v3, 2026-10-04).

**v4 (owner, 2026-10-04):** S04's v3 take turned Billy's wings into human hands. `talk_bad_billy` and `billy_shocked` now add "Wings stay as feathered bird wings at all times, no human hands, no fingers, no arms." The owner approved S04 as-is, so S04 is tagged `prompt:talk_bad_billy_v3` (the unchanged v3 text). Its approved clip is reused, not regenerated.

## v2/v3: Kling 3.0 (owner's prompts, 2026-10-04): in use
- **Talking:** `fal-ai/kling-video/v3/turbo/standard/image-to-video`, $0.112/s, 720p.
  - Kling's own audio is always on. Kling speaks the line, the beak follows its voice, and ElevenLabs Voice Changer then turns that voice into the character's approved voice.
  - Turbo can't take a negative prompt or an end frame.
- **Action:** `fal-ai/kling-video/v3/standard/image-to-video`, $0.084/s with audio off.
  - Animates from the first frame to the last frame, and uses the negative prompt below.
- **Choosing a template:** a script line picks one with the tag `prompt:<name>`. Talking lines default to `talk_<character>`.

**S02 pilot result and v8 (owner, 2026-10-05).**
- **Pilot:** the Turbo pilot (v7) had the best beak and energy so far (sync r=0.52), but Billy's wings became fists
  with fingers for about 3 s.
- **Why:** every wing gesture we asked for turned into a hand.
- **v8:**
  - No wing gestures; the wings stay folded and only the head and body act.
  - S02 moves to Kling 3.0 Standard (tag `kling3std`), which takes a negative prompt and an end frame (the keyframe
    itself, to return to the start pose).
  - Like Turbo, Standard speaks the line itself (fal has no audio input for it), and ElevenLabs re-voices it.
- **Negative set `billy_hands`** (script header `negatives: billy_hands`; added to every Kling 3.0 Standard shot with
  Billy on screen): human hands, human fingers, fists, clenched hands, fingers spread, arms, human limbs, hand gestures

**v7 EP002 prompts (owner, 2026-10-04, after the Wan tests).**
- **Energy:** Billy at about **65%**, not maximum. Wan's MAX ENERGY test showed that full energy breaks the model (badge,
  hair, hand-like wings, a beak stuck open). So: ONE big lean, wings spread ONCE, head on the rhythm, and he returns near
  his start pose.
- **Fixed sentences:** every Billy prompt carries the owner's exact sentences for the monocle, the wings and the style
  lock. Ground shots also carry the beak and grounding sentences.
- **Colours:** taken from the model sheet: silver badge with a red B, blue moustache curls, dark red vest.
- **Avatar shots:** S03 and S04 use Kling Avatar with a per-shot prompt (`prompt:` tag). Avatar shots without a tag
  (EP001) keep `characters:`.

**v6 principles (owner, 2026-10-04: "Billy is a VILLAIN: cocky, theatrical, dramatic"; Kling won on energy, Wan test 1 was
too static).** In every Billy prompt he throws his whole body into each word: he leans far forward to taunt, pulls back hard
when shocked, spreads his wings wide for emphasis, tilts and bobs his head with the rhythm, shifts and stomps his feet, and
always shows off. The v4 rules stay: feathered wings (no hands), monocle on the LEFT eye, static camera, one speaker.
Texts that made a finished clip are frozen under a versioned name, so that clip still matches its request (`billy_shocked_v5`,
`wan_bad_billy_v1`, `talk_bad_billy_v3`).

**Additions to the owner's text** (each one fills a placeholder; nothing else was changed):
- `{line}`: Kling must hear the exact line to speak it.
- `{facing}`: S02 and S06 face left as drawn; Billy is never mirrored.
- `{acting}`: the script's direction, e.g. "skeptical".
- `{direction}`: the script's `enter-right` tag. Billy's walk-in art faces left, so he enters from the right; the owner's text said "from left".

| Template | Used by | Prompt |
|---|---|---|
| `talk_bad_billy` | default for Billy's Kling 3.0 talking lines (v6 villain energy, 2026-10-04) | Cartoon bird villain, orange beak, black top hat, monocle on left eye, {facing}, standing on rocky ground. A cocky, theatrical show-off: every line is a performance. He is {acting} and says: "{line}" Beak opens WIDE and snaps shut with each word. He throws his whole body into the line: leans far forward on the taunts, rocks back on his heels for effect, head tilting and bobbing with the rhythm of the words. Wings flare out wide for emphasis, then fold back. Feet shift and stomp on the ground, never floating. Big, bold villain personality, never casual. Wings stay as feathered bird wings at all times, no human hands, no fingers, no arms. Static camera. Consistent 2D cartoon style. No smearing. |
| `talk_bad_billy_max_energy` | **test only**: the most expressive version (Kling 3.0 Turbo or Wan 2.7) | 2D cartoon animation in exactly the same art style and colours as the input image. Cartoon bird villain, orange beak, black top hat with a "B" badge, monocle on his LEFT eye, {facing}, on the ground. MAXIMUM energy: he is {acting} and delivers his line like a scene-stealing stage villain: "{line}" His beak flies WIDE open and snaps shut on every word. Big full-body motion from the first frame to the last: he lunges far forward with his neck stretched out, then whips back upright; his head jabs, tilts and bobs to the rhythm of the words; both wings sweep out wide like a showman's cape and snap back to his sides; he stomps one foot, shifts his weight and bounces on his knees. Huge, exaggerated cartoon acting, always the same character design. The top hat and monocle stay on. Wings stay feathered yellow bird wings at all times, no human hands, no fingers, no arms. Static camera. Consistent 2D cartoon style. No smearing. |
| `talk_bad_billy_v3` | S04 take 1 (approved as-is, in the current final; kept in `shots/S04/takes/` once the retake runs) | Cartoon bird character, orange beak, black top hat, monocle on left eye, {facing}, standing on rocky ground. He is {acting} and says: "{line}" Beak opens WIDE and moves expressively with each word. Full body natural movement, body leans forward with energy, wings gesture to emphasize words. Feet firmly on ground. Dust particles at feet. Big personality. Static camera. Consistent 2D cartoon style. No smearing. |
| `billy_taunt` | S04 retake (v5) | Cartoon bird character, orange beak, black top hat, monocle on left eye, {facing}, standing on rocky ground on the right side of the frame. Character faces left toward his opponent. He is {acting}, taunting and insulting, looking directly at his opponent to the left, and says: "{line}" Beak opens WIDE and moves expressively with each word. Full body natural movement, body leans forward with energy, wings gesture to emphasize words. Wings stay as feathered bird wings at all times, no human hands, no fingers, no arms. Feet firmly on ground. Dust particles at feet. Big personality. Static camera. Consistent 2D cartoon style. No smearing. |
| `billy_terrified` | S08 retake (v5) | Cartoon bird character, orange beak, black top hat, monocle on left eye, {facing}, standing on rocky ground. Terrified expression, eyes wide with fear, backing away, absolutely horrified. Mouth drops open in horror. Not smiling, not grinning. He cries out: "{line}" Beak opens WIDE and moves with each word. Full body natural movement, body recoils backwards in fear. Wings stay as feathered bird wings at all times, no human hands, no fingers, no arms. Feet firmly on ground. Dust particles at feet. Big personality. Static camera. Consistent 2D cartoon style. No smearing. |
| `billy_shocked_v5` | EP001 S09 final (frozen; EP001 is tagged with it) | Cartoon bird character, orange beak, black top hat, monocle on left eye, {facing}. Looks up in shock and fear at something enormous. Mouth drops open wide. Body shrinks back slightly. Wings stay as feathered bird wings at all times, no human hands, no fingers, no arms. Eyes wide. Speaks with trembling voice, beak moving with words: "{line}" Feet on rocky ground. Static camera. 2D cartoon style. |
| `billy_shocked` | v6 villain energy (next use) | Cartoon bird villain, orange beak, black top hat, monocle on left eye, {facing}, on rocky ground. He looks up in total shock at something ENORMOUS towering over him and recoils dramatically: his whole body jerks back, wings fly up and out wide in panic, mouth drops open. His bravado cracks and he stammers in a trembling voice, beak moving with every word: "{line}" Head shakes in disbelief, knees wobble, feet scramble a step backwards. Over-the-top, theatrical fear. Wings stay as feathered bird wings at all times, no human hands, no fingers, no arms. Static camera. Consistent 2D cartoon style. No smearing. |
| `talk_young_saul` | S03 | Small pink cartoon worm character, huge round pale-blue eyes, white cartoon gloves, {facing}. He says: "{line}" Mouth opens wide and moves expressively as he speaks a long sentence. Body sways gently. Confident and helpful expression. Rocky ground. Static camera. 2D cartoon style. |
| `billy_walk` | S01 | Cartoon bird character, orange beak, black top hat, monocle on left eye. Walks confidently {direction} into frame with cocky strut. Each foot clearly contacts rocky ground. Body bobs with walking rhythm. Small dust puffs at each footstep. Wings swing with stride. Static camera. 2D cartoon style. |
| `billy_scroll` | S05 | Cartoon bird character, orange beak, black top hat, monocle on left eye, {facing}. Holds a scroll in wings, unrolls it dramatically. Eyes scan the scroll. Natural wing and body movement. Rocky ground, worm hole visible. Static camera. 2D cartoon style. |
| `big_guy_erupt` | S07 | Enormous cartoon worm bursts dramatically upward from hole in rocky ground. Ground cracks and splits. Dirt and rocks fly outward. Worm rises showing enormous size. Static camera. Dramatic powerful motion. 2D cartoon style. |
| `saul_brave` | EP002 S01 (v7, Kling 3.0 Turbo two-shot) | Static camera, two cartoon characters in a grassy meadow by a tree stump. On the left: a small pink cartoon worm with huge round pale-blue eyes, brown eyebrows, two buck teeth and white cartoon gloves on his tiny hands, {facing}, standing up as tall as he can. On the right, towering over him: a cartoon bird villain with a long ORANGE beak, a yellow feathered body, a tall black top hat with a crack and a round silver badge with a red letter B, wild brown and orange head feathers, curly blue moustache whiskers, a dark red vest with a gold belt buckle, red-and-black striped shorts and blue-and-red sneakers, facing left, completely silent. Only the worm speaks: "{line}" The worm is brave despite his tiny size: chin up, chest out, his body swaying with confidence, one gloved hand raised politely at the start. His mouth opens WIDE and clear on every word and closes between words. The bird stays SILENT with his beak CLOSED the whole time: he only leans slowly over the worm with a suspicious glare. The huge size difference stays dramatic. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Check the monocle position in every frame. His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. Only feathered wings that gesture and fold. Both characters keep their feet on the ground. No new characters, no text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `billy_outraged` | EP002 S02 (v8, 2026-10-05: wings folded, no wing gestures; Kling 3.0 Standard `kling3std` + `billy_hands` negative + keyframe as end frame) | A cartoon bird villain with a long ORANGE beak, a yellow feathered body, a tall black top hat with a crack and a round silver badge with a red letter B, wild brown and orange head feathers, curly blue moustache whiskers, a dark red vest with a gold belt buckle, red-and-black striped shorts and blue-and-red sneakers, {facing}, standing in a meadow of big smiling flowers. A theatrical stage villain, big but controlled. He is {acting}, outraged that anyone dares to speak to him, and shouts: "{line}" On "REALLY" his whole body jerks BACK in disbelief, eyes popping; then he leans far forward ONCE, neck stretched out, glaring down, his head jabbing on "Who", "dares", "talk" and "me"; then he settles back into his starting pose. His wings stay folded flat and tight against his sides throughout the entire clip. The wings do not spread, do not gesture, do not move away from his body. Only his HEAD and BODY move — neck stretches, head jabs, body leans. No wing movement. The orange beak flies WIDE open — wide enough to see inside — and snaps shut cleanly between words. The beak moves with the EXACT rhythm of speech, not just generally open during talking. His weight shifts from foot to foot and he stomps once. Both feet stay planted on the ground. When he shifts weight, one foot stays down. Dust or small ground disturbance when he stomps. Billy never floats or hovers. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Check the monocle position in every frame. His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. Only Billy is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `billy_outraged_v7` | EP002 S02 Turbo pilot (frozen; rejected for fists) | A cartoon bird villain with a long ORANGE beak, a yellow feathered body, a tall black top hat with a crack and a round silver badge with a red letter B, wild brown and orange head feathers, curly blue moustache whiskers, a dark red vest with a gold belt buckle, red-and-black striped shorts and blue-and-red sneakers, {facing}, standing in a meadow of big smiling flowers. A theatrical stage villain, big but controlled. He is {acting}, outraged that anyone dares to speak to him, and shouts: "{line}" On "REALLY" his whole body jerks BACK in disbelief and his wings spread wide ONCE in shock; then he leans far forward ONCE, neck stretched out, glaring down, his head jabbing on "Who", "dares", "talk" and "me"; then his wings fold back and he settles close to his starting pose. The orange beak flies WIDE open — wide enough to see inside — and snaps shut cleanly between words. The beak moves with the EXACT rhythm of speech, not just generally open during talking. His weight shifts from foot to foot. Both feet stay planted on the ground. When he shifts weight, one foot stays down. Dust or small ground disturbance when he stomps. Billy never floats or hovers. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Check the monocle position in every frame. His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. Only feathered wings that gesture and fold. Only Billy is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `saul_pitch` | EP002 S03 (v7, Kling Avatar with our audio; tag prompt:saul_pitch) | A small pink cartoon worm with huge round pale-blue eyes, brown eyebrows, two buck teeth and white cartoon gloves on his tiny hands, {facing}, in a meadow beside a wooden sign. A clever little salesman pitching a deal: confident, persuasive, selling hard. His mouth opens WIDE and clearly on every word and closes between words, in the exact rhythm of the voice. His eyes stay wide and expressive. He leans forward into the pitch, one gloved hand sweeps up high to show how huge something is, and his excitement builds through the line. Only the worm is in the frame. Static camera. No new characters, no text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `billy_menace` | EP002 S04 (v7, Kling Avatar with our audio; tag prompt:billy_menace) | A cartoon bird villain with a long ORANGE beak, a yellow feathered body, a tall black top hat with a crack and a round silver badge with a red letter B, wild brown and orange head feathers, curly blue moustache whiskers, a dark red vest with a gold belt buckle, red-and-black striped shorts and blue-and-red sneakers, {facing}, standing in a meadow of big smiling flowers. Cold, controlled menace, never shouting: a slow, suspicious nod at the start, then he leans in slowly and menacingly, his eyes narrowing to slits; he points one feathered wing tip forward for the threat, then folds it back and settles close to his starting pose. The orange beak opens clearly and deliberately on every word, wide enough to see inside on the strong words, and closes cleanly between words, in the EXACT rhythm of his slow, low speech, never just hanging open. Head moves slowly with the rhythm of the words. Both feet stay planted on the ground. When he shifts weight, one foot stays down. Dust or small ground disturbance when he stomps. Billy never floats or hovers. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Check the monocle position in every frame. His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. Only feathered wings that gesture and fold. Only Billy is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `billy_flight` | EP002 S05 (v7, Kling 3.0 Standard, start → end frame) | A cartoon bird villain with a long ORANGE beak, a yellow feathered body, a tall black top hat with a crack and a round silver badge with a red letter B, wild brown and orange head feathers, curly blue moustache whiskers, a dark red vest with a gold belt buckle, red-and-black striped shorts and blue-and-red sneakers flies from left to right across the sky past a floating tree island, carrying a small pink cartoon worm with huge round pale-blue eyes, brown eyebrows, two buck teeth and white cartoon gloves on his tiny hands on his back. Billy's feathered wings beat in a strong, steady rhythm, down and up, as he glides forward, beak pointed ahead with determination. The worm clings tight to the feathers on Billy's back with both gloved hands, eyes wide with joy; he never slips or falls off. Both lean slightly forward into the wind. The floating island stays in place in the background while they move past it. Smooth, continuous motion, no stuttering, no speed blur. The top hat stays on. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Check the monocle position in every frame. His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. Only feathered wings that gesture and fold. Static camera. No new characters, no text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `saul_riding` | EP002 S06 (v7, Turbo + re-voice) | Static camera, high in a pastel sky with rainbows and an airship. A small pink cartoon worm with huge round pale-blue eyes, brown eyebrows, two buck teeth and white cartoon gloves on his tiny hands rides on the back of a flying bird: a cartoon bird villain with a long ORANGE beak, a yellow feathered body, a tall black top hat with a crack and a round silver badge with a red letter B, wild brown and orange head feathers, curly blue moustache whiskers, a dark red vest with a gold belt buckle, red-and-black striped shorts and blue-and-red sneakers, {facing}. Only the worm speaks: "{line}" On "Oh wow!" his eyes go even WIDER with wonder, the wind pushes his cheeks back and his mouth opens in a huge joyful shout, opening WIDE on every word; his gloved hands grip the feathers tight. Pure joy. The bird keeps flapping his wings in a steady rhythm and stays SILENT with his beak CLOSED the whole time. The top hat stays on. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Check the monocle position in every frame. His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. Only feathered wings that gesture and fold. No new characters, no text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `billy_crash` | EP002 S07 (v7, Standard, start → end frame) | A cartoon bird villain with a long ORANGE beak, a yellow feathered body, a tall black top hat with a crack and a round silver badge with a red letter B, wild brown and orange head feathers, curly blue moustache whiskers, a dark red vest with a gold belt buckle, red-and-black striped shorts and blue-and-red sneakers, flying fast. He swoops down from the upper left toward the rocks, touches down and immediately starts sliding through the mud; his legs shoot out from under him, he trips on a rock and tumbles head over heels, one feathered wing clamping the top hat down onto his head. Mud and dust spray out from the skid. Real cartoon physics: weight, momentum and comic timing. He ends in a heap, beak-first against the rocks with a heavy impact, the top hat still on his head. The top hat stays on his head the whole time. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Check the monocle position in every frame. His wings are feathered yellow bird wings at all times. No human hands appear. No fingers. No arms. Only feathered wings that gesture and fold. Static camera. No new characters, no text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `action` | any action line without a `prompt:` tag (none in EP001) | {acting} Real weight and momentum: everything that moves has follow-through, nothing floats or slides. Static camera. 2D cartoon style, exactly the same art style and colours as the image. |

**Negative prompt** (Kling 3.0 Standard action shots):
> floating, hovering, sliding, feet off the ground, flickering, morphing, melting, smearing, extra limbs, extra characters, text, captions, watermark, logo, blur, distortion, 3D render, realistic, style change, monocle on the right eye, mirrored character

**Talking-shot framing:** Kling 3.0 talking shots start from Billy's full model-sheet pose that faces the same way as the scripted expression (`kling_body` in `bad_billy.yaml`). They no longer start from a pasted head-on-body close-up, which looked like a puppet in the Avatar test. The expression goes into the prompt instead.

## Wan 2.7 (owner test, 2026-10-04): not in production yet
- **Endpoint:** `fal-ai/wan/v2.7/image-to-video`, $0.10/s at 720p (model page; 1080p is $0.15/s and is the API default, so the
  tool always sends `resolution: "720p"`). Whole seconds, 2–15 s.
- **Inputs:** the shot's keyframe (`image_url`), the approved line, trimmed to −16 LUFS (`audio_url`, the *driving audio*
  for lip sync and timing), `duration` = the line rounded up, the shared negative prompt, `enable_prompt_expansion: false`.
- **Script tag:** `wan` on a talking line (header `talking_engine: wan` for all of them).
- **First test:** EP001 S02 rebuilt in `productions/test-wan27-ep001-s02/` (same keyframe and approved audio) to compare with
  the finished Kling Avatar take.

| Template | Used by | Prompt |
|---|---|---|
| `wan_characters.bad_billy` | default for Billy's Wan lines (v6 villain energy) | 2D cartoon animation in exactly the same art style, colours and line work as the input image. A cartoon bird villain with an orange beak, a black top hat with a "B" badge and a monocle on his LEFT eye, {facing}. He is {acting}, cocky and theatrical, and performs the words in the audio like a show-off: his beak opens WIDE and snaps shut in time with every word. He throws his whole body into it: leans far forward on the strong words, rocks back, head tilting and bobbing with the rhythm of the voice, wings flaring out wide for emphasis and folding back, feet shifting and stomping on the ground. Big villain energy, never standing still, never casual. His wings stay feathered yellow bird wings at all times: no hands, no fingers, no arms. Static camera. The character stays exactly on model. No new characters, no text. |
| `wan_bad_billy_v1` | Wan test 1 (frozen) | 2D cartoon animation in exactly the same art style, colours and line work as the input image. A cartoon bird with an orange beak, a black top hat with a "B" badge and a monocle on his LEFT eye, {facing}. He is {acting} and speaks the words in the audio: his beak opens and closes in time with the voice, with small natural head and body movements. His wings stay feathered yellow bird wings at all times: no hands, no fingers, no arms. Feet stay on the ground. Static camera. The character stays exactly on model. No new characters, no text. |


### Wan 2.7 test 1: EP001 S02 (approval code 35315E81, 2026-10-04)
- **Request:** `01a107df-465e-7a12-9f17-667d0cc23598`. Ledger estimate $0.50 (5 s × $0.10). The actual charge is not
  readable with this key (check fal.ai > Billing).
- **Output:** 5.0 s, 720×1280, 30 fps. Same keyframe and audio as the Kling Avatar take.
  Comparison: `productions/test-wan27-ep001-s02/compare/`.
- **Beak:** opens wide on the words, much more visible than the Avatar take. Auto sync score r=0.12 (Avatar 0.16); both
  are weak by this measure, so judge by eye.
- **On model:** hat with the B badge and crack, monocle on the LEFT eye, moustache curls, feathered wings and shoes all
  hold. Small drift: the hat's top and brim reshape slightly, and the hair is smoothed a little.
- **Motion:** calmer than the Avatar take (average change per frame 0.96 vs 1.46). It ends close to the keyframe (drift
  4.9 vs 14.4), with the feet planted.
- **Flaw:** a visible pose snap at 4.6 s (frames 138→139), as the last word ends.
- **Auto "No style drift" check:** 1.9/10 (FAIL). The same metric gives the approved Avatar take 1.3/10, so it does not
  work for talking clips yet.

## Official character descriptions (from Jason's sheets, 2026-10-05)
Use them in any template as `{identity_bad_billy}` or `{identity_young_saul}`. With the script header `elements: on`,
Kling 3.0 Standard also receives the official sheets as character reference images (see `docs/PROMPT_GUIDE.md`, Section 6).

| Key | Text |
|---|---|
| `official_identity.bad_billy` | Bad Billy: a cartoon bird villain with a yellow feathered body; wild dark-brown head feathers with orange eyebrow feathers; a tall black top hat with one lightning-bolt crack near the top that never overlaps the badge, and a round silver badge with a white rim and a red script letter B; a round monocle with a thin black frame and a thin chain on his LEFT eye only; a long orange beak with NO teeth inside when it opens; teal curly moustache whiskers with the same spiral shape on both sides; a dark red vest, a brown belt with a gold square buckle and red-and-black striped shorts; teal-and-red high-top sneakers with a white star and pink-white soles; three long yellow tail feathers. His wings act as his arms: each wing ends in five long yellow primary feathers, never human hands or fingers, never fists. |
| `official_identity.young_saul` | Young Saul: a small light-pink cartoon worm with no legs and no feet, dark plum rings near his tail, huge round pale-blue eyes with black pupils and white highlights, small brown eyebrows, two little buck teeth when he smiles, and white cartoon gloves on his tiny hands (always white). Happy, curious, playful and loyal. |

## EP003 "Rule Number One" templates (2026-10-05)
Per-shot rationale: `productions/ep003/PROMPTS.md`.

| Template | Used by | Prompt |
|---|---|---|
| `billy_hungry` | EP003 S01 (Kling 3.0 Standard + references, start = end frame) | {identity_bad_billy} {facing}, close up, half hidden against the trunk of a giant old oak tree, pink sky behind. He is theatrically hungry and sorry for himself: he slumps, his head droops low and he looks down at his own empty tummy, then his head snaps up in outrage and he says: "{line}" On "EMPTY" his eyes pop wide and his beak flies open wide (no teeth inside) and snaps shut between words, in the rhythm of the words. His body sags, then puffs up indignantly, then settles back into his starting pose. His wings stay folded flat against his sides the whole clip: they do not spread or gesture. Only his HEAD and BODY act. Both feet stay planted; when he shifts his weight one foot stays down. He never floats. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Only Billy is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `saul_pop` | EP003 S03 (Standard action: empty stump → Saul) | {identity_young_saul} A grassy meadow with a hollow tree stump and a little ladder; static camera. Saul pops straight up out of the hollow stump with a happy bounce, holding his round yellow ball in his white gloves, looks around with big curious eyes and lands in front of the stump, smiling, ending exactly in the pose of the last frame. Real cartoon weight: the pop has a quick squash and stretch. The ball stays round and yellow; his gloves stay white; he has no legs. No other characters. No new text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `saul_balltime` | EP003 S04 (Kling Avatar, our audio) | {identity_young_saul} {facing}, in a sunny meadow, holding his round yellow ball. Bursting with excitement, he shouts: "{line}" His mouth opens WIDE and clearly on every word and closes between words, in the exact rhythm of the voice; his eyes sparkle, his body bounces once with joy and he lifts the ball. Only Saul is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `billy_lunch` | EP003 S06 (Standard + references, start = end frame) | {identity_bad_billy} {facing}, close up, half hidden against the trunk of a giant old oak tree, pink sky behind. A sly, menacing villain who has just spotted his lunch on the ground below: his eyes narrow, a slow wicked smile spreads across his beak, he leans slowly forward and down toward the camera and purrs: "{line}" The beak opens slowly and clearly on each word (no teeth inside) and closes between them; one eyebrow rises. Then he settles back into his starting pose with a smug look. His wings stay folded flat against his sides the whole clip: they do not spread or gesture. Only his HEAD and BODY act. Both feet stay planted; when he shifts his weight one foot stays down. He never floats. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Only Billy is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |
| `saul_fear` | EP003 S07 (Standard action, start = end frame) | {identity_young_saul} {facing}, in a grassy meadow by a hollow tree stump, looking up toward a big tree. He slowly realises he is being watched: his huge eyes go even wider, his eyebrows shoot up, he gulps, and his whole body trembles with fear in small quick shivers, leaning back a little, then he freezes, ending exactly in the pose of the last frame. He stays silent, mouth closed in a nervous wobble. His gloves stay white; he has no legs. No other characters. No text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. |

**Negative set `saul_body`** (header `negatives: …,saul_body`): legs, feet, shoes, human hands, bare hands, coloured gloves, extra fingers, deformed ball
