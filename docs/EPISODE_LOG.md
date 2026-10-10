# Episode Production Log

## EP001 — "The Scroll and The Big Guy"
- Status: COMPLETE ✅
- Generated: October 4, 2026
- Duration: 45.8 seconds after the free trims (originally 47.9 s; 720×1280, 9:16; audio −16.4 LUFS, true peak −2.9 dBTP)
- Source: *Bad Billy the Bird*, pp. 28–31 (printed edition, top-hat Billy)
- Script: `productions/ep001-big-guy/script.md`
- Final file: `productions/ep001-big-guy/exports/ep001-big-guy_FINAL_9x16.mp4`
- Instagram: `productions/ep001-big-guy/exports/ep001-big-guy_FINAL_4x5.mp4` (720×900)
- Captions: `productions/ep001-big-guy/exports/ep001_captions.srt` (import into CapCut; nothing is burned in)
- QA: `productions/ep001-big-guy/reviews/qa.md`: **PASS**

### Cost
| Item | Amount |
|---|---|
| fal.ai, final batch (approval code 27C34623) | $3.11 |
| fal.ai, S04 tests (Avatar $0.11, Kling 3.0 Turbo $0.34) | $0.45 |
| fal.ai, retakes S04 + S08 (codes B30A4EEA, 61261DC2) | $0.67 |
| **fal.ai total (Kling 3.0 + Avatar)** | **$4.23** |
| **ElevenLabs, total used this billing period** (voice tests, all dialogue, re-voice, music, SFX) | **1,196 of 39,482 credits** |
| … of which the two retake re-voices (actual) | 60 credits |
| ElevenLabs credits left (resets 2026-11-03) | 38,286 |
| fal.ai balance remaining | ~$5.77 (calculated as $10 − $4.23; our key can't read the balance, so check fal.ai > Billing) |

The 1,196 comes from the ElevenLabs account and already includes every re-voice, so nothing is added again.

### Voices Used
| Character | Voice ID | Status |
|---|---|---|
| Bad Billy | P7F9PUE00ia0MTMWykwh | ✅ Approved |
| Young Saul | h4gMqfA5m1KtiSa1x7eg | ✅ Approved |
| Narrator | 5FWWdk2JXJXw27LbrXGx | ✅ Approved |
| Big Pea | PhCtPaVMVgQuV2ts4Ghy | ⏳ Test pending (not in EP001) |
| Snail | QjFbUJVm3vUxlxuBOery | ⏳ Test pending (not in EP001) |

### Shots
| Shot | Content | Engine | File | Cost |
|---|---|---|---|---|
| S01 | Billy walks in | Kling 3.0 Std | shots/S01/kling3.mp4 | $0.25 |
| S02 | Billy "Where is the worm?" | Kling Avatar | shots/S02/kling_avatar.mp4 | $0.28 |
| S03 | Saul "Don't sweat..." | Kling Avatar | shots/S03/kling_avatar.mp4 | $0.34 |
| S04 | Billy "Silly little worm!" (retake: on the right, facing Saul) | Kling 3.0 Turbo + re-voice | shots/S04/kling3.mp4 | $0.34 (+ $0.34 take 1 in `takes/`) |
| S05 | Billy unrolls scroll | Kling 3.0 Std | shots/S05/kling3.mp4 | $0.25 |
| S06 | Billy "Hey Big Guy!" | Kling Avatar | shots/S06/kling_avatar.mp4 | $0.56 |
| S07 | Big Guy erupts | Kling 3.0 Std | shots/S07/kling3.mp4 | $0.42 |
| S08 | Billy "Oh POOP!" (retake: terrified) | Kling 3.0 Turbo + approved line | shots/S08/kling3.mp4 | $0.34 (+ $0.34 take 1 in `takes/`) |
| S09 | Billy "This worm is..." | Kling 3.0 Turbo + re-voice | shots/S09/kling3.mp4 | $0.67 |
| S10 | End card | Local free | shots/S10/local.mp4 | $0.00 |

All shot paths are relative to `productions/ep001-big-guy/`. The Kling 3.0 talking shots play the re-voiced audio in `shots/Sxx/voice_revoiced.wav`.

### Free edits (2026-10-04, `./bbtb export`, $0)
- S01: `trim:1.5` cuts the 1.5 s of empty scene, so the shot opens as Billy pops up.
- S09: `trim:0.6` cuts the front-on hold before Billy turns; the first word starts 0.06 s into the shot.

### Retakes (owner-approved, 2026-10-04, $0.67 + 60 credits)
- **S04** (`billy_taunt`, code B30A4EEA): Billy on the right, facing left toward Saul, feathered wings (no hands). The re-voice says "Silly little worm!" exactly.
- **S08** (`billy_terrified`, code 61261DC2): terrified, eyes wide, backing away, not smiling.
  - **Audio:** the Voice Changer returned "Owwooooo H OHP!", so the word check rejected it (kept as `voice_sts_rejected.mp3`). The final plays the approved ElevenLabs "Oh POOP!", placed on Kling's word timings ("Oh" at 0.8 s, "Poop" at 2.3 s). Whisper hears "Oh poop".
- **Old takes:** both are kept in `shots/S04/takes/` and `shots/S08/takes/`.

### Known Issues for EP002
- **S01:** Billy pops up from behind the rocks instead of walking in, and auto-QA scored the motion low (1.4). Fix the prompt for the next episode.
- **Screams and short exclamations:** the Voice Changer mangles them (S08: "Ahh", then "Owwooooo H OHP"). Fixed: re-voices are word-checked, and the approved line is used instead when they fail.
- **Staging:** the backgrounds are three crops of one plate, and there is no shot of Billy and Saul together. Plan two-shots and reverse angles before EP002 is generated.
- **Auto-QA:** "consistency 0/10" and "mirrored" are false alarms on shots where the character turns. The metric compares pixels against the first frame, so it needs a better check.

### Next Episode
- Budget available: ~$5.77 fal.ai + 38,286 ElevenLabs credits
- Estimated cost per episode: ~$3.50
- Episodes remaining at current budget: ~1-2 more episodes
- Recommend: ask Jason to top up fal.ai by $10 for EP002+

---

## EP002 — "The Deal" (PLANNED, not generated)
- Status: script + plan written 2026-10-04. **Free animatic made** (`productions/ep002/preview/animatic.mp4`, 45.2 s, silent placeholder voices; no captions or subtitle track, the lines are in the `animatic.srt` sidecar only). Nothing generated or spent.
- **Backgrounds:** 6 looks across 4 locations. Five new plates were cropped from the originals into `library/backgrounds/`; review sheets are in `productions/ep002/reviews/backgrounds.jpg` and `keyframes.jpg`.
- Script: `productions/ep002/script.md`. Research, scores, feasibility: `productions/ep002/PLAN.md`.
- **Story:** book pp.19–27, the only stretch never animated in any existing video (all 12 marketing clips and EP001 were checked).
  - Young Saul stands up to Bad Billy and offers a deal ("Have you seen The Big Guy?").
  - The two fly off together.
  - Billy crash-lands with a CRASH! and a THUD!
  - It's the **prequel to EP001**: it ends where EP001 starts.
- **Format:** 8 shots, about 43 s, 4 locations: STUMP_GRASS, FLOATING_TREE, SKY_CLOUDS, BIG_WORM_HOLE, plus the end card.
- **Cast:** top-hat Billy (for EP001 continuity; the flight and crash animation sheets exist only for him), Young Saul and the Narrator. All three voices are already approved, so nothing needs cloning.
- **Estimated cost:**
  - **fal:** about $3.14 (under $4).
  - **ElevenLabs:** about 700–850 credits (dialogue about 640, re-voice 40–200), plus about $0.36 API-equivalent for SFX (unless the owner supplies the sounds).

| Shot | Content | Engine | Est. cost |
|---|---|---|---|
| S01 | Hook: tiny Saul, "Excuse me, Bad Billy…" | Kling 3.0 Turbo + re-voice (two-shot) | $0.67 |
| S02 | Billy: "REALLY?! Who dares talk to me?" | Turbo + re-voice | $0.34 |
| S03 | Saul: "Have you seen The Big Guy?…" | Kling Avatar | $0.34 |
| S04 | Billy: "Okay. But if this is a trick…" | Kling Avatar | $0.45 |
| S05 | Flight past the floating island | Kling 3.0 Std | $0.50 |
| S06 | Saul: "Oh wow! I always wanted to fly!" | Turbo + re-voice | $0.34 |
| S07 | Crash landing, Billy clamps his top hat on | Kling 3.0 Std | $0.50 |
| S08 | End card 1 (tease): Billy's eye twitches; "Did a tiny worm just outsmart the baddest bird around?" | Local | $0.00 |
| S09 | End card 2 (book): cover + CTA D "Bedtime just got WAY more fun…" + LINK IN BIO + Follow | Local | $0.00 |

- **Before the free dry-run** (all free; listed in PLAN.md):
  - cut-outs from the flying-with-Saul and landing sheets;
  - a `with:` two-shot tag and flying poses on a scene with no ground (small code changes);
  - five Kling templates.
- **Owner decisions:** `session_cap` (1 blocks a one-go batch); S04 is about 7.5 s; top-hat Billy for EP002.

## EP002 "The Deal": generated 2026-10-05 (code 83A9D140), NOT ready to publish
- **Exports:** `productions/ep002/exports/ep002_FINAL_9x16.mp4` and `ep002_FINAL_4x5.mp4` (47.8 s, −16.7 LUFS) plus
  `ep002_captions.srt`. Older `ep002_v1`–`v3` files are S02-only previews.
- **fal spend:** $4.29 by the ledger: S02 three takes $1.46, batch $2.83.
- **Shot review (by eye, every frame):**
  - **PASS:** S01, S02 (take 2: on model, low energy), S03, S05, S06, S08/S09 (local end card).
  - **S04 FAIL (Kling Avatar):** a human pointing hand from about 1.3 s to 2.5 s. The v7 `billy_menace` prompt asked him
    to "point one feathered wing tip forward", and Avatar takes no negative prompt.
  - **S07 FAIL (Kling 3.0 Standard):** Billy dissolves into fragments, hat gone, from about 3.3 s to 5.2 s mid-tumble,
    then snaps into the end-frame pose. Auto-QA passed it at 9.9/10 because it only compares the first and last frames.
- **Lessons:**
  - Never ask Billy's wings to point or gesture on engines without a negative prompt.
  - Auto clip QA must sample the middle of action clips, not just the ends.
- **Free fixes, 2026-10-05 (owner: $0.49 left on fal, no paid retakes):**
  - **S07:** the clip now ends at 3.2 s (tag `cut:3.2`). The drawn Trip-2 end frame holds for the rest of the shot,
    with a decaying impact shake on the THUD (3.3 s). The meltdown is gone.
  - **Tease card (S08):** simplified to Billy's official head art (`BILLY'S_HEAD.png`, never enlarged) over the blurred
    crash site, plus the question in outlined text. The pasted head-on-body, the dark box and the eye twitch are gone.
  - **S05 background:** left unchanged. It is the printed book's p.23 art, the floating tree island and windmill
    (checked against the PDF).
  - **Saul in S05/S06:** visible throughout. In S05 the wing covers him only partly on upstrokes, as drawn on the
    flying sheet. No freeze needed.
  - **S04:** still has the pointing hand (about 1.3–2.5 s). It needs a paid retake (~$0.28 Avatar) or a free
    cut/hold; the owner has not decided.
- **Recut, 2026-10-05 (owner's final decision, free):**
  - **Removed:** the old S05 flight (Kling, "looks boring") and the old S07 crash (Kling, meltdown). **Reason:** AI
    generation quality was not acceptable for these action shots at the current budget. Both clips are kept in
    `shots/_removed/` and were not deleted ($1.09 of the spend).
  - **Removed narration:** "Then off the two jumped…", "They flew, and they flew…" and "The bird tripped and fell with
    a CRASH! and a THUD!", along with the crash and thud sound effects.
  - **New S06 (free, local):** Billy glides in over the worm hole and touches down, connecting to EP001. It uses the
    landing-approach → landing-touchdown sheet art, a whoosh, and the already-rendered "But while touching down and
    sliding through the mud," (no new credits). It is 3.5 s long (new tag `secs:`).
  - **New tease card (S07):** "Saul said The Big Guy was real... but did the little worm just trick the baddest bird
    around?". It is shown on screen only (new tag `silent`) because a new narrator recording would cost ElevenLabs
    credits.
  - **Book card (S08):** unchanged.
  - **Shot numbers:** Saul's "Oh wow!" is now S05 (its folder was moved, and the paid clip and re-voice are reused).
  - **New length:** 40.7 s. Nothing was regenerated and nothing was spent.
  - **Known issue left:** S04's pointing hand at about 1.3–2.5 s.
- **Final structure, 2026-10-05 (owner, free):** S01–S05, then an end card made from the marketing title video
  (`Video/1. BBTB TITLE.mp4`).
  - **Title video use:** video only; its voice and music are never used, and the original is only read. It plays
    0–6.85 s (Billy flies in, then the close-up), then the last frame holds.
  - **Framing:** centred 4:5 over a blurred fill, which is exactly the 4:5 export.
  - **Sound:** our music underneath, no narration (new `card:title`).
  - **Text (white, black outline):** "What did Saul do to Bad Billy?" at 1.0 s, "Find out in the book! 📖" at 2.5 s, and
    "Bad Billy the Bird — Link in bio" (smaller) at 4.0 s.
  - **Removed:** the arrival shot, the tease card and the book-cover card (local renders moved to `shots/_removed/`).
  - **Length:** 35.2 s (end card 9.5 s, `secs:9.5`; the footage alone would give 32.5 s, under the 35–40 s target).
- **End card v2, 2026-10-05 (owner):** the title video (first 6 s, video only, then the close-up holds) now carries the
  narrator line "What did Saul do to Bad Billy? Find out in Bad Billy the Bird — link in bio!" (3.9 s; ElevenLabs
  76 credits, code 92E15EBB) over our music.
  - **On screen:** only a small "Link in bio 🐛" (new tag `show:`). No captions, no book cover.
  - **Final length:** 35.2 s, −16.7 LUFS.
  - **Known issue:** S04's pointing hand (about 1.3–2.5 s) is still in it.

## EP003 "Rule Number One": planned 2026-10-05 (pipeline v3.0), NOT generated
- **Story:** book pp.16–18 plus "Rule Number One" (p.12). It is the prequel to EP002: it ends with Saul trapped at
  the stump. 8 shots, about 36–42 s; the length is final after the voices render.
- **Quality targets (Jason's feedback):**
  - Every character shot gets the official sheets as Kling references.
  - Cut-outs have no white edges.
  - Billy at 65% energy with folded wings.
  - The keyframe is both the start and the end frame (keeps him on model).
  - No text in AI shots: the canon sign appears only in a free local shot.
  - One take per shot.
- **Cost plan:** fal minimum $1.71, maximum $3.42 (one retake each), target $2.05. ElevenLabs: 580 credits for the
  voices (code E4CF3BEB), about 100 for re-voice, and a new "tummy" sound effect.
- **Sheets:** `productions/ep003/PRE_PRODUCTION.md` and `PROMPTS.md`, regenerated with `./bbtb preprod`.

- **Generated 2026-10-05:**
  - **Runs:** code 3AA3AEC3 produced S05 only; the 4 Kling 3.0 shots were rejected by fal (HTTP 422: reference image
    aspect over 2.5; not generated). They were re-sent after the fix with code 7B78FC61 and all completed.
  - **fal spend (ledger):** $1.67 (S01 $0.50, S04 $0.25, S05 $0.11, S07 $0.38, S08 $0.42).
  - **Final:** `exports/ep003_FINAL_9x16.mp4` / `_4x5.mp4`, 36.5 s, −17.0 LUFS.
  - **Frame review:**
    - **S01:** on model; the wings hug the tummy with feather fingers (as on the official turnaround), big fling on
      "EMPTY", returns to the start pose. 0.3–0.5 s: a wing sweeps across the face with some smear.
    - **S04:** Saul pops, hops and lands; about 2 ghosted frames at 1.30–1.38 s.
    - **S05:** Avatar, ended at 1.6 s (`cut:1.6`) before a face-swelling jump.
    - **S07:** the cleanest Billy clip so far: one monocle on the LEFT eye, sharp badge, beak on the words.
    - **S08:** Saul's fearful gasp and tremble, on model.
  - **References:** the first episode with the official sheets as Kling references. The badge, monocle side, hat,
    moustache and Saul's gloves held in every Kling clip. Compare EP002 S02 retake 3: a redesigned Billy without
    references.
- **S01 final choice (owner, 2026-10-06):** the FIRST take, for its performance, with the white trapped under Billy's
  chin removed for free at render time (`productions/ep003/clip_fixes.yaml`, `studio/bbtb/clipfix.py`; the paid clip
  itself is unchanged). The two retakes are archived in `shots/S01/takes/`: the clean-chin calm take `kling3_1c84e2d0`
  and the overacted take `kling3_9d0c84d3`. EP003 fal spend $2.67. The final is not assembled yet (owner's call).
- **EP003 final assembled 2026-10-06:** 36.5 s, −17.0 LUFS, QA pass. S01 is the first take and S07 the original take,
  both with the chin white removed at render time (`clip_fixes.yaml`). White under the chin in the final's Billy shots:
  median 0–3 px per frame (S07 before the fix: median 2,566). This is the version to show Jason.
- **EP003 final re-exported 2026-10-06 (the version to show Jason):** 36.5 s, −17.0 LUFS, QA pass. S05 = the Avatar take
  (owner): the Standard retake was worse and the art-based close-up was rejected (blurry). Total fal spend $3.05.
- **EP003 Saul eyes, 2026-10-06 (free):** S05 ends at 0.56 s, before the Avatar squint at 0.60 s (frame 18 of 30 fps), and
  holds that frame. S04 frames 38–46 (blink after landing) and S08 frames 32–37, 60–70 and 104–107 (droop and blinks)
  hold the last fully open frame (`clip_fixes.yaml`). Every Saul frame in the final now shows full-size eyes. 36.5 s, QA pass.

## EP004 "WATCH OUT!" (book pp.14–15): in production, 2026-10-06
- **Concept/storyboard/script:** approved (`productions/ep004/CONCEPT.md`, `STORYBOARD_EXPLANATION.jpg`, `script.md`).
  The old v3 "Two Hungry Villains" files are in `productions/ep004/_v3_superseded/`.
- **Narrator:** 2 book lines rendered, 124 ElevenLabs credits (code 1A20F81B).
- **End card:** new animated `card:rule` ("RULE NUMBER ONE... LOOK UP! 👆" + "Tag a friend who'd be worm #5 🐛").
- **S07 take 1 REJECTED by the owner:** Billy's sneakers on the stump rim (floating). $0.42 (code 5B518372), archived in
  `shots/S07/takes/`. The performance was good; the keyframe was the bug.
- **Grounding gate built** (`ground_zones.yaml`, pre-flight `grounding`, contact shadows, FEET panel). S02 moved to
  GRASS_FLOWERS, S05 to GRASS_STUMP, S07 to GRASS_FLOWERS; prompts `_v2` change only the place description.
- **Spend so far:** $0.53 on fal ($0.11 old v3 test + $0.42 rejected S07); 124 ElevenLabs credits.
- **S02 generated** ($0.25, code CF4AA0A7): QA pass (10/10 start, 9.9/10 end); waiting for the owner's frame review.
- **Location continuity fix:** S03, the count and S07 moved to GRASS_STUMP (one spot); S07 v3 card (prompt `billy_full_v3`,
  only the place changes); worm cut-outs from Jason's art (red test pass); continuity board. Spend so far $0.78.
- **2026-10-06 owner review:** S02 APPROVED with a free cut at 1.8 s (ends on the open-mouth shout, before the 2.0 s smear
  and white eyes); bubble + alarm moved onto the shout (0.35 s). Continuity board APPROVED (one spot: GRASS_STUMP). S07 v3
  card APPROVED (generate after S05 is approved).
- **S05 generated** ($0.25, code B07A961F): QA pass; waiting for the owner's frame review (see notes: smear at ~0.38 s,
  face-plant in the dust 0.5-1.2 s, the skid pose only after 2.3 s).
- **Count fixes (mock shown, not built):** cartoon zip (stretch + speed lines + dust puff) instead of the straight line;
  numbers one at a time in the clear sky top-right; opening head turn on the official turnaround (3/4 right -> front -> 3/4 left);
  FOUR! on the official worm-in-beak face. Narration re-timed for free: `audio/L070_count_split.wav` (1 at 1.57 s, 2 at 2.44,
  3 at 3.28, 4 at 4.57). S03: the worms panic but stay in the spot (so the count has four worms to eat).
- **EP004 spend so far:** $1.04 on fal ($0.11 old v3 test, $0.42 rejected S07, $0.25 S02, $0.25 S05) + 124 ElevenLabs credits.
- **S05 take 1 REJECTED** (face-plant + smear; $0.25, archived in `shots/S05/takes/`). New S05 v2 card: only the last
  small move (official Approach 4 just above the grass -> Touchdown on the ring), negative adds face-plant/head-first/
  upside down/rolling/crash/big dust cloud/hidden in dust. Waiting for approval.
- **Count mock REJECTED** (no eating reads, paper puppet, floating head). New plan: the count = a reaction cutaway to the
  Snail (S06, Kling 3.0 Std 6 s, used to 5.5 s, $0.50); CHOMP/GULP off screen on the re-timed narration; numbers on the
  open grass in his eyeline. Card waiting for approval. Continuity board v2 rebuilt.
- **EP004 spend so far:** $1.04 on fal + 124 ElevenLabs credits (unchanged: nothing generated this round).
- **Owner approvals:** S05 v2 card, continuity board v2, S06 card with a change (no shell duck: a wide-mouth GASP on FOUR!,
  negative adds ducking/hiding in the shell). S06 v2 card rebuilt, waiting.
- **S05 v2 generated** ($0.25, code 2D6F9370): upright, no face-plant, but a smear at ~0.1-0.4 s and a big dust cloud
  0.5-1.6 s hiding his feet; waiting for the owner's frame review. Spend so far $1.29 + 124 credits.
- **S05 v2 APPROVED with trim:0.79** (f19 = first frame with sharp body + wings; hard cut from S04 into the impact puff).
  S06 v2 card APPROVED (gasp on FOUR!).
- **S07 generated** ($0.42, code 9ED5D3E7) on GRASS_STUMP at the landing spot: feathered-wing pats, burp at ~3.2 s, hat
  wobbles but stays on; badge/face soft for ~0.33 s (2.75-3.08 s) as he rears back. Waiting for the owner's frame review.
- **EP004 spend so far:** $1.71 on fal + 124 ElevenLabs credits.
- **New tag `out:<s>`:** the shot ENDS at <s> of the clip (hard cut). `cut:` held a drawn still for the rest of the shot:
  S02 now `out:1.8` (it would have frozen 1.2 s). S05 APPROVED with trim:0.79 + out:2.0 (1.21 s on screen). S07 APPROVED
  with out:4.375 (f104 last sharp badge), BURP at 3.05 s (beak opens f73), ball stops at 2.9 s (local).
- **S06 generated** ($0.50, code 6214EF13): calm 0-1.7 s; the flinches came out as eye-SQUEEZES (eyes shut 2.1-3.25 and
  3.75-3.9) with ghosting at 2.25-2.5 and 3.62; the gasp starts at 4.0 s (not 4.9) with WHITE eyes, held to 5.45 s.
  Waiting for the owner (free fixes possible: re-sync, eye tint). **Spend so far $2.21 fal + 124 credits.**
- **S05 + S07 trims APPROVED.** S06 take 1 reviewed: eye-squeezes (brown blobs), jump at 2.25-2.62 s, see-through eyes
  3.62 s unusable; rebuilt for free as PUNCH-IN CUTS from the clean parts (clip_fixes.yaml `edit:` + `tint_eyes:`), 4.33 s,
  narration re-cut (`audio/retimed/count_punch.wav`). Preview `reviews/S06_punchin_preview.mp4`, waiting for approval.
- **S04 REJECTED BY FAL'S CONTENT CHECKER** (HTTP 422, ledger 'failed', not charged; request 01a11289-4705-72b3-a4df-2dd3f4356235).
  Not retried. v2 card: the same move worded as flying. Waiting for approval. Spend still $2.21 fal + 124 credits.
- **2026-10-07: S06 punch-in APPROVED** (numbers moved to x 0.85: 0 px overlap, >= 26 px gap). **S04 v2 generated**
  ($0.25, code 82A1FF2D; passed the content checker). Cut on the action: trim:1.29 + out:2.125 = 0.835 s (f31-f50). Waiting
  for the owner (board `reviews/S04_to_S05_cut.jpg` + clip `.mp4`). Spend $2.46 fal + 124 credits. Current cut 29.7 s.
- **2026-10-07 build:** S04 starts at f39 (trim:1.625, out:2.125, 0.5 s; f34-f38 crumpled). S01 = one free shot (worms
  play at the spot 2.5 s | cut | crane up the oak over book page 12, ending on S04's framing, glint, WATCH OUT burst);
  S03 worms panic 3 s; end card 5.5 s; overlays: S02 bubble, S06 numbers, S07 ball (localanim.py). Full animatic v2
  `preview/animatic_full_v2.mp4` = 25.2 s. Missing sounds (alarm, burp, gulp: silent) - `bbtb sfx` codes shown.
- **2026-10-07: animatic v2 REJECTED by the owner** (slideshow: art-animated characters read as stills; almost no voices;
  WATCH OUT twice; S04 off model). Not exported. New shot list v5: S01a worms play (Kling), S01b Billy watching (Kling),
  S02, S03 worms panic (Kling), S04 DROPPED, S05, S06, S07 + "Mmm... delicious!", S08 Snail original line, S09 4 s card.
  Step 1 (voices) shown: `productions/ep004/VOICES_PLAN.md`. Snail clone test code EF26DED8 (~10 credits).
- Animatic v2 audio (checked): one mono AAC track at -18.1 LUFS with cached ElevenLabs music, the 2 narrator lines and
  whoosh/thud/chomp/pop; alarm, gulp and burp were missing (silent).
- **Snail clone rebuilt (denoised) + APPROVED by the owner after listening.** Script v5 (pinned ids, voice-overs).
  One code for all new voices + SFX: A734A549 (~496 credits). ElevenLabs used so far ~134 credits.
- **Voices + SFX rendered** (code A734A549): narrator p.12 4.41 s, p.13 3.56 s, Snail "WATCH OUT!" 1.06 s, Billy
  "Mmm... delicious!" 2.69 s (speech 2.15 s: does NOT fit 1.3-3.0 s; set to 0.85 s pending the owner), SFX giggles 2.0,
  aaah 1.0, alarm 1.48, gulp 1.0, burp 1.0 s. Worms = one `worms_group` composite of Jason's four (per-figure grounding).
  Cards: S01a $0.42, S01b $0.50 (1.5x push-in), S03 $0.25, S08 Avatar $0.22 - waiting. Script v5 = 33.6 s.
- **Owner card review (2026-10-07):** Billy's line option A (0.85 s). Cards revised: S01a ball in both keyframes, 2 short
  tosses; S01b head-and-chest (official look-down head on the 3/4-right body, neck join fixed, red test PASS), 1.55x push-in;
  S03 look-up + gloves to cheeks, no jumping (+ bumping/touching/overlapping/jumping), starts on S01a's end frame, ball
  drops; S08 prompt without eye actions. Order after approval: S08, S01b, S01a, S03.
- **S08 generated** (Avatar, $0.22, code 6422E7AF): on model, eyes pale green, head out of the shell, no smear; but the
  motion is very small (lips part slightly, almost no head shake; auto-check 'beak moves' FAIL r=0.01). Waiting for the
  owner. S01b prompt v3 (smile + lean) written, frames/refs/negative unchanged. Spend $2.69 fal.
- **Owner 2026-10-07: "don't worry about budget, make the best video with fewer retakes."** EP004 caps raised to $6 (budget, spend_cap, session_cap); shot_cap $0.70 kept. Per-shot approval rule unchanged.
- **S01b generated** ($0.50, code BFF93DF8; QA 10/10 start and end): on model, no teeth, no smear except a soft wing at
  2.79 s. But Kling performed more than asked: still and looking down 0-1.25 s; one wing to the hip 1.3-2.8 s; villain
  wing-rub 2.9-3.2 s; turns TO CAMERA with an open-beak grin 3.25-4.6 s (prompt said beak closed, never at camera);
  back to the start pose 4.9-6.0 s. Waiting for the owner. EP004 spend $3.19.
- **S01b take 1 REJECTED by the owner** (style collapse from ~1.5 s, turned to camera at ~3.25 s, monocle; $0.50, archived
  in `shots/S01b/takes/`). v4 card: no wing/head movement, gaze down, stricter negative (`billy_watch_still`). Waiting.
- **S01b v5 card** (owner 2026-10-07): official `billy_tophat_sideright` as ONE piece for start and end (no composite),
  head-and-chest 1.55x at pos 0.22/0.31/0.72 (full beak in frame); prompt `billy_watch_v5`; @Element1 frontal = the same
  side-right art (was the look-down composite); refs and negative unchanged. Waiting for approval.
- **S01b v6 card** (owner 2026-10-07): official `billy_tophat_34right`, single piece, unmirrored (the mirrored-34left idea
  was dropped: reversed badge B, monocle on the wrong eye); 1.55x at pos 0.42/0.30/0.66; prompt `billy_watch_v6`;
  @Element1 frontal = 34right; negative unchanged. Waiting for approval.
- S01b v6: owner removed 'facing forward' and 'facing camera' from the negative (the 34right keyframe faces near-forward). Free check: code 3A3CEB67, matches the card; waiting for the owner's approve command.
- **S01b v6 generated** ($0.50, code 3A3CEB67; QA start 10/10, end 9.9/10). Review (full-size eye crops): monocle stays single on the
  LEFT eye; but eyes fully CLOSED 0.25-3.75 s (reads asleep), wings fold across the chest 2.0-3.75 s, beak opens a crack
  (red) 0.12-0.5 and 2.6-3.0 s; on model only 3.9-6.0 s, nearly still from 4.75 s. Not recorded; waiting for the owner.
  EP004 spend $3.70.
- **S01b v6 REJECTED** (owner; archived). **S01b v7 card: Kling AI Avatar** on the official 34right keyframe (1.55x),
  driven by 3.80 s silence + his original 'Arrrr' (the narrator is NOT fed to Avatar: it would lip-sync Billy to the
  narration); growl lands at 3.95 s. New tool mode: ACTION tag `avatar` (driver = on-screen character's timed line).
  Billed 6 s (whole seconds) = $0.34. Waiting for approval.
- S01b v7 free check: code AD15E958, request matches the card (Avatar, 5.15 s audio billed 6 s, $0.34).
- **S01b v7 generated** (Avatar, $0.34, code AD15E958). Clip 7.2 s (Avatar padded 2 s past the 5.15 s audio; the shot uses
  0-5.4 s). On model and very still (no wing/head turn, single monocle, badge correct). Eyes: half-closed 0-2.2 s, pop
  WIDE 2.3-3.6 s, narrow menacingly 3.9-4.9 s (on the growl), wide again ~5.2 s. Beak stays CLOSED on the growl.
  Waiting for the owner. EP004 spend $4.03.
- S01a v3 (owner 2026-10-07): 'sway and wiggle' instead of 'bounce'; 'monocle on the right eye' dropped for this shot only (new drop-only set worms_keep_monocle). Free check code 56ADCC7D, matches the card. S03 untouched (same issue applies there: flagged).
- **S01a generated** ($0.42, code 56ADCC7D; QA 10/9.9). Good: grounded, all 4 present and in place, tosses + giggling,
  hats/bow/cap on. Flaws: a SECOND blue ball appears (two balls 0.5-1.0 s and ~2.0 s, the bow worm holds one); smear/ghosting
  0.4 s, 0.9-1.1 s, 1.6-1.9 s; the tuft worm's gloves ghost on the catches; the top-hat worm's monocle goes missing ~2.0 s.
  Clean 2.4-4.4 s. Waiting for the owner. EP004 spend $4.45.
- **S01a take 1 REJECTED** (legs/feet; archived). v4 card: no throwing, one bounce in its own gloves at 2.0 s, gen 4 s ($0.34), slowed 0.82x under the narration (free, clip_fixes); negative adds knees, standing, walking, limbs, human body parts, arms, elbows. Waiting.
- S01a v4: owner removed 'arms, elbows, limbs' from the negative. Free check passed; code in the session.
- **S01a v4 generated** ($0.34, code F3D4B746). No new legs/feet (lower bodies = Jason's curled tails, as in the keyframe); one ball; all 4 in place; gentle; glove/hand ghosting 1.75-3.1 s; low motion (1.6). Waiting for the owner. EP004 spend $4.79.
- **S01a v4 REJECTED** (blank faces; knees/crouch read; archived). v5 card: laughing open mouths + bright eyes; negative adds closed mouths, neutral expression, blank face, serious expression. Waiting.
- **S01a v5 generated** ($0.34, code BC3ECD0E; QA 10/10 both ends). Big open-mouthed laughter + happy closed-eye smiles from ~0.4 to 3.6 s; one ball (the tuft worm lifts it once); all 4 in place; hats/bow/cap/monocle on. Faint glove trail under the tuft worm ~2.9-3.3 s. Lower bodies = Jason's curled tails (unchanged). Waiting. EP004 spend $5.13.
- **S01a v5 APPROVED** (as-is). S03 v3 card: open-mouthed panic, monocle term dropped, negative adds closed mouths / neutral expression / blank face. Waiting.
- S03 v3: owner added the no-legs terms (knees, standing, walking, human body parts). Free check passed; code in the session.
- **S03 generated** ($0.25, code 4899D62B; QA 10/10 both ends). Open-mouthed screams 0.5-2.5 s, one ball (drops by 0.12 s, stays on the grass), all 4 in place, no new legs. Smear: bow + top-hat worms ghost with closed eyes 0.33-0.5 s; tuft worm blinks ~0.12-0.38 and ~2.0 s; small dip ~2.1 s. Waiting. EP004 spend $5.38.
- **EP004 animatic v5 built** (preview/animatic_v5.mp4, 32.96 s, -16.1 LUFS, mono audio: narration p.12/p.13/p.14/count, Snail WATCH OUT + closing line, Billy growl + 'Mmm... delicious!', SFX, ducked music). All 8 paid shots approved. Waiting for the owner's review; NOT exported.
- **EP004 FINAL exported 2026-10-07** (owner approved animatic v5): `exports/ep004_FINAL_9x16.mp4` (32.96 s, 720x1280, 7.4 MB,
  -16.1 LUFS, true peak -2.7 dBTP) + `ep004_FINAL_4x5.mp4` (720x900, 6.5 MB) + `ep004_captions.srt`. Video identical to the
  approved animatic. QA PASS; audit 99 originals unchanged; 133 tests pass. Spend: $5.38 fal + ~210 ElevenLabs credits.
- **Owner 2026-10-07 after the final:** narrator too quiet under the giggles in S01a. Free rebalance via new SFX tag 'vol' (giggles 0.1, aaah 0.05, alarm 0.06, gulp 0.35); preview preview/animatic_v6_balance.mp4. End-card CTA voiced (removed 'silent'): narrator line render code 06859FDB (~65 credits), waiting for approval; then re-export.
- **EP004 S02 bubble moved + finals re-exported 2026-10-07 (owner: the bubble covered the Snail's eyes).** Free composite
  fix on the approved S02 take, no regeneration: `bubble:WATCH OUT!!!!@0.35@x0.24/y0.24/s0.85/tail0.45/0.295` (new
  `@x/y/s/tail` keys in `localanim.bubble`; ellipse and tail drawn as one outlined shape). The bubble sits left of his
  head, clear of the eyes and hat on every frame 0.35-1.8 s, and inside the 4:5 safe area (a first try above his head
  was cut off in the 4:5 crop). Includes the SFX rebalance. S09 kept `silent` (the CTA voice still needs code
  06859FDB). `exports/ep004_FINAL_9x16.mp4` (32.96 s, 7.8 MB) + `ep004_FINAL_4x5.mp4` (6.8 MB), -17.3 LUFS, QA PASS,
  99 originals unchanged. Previous finals kept in `exports/_previous_2026-10-07/`. Check sheet:
  `reviews/S02_bubble_final_check.jpg`.
- **EP004 end-card CTA voiced + finals re-exported 2026-10-07 (owner approved code 06859FDB).** `voices render` bought
  the narrator line "Rule number one: look up! Tag a friend who'd be worm number five." (65 characters, one request;
  `audio/lines/L073_narrator.wav`, 3.16 s); S09 `silent` removed. The line starts 0.22 s into the 4 s card and ends at
  3.4 s; the card text reveals within ~0.3 s of the words. CTA -17.4 LUFS vs the Snail's line -17.9 (level).
  `exports/ep004_FINAL_9x16.mp4` (33.17 s, 7.9 MB) + `ep004_FINAL_4x5.mp4` (6.9 MB), -17.2 LUFS, peak -2.3 dBFS, QA PASS,
  99 originals unchanged. Includes the S02 bubble move and the SFX rebalance.

## EP001 fix-ups from Jason's batch-1 notes (2026-10-08 to 2026-10-10)
- **Finals re-exported 2026-10-10** (owner approved the old/new sheet `reviews/EP001_old_vs_new.jpg`):
  `exports/ep001-big-guy_FINAL_9x16.mp4` + `_FINAL_4x5.mp4`, 45.79 s, -16.4 LUFS (unchanged length and loudness),
  captions byte-identical. Old finals, captions and animatic in `exports/_previous_2026-10-10/`. No regeneration, $0.
- **Free render-time fixes** (`clip_fixes.yaml`, each shot approved on its own before/after sheet):
  - S01, S02, S05, S06: `trapped_white` (chin white inside the moustache curl) -> 0 px. S05 `keep_collar` +
    `keep_scroll`, S06 `keep_collar` (new opt-in guards so the shirt collar and scroll paper are never filled).
  - S03 (Saul): new `under_white` rule: the white strip under his body, 212 -> 25 px median (faint dashes at 2x).
  - Not fixed: S04 (a fix marked his grey shirt), S08 (the "white" was his sneaker toe-cap), the white between the
    feathers of his right wing in S02 (`feather_white` damaged wing-vest and beak highlights; removed).
- Avatar clips now get clip fixes too (pipeline change). Tests 146 pass; 99 originals unchanged.
- Not done (owner: confirm with Jason first): note 5C/5D, cutting "worm" from S02/S06 narration (Avatar lip sync).
- **EP001 delivery copy without music (Jason, 2026-10-10):** `exports/ep001-big-guy_FINAL_9x16_nomusic.mp4` (15.7 MB) +
  `ep001-big-guy_FINAL_4x5_nomusic.mp4` (14.3 MB), 45.79 s, -16.3 LUFS: voices + SFX only, music bed removed (new
  `./bbtb export --no-music`; header `music: off` also works). The finals with music are unchanged (checksums).
  From now on every export has two versions: with music for our review, without music for delivery to Jason.
