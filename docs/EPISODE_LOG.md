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
