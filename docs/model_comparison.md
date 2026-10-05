# Video model comparison scorecard

**Target:** a model + prompt combination that scores **8+/10 overall** on Billy's talking shots.

**Benchmark:** EP001 S02, Billy saying "Well, where is the worm? Is he scared to appear?!".
- Every new test uses the same keyframe (`productions/ep001-big-guy/keyframes/S02_first.jpg`).
- It also uses the same approved ElevenLabs line (4.74 s, −16 LUFS:
  `productions/test-wan27-ep001-s02/shots/S01/wan_voice.wav`).
- Only the model and the prompt change.
- The Kling 3.0 Turbo row is a different shot (EP001 S04), included as the energy reference.

**Scores** are 1–10, given by the owner after watching with sound, side by side. **Overall** is the average of the five
scores.
- **Body movement:** the whole body acts (leans, wings, feet), not just the head.
- **Beak visible:** the beak clearly opens and closes on the words.
- **On model:** hat, B badge, crack, monocle on the LEFT eye, moustache curls, feathered wings (no hands), shoes.
- **Energy feel:** a cocky, theatrical villain, not a polite talker.
- **Consistency:** no morphing, drift, snaps or style change from the first frame to the last.

The tool's automatic "No style drift" number is **not** used. It rated the approved Kling Avatar take 1.3/10, so it
treats normal talking motion as drift.

| Test | Model | Prompt version | Body movement | Beak visible | On model | Energy feel | Consistency | Overall | Notes |
|---|---|---|---|---|---|---|---|---|---|
| EP001 S02 | Kling Avatar v2 | v1 original (`characters.bad_billy`) | 6/10 | 3/10 | 8/10 | 4/10 | 7/10 | **5.6/10** | **Good:** synced to our voice; head and shoulder sway; on model. **Bad:** beak barely opens; low energy. Cost $0.28 (code 27C34623) |
| EP001 S04 | Kling 3.0 Turbo | v3 original (later `billy_taunt` v5 retake) | 8/10 | 8/10 | 6/10 | 7/10 | 5/10 | **6.8/10** | **Good:** best body energy and beak so far. **Bad:** Kling speaks its own voice (re-voiced by ElevenLabs Voice Changer, which garbles screams); wings can turn into hands without the wing rule; more drift. $0.34 per 3 s |
| EP001 S02 | Wan 2.7 | v1 original (`wan_bad_billy_v1`) | 4/10 | 7/10 | 8/10 | 3/10 | 8/10 | **6.0/10** | **Good:** our voice drives the beak, which opens wide; very stable, ends near the keyframe. **Bad:** "Billy just stands and talks"; pose snap at 4.6 s. $0.50 est. (code 35315E81) |
| EP001 S02 | Wan 2.7 | MAX ENERGY (`talk_bad_billy_max_energy`) | 9/10 | 4/10 | 5/10 | 8/10 | 3/10 | **5.8/10** | **Good:** huge performance (wings flung wide from 1.0 s, lunges, two foot stomps); monocle stays on the LEFT eye. **Bad:** beak stuck WIDE open from 1.0 to 4.5 s, a frozen scream with no sync to the voice (r=0.02); **hard cut back to the start pose at 4.6 s**; B badge garbles (2.0/3.5/4.5 s); hair turns into long locks; wing tips splay like hands; smear at 2.0 s; pose pop at 3.2 s. $0.50 est. (code E89AC0B2) |
| EP001 S02 | PixVerse v6 | MAX ENERGY (to adapt) | ? | ? | ? | ? | ? | ? | Not wired up yet. About $0.43 (5 s × $0.045 silent + 5 s × $0.04 lipsync pass with our voice); lipsync is described as "realistic", cartoon faces untested |
| EP001 S02 | MiniMax H3 Max | MAX ENERGY (owner's version) | ? | ? | ? | ? | ? | ? | Free manual test: `docs/MINIMAX_TEST_INSTRUCTIONS.md`. Save the clip to `productions/test-h3max-ep001-s02/H3MAX_free_1.mp4` |

**EP002 S02 ("REALLY?! Who dares talk to me?", 4 s; Kling speaks the line, then it's re-voiced by ElevenLabs with a 100% word match in all three takes)**

| Take | Model | Prompt / setup | Body | Beak | On model | Energy | Consistency | Overall | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 (`takes/kling3_bb7a5dd5`) | Kling 3.0 Turbo | v7, 65% energy | 9 | 9 | 4 | 9 | 4 | **7.0** | Best beak sync yet (r=0.52), badge and monocle clean. **FAIL: wings became fists with fingers from 0.6 s.** $0.45 (C7AADBAB) |
| 2 (`takes/kling3_c7346b36`) | Kling 3.0 Standard + speech | v8 wings folded, `billy_hands` negative, **keyframe as end frame** | 4 | 4 | 9 | 4 | 9 | **6.0** | **No hands in all 97 frames**, on model, returns to the start pose. Low energy: one jerk-back on "REALLY", the beak barely moves after. $0.50 (4B88755F) |
| 3 (current `kling3.mp4`) | Kling 3.0 Standard + speech | as take 2, **no end frame** | 9 | 7 | **2** | 8 | **1** | **5.4** | **FAIL: Billy is redesigned from 0.4 s** (new style, no head feathers, long neck, shirt collar, block-letter B); camera pans to a dirt path from 2.4 s and he walks off. No fingers. $0.50 (44620674) |

**Lessons from S02:**
- **Hands:** the hand-block negative plus "wings folded" fixes them, but needs Kling 3.0 Standard (Turbo can't take a negative prompt).
- **The end frame is what keeps Billy on model.** Without it, Standard drifts within half a second.
- **The cost of the end frame:** a 4 s "go and come back" leaves little room for acting.

**EP003 (pipeline v3.0: Kling 3.0 Standard + official-sheet references + start = end frame, 65% energy, wings folded)**

| Shot | Body | Beak | On model | Energy | Consistency | Overall | Notes |
|---|---|---|---|---|---|---|---|
| S01 Billy "My tummy... EMPTY again!" | 8 | 8 | 8 | 8 | 7 | **7.8** | Feather-finger wings (on model per the turnaround), big fling; smear 0.3–0.5 s |
| S07 Billy "Lunch... is served!" | 5 | 8 | 10 | 6 | 10 | **7.8** | Cleanest Billy yet: single LEFT-eye monocle, sharp badge, sync with the words |
| S04 Saul pops from the stump | 8 | – | 8 | 8 | 7 | **7.8** | ~2 ghosted frames mid-leap |
| S08 Saul trembles | 6 | 7 | 9 | 7 | 9 | **7.6** | Fearful gasp, on model |

**Verdict:** the references plus the end frame are the best combination tested so far, at about 7.8 against 5.4–7.0
before. The remaining flaws are short motion smears during fast moves, not character redesigns.

**Where we stand (2026-10-04, after Wan test 2):** nothing reaches 8 yet.
- **Did MAX ENERGY help? Partially.** Body movement went 4 → 9 and energy 3 → 8: the prompt clearly works. But
  consistency fell 8 → 3, on-model 8 → 5 and beak sync 7 → 4, so the overall dropped from 6.0 to 5.8. Wan gives energy
  OR stability, not both.
- **Is Wan 2.7 competitive with Kling 3.0 Turbo? Not yet** (5.8 vs 6.8). Both Wan clips also cut back to the start
  pose at 4.6 s. That's a model behaviour, not a prompt one; with a big pose it becomes a hard visual cut.
- **Below the 6.5 switch threshold,** so Wan is dropped for Billy's talking shots.
- **Recommended next step:** keep Kling 3.0 Turbo for Billy's energetic lines, now with the v6 villain prompts (never
  tested yet), and use EP002 S02 (3 s, $0.34) as the pilot shot. Run the free MiniMax H3 Max sandbox test in parallel.
- **Auto-QA caveat:** on test 2 it flagged "looks MIRRORED". Every frame checked by eye has the monocle on the correct
  eye: the check compares against the start pose and fails when the pose changes this much.

**Clips to compare:** `productions/test-wan27-ep001-s02-v2/compare/THREE_WAY_comparison.mp4` (Kling Avatar | Wan #1 | Wan #2,
same audio). Older pair: `productions/test-wan27-ep001-s02/compare/`.
