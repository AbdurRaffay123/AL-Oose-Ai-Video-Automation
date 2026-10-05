# AL-Oose Studio: Master Prompt, Status and Plan

> **What this file is.** The single place that explains what we are building, how, what is finished, what is
> left, and what the owner still has to provide. Paste the **"Start-of-session prompt"** (section 1) into a new
> Claude Code session to continue the work without the old conversation.
>
> Last updated: **2026-10-04**. Status: **EP001 COMPLETE ✅**, made with the hybrid Kling pipeline on fal.ai for $4.23 (incl. tests and 2 retakes).
> Episode record: [`EPISODE_LOG.md`](EPISODE_LOG.md).

---

## 1. Start-of-session prompt (copy this into a new Claude Code session)

```text
You are working on the AL-Oose Studio in /Users/abdurraffay/Documents/Al-oose-Ai-video.
Read, in this order: CLAUDE.md (rules), docs/PROMPT.md (goal, status, plan), README.md (how to run),
docs/DECISIONS.md (owner decisions + findings), docs/EPISODE_LOG.md (finished episodes, costs, known issues),
docs/kling_prompts.md (prompt templates + results). Then run:
  ./bbtb audit
  ./bbtb voices status
  ./bbtb status productions/ep001-big-guy/script.md
  PYTHONPATH=studio .venv/bin/python -m pytest studio/tests -q
Report what you find, then continue with the first unfinished item in docs/PROMPT.md section 7
("What is left to do"), respecting every rule in CLAUDE.md. Never spend money or ElevenLabs credits, clone
or approve a voice, or pick a narrator voice without my explicit approval in this conversation.
```

---

## 2. The goal

Build a **reusable, local-first "script → finished video" studio** for the children's book
***Bad Billy the Bird*** by AL-Oose (Jason Metcalfe; Austin Macauley, 2025).

The owner writes (or approves) a short script. The studio then turns it into a **publishable** animated video:

- **The characters look exactly like the book.** Real artwork is used, never redrawn. Expressions and costume details stay on-model: Billy's monocle on his left eye, the cracked top hat with the "B" badge, and so on.
- **The characters sound like themselves.** The original recordings are used where a line matches. Otherwise each character has a permanent cloned voice (ElevenLabs).
- **Speaking characters visibly talk.** The mouth or beak moves in time with the voice. Perfect phoneme lip-sync is *not* required.
- **Music and sound effects** play underneath, with the voices always clear.
- **Short and entertaining:** under 50 s, ideally 40–45 s, in vertical 9:16 plus a 4:5 social crop.
- **Cheap and safe:** a target of **under $3 per video** at 720p. No paid call ever happens without the owner's approval code. Nothing is ever paid for twice.
- **Repeatable:** the voice library and character art are set up once and reused for every future episode.

**Permanent workflow:**

```
character recordings → one-time voice clone per character → saved voice IDs (library/voices.yaml)
→ new script → dialogue mapped to saved voices → ElevenLabs speech (approved, cached)
→ keyframes from real artwork → free local animation + selective LTX AI shots (approved)
→ music/SFX → mix, captions, export → QA report → owner review → publish
```

---

## 3. What I have understood (project facts)

### The book (canon)
- `Al-Oose-content/CONTENT/BBTB MARKETING/Book/BAD BILLY THE BIRD-story.pdf`: 37 pages, with the story on pp. 7–35. It's rhyming verse in the font *FunnySports*, so the extracted text needs accent normalisation.
- **Story:**
  - Bad Billy and Big Pea hunt for worms; Billy gobbles four of them.
  - Young Saul offers him "The Big Guy" instead and makes Billy read a magic scroll.
  - The Big Guy erupts from the ground ("Oh POOP!") and swallows Billy.
  - Big Pea finds only a scroll and some shoes.
- **Two editions of Billy, both canon** (the owner's ruling):
  - **Top hat:** the printed edition, the cover, all the animation sheets, and every marketing video.
  - **Goggles and red sneakers:** the PDF interior pages.
  - Which one appears is chosen per script; expressions and theme must stay on-model either way.
- **Speech bubbles** in the art (e.g. "Silly little worm!" on p. 29) count as canon too.

### Characters and assets (all verified, hashed in `library/assets.yaml`)

| Character | Art available | Voice reference (measured clean speech) |
|---|---|---|
| Bad Billy (top hat) | Turnaround ×6, 14 expression heads, 5 scroll poses, landing, flying sheets → **25 cut-outs** | 4 clips, **5.3 s** |
| Bad Billy (goggles) | Book crops BB-1…8 and an AI sheet (no cut-outs yet) | same voice |
| Young Saul | 28-pose character bible → **7 cut-outs** | 2 clips, **2.3 s** (too short) |
| The Big Guy | 2 sheets (misfiled under `Snail/`) and book crops → **5 cut-outs** | no dialogue; his roar is a sound effect |
| Big Pea | 2 sheets and book crops (no cut-outs yet) | 3 clips, **5.0 s** |
| Snail | Book pages only | 2 clips, **4.4 s** (too short, noisy) |
| Narrator | – | **5.8 s**, recovered from the marketing videos with the music removed (Demucs) |

- **Backgrounds:** clean plates such as BIG_WORM_HOLE, STUMP_GRASS, STUMP_SIGN, FLOATING_TREE, TUNNELS and SKY. One layered PSD with 43 layers is disguised as `1. GREEN GRASS.jpg`.
- **No layered character files exist and none can be obtained.** All animation works from flattened art.
- **Voice findings:**
  - Billy and Big Pea sound nearly identical (similarity 0.93), so they were probably one performer.
  - One file is misnamed: `BigPea_Go_Away_Stop_following_me.wav` actually says "Go away, I'm hungry!".
- **Existing marketing videos:** 12 short clips made with Kling AI plus cut-outs.
  - Billy smears during fast AI motion (`BILLY landing FUNny.mp4` at about 0.5 s).
  - Two worms morph together (`FUNY 2.mp4` at about 1.5 s).
  - Four clips carry a KlingAI watermark.
  - **The lesson:** lock the character art locally, keep AI motion short and simple, and never ship a watermark.

### Owner decisions so far
- Hybrid approach: local 2D animation plus selective AI video. The owner picked **LTX-2.3 Pro** for AI video.
- **ElevenLabs is the primary voice engine** (owner decision). Clips are clone references, and new or adapted script lines are allowed if labelled.
- The first video is **published**, not an experiment, so it must meet production quality.
- Budget is limited: **under $3 per video, 720p first.**
- Rough lip-sync is fine; the character just has to visibly talk.

---

### Status update (2026-10-03, after the ElevenLabs setup and the cleanup)
- **ElevenLabs works.**
  - The key's permissions are fixed (text_to_speech, voices, voice_generation, models, user, history, sound_effects, music_generation).
  - Starter plan, **39,482 credits** (reset 2026-11-03), 1 credit per character on `eleven_multilingual_v2`.
  - **Bad Billy is cloned** (voice id `fFaS1yzAqPneDXnQ0rbL`) but **not yet tested or approved**. His one test line ("Silly little worm!", about 18 credits) is waiting for the owner's approval code.
  - Saul, the narrator, Big Pea and the Snail are not cloned.
- **Owner credit rules are enforced in code:**
  - one `/with-timestamps` request per character, sliced by timings;
  - one test line per character;
  - any failure → `unknown` and stop, never retried;
  - a voice must be approved after listening before any render.
- **Chatterbox and macOS `say` are no longer used for anything the owner hears.** Previews without real voices use *silent* placeholders, kept in `_work/` and never in `audio/`.
- **All placeholder audio has been purged:** 7 macOS-voice and 8 silent line files, plus the 6 LTX upload files built from them, were deleted. The 19 old Chatterbox samples were moved to `reviews/voice_test/chatterbox/` (never used; deleted in the 2026-10-04 cleanup).
- **The project was reorganised by source** (EL / LTX / LOCAL / OG / ❌); see [`STRUCTURE.md`](STRUCTURE.md) sections 2 and 7.
  - `audio/lines/` = ElevenLabs only; `audio/originals/` = original recordings.
  - `shots/Sxx/{voice.mp3, ltx.mp4, local.mp4}`.
  - `preview/animatic.mp4`; `reviews/{qa.md, frames.jpg, voice_test/elevenlabs/}`.
- **Spent so far: $0 LTX, 0 ElevenLabs credits** (only free account checks and Billy's clone, which uses a voice slot, not credits).

### Status update (2026-10-04): EP001 COMPLETE ✅
- **ElevenLabs works, and all EP001 voices are approved:** Bad Billy, Young Saul and the Narrator.
  - Big Pea and the Snail are cloned, but their test lines are still pending. Neither appears in EP001.
  - **Credits:** 1,136 of 39,482 used this period, so **38,346 are left** (resets 2026-11-03).
- **fal.ai is integrated, running the hybrid Kling 3.0 pipeline** (owner decision, 2026-10-04):
  - **Kling 3.0 Standard** (silent, first → last frame) for action: S01, S05, S07.
  - **Kling AI Avatar v2**, driven by our ElevenLabs audio, for long dialogue: S02, S03, S06.
  - **Kling 3.0 Turbo** for short talking shots: S04, S08, S09. Kling speaks the line so the beak and body act it; the ElevenLabs Voice Changer then turns that voice into the character's approved voice.
  - The end card is local and free: S10.
  - Prompts live in `library/kling_prompts.yaml`, quoted in `docs/kling_prompts.md`. In v4, Billy's wings stay feathered.
- **EP001 was generated on 4 October 2026 for $3.56 on fal.ai:**
  - $3.11 for the final batch;
  - $0.45 for the S04 tests.
- **Deliverables:**
  - `productions/ep001-big-guy/exports/ep001-big-guy_FINAL_9x16.mp4`: 47.9 s, 720×1280, −16 LUFS;
  - `_FINAL_4x5.mp4`;
  - `ep001_captions.srt`.
- **Retakes (later the same day, $0.67):**
  - S04 now faces Saul.
  - S08 is terrified.
  - Free trims on S01 and S09; the final is now 45.8 s.
  - fal.ai total: **$4.23**.
- **About $5.77 is left on fal.ai.** This is calculated as $10 − $4.23; check fal.ai > Billing.
- **Known issues for EP002** (details in `docs/EPISODE_LOG.md`):
  - S01 pops Billy up instead of walking him in.
  - S08's re-voice says "Ahh!" instead of "Oh!".
  - The auto-QA consistency and mirror checks give false alarms on shots where the character turns.
- **Project cleanup (2026-10-04):** old exports, test clips and the voice-experiment folders were removed (see `docs/STRUCTURE.md` §2). Every paid clip and its sidecar is kept, so nothing can be bought twice.

## 4. The approach (and why)

| Need | Solution | Why |
|---|---|---|
| Characters stay exactly on-model | **Keyframes are composed locally** from cut-outs of the real sheets on real backgrounds. AI only animates *from* those frames | Generative models drift: the Kling clips smeared Billy. Locking the first frame keeps the design. |
| Expressions are exact | Close-ups are "busts": the sheet's real expression head placed on a real body | No redrawing; the faces in the video are the faces in the sheets |
| Cheap simple motion | **Free local animation**: hop-ins, pose changes, camera shake, idle bob, and a **mouth flap** that swaps matching closed and open heads to the voice's loudness | Most moves don't need AI. This saves money and is always on-model |
| A talking character moves its mouth | **LTX audio-to-video**: keyframe plus the line's audio, $0.06/s at 720p | The voice audio itself drives the mouth. Our own audio always replaces any AI audio in the final mix |
| Action that needs real motion (e.g. The Big Guy erupting) | **LTX image-to-video**: silent, first and last frame, 6/8/10 s, $0.04/s at 720p | Only where AI clearly adds value |
| Voices sound like the characters | Original clip when the words match; otherwise a **permanent ElevenLabs clone per character** | Consistent across episodes; cloned once, reused forever |
| No silent quality drops | Placeholder voices only with an explicit preview flag; never final; QA fails them; LTX is blocked | The owner's rule: report, don't substitute |
| Never overspend | Dry run → cost table → **approval code** (a hash of the exact jobs and budget) → ledger written *before* every paid request → no automatic paid retries | No provider here offers idempotency keys |
| Reproducible and safe | Originals are read-only and SHA-256 audited. Every derived asset records its parent. Secrets live only in `.env` | Handoff to any future session or developer |

**Staging rules:**
- One speaker per talking shot (shot/reverse-shot).
- No text inside AI shots; captions are overlaid locally.
- Faces and captions stay inside the 4:5 safe area.
- Billy is never mirrored.

---

## 5. What has been done

### Environment
- ffmpeg repaired (upgraded to 9.0.2).
- Python venv `.venv` with Pillow, numpy, PyYAML, requests and pytest.
- Optional `.venv-voice` (Python 3.11) with Chatterbox, Whisper, Resemblyzer and Demucs, all free and local.
- Git initialised, with `.env`, media and generated files excluded. **Nothing committed yet.**

### Library (built once, reused)
- `library/assets.yaml`: all 91 originals hashed. `library/asset_notes.yaml`: provenance, misfiles and duplicates.
- `library/cutlist.yaml` → `library/derived/cutouts/`: **39 transparent cut-outs**, including hand-fixed leg gaps.
- `library/characters/*.yaml`: the character bible, with variants, poses, expressions, facing direction, bust rules, mouth pairs, identity prompts for AI, voice sources, and relative heights.
- `library/backgrounds.yaml`: scene name → background plate, with focus point and ground line.
- `library/voices.yaml`: the **voice registry**. It holds measured assessments now; voice IDs are added once cloning happens.

### The studio code (`studio/bbtb/`)

| Module | Does |
|---|---|
| `script_parser.py` | Reads `script.md`: scenes, speakers, tags (variant/pose/expression/`local`/motion), sources `canon:`/`adapted:`/`production` |
| `shots.py` | Staging rules → shot list (engine per shot, framing, facing-based placement, narration and SFX placement, durations) |
| `keyframes.py` | Composes keyframes (cut-outs on plates, busts for close-ups) and the end card |
| `animate.py` | Free local animation (hop-in, pose change, shake, idle bob, audio-driven mouth flap) |
| `voices.py`, `elevenlabs.py`, `voice_cli.py` | ElevenLabs voice library: assess recordings, clone once, verify, test line, render a script's lines, cache, approval, plain-language errors |
| `ltx.py` | LTX V2 async client: cost, ledger before submit, duplicate guard, safe polling, resume |
| `audio_bed.py` | Music and SFX: your files → ElevenLabs (approved) → free synthesized SFX |
| `assemble.py`, `pipeline.py`, `qa.py` | Mix (−14 LUFS, ducked music), captions, 9:16 + 4:5 exports, animatic, QA report and frame sheet |
| `cutout.py`, `registry.py`, `ledger.py`, `env.py`, `media.py`, `voicelab.py` | Cut-out extraction, hashing, spend ledger, secrets, ffmpeg helpers, voice measurements |

- **CLI** `./bbtb`: `make` (with `--approve`, `--only`, `--placeholder-voices`), `status`, `resume`, `audit`, `cutouts`, `ltx forget`, and `voices` (`status`, `assess`, `account`, `clone`, `set`, `verify`, `test`, `approve`, `use`, `tune`, `render`).
- **Tests:** 28 offline tests pass (`studio/tests/`), covering parsing, staging, LTX money safety, the ElevenLabs workflow, and voice gating.
- **Docs:** `README.md` (runbook), `CLAUDE.md` (rules), `docs/DECISIONS.md` (decisions and findings), and the skill `.claude/skills/bbtb-make-video/` with three reference files.

### Episode 1: "The Scroll and The Big Guy" (book pp. 28–31): COMPLETE ✅
- **Script:** `productions/ep001-big-guy/script.md`, 10 shots. Every line is tagged canon, adapted or production.
- **Final:** `exports/ep001-big-guy_FINAL_9x16.mp4` (47.9 s) + `_FINAL_4x5.mp4` + `ep001_captions.srt`. QA: **PASS**.
- **Cost:** **$3.56 on fal.ai** and **1,136 ElevenLabs credits** in total (tests, dialogue, re-voice, music, SFX).
- **Full per-shot record:** [`EPISODE_LOG.md`](EPISODE_LOG.md).

---

## 6. Current blockers

None for making episodes. Open items:
1. **fal.ai balance is about $6.44**, roughly 1–2 more episodes at about $3.50 each. Recommended: ask Jason to top up $10 before EP002.
2. **Big Pea and Snail** need one test line each, plus the owner's approval, before they can speak. The Snail clone is rough (4.4 s of noisy audio).
3. **The fal key can't read the account balance** (it needs an Admin-scope key), so balances are calculated from the ledger.

---

## 7. What is left to do (in order)

### Done
- [x] Voice library: Billy, Saul and the Narrator are cloned, tested and approved; Big Pea and the Snail are cloned.
- [x] Video engine chosen: the hybrid Kling pipeline on fal.ai. An LTX test was never run; Kling replaced it.
- [x] EP001 generated, assembled, QA'd and exported (2026-10-04, $3.56).
- [x] Project cleanup and documentation update (2026-10-04).

### Next: fixes before EP002 (all free to build)
- [ ] **S01-style walk-ins:** a better `billy_walk` prompt or framing, so Billy walks in instead of popping up.
- [ ] **Re-voice accuracy:** after re-voicing, compare the words with the script line (as the "Ahh"/"Oh" case shows) and flag any mismatch before the shot is accepted.
- [ ] **Auto-QA:** replace the pixel-consistency and mirror checks, which give false alarms whenever the character turns.
- [ ] Owner: test lines for Big Pea and the Snail if EP002 uses them.

### Episode 2
- [x] Research + script (2026-10-04): `productions/ep002/script.md`, "The Deal" (book pp.19–27, never animated before; the prequel to EP001). 8 shots, about 43 s, 4 locations, about $3.14. Research (all 12 videos + every book beat), scores and feasibility: `productions/ep002/PLAN.md`.
- [ ] Owner approves the script, then the free prerequisites in PLAN.md (flight + landing cut-outs, `with:` two-shot tag, 5 Kling templates).
- [ ] Write the script → `voices render` (owner's code) → free `make` → `make --approve` (owner's code) → QA → export.

### Later (each needs owner approval)
- [ ] Cut-outs for **goggles Billy**, **Big Pea** and **Snail**, plus more Saul expressions.
- [ ] A local cartoon upscaler; 1080p renders.
- [ ] Commit the project to git (only when the owner asks).

---

## 8. What I need from you (owner checklist)

| # | Action | Why |
|---|---|---|
| 1 | Watch `exports/ep001-big-guy_FINAL_9x16.mp4` and publish it (the 4:5 is for Instagram; captions via CapCut) | EP001 is finished |
| 2 | Ask Jason to **top up fal.ai** (about $10) before EP002, and check the real balance in fal.ai > Billing | About $6.44 left, roughly one more episode |
| 3 | Choose the **pages for EP002** | The next script |
| 4 | If Big Pea or the Snail speak in EP002: approve one test line each, then listen and approve | Voices must be approved before use |

---

## 9. Costs at a glance (EP001 actuals, 2026-10-04)

| Item | Rate (fal pricing API, 2026-10-04) | EP001 |
|---|---|---|
| Kling 3.0 Standard i2v, silent, 720p | $0.084/s (whole seconds, 3–15 s) | $0.92 (S01, S05, S07) |
| Kling AI Avatar v2 Standard | $0.0562/s of audio | $1.18 (S02, S03, S06) |
| Kling 3.0 Turbo i2v (with Kling audio), 720p | $0.112/s | $1.34 (S04, S08, S09) |
| S04 Avatar test (rejected) | – | $0.11 |
| **fal.ai total** | | **$3.56** |
| ElevenLabs: tests, dialogue, re-voice (~203), music, SFX | about 1 credit per character; Voice Changer about 1,000 credits/min | **1,136 credits** (of 39,482) |

---

## 10. Possible implementations and alternatives considered

| Option | Verdict |
|---|---|
| **Kling 3.0 + Kling AI Avatar on fal.ai** (current, EP001) | Hybrid: Standard for action, Avatar for long dialogue with our audio, Turbo + ElevenLabs re-voice for short talking shots. On-model at the first frame, clear beak motion, $3.56 per episode |
| **LTX-2.3 Pro** | Integrated with all the safety controls, but never tested; replaced by Kling for EP001 |
| **Hedra Character-3** | Best fallback for talking shots: audio-driven, works on cartoons, about $0.05/s at 720p (third-party). Add as a second engine if LTX fails |
| **Seedance 2.0 / Mini** | Strong multi-reference character consistency, 4–15 s clips. **Cannot use our exact voice audio** (it generates its own), and costs about $0.08–0.155/s at 720p. Only worth a pay-as-you-go A/B on silent action shots |
| **Veo 3.1** | $0.10–0.40/s; too expensive for the budget |
| **Chatterbox** (local, free) | Kept as an optional voice provider. Too slow on this Mac (about 3.5 min per line); quality unscored |
| **Inworld TTS** | Removed in favour of ElevenLabs (owner decision) |
| **Blender / Grease Pencil** | Deferred. The Python cut-out animator covers current needs |
| **GUI** | Not needed; the CLI plus reports are enough |

---

## 11. Rules for any AI or developer working on this (summary of `CLAUDE.md`)

- Never modify `Al-Oose-content/` (originals). `./bbtb audit` must say "all 91 originals unchanged".
- No paid call (LTX, ElevenLabs speech or music) without the **owner's** approval code. Never compute or reuse a code yourself.
- Never clone or approve a voice, or pick a narrator, without explicit owner confirmation. Never re-clone a voice that already exists.
- No placeholder or borrowed voices in anything final. If something is missing, **stop and report**.
- No automatic paid retries. A ledger row in state `unknown` means check the provider console first.
- Never print or commit keys (`.env` only).
- Never mirror Billy; never redraw characters. Art comes from `library/derived/cutouts/`.
- Tag every script line `canon:pN`, `adapted:pN` or `production`. Never present adapted text as a quotation from the book.
- After code changes: `PYTHONPATH=studio .venv/bin/python -m pytest studio/tests -q`.

---

## 12. Key commands

```sh
./bbtb audit                                   # originals untouched?
./bbtb voices status | assess | account | verify
./bbtb voices clone <char> --confirm-rights    # once per character (owner-approved)
./bbtb voices test <char> "line" [--approve CODE]
./bbtb voices approve <char> --confirm-rights  # owner, after listening
./bbtb voices render <script> [--approve CODE] # all speech for a script (credits)
./bbtb make <script>                           # free: animatic + LTX cost + code
./bbtb make <script> --only S04,S07 [--approve CODE]
./bbtb make <script> [--max-cost N] --approve CODE   # fal (Kling) generation + re-voice + export + QA
./bbtb make <script> --placeholder-voices      # free timing preview only (never final)
./bbtb status <script> | resume <script>
./bbtb export <script>                         # free re-export from existing clips (after trim:<s> edits)
```

---

## 13. Known issues and risks

- Every voice reference is far below ElevenLabs' recommended ~60 s, so clones may only loosely match. Listening and approval are mandatory.
- Sheet art is small (full-body Billy is about 355 px tall), so it looks soft at 720p and softer at 1080p.
- Kling 3.0 can drift off-model during big moves (S04: wings → hands). The v4 prompt fixes it for Billy, but check every new template.
- The ElevenLabs Voice Changer can change a word (S08: "Oh" → "Ahh"). Listen to every re-voiced shot.
- Big Pea, the Snail and goggles Billy have no cut-outs yet, so scripts can't use them.
- The Old Wise Worm and the HELP WORM verse are marketing content, **not** book text.

## 14. References

- LTX API: https://docs.ltx.io (V2 only; V1 deprecated after 2026-10-26)
- ElevenLabs API: https://elevenlabs.io/docs/api-reference
- Claude Code skills: https://code.claude.com/docs/en/skills
- Project docs: `README.md`, `CLAUDE.md`, `docs/DECISIONS.md`, `.claude/skills/bbtb-make-video/`
