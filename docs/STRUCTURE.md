# AL-Oose Studio: Project Structure and Architecture

> A reference map of the codebase: what every folder and file is for, the tech stack, how the `bbtb` CLI maps
> to code, the data-file formats, the pipeline's data flow, and the conventions the code follows.
> For goals, status and the plan, see [`PROMPT.md`](PROMPT.md); for running it, [`../README.md`](../README.md);
> for rules, [`../CLAUDE.md`](../CLAUDE.md).
>
> Generated **2026-10-03** by reading the project. Section 2 (folder tree) and section 7 (pipeline flow) were
> rewritten on **2026-10-04**, after EP001 was finished with the hybrid Kling pipeline and the folders were cleaned up.

### Legend: where every file comes from

| Tag | Meaning |
|---|---|
| **EL** | ElevenLabs: paid, real cloned voices, re-voice, music, SFX (credits) |
| **FAL** | fal.ai: paid AI video, Kling 3.0 Standard/Turbo and Kling AI Avatar v2 ($) |
| **LTX** | LTX video API: paid AI video ($). Integrated, but not used since EP001 switched to Kling |
| **LOCAL** | Generated locally for free: keyframes, local animation, animatic, synthesized SFX, previews |
| **OG** | Original source material: book, art, voice recordings. **Never touch** |
| **❌** | Placeholder or scratch: **never ship** (silent timing placeholders, `_work/`) |

**Status of each production file** (used in the `productions/` part of the tree):

| Status | Meaning |
|---|---|
| **FINAL** | Delivered output; this is what gets published |
| **APPROVED** | Paid, owner-approved material the finals are built from. Never delete: the tool uses these files to avoid paying twice |
| **REFERENCE** | Kept for comparison and QA evidence. Not shipped |
| **FREE** | Rebuilt locally at no cost by any `./bbtb make` run. Safe to delete |

---

## 1. Overview

A local Python command-line studio that turns a `script.md` into a finished, voiced, animated *Bad Billy the Bird*
video. It composes keyframes from the book's real artwork, animates simple shots locally for free, sends selected
shots to **fal.ai** (Kling 3.0 and Kling AI Avatar; the older **LTX** client is still available), voices lines with original recordings or **ElevenLabs** clones, then mixes,
captions and exports with **FFmpeg**. Every paid step is gated by an owner approval code and recorded in an
append-only ledger.

---

## 2. Annotated folder tree

Skipped: `.venv/`, `.venv-voice/`, `__pycache__/`, `.git/`, `.pytest_cache/`. Each folder is tagged with its source
(see the legend above).

```
Al-oose-Ai-video/
├── bbtb                         Shell wrapper: runs `python -m bbtb.cli` from .venv with PYTHONPATH=studio
├── CLAUDE.md                    Rules for AI sessions, incl. the ElevenLabs credit rules
├── README.md                    Runbook: setup, voices, make a video, script format, safety, troubleshooting
├── .env                         Secrets (LTX_API_KEY, ELEVEN_LABS_API_KEY). Git-ignored. Never print it.
├── .env.example  .gitignore  .env.save (stray editor backup)
│
├── .claude/skills/bbtb-make-video/      Claude Code skill (/bbtb-make-video) + reference/ (script format, LTX, voice)
├── docs/                        PROMPT.md (goal/status/plan) · DECISIONS.md (decisions + findings) · STRUCTURE.md
│
├── Al-Oose-content/             OG  Originals, read-only, 91 files hashed in library/assets.yaml. NEVER TOUCH.
│   └── CONTENT/BBTB MARKETING/
│       ├── Book/                    OG  BAD BILLY THE BIRD-story.pdf
│       ├── Audio/                   OG  15 voice clips: Bad Billy/, Big Pea/, Saul the Worm/, Snail/
│       ├── Images/                  OG  Sheets/, Scenes/, Characters/ (Snail/ holds Big Guy art), Backgrounds/, Marketing/
│       ├── Video/                   OG  12 marketing clips (Kling AI; 4 watermarked)
│       └── Screenshots/             OG
│
├── library/                     Shared by every episode
│   ├── assets.yaml                  LOCAL  generated registry of the originals (id, path, sha256, size/duration)
│   ├── asset_notes.yaml             curated provenance of originals (misfiles, duplicates)
│   ├── characters/*.yaml            character bible (variants, poses, expressions, facing, bust, mouth pairs, voice)
│   ├── backgrounds/                 LOCAL  9:16 plates CROPPED from originals by `bbtb plates` (book spreads, environment
│   │                                art; never painted) + manifest.yaml (parent, hash, crop box). EP002: GRASS_STUMP,
│   │                                GRASS_FLOWERS, GRASS_SIGN, FLOATING_ISLAND, SKY_SHIP; 2026-10-05: 9 BG_* plates
│   │                                cut from the story PDF pages (pdf_page:). INVENTORY.md + INVENTORY.jpg = all 21
│   │                                backgrounds, ratings, scene types, every book page reviewed
│   ├── backgrounds.yaml             scene name → background plate (+ rating, types for scene-type matching)
│   ├── sheet_crops.yaml             named crops of Jason's official character sheets (references)
│   (references live per episode: productions/<ep>/scene_references/, built by `bbtb references`)
│   ├── derived/book_pages/          cached page paintings extracted from the story PDF (pdfimages, read-only)
│   ├── cutlist.yaml                 how each cut-out is cut from a sheet
│   ├── voices.yaml                  voice registry: EL voice id per character, source hash, settings, test file,
│   │                                rights, approval
│   ├── kling_prompts.yaml           Kling prompt templates (v1 Avatar per character; v3/v4 Kling 3.0 per shot type).
│   │                                Quoted word for word in docs/kling_prompts.md (a test checks this)
│   ├── derived/                     LOCAL  made FROM originals; reproducible
│   │   ├── cutouts/                     39 transparent PNG cut-outs (+ manifest.yaml: parent + hash of each)
│   │   └── voice_refs/                  joined/trimmed reference WAVs used for cloning (source material; don't move).
│   │                                    narrator_helpworm_vocals.wav = narrator separated from video 5 with Demucs
│   └── audio/
│       ├── generated/                   LOCAL  free synthesized SFX ONLY (synth_rumble/roar/whoosh/pop/scroll.wav)
│       ├── elevenlabs/                  EL     (created on first use) paid ElevenLabs SFX/music, cached forever
│       ├── music/                       owner-supplied royalty-free music (<mood>.mp3)
│       └── sfx/                         owner-supplied SFX (<name>.wav)
│
├── productions/
│   └── ep001-big-guy/
│       ├── script.md                The episode script (source of truth)
│       ├── plan.json                FREE  written on each `make`: shots, paid jobs, cost, approval code
│       ├── ledger.jsonl             APPROVED  append-only log of every paid request (fal, EL); never edit
│       ├── audio/                   APPROVED  the dialogue the final uses
│       │   ├── lines.json               index of every FINAL-capable line (source: elevenlabs | original)
│       │   ├── lines/                   EL   ElevenLabs lines ONLY (<line_id>.wav). Never a placeholder.
│       │   │   ├── _by_key/                 EL   content-addressed store (renumbered lines are never re-bought)
│       │   │   └── _batches/                EL   raw one-request-per-character batches + timings (re-sliced free)
│       │   └── originals/               OG→  lines taken from the original book recordings
│       ├── keyframes/               FREE  Sxx_first.jpg (+ Sxx_last.jpg): first/last frames composed from the cut-outs.
│       │                            They are part of each paid request's hash, so don't edit them by hand
│       ├── shots/                   one folder per shot; every file below is APPROVED unless marked
│       │   ├── S01/ S05/ S07/           FAL  kling3.mp4: Kling 3.0 Standard, silent action
│       │   ├── S02/ S03/ S06/           FAL  kling_avatar.mp4: Kling AI Avatar lip-synced to our audio
│       │   │                                 + kling_voice.wav/.json: the exact audio sent (part of the request hash)
│       │   ├── S04/ S08/ S09/           FAL  kling3.mp4: Kling 3.0 Turbo (Kling speaks the line; the beak follows)
│       │   │                            EL   + voice_revoiced.wav/.mp3/.json: Kling's voice turned into the
│       │   │                                   character's approved voice (this is what the final plays)
│       │   │                            REFERENCE  + kling_audio.wav: Kling's own voice, the re-voice input
│       │   ├── S10/                     FREE  local.mp4: the end card
│       │   ├── Sxx/takes/<clip>_<hash>/ REFERENCE  earlier paid takes, moved aside automatically by a retake
│       │   └── every Sxx/               + <clip>.json sidecar: request hash + approval code. It proves the clip was
│       │                                  paid for and stops it being bought again. **Never delete.**
│       │                                REFERENCE  + <clip>_qa.jpg/.json: the automated QA frames and scores
│       ├── preview/                 FREE  animatic.mp4 + animatic.srt: the latest free preview (storyboard
│       │                            stills or local stand-ins wherever no generated clip exists)
│       ├── exports/                 FINAL
│       │   ├── ep001-big-guy_FINAL_9x16.mp4   the episode (720×1280, −16 LUFS): to show and publish
│       │   ├── ep001-big-guy_FINAL_4x5.mp4    Instagram crop (720×900)
│       │   └── ep001_captions.srt             captions for CapCut/DaVinci (never burned in)
│       │                            (a new final run also writes <ep>_vN_9x16/_4x5.mp4 and refreshes the _FINAL_ copies)
│       ├── reviews/
│       │   ├── qa.md                    REFERENCE  QA report of the latest export
│       │   ├── frames.jpg               REFERENCE  one frame per shot (linked from qa.md)
│       │   ├── S04_kling3_revoiced.mp4  REFERENCE  the S04 test clip with Billy's re-voiced audio (for comparison)
│       │   └── voice_test/              README.md = voice status + test credits
│       │       └── elevenlabs/approved/     APPROVED  the owner-approved test line per voice (Billy, Saul, Narrator).
│       │                                    `voices test` recreates elevenlabs/pending/ when a new test is made
│       └── _work/                   FREE/❌  scratch, git-ignored, rebuilt every run: placeholders/ (SILENT timing
│                                    placeholders), preview/ and final/ (concat list, mix.wav, fitted clips)
│
└── studio/                      Source code
    ├── bbtb/                    The application package (section 4)
    ├── tests/                   test_core.py, test_elevenlabs.py: 32 offline tests, no network
    └── voicetools/              vt.py, eval_voices.py: analysis tools run in .venv-voice (Whisper, Resemblyzer, Demucs).
                                 Never used to make audio the owner hears.
```

**Voice tests:** `elevenlabs/approved/` = production ready. `bbtb voices test` writes into `pending/` (created on
demand), and `bbtb voices approve` moves the file into `approved/` (the registry path follows it).

**Rules the layout enforces (in code):**
- `audio/lines/` only ever receives ElevenLabs output.
- Placeholders can only be written to `_work/placeholders/`.
- Audio uploaded for a talking shot (Avatar `kling_voice.wav`, LTX `voice.mp3`) is only made from final voices (EL approved, or OG).
- Kling 3.0 talking shots are only re-voiced with an owner-approved voice. If Whisper doesn't hear the script line, the shot stops before any credits are spent.

### Cleanup on 2026-10-03 (owner-approved)

| Action | Files |
|---|---|
| **Deleted (42)** | 15 placeholder line WAVs: 7 macOS `say` voices + 8 silent; 6 `voice.mp3` built from placeholders or old shot numbers (S02, S03, S06, S08, S09, S10); preview intermediates (`mix.wav`, `video.mp4`, `video.txt`, 16 caption PNGs); old shot S11 (`S11_preview.mp4`, `S11_first.jpg`) |
| **Moved (32)** | L013 original → `audio/originals/`; `lines.json` → `audio/lines.json` (only L013 kept); `preview/Sxx_preview.mp4` → `shots/Sxx/local.mp4`; animatic → `preview/animatic.mp4`; 19 Chatterbox samples → `reviews/voice_test/chatterbox/` |
| **Kept untouched** | `Al-Oose-content/`, `library/derived/voice_refs/`, cut-outs, synthesized SFX, `shots/S04/voice.mp3` (made from the original recording) |

At that point there were no EL or LTX outputs anywhere (0 credits, $0 spent).

### Cleanup on 2026-10-04 (owner-requested, after EP001 was finished)

| Action | Files |
|---|---|
| **Deleted (51 files + 3 empty folders)** | `exports/`: the 6 versioned exports `_v1_`/`_v2_`/`_v3_` (v3 was byte-identical to `_FINAL_`). `shots/`: the S04 Avatar test (`kling_test.mp4/.json`, `kling_test_qa.jpg/.json`) and its upload (`kling_voice.wav/.json`); S04 `voice.mp3` (old LTX upload); stale S09 `kling_voice.wav/.json`; stale `local.mp4` in S01–S09. `reviews/voice_test/`: `chatterbox/archive/` (19), `pitch_experiments/` (7), `elevenlabs/rejected/` (1 file) and the empty `elevenlabs/pending/` |
| **Kept on purpose** | Each clip's `.json` sidecar, the Avatar `kling_voice.wav` (S02/S03/S06) and the re-voice files (S04/S08/S09). The tool reads these to know a clip is paid for; deleting them would make the next run pay again. QA frames and Kling's raw audio are kept as REFERENCE |
| **Checked afterwards** | All 9 paid shots still count as done (re-running costs $0.00); all 91 originals unchanged; tests pass |

## 3. Tech stack

| Layer | What | Version / notes |
|---|---|---|
| Language | Python | **3.14.4** in `.venv` (main app); **3.11.14** in `.venv-voice` (ML tools only) |
| Image work | Pillow, numpy | 12.3.0, 2.5.3: cut-outs, keyframes, frame-by-frame animation |
| Config/data | PyYAML, json | 6.0.3: YAML for human-edited files, JSON/JSONL for machine state |
| HTTP | requests | 2.34.2: LTX and ElevenLabs clients (injectable `Session` for tests) |
| Tests | pytest | 9.1.1: 28 offline tests |
| Media | **FFmpeg / ffprobe** (system, Homebrew) | 9.0.2, called via `subprocess` in `media.py`. Uses libx264, aac, libmp3lame, loudnorm/ebur128, sidechaincompress, zoompan, overlay, blackdetect |
| Fonts | macOS system fonts | Arial Rounded Bold (end card), Chalkboard SE Bold (captions) |
| Placeholder audio | ffmpeg `anullsrc` silence | Only with `--placeholder-voices` / `--only`; never final. macOS `say` and Chatterbox are no longer used for anything the owner hears |
| ML (optional, analysis only) | torch, torchaudio, chatterbox-tts, openai-whisper, Resemblyzer, demucs | 2.6.0, 2.6.0, 0.1.7, 20250625, 0.1.4, 4.1.0, in `.venv-voice`, bridged by subprocess + JSON. Used for the same-speaker check, transcription and vocal separation. Chatterbox is installed but **not** a voice provider |
| Used during setup only | ImageMagick 7.1.2, poppler (`pdftotext`, `pdftoppm`), Swift/AVFoundation | Not called by the app |

**External APIs** (all paid calls gated by approval codes):

| Service | Endpoints used | Module |
|---|---|---|
| **fal.ai** (video, used for EP001) | `POST https://queue.fal.run/<model>` with `fal-ai/kling-video/v3/standard/image-to-video`, `…/v3/turbo/standard/image-to-video` and `…/ai-avatar/v2/standard`; poll `status_url`, fetch `response_url`, download `video.url`; `GET /v1/models/pricing` (free) | `fal.py` |
| **ElevenLabs** (re-voice) | `POST /v1/speech-to-speech/{voice_id}` (Voice Changer, `eleven_multilingual_sts_v2`) | `revoice.py` → `elevenlabs.py` |
| **LTX** (video; not used since EP001) | `POST /v2/image-to-video`, `POST /v2/audio-to-video`, `GET /v2/<endpoint>/<id>`, then download `result.video_url` | `ltx.py` |
| **ElevenLabs** (voice) | `POST /v1/voices/add` (clone), `POST /v1/text-to-speech/{voice_id}`, `GET /v1/voices/{id}`, `GET /v1/user/subscription`, `GET /v1/models` | `elevenlabs.py` |
| **ElevenLabs** (audio bed) | `POST /v1/sound-generation`, `POST /v1/music` (only in an approved final run, and only if no local file exists) | `audio_bed.py` |

Model and asset downloads for `.venv-voice` come from Hugging Face (about 5 GB, cached in `~/.cache/huggingface`).

---

## 4. Code architecture (`studio/bbtb/`)

Modules grouped by layer (lines of code in brackets):

| Layer | Module | Responsibility |
|---|---|---|
| **Entry** | `cli.py` (172) | `argparse` CLI: `make`, `status`, `resume`, `audit`, `cutouts`, `ltx forget`; registers `voices` |
| | `voice_cli.py` (234) | `bbtb voices …` subcommands (setup, verify, test, approve, render) |
| **Orchestration** | `pipeline.py` (256) | `prepare()` (free), `jobs()`, `approval_code()`, `cost_table()`, `make()`, `voice_blockers()`, `render()` |
| **Script → shots** | `script_parser.py` (174) | Parses `script.md` → `Script(title, meta, events)`, where each `Event` has kind, speaker, variant, pose, expression, direction, source |
| | `shots.py` (301) | Staging rules → `Shot` list (engine, cast/`OnScreen`, lines, sfx, prompt, motion); `apply_durations()`; LTX prompt text |
| **Voices** | `voices.py` | Voice registry, source assessment, clone-once, line plan, one-request-per-character batching + timestamp slicing, content cache, silent placeholders, `is_final()`, `VoicesNotReady` |
| | `elevenlabs.py` (156) | ElevenLabs HTTP client, plain-language errors, ledger-before-request TTS |
| | `voicelab.py` (69) | numpy pitch (YIN), active-speech seconds, brightness |
| | `voice_page.py` (44) | HTML listening page for clone tests. **Currently unused** (no caller) |
| **Pictures** | `cutout.py` (148) | Sheet → transparent PNG (border flood-fill, largest component, hole seeds); manifest |
| | `keyframes.py` (198) | Background plate cropping, `bust()` (expression head on body), `layout()`/`draw()`/`compose()`, end card |
| | `animate.py` (161) | Local animation renderer (hop-in, pose swap, shake, idle bob, audio-driven mouth flap) → FFmpeg pipe |
| **Video gen** | `fal.py` (274) | fal.ai client: Kling 3.0 Standard/Turbo + Kling AI Avatar `Job` (cost, request hash, `.json` sidecar), `Client.submit/wait/run`, no-retry header, polling, download |
| | `revoice.py` (121) | Kling 3.0 talking shots: Kling's voice → the approved ElevenLabs voice (Voice Changer), with a Whisper line check before and after |
| | `preflight.py` (269) | Free checks before any paid call: on-model art, not mirrored, monocle on LEFT eye, safe area, upload audio prep |
| | `clip_qa.py` (183) | Automated QA of each generated clip → `shots/Sxx/<clip>_qa.jpg/.json` |
| | `ltx.py` (202) | LTX client (`Job`, `Client.submit/wait/run`); kept, but not used since EP001 |
| **Audio + assembly** | `audio_bed.py` (158) | Music/SFX lookup: local file → ElevenLabs (approved) → synthesized SFX |
| | `assemble.py` (146) | `still_clip`, `fit_clip`, `concat`, `mix` (+ `normalize` to −16 LUFS), `mux` (9:16 / 4:5), `write_srt` (captions as an .srt only, never burned in) |
| | `qa.py` (75) | Duration, loudness, black frames, final-voice check, frame contact sheet → `reviews/qa.md` + `reviews/frames.jpg` |
| **Infrastructure** | `registry.py` (125) | Hash/verify originals, asset ids, `path_of(id)` |
| | `ledger.py` (45) | Append-only JSONL ledger; `find()`, `latest()`, `spent()` |
| | `media.py` (77) | FFmpeg helpers: `to_wav`, `to_mp3`, `concat_audio`, `duration`, `loudness` |
| | `env.py` (36) | `.env` loading, `require()`, `redact()` |
| | `paths.py` (17) | `ROOT`, `ORIGINALS`, `LIBRARY`, `DERIVED`, `CHARACTERS`, `PRODUCTIONS`, `ENV_FILE`, `rel()` |

**Dependency direction:**
`cli`/`voice_cli` → `pipeline` → (`script_parser`, `shots`, `voices`, `keyframes`, `animate`, `fal`, `revoice`, `preflight`, `clip_qa`, `ltx`, `audio_bed`, `assemble`, `qa`) → (`registry`, `media`, `ledger`, `env`, `paths`). Lower layers never import upward.

---

## 5. CLI architecture

`./bbtb` sets `PYTHONPATH=studio` and runs `.venv/bin/python -m bbtb.cli`.

- `cli.main()` builds the `argparse` tree. Each subcommand sets `f=<handler>`. Handlers import heavy modules lazily.
- Any exception is printed as `error: <message>` with secrets redacted (`env.redact`), then exits 1.
- `VoicesNotReady` gets its own friendly "STOPPED at the voice stage" output.

| Command | Handler | Calls | Paid? |
|---|---|---|---|
| `make <script>` | `cli.cmd_make` | `pipeline.make()`: prepare, jobs, cost table, code, animatic | free |
| `make <script> --only S04,S07` | same | uses placeholders for unselected lines' timing; cost and code cover only those shots | free |
| `make <script> --placeholder-voices` | same | timing preview with SILENT placeholders (in `_work/`); paid generation disabled | free |
| `make <script> [--only …] [--max-cost N] --approve CODE` | same | checks code, voice gate, pre-flight, budget and caps → `fal.Client.run()` (+ `revoice.run()` for Kling 3.0 talking shots) per job → `render(final)` → `_FINAL_` copies → `qa.check()` | **fal $ + ElevenLabs re-voice credits** (+ LTX $ for LTX shots; ElevenLabs music/SFX if no local files) |
| `plates [--only P]` | `cmd_plates` | `bgplates.build()`: crops every `crop:` scene in backgrounds.yaml to library/backgrounds/ | free |
| `export <script>` | `cmd_export` | `pipeline.export()`: re-renders the final from the existing clips (after `trim:` edits); cached or synthesized music/SFX only | free |
| `status <script>` | `cmd_status` | reads `plan.json`, ledger and exports | free |
| `resume <script>` | `cmd_resume` | `prepare()` then `Client.wait()` for submitted jobs; never resubmits | free (polls only) |
| `audit [--rebuild]` | `cmd_audit` | `registry.verify()` / `registry.build()` | free |
| `cutouts [--only PREFIX]` | `cmd_cutouts` | `cutout.run()` | free |
| `ltx forget <script> <hash>` | `cmd_forget` | marks an `intent`/`unknown` ledger row failed (after checking the console) | free |
| `voices status` | `voice_cli.status` | registry + `voices.assess()` | free |
| `voices assess [char]` | `voice_cli.assess` | `voices.assess()` (+ Resemblyzer same-speaker check if `.venv-voice` exists) | free |
| `voices account` | `voice_cli.account` | `GET /v1/user/subscription` | free |
| `voices clone <char> --confirm-rights [--allow-short]` | `voice_cli.clone` | `voices.clone()` → `POST /v1/voices/add` (skipped if already cloned from the same audio) | uses a voice slot |
| `voices set <char> <voice_id>` | `voice_cli.set_voice` | `voices.set_existing()` | free |
| `voices verify [char]` | `voice_cli.verify` | `GET /v1/voices/{id}` | free |
| `voices test <char> "text" [--approve CODE] [--retest] [--name N] [--episode E]` | `voice_cli.test` | `elevenlabs.Client.tts()` → `productions/<E>/reviews/voice_test/elevenlabs/pending/`; one per character | **credits** |
| `voices forget <request_hash> [--script S]` | `voice_cli.forget` | clears an `unknown` EL ledger row after the owner checks ElevenLabs History | free |
| `voices approve <char> --confirm-rights` | `voice_cli.approve` | sets `approved: true` (the owner, after listening); moves the test file `pending/` → `approved/` | free |
| `voices reclone <char> --confirm-rights` | `voice_cli.reclone` | new clone from ALL `clone_reference` clips joined (`voice_refs/<char>_vN.wav`); old voice deleted only after the new one is saved | voice slot |
| `voices tune <char> --stability …` | `voice_cli.tune` | updates settings, resets approval | free |
| `voices render <script> [--approve CODE]` | `voice_cli.render` | `voices.render_lines(allow_paid=True)`: ONE `/with-timestamps` request per character for uncached lines | **credits** |

> Note: the `cli.py` help text shows `bbtb ltx forget <request_hash>`, but the parser requires `<script> <request_hash>`. Also, `tempfile` is imported in `cli.py` and `PRODUCTIONS` in `pipeline.py`, but neither is used.

---

## 6. Key data files and formats

### 6.1 `library/assets.yaml` (generated by `bbtb audit --rebuild`; never hand-edit)
```yaml
assets:
  images.sheets.landing-sheet-v-777:          # id = slug of the path below Al-Oose-content/.../BBTB MARKETING
    kind: image                                # image | psd | audio | video | pdf (psd detected by magic bytes)
    path: Al-Oose-content/CONTENT/BBTB MARKETING/Images/Sheets/LANDING SHEET V.777.jpg
    bytes: 1008669
    sha256: 8820f982…
    size: [1491, 1055]
    alpha: false
  audio.bad-billy.badbilly-silly-little-worm:
    kind: audio
    duration: 1.757
    …
```
`asset_notes.yaml` (curated, keyed by the same ids) adds `provenance`, `character`, `variant`, `misfiled`, `duplicate_of` and `note`.

### 6.2 `library/characters/<id>.yaml` (character bible)
```yaml
id: bad_billy
display_name: Bad Billy
aliases: [BILLY, BAD BILLY]          # names usable in scripts
height: 1.0                          # relative on-screen height (Billy = 1.0)
mirror_ok: false                     # Billy must never be flipped (monocle on LEFT eye)
default_variant: tophat
variants:
  tophat:
    identity_prompt: "…"             # appended to LTX prompts
    rules: [...]
    poses:       {34left: billy_tophat_34left, scroll-reading: billy_tophat_scroll_reading, …}   # name → cut-out id
    expressions: {skeptical: billy_tophat_head_skeptical, shock: billy_tophat_head_shock, …}
    facing:      {34left: left, skeptical: right, …}     # drives screen placement (face into the frame)
    bust: {bodies: {front: …, right: …, left: …}, cut: 0.50, neck: 0.54, head: 0.56, dx: {…}}   # close-ups
    mouth_pairs: {front: [neutral, angry], right: [skeptical, talking]}    # [closed, open] for local mouth flap
  goggles: {…}                       # identity prompt only; no cut-outs yet
voice:
  needed: true                       # big_guy sets false (no dialogue)
  originals: {"Silly little worm!": audio.bad-billy.badbilly-silly-little-worm, …}   # exact-match lines
  clone_reference: [asset ids…]      # clips used for cloning
  clone_reference_files: [paths…]    # derived files (narrator)
```

### 6.3 `library/cutlist.yaml` → `library/derived/manifest.yaml`
```yaml
sheets:
  images.sheets.bad-billy-key-frames-sheet:
    tol: 38                                          # optional colour tolerance
    cuts:
      billy_tophat_front: {box: [25, 165, 200, 528], holes: [[104, 473]]}   # sheet pixels; hole seeds clear enclosed gaps
```
The manifest records, per cut-out: `file`, `parent`, `parent_sha256`, `box`, `method`, `size`, `sha256` and `status` (draft → approved).

### 6.4 `library/backgrounds.yaml`
```yaml
BIG_WORM_HOLE: {asset: images.backgrounds.big-worm-hole, focus: [1220, 900], ground_y: 1290, note: "…"}
```
`focus` is the centre point used when cropping the plate to 9:16 or 16:9. `ground_y` is informational; feet lines are set by framing constants in `keyframes.py`.
- **Book plates:** `parent: book.bad-billy-the-bird-story, pdf_page: N, crop: [...]`. The box is in that page's
  embedded painting (2591×3378 at 300 ppi; the verse is a text layer, so it is never included).
- **`rating`** (3 clean, 2 tiny figures, 1 unusable) and **`types`** (conversation, flying, underground…) drive
  `keyframes.resolve_scene()`. `## SCENE <type>` picks the best-rated background of that type, never the same as the
  previous shot. 21 backgrounds in all (16 rated ⭐⭐⭐); see `library/backgrounds/INVENTORY.md`.

### 6.5 `library/voices.yaml` (voice registry)
```yaml
defaults: {provider: elevenlabs, model_id: eleven_multilingual_v2}
characters:
  bad_billy:
    provider: elevenlabs              # the only provider for anything the owner hears
    rights_confirmed: true
    approved: false                   # becomes true only via `voices approve` after listening
    elevenlabs:
      voice_id: fFaS1yzA…             # saved once, reused by every episode
      source_files: [...]             # clips uploaded at clone time
      source_sha256: a61ca421…        # re-clone is skipped while this is unchanged
      cloned_at: '2026-10-03T16:09:25'
      settings: {stability: 0.45, similarity_boost: 0.85, style: 0.3, use_speaker_boost: true, speed: 1.0}
    assessment: {verdict: limited, speech_seconds: 5.3, note: "…"}
```
**Current state:**
- Bad Billy is **cloned but not approved**.
- Big Pea and the narrator are *limited*, not cloned.
- Snail and Saul are *insufficient*, not cloned.
- Big Guy needs no voice.

### 6.6 `productions/<ep>/script.md`
```markdown
# EP001 Title                                   ← title
format: 9:16  resolution: 720p  music: playful-adventure  budget: 3  captions: on   ← header (also fps, model)
<!-- comments are ignored -->
## SCENE BIG_WORM_HOLE                          ← background id from backgrounds.yaml, or END_CARD
ACTION [wide, local, enter-right]: Bad Billy hops in.                     ← local animation
BILLY [tophat, 34left, suspicious, canon:p28]: Well, where is the worm?  ← talking shot (LTX audio-to-video)
ACTION [medium, local, scroll-pickup>scroll-reading]: Billy unrolls the scroll.   ← pose change
SFX [at 3.5]: roar                                                        ← sound 3.5 s into the next shot
ACTION [wide, end: BIG GUY arms-up]: The Big Guy bursts out.             ← LTX image-to-video with end frame
NARRATOR [canon:p30]: Then deep from below…                              ← voice-over on the next ACTION, else a hold shot
```

| Tag type | Values | Effect |
|---|---|---|
| Variant | `tophat`, `goggles` | Which design |
| Pose | e.g. `34left`, `holding-scroll` | Medium full-body shot |
| Expression | e.g. `skeptical`, `shock` | Close-up bust |
| Engine | `local` / `ltx` | `local` = free animation (talking: mouth flap; action: motions) |
| Motion | `enter-left`, `enter-right`, `shake`, `a>b` | Local animation moves |
| Framing | `wide`, `medium` | Action framing |
| End frame | `end: <NAME> <pose>` | Character appears by the last frame (LTX only) |
| Source | `canon:pN`, `adapted:pN`, `production` | Provenance of the words |
| Other | anything else, or a leading `(…)` | Acting direction |

Line ids are `L<line number:03d>_<speaker>` (e.g. `L016_bad_billy`).

### 6.7 Machine state inside a production
| File | Format | Contents |
|---|---|---|
| `audio/lines.json` | JSON `{line_id: {...}}` | `key` (content cache key), `source` (`elevenlabs` or `original` only), `speaker`, `text`, `path`, `line_source`, `seconds`; plus `voice_id`, `model_id`, `settings` or `asset`. Placeholders are never written here |
| `plan.json` | JSON | `title`, `meta`, `approval_code`, `new_cost`, `shots[]` (`Shot.to_dict()`), `jobs[]` (`shot`, `endpoint`, `cost`, `request_hash`) |
| `ledger.jsonl` | JSON Lines, append-only | One row per state change: `request_hash`, `ts`, `state` (intent→submitted→completed / failed / unknown / expired), `kind` (fal/ltx/tts/sts/audio), `cost_estimate` ($) or `credits_estimate`, `approval_code`, `request_id`/`job_id`, `output_sha256`, `error` |
| `reviews/qa.md` + `reviews/frames.jpg` | Markdown, JPEG | QA verdict (PASS / PASS with warnings / FAIL) for the latest export, plus one frame per shot |

---

### 6.8 Staging tags (added for EP002, 2026-10-04)
| Tag | Where | Effect |
|---|---|---|
| `with: <NAME> <pose>` | talking line | Silent partner in a two-shot: placed half out of frame on the opposite side, behind the speaker (e.g. Billy looming over Saul) |
| `zoom:<f>` | talking/action line | Camera push-in: the frame is composed at f x size from the originals and cropped around the face (`face:` anchor in the character file), so it stays sharp; the hat stays in the 4:5 safe area |
| `far` | action line | Small figure in a big world (24% of the height) |
| `pass-right` / `pass-left` | Kling 3.0 action with `a>b` poses | Start frame on one side, end frame on the other (travel across the frame) |
| `trim:<s>` | Kling 3.0 line | Cut the start of the generated clip in the edit (free; never changes the paid request) |
| `airborne:` (character file) | pose art ids | Flying art is centred at the scene's `air_y` with no ground shadow |
| `pace_wps` (character file, `voice:`) | – | Words/second of the approved voice; silent placeholders use it so the animatic timing is realistic |

## 7. Pipeline flow

### Pipeline v3.0 (EP003 on, 2026-10-05): "maximum preparation, one take per shot"
```
script.md ─► ./bbtb voices render (approval code, ElevenLabs credits)
          ─► ./bbtb references   (free) per-shot boards + Kling @Elements from Jason's official sheets
          ─► ./bbtb preprod      (free) PRE_PRODUCTION.md: GO/NO-GO per paid shot (pre-flight, final voice,
          │                       references, cut-out white edge, facing, prompt reviewed, shot_cap, background),
          │                       risk order, min/max/target cost + PROMPTS.md (exact prompts + rationale)
          ─► ./bbtb make         (free) animatic + approval code
          ─► ./bbtb make --approve CODE   paid, LOW → MEDIUM → HIGH risk order; caps: session_cap, spend_cap,
                                          shot_cap (no single shot above it); no automatic retakes
          ─► QA ─► export
```
- **Header switches:**
  - `elements: on` sends character references.
  - `bg_element: on` sends the background as an element (experimental).
  - `negatives: billy_hands,saul_body` adds opt-in negative prompts.
  - `shot_cap: 0.70` is the per-shot cost cap.
  - `keyframes: locked` marks a finished episode.
  - `music: auto[:mood]` uses Jason's music library.
- **Music:** `library/audio/music/jason/`. `./bbtb music` analyses each track (duration, tempo, loudness, brightness,
  then an estimated mood, energy and best use) into MUSIC_INVENTORY.md. `music: auto` never repeats the previous
  episode's track and falls back to the cached bed while the folder is empty.
- **Backgrounds:** 21 in `library/backgrounds/INVENTORY.md` (16 rated ⭐⭐⭐), with scene-type matching.
- **Red-background test (2026-10-06):** `cutout.red_test()`. Every enclosed white patch in a cut-out must be cleared
  (`holes:`) or approved (`keep_white:`) in `cutlist.yaml`. It is checked by `bbtb cutouts` (review images in
  `library/derived/cutout_review/`), by pre-flight for every keyframe character, and by `bbtb preprod`.
- **Reference checks:** Saul shots need a face close-up, the big-eye rule and `saul_eyes`; Billy shots need a head
  close-up. Reusable sets: `library/character_refs.yaml` → `library/scene_references/<char>/`
  (`bbtb references --characters`).

**What Kling 3.0 Standard receives per shot (EP003 on, header `elements: on`):**
1. The keyframe as the start frame, plus an optional end frame: our cut-out on the background plate, which already
   shows WHERE.
2. Character references: per character `@ElementN`, a frontal pose plus up to 3 images cut from Jason's official
   sheets (WHAT they look like).
3. Optional: the background as one more element (header `bg_element: on`, experimental; see `docs/PROMPT_GUIDE.md`).
4. The text prompt (HOW they move), with the shared and opt-in negative prompts.

Kling 3.0 Turbo takes only the start frame, so references need `kling3std` lines.

```
script.md
   │  script_parser.parse()  → Script(meta, events)            [names → ids via aliases; tags classified]
   │  shots.lines_of()       → Line[] (dialogue + narration, with canon/adapted/production source tags)
   ▼
VOICE STAGE  voices.render_lines(audio_dir)
   │  per line:  words match an original clip? ──yes──► OG  audio/originals/<id>.wav            (free)
   │                                           └─no──► EL  needs the character's APPROVED voice id
   │     cached in audio/lines/_by_key/ ? ──yes──► copy to audio/lines/<id>.wav               (free)
   │     not cached:
   │        `bbtb voices render --approve CODE`  →  ONE request per character
   │            POST /v1/text-to-speech/{voice_id}/with-timestamps (lines joined with <break>)
   │            → audio/lines/_batches/<char>_<key>.mp3 + .json (timings) → sliced → _by_key/ → lines/   (EL, credits)
   │        plain `make` → STOP (VoicesNotReady)   |   `make --placeholder-voices` → ❌ silence in _work/placeholders/
   ▼
shots.plan() + apply_durations()  ← real line lengths (0.25 s padding)
   │  engine per shot (HYBRID, from script tags / header):
   │     ACTION                  → kling3_action  Kling 3.0 Standard, silent, first → last frame   (S01, S05, S07)
   │     long dialogue  [kling]  → kling_avatar   Kling AI Avatar v2 driven by OUR audio           (S02, S03, S06)
   │     short talking  (header) → kling3_talk    Kling 3.0 Turbo, Kling speaks the line           (S04, S08, S09)
   │     END_CARD                → local_endcard  free                                              (S10)
   ▼
keyframes.compose()/end_card()   → keyframes/Sxx_first.jpg (+ _last)                         LOCAL
   ▼
pipeline.jobs()  → fal.Job per shot. Prompt = library/kling_prompts.yaml template (+ {facing} {line} {acting} {direction})
   │     avatar: keyframe + shots/Sxx/kling_voice.wav (trimmed, −16 LUFS, ONLY from EL/OG audio)
   │     turbo : keyframe, duration 3–15 s        standard: start (+ end) frame, negative prompt, silent
   ▼  pre-flight (art on-model, not mirrored, monocle LEFT, safe area, voice approved) + cost table + caps
   ▼  approval code (hash of the exact jobs + budget) → plan.json
   ▼
render(final=False)  → preview/animatic.mp4 + animatic.srt: storyboard stills / local stand-ins + EL/OG voices    LOCAL
   │
   │  ── owner reviews; replies with the approval code ──
   ▼
`make --approve CODE`: code ✓ · voices FINAL ✓ · pre-flight ✓ · budget / spend_cap / session_cap / --max-cost ✓
   ▼  for each shot, in order:  fal.Client.run(job): ledger intent → POST queue.fal.run (X-Fal-No-Retry)
   │        → poll → download → shots/Sxx/kling3.mp4 | kling_avatar.mp4 (+ .json sidecar)              FAL ($)
   │     kling3_talk only → revoice.run: extract Kling audio → Whisper checks the line (free) →
   │        ElevenLabs Voice Changer (approved voice) → Whisper again → shots/Sxx/voice_revoiced.wav   EL (credits)
   │     clip_qa.check → shots/Sxx/<clip>_qa.jpg/.json
   │     a failed shot is logged, never retried, and skipped (local fallback); a failed ElevenLabs call stops the run
   ▼  music/SFX: library/audio/music|sfx (owner) → library/audio/elevenlabs (EL, approved run) → generated/ (LOCAL)
   ▼
render(final=True)   → per shot: generated clip fitted (_work/final) | free local fallback
                     → concat + mix (dialogue + SFX + ducked music, −16 LUFS)
                     → exports/<ep>_vN_9x16.mp4 + _4x5.mp4, copied to <ep>_FINAL_9x16/_4x5.mp4, + <ep>_captions.srt
   ▼
qa.check             → reviews/qa.md + reviews/frames.jpg (FAILS if any line is not EL-approved or OG)
```

**Timing model:**
- A talking shot lasts line length + 0.25 s on each side.
- Lines start at a per-engine `LEAD` offset inside their shot.
- Avatar shots: the clip is aligned with our line using the per-engine lead plus the silence trimmed from the upload.
- Kling 3.0 talking shots last a whole number of seconds (3–15) and play the re-voiced audio, which keeps Kling's timing so the beak stays in sync.
- Generated clips' own audio is never used directly; the mix is always built from our voices.

## 8. Conventions and patterns

1. **Originals are immutable.** All reads go through `registry.path_of(id)`; `bbtb audit` re-hashes them. Derived files record their parent id and hash (`derived/manifest.yaml`, `voice_refs/*.key`).
2. **Stable ids, not filenames.** Assets use path slugs (`images.sheets.…`, `audio.bad-billy.…`), characters use snake_case ids, cut-outs use `<char>_<variant>_<pose>`, shots `S01…`, lines `L<lineno>_<speaker>`.
3. **YAML for people, JSON for machines.** Hand-edited config is YAML (characters, cutlist, backgrounds, voices). Generated state is JSON/JSONL; generated YAML files carry a "GENERATED" header.
4. **Free by default; paid behind a code.**
   - Every paid path takes a `Ledger`, writes an `intent` row *before* the request, and never auto-retries.
   - A request that gets no response becomes `unknown` and blocks resubmission.
   - Approval codes are the first 8 hex characters of SHA-256 over the exact work: LTX jobs + budget; or TTS cache keys; or the test line hash.
5. **Stop, don't substitute.** Missing voices raise `VoicesNotReady`. Placeholders are explicit and never final. `is_final()` gates both LTX talking shots and QA.
6. **Plain-language errors.** Domain exceptions (`ScriptError`, `LtxError`, `ElevenLabsError`, `VoicesNotReady`, `MediaError`) carry user-facing messages. The CLI redacts secrets before printing.
7. **Secrets** are read only via `env.get`/`env.require`/`elevenlabs.api_key()` (both `ELEVENLABS_API_KEY` and `ELEVEN_LABS_API_KEY` are accepted). Never logged.
8. **Media via FFmpeg subprocess** (`media.py`, `assemble.py`, `animate.py` pipes raw RGB frames). Inputs are never overwritten; every step writes a new file.
9. **Art is only moved and scaled, never redrawn.** Cut-outs only remove background pixels. Busts paste the real head onto a real body. Mirroring is controlled per character (`mirror_ok`).
10. **Staging rules live in one place** (`shots.py`): one speaker per talking shot; placement from `facing`; expression-only tag means close-up; `local` tag means a free engine; narration rides on the next ACTION.
11. **Constants at module top** (prices, durations, framing fractions, loudness targets), with a source or date comment where they come from external docs.
12. **Testability:** HTTP clients accept an injected `session`; tests use fake sessions and temporary registries; no test touches the network or the originals.
13. **Two environments:** the app (`.venv`, Python 3.14) shells out to `.venv-voice` (Python 3.11) through `studio/voicetools/vt.py`, exchanging JSON over stdout. The app works without `.venv-voice`, minus the optional features.
14. **Frame defaults:** 24 fps, 9:16 at 720×1280 (1080×1920 optional). Faces and captions stay in the central 4:5 band.

---

## 9. Known issues worth fixing (found while documenting; not yet changed)

| # | Issue | Risk | Suggested fix |
|---|---|---|---|
| 1 | ~~Speech cache keyed by line id~~ **FIXED 2026-10-03**: ElevenLabs audio is now stored by content key in `audio/lines/_by_key/` | – | – |
| 2 | **LTX clips are reused if `shots/<id>/ltx.mp4` exists** (`Client.run`, `cost_table`, `render`) without checking the request hash. If shot numbers shift after an edit, an old clip could be shown, and counted as "already paid", for a different shot | Wrong clip in the final video; missed cost | Store each clip's request hash next to it (or name clips by hash) and reuse only on a match |
| 3 | `resume` calls `prepare()` without placeholders, so it stops at the voice stage if any line lacks final speech | `resume` unusable during `--only` tests | Let `resume` use the same placeholder rule as `--only` |
| 4 | `cli.py` help says `ltx forget <request_hash>`; the parser needs `<script> <request_hash>` | Confusing help | Fix the help text |
| 5 | Unused: `voice_page.py` (no caller), `tempfile` import in `cli.py`, `PRODUCTIONS` import in `pipeline.py` | Clutter | Remove, or wire `voice_page` to `voices test` output |
| 6 | `lines.json` stores absolute paths (YAML files store repo-relative ones) | Breaks if the folder moves | Store paths relative to the production folder |
| 7 | ~~Stale files~~ **CLEANED 2026-10-03** (see the cleanup table in section 2) | – | – |
| 9 | ElevenLabs music/SFX are estimated in **dollars** ($0.12 per SFX, about $0.15/min music: third-party figures), but on the Starter plan they actually use **credits**. Now that the key is found, the final run would buy ElevenLabs SFX instead of using the free synthesized ones | The estimate is mislabelled; credits spent on SFX that free synth already covers | Prefer free synth SFX by default (ElevenLabs SFX only on request), and show music/SFX in credits |
| 8 | ElevenLabs credit cost assumes 1 credit per character (the key lacks `models_read`) | Estimate may be off | Re-check once the key permissions are fixed (`voices account`) |
