# Handoff for an advisor chat (2026-10-10, after the EP001 fix-ups and the O3 model test)

## 1. Project
- **What:** AL-Oose Studio turns a script into finished short vertical videos (9:16, about 30–40 s) of *Bad Billy the
  Bird*, a children's picture book by **Jason Metcalfe (AL-Oose)**. Jason is the client; the owner (Abdur Raffay)
  runs production.
- **Stack:** a local Python CLI (`./bbtb`).
  - Video: **Kling 3.0 Standard** (primary: image-to-video, references, negative field, start and end frames) and
    Kling AI Avatar (mouth driven by audio), both via fal.ai. Kling O3 is wired in but on hold (section 3).
  - Voices and sound effects: ElevenLabs.
  - Edit, overlays, audio mix and free clip fixes: ffmpeg and Python, locally.
- **Art:** only Jason's official sheets and book art, as cut-outs. Never redrawn.
- **Budget:** quality first, cost secondary. Every paid call needs the owner's approval code, one shot at a time.
- **Episodes:** EP001–EP004 are done. **EP001's white artefacts are fixed** (section 2). Fix-ups for EP002, EP003
  and EP004 are pending the owner's feedback. **EP005 "Big Pea DOOF" (pp.6–9) is not started.**

## 2. EP001 fix-ups (Jason's "BB BATCH 1. FIX UP'S.pdf"): DONE 2026-10-10
- **Finals re-exported:** `productions/ep001-big-guy/exports/ep001-big-guy_FINAL_9x16.mp4` + `_FINAL_4x5.mp4`
  (45.79 s, -16.4 LUFS, same length and loudness as before; captions byte-identical). Old files in
  `exports/_previous_2026-10-10/`. Old/new sheet: `reviews/EP001_old_vs_new.jpg`. No regeneration, $0.
- **Free render-time fixes** (`productions/ep001-big-guy/clip_fixes.yaml`, each shot approved on its own sheet):

| Shot | Fix | Result |
|---|---|---|
| S01 walk-in | `trapped_white` (chin) | 320 → 0 px in the used part |
| S02 "Where is the worm?" (Avatar) | `trapped_white` | 803 → 0 px |
| S03 Saul + scroll (Avatar) | new `under_white` (strip under his body) | 212 → 25 px median; faint dashes at 2x |
| S05 unrolls scroll | `trapped_white` + `keep_collar` + `keep_scroll` | 2,023 → 0 px; collar and scroll paper kept |
| S06 "Hey Big Guy!" (Avatar) | `trapped_white` + `keep_collar` | 2,589 → 0 px; collar kept |
| S04, S08, S09 | none | S04: a fix marked his shirt; S08: the "white" was his sneaker; S09: negligible |

- **Not fixed:** white between the feathers of Billy's right wing in S02 (`feather_white` damaged wing-vest and beak
  highlights and was removed everywhere).
- **Not done, waiting on Jason:** notes 5C/5D (cut "worm" from the S02/S06 narration, multiple-choice ending). The
  word is inside Avatar lip-sync, so it means regenerating S02 + S06 (about $0.84).
- **Code added:** clip fixes now run on Avatar clips; opt-in `keep_collar`, `keep_scroll`, `under_white`. Tests:
  **147 pass**; 99 originals unchanged.

## 3. Model test: Kling O3 vs Kling 3.0 Standard (2026-10-10, `productions/test-o3-ep001`)
- Same keyframe (`billy_tophat_34left`, 1.55x on BIG_WORM_HOLE), prompt and references; 4 s each; $0.67 in total.
  Sheet: `reviews/O3_vs_control.jpg`.
- **O3:** more expressive eyes; the reference video (EP004 S07, 0–3 s) helps the acting. But the beak flickered open
  at 3.0–3.4 s on a "beak closed" shot, there is no negative field, and two submits were refused before the third
  worked (an element is images OR a video; the prompt limit is effectively under 2,500, guard set to 2,400).
- **Kling 3.0 Standard:** beak closed throughout, proven pipeline, negative field works (its eyes closed fully at
  2.5–3.3 s).
- **Decision:** Kling 3.0 Standard stays primary. O3 is reserved for action shots where motion matters more than
  beak control. **Test O3 again on a walking or landing shot before EP005.** O3 shot tags: `o3`,
  `refvideo:<path>`, `never:o3_never_billy`.

## 4. Money
| Item | fal spend |
|---|---|
| EP001 | $4.23 |
| EP002 | $4.29 |
| EP003 | $3.05 |
| EP004 | $5.38 |
| Model tests (Wan, 2026-10-04) | $1.00 |
| **Model test O3 vs Kling 3.0 Std (2026-10-10)** | **$0.67** |

- **fal.ai balance:** about **$41.39** ($42.06 minus today's $0.67). The two refused O3 submits should be $0. The API
  key can't read billing: **confirm in fal.ai > Billing.**
- **ElevenLabs:** **36,826 credits left** this month (resets 2026-11-03). Nothing used since EP004.

## 5. Hard rules (`docs/PRODUCTION_FLOW.md`, `CLAUDE.md`)
- Follow `PRODUCTION_FLOW.md` step by step: concept → storyboard → script → voices → keyframes → cards → generate
  one → animatic → final → records.
- Before ANY concept work, read `docs/IDEAS_LOG.md`, `docs/JASON_VIDEOS.md` and `docs/STORY_MAP.md`.
- One shot = one approval card = one generation. Approval codes come only from the free run; never compute, guess or
  reuse one. No automatic retries.
- GROUNDING (feet on walkable ground), LOCATION CONTINUITY, every shot real moving video, every beat voiced, review
  the whole animatic with sound.
- Billy: wings never hands, monocle on the LEFT eye only, no white under the chin, never mirrored. Saul: big round
  eyes. The Snail: no eye actions.
- Never modify `Al-Oose-content/` (`./bbtb audit`). Never print API keys. The GitHub repo is public.
- **Clip fixes:** judge them on 2–3x crops of every shot, never on pixel counts alone (EP001: the counts missed the
  collar, the scroll, the sneaker and the wing damage).

## 6. Exact next action
1. **Wait for the owner's feedback on EP002, EP003 and EP004** (Jason's later fix-up notes). Same method as EP001:
   audit first, one before/after sheet per shot, free fixes before any regeneration.
2. Done 2026-10-10: EP004's 8 clips registered in `library/clips/clips.yaml` (38 clips, 12 rated A); Kling 3.0 Turbo
   permanently retired (`CLAUDE.md`, `docs/LESSONS_LEARNED.md`); EP001 caps raised to $6 (nothing spent).
3. Before EP005: one more O3 test on a walking or landing shot (card + code first).
4. EP005 "Big Pea DOOF" from the concept step. Big Pea's voice clone exists but is **NOT approved** (5.0 s of
   speech): one test line and the owner's listen first. Never re-clone him.

**Pending approval codes:** none. Every code issued so far is spent or void.
