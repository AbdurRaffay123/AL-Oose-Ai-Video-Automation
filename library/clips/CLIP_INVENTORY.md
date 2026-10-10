# Clip inventory

**38 generated clips** ($15.04 of fal spend, ledger estimates) across EP001–EP004 and the Wan tests. Every
clip has a 0.5 s contact sheet in `library/clips/sheets/<ID>.jpg`. The machine-readable library is `library/clips/clips.yaml`.

**Reusing a clip costs $0; a new one costs $0.30–0.76.** In a script, `reuse:<ID>` plays a clip (see README).

**Reusable rating**
- **A:** reuse freely. **12 clips:** EP001_S01, EP001_S05, EP001_S07, EP001_S08, EP001_S09, EP002_removed-S05_flight_kling, EP003_S04, EP003_S08, EP004_S01a, EP004_S01b, EP004_S03, EP004_S07.
- **B:** only with its own line, or in its own context (talking clips: the beak or mouth moves).
- **C:** has a known flaw (see the notes).
- **no:** a rejected take or a test.

**Before reusing, check:**
- **"Chin white":** Billy clips made before the red test (2026-10-06). They need a free `trapped_white` clip fix tuned to
  their framing; `bbtb preprod` blocks them until it's set.
- **Saul blinks:** use the listed `hold_frames`.
- **Usable windows:** clips with `best: a-b` in clips.yaml are only clean inside that range (`reuse:` enforces it).

| Clip | Duration | Characters | Shows | Talking | Reusable | Notes |
|---|---|---|---|---|---|---|
| `EP001_S01` | 3.0s | Billy | Empty rocks 0–1.5 s, then Billy walks in from the right and stops by the worm hole | no | **A** | Great establishing/arrival shot at the rocks. Chin white (needs clip fix). |
| `EP001_S02` | 4.8s | Billy | Billy at the rocks, suspicious, says 'Well, where is the worm?…' (head sway) | Billy (canon p28) | **B** | Talking: reuse only with its own line. Chin white. |
| `EP001_S03` | 5.1s | Saul | Saul holds the scroll and talks, gloved hand gestures | Saul (adapted p28) | **B** | Talking: reuse only with its own line. On model, big eyes. |
| `EP001_S04` | 3.0s | Billy | Billy taunts 'Silly little worm!', leans, wing gestures, dust at his feet | Billy (canon p29) | **B** | Talking. Chin white. |
| `EP001_S04_take-05fe599f` | 3.0s | Billy | First take of the taunt (facing the wrong way) | Billy | **no** | Rejected take. |
| `EP001_S05` | 3.0s | Billy | Billy picks up the scroll and unrolls it, reading | no | **A** | Silent action; good for any 'reads the scroll' beat. Chin white. |
| `EP001_S06` | 9.9s | Billy | Billy reads the scroll aloud, 'Hey Big Guy!…' (9.9 s) | Billy (canon p29) | **B** | Talking, long. Chin white. |
| `EP001_S07` | 5.0s | Big Guy | Ground shakes (0–2 s), hole opens, the Big Guy bursts up and roars with arms up (2.5–5 s) | no | **A** | Best hook clip we own: huge, funny, on model. 2.5–5.0 s is the burst. |
| `EP001_S08` | 3.0s | Billy | Billy terrified, 'Oh POOP!', jumps back with a dust puff | Billy (canon p31) | **A** | Short, funny, high energy; reuse WITH its line. Chin white. |
| `EP001_S08_take-938a67ae` | 3.0s | Billy | First 'Oh POOP!' take (smiling, not scared) | Billy | **no** | Rejected take. |
| `EP001_S09` | 6.0s | Billy | Billy shocked, 'This worm is a worm of super-duper size!…', backs away | Billy (adapted p31) | **A** | Reuse WITH its line. Chin white. |
| `EP002_S01` | 6.0s | Saul + Billy | Saul with his ball faces looming Billy, 'Excuse me, Bad Billy…' | Saul (canon p20) | **C** | Saul's eyes droop ~5 s (owner flagged). Avoid. |
| `EP002_S02` | 4.0s | Billy | Billy 'REALLY?!', jerk back then settle (low energy) | Billy | **B** | Talking; on model, no hands. Chin white. |
| `EP002_S02_take-834ca51e` | 4.0s | Billy | Redesigned Billy walks off on a dirt path | Billy | **no** | Rejected (off model). |
| `EP002_S02_take-bb7a5dd5` | 4.0s | Billy | Big outraged performance but wings become fists | Billy | **no** | Rejected (hands). |
| `EP002_S03` | 7.2s | Saul | Saul pitches The Big Guy, gestures with gloves (7.2 s) | Saul (adapted p21) | **B** | Talking; eyes OK. |
| `EP002_S04` | 4.8s | Billy | Billy 'Okay. But if this is a trick…' with a POINTING HAND | Billy | **no** | Human hand 1.3–2.5 s. Avoid. |
| `EP002_S05` | 4.0s | Saul + Billy | Saul riding on Billy's back in the pastel sky, 'Oh wow!' | Saul (adapted p23) | **B** | Talking; two short laughing squints. |
| `EP002_removed-S05_flight_kling` | 7.0s | Billy + Saul | Billy flies past the floating tree island with Saul on his back, steady flapping (7 s) | no | **A** | Silent flight; owner called it 'boring' as a 7 s shot, fine as a 2–3 s cutaway. |
| `EP002_removed-S07_crash_kling` | 6.0s | Billy | Billy swoops in and skids (0–3.2 s), then MELTS (3.3–5.2 s) | no | **B** | Use 0–3.2 s ONLY (swoop + skid). |
| `EP003_S01` | 4.0s | Billy | Billy at the oak: swoon, hugs tummy, wing fling 'My tummy… EMPTY again!' | Billy (production) | **B** | Talking; chin white removed by EP003 clip_fixes. |
| `EP003_S01_take-1c84e2d0` | 4.0s | Billy | Calm version of the tummy line, CLEAN chin | Billy | **B** | Talking; clean keyframe. Less energy. |
| `EP003_S01_take-9d0c84d3` | 4.0s | Billy | Over-the-top version of the tummy line | Billy | **C** | Owner: over-reaction. Clean chin. |
| `EP003_S04` | 3.0s | Saul | Empty meadow, Saul pops out of the stump with his ball and lands | no | **A** | Silent action; blink at 1.58–1.92 s (hold frames 38–46). |
| `EP003_S05` | 2.1s | Saul | Saul with ball, 'Ball time!' (Avatar) | Saul | **C** | Squint from 0.60 s; only 0–0.56 s usable. |
| `EP003_S05_take-05920c08` | 3.0s | Saul | Saul 'Ball time!' (Standard) | Saul | **no** | Eyes droop 37% of frames. |
| `EP003_S07` | 3.0s | Billy | Billy at the oak, sly 'Lunch… is served!' | Billy (production) | **B** | Talking; chin white removed by EP003 clip_fixes. |
| `EP003_S08` | 5.0s | Saul | Saul looks up, eyes widen, gasps and trembles (silent, 5 s) | no | **A** | Silent fear reaction; hold frames 32–37, 60–70, 104–107 (blinks). |
| `WANTEST1_S01` | 5.0s | Billy | Wan 2.7 test: Billy talks, very static | Billy | **no** | Test only. |
| `WANTEST2_S01` | 5.0s | Billy | Wan 2.7 MAX ENERGY test: off model | Billy | **no** | Test only. |
| `EP004_S01a` | 4.0s | Worms (4) | The four naughty worms play ball at the stump, open-mouthed laughter, one ball | no | **A** | Silent; faint glove trail 2.9–3.3 s. Pose worms_group_ball, GRASS_STUMP. |
| `EP004_S01b` | 7.2s | Billy | Billy head-and-chest on the treehouse porch, still, looking down; eyes narrow on his growl | no | **A** | Avatar, beak closed; use 0–5.4 s. Pose 34right 1.55x, BG_OAK_TREEHOUSE. Clean chin. |
| `EP004_S02` | 3.0s | Snail | The Snail looks up, eyes snap wide, silent open-mouth shout | no | **B** | Use 0–1.8 s only (white eyes + smear after 2.0 s). GRASS_FLOWERS. |
| `EP004_S03` | 3.0s | Worms (4) | The worms panic in place, the ball drops | no | **A** | Silent; hold frames 8–12 over the ghosting. GRASS_STUMP. |
| `EP004_S05` | 3.0s | Billy | Billy's touchdown and short skid (last move of a landing) | no | **B** | Use 0.79–2.0 s only. Pose landing_approach4 > touchdown, GRASS_STUMP. Clean chin. |
| `EP004_S06` | 6.0s | Snail | The Snail watches off screen, flinches, gasps | no | **C** | Eye-squeezes, a jump and white eyes; clean only 0–2.05 s and 4.0–5.46 s (tinted). GRASS_FLOWERS. |
| `EP004_S07` | 5.0s | Billy | Billy full and smug at the stump, pats tummy, big burp | no | **A** | Silent (lines were voice-overs); end by 4.375 s. Pose 34left, GRASS_STUMP. Clean chin. |
| `EP004_S08` | 3.2s | Snail | The Snail: 'Ah, these birds are big trouble makers, mun.' | Snail (his original) | **B** | Talking: reuse only with its own line; lips barely move. GRASS_FLOWERS. |
