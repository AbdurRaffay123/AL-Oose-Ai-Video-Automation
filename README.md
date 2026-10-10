# AL-Oose Studio: script → finished Bad Billy video

You write a script. The studio turns it into a voiced, animated video. Characters keep their exact book design, their mouths move while they talk, and music and SFX play underneath.

```
recordings → one-time ElevenLabs clone → saved voice IDs → script.md → ElevenLabs speech (approved)
  → keyframes → local animation → [cost + approval code] → LTX shots → mix + captions → exports/*.mp4
```

| Step | What happens | Cost |
|---|---|---|
| Voices | Original recording if the line matches it exactly; otherwise the character's **saved ElevenLabs voice** (one permanent clone per character) | ElevenLabs credits, about 1 per character of text |
| Keyframes | Exact character cut-outs (from the reference sheets) placed on the book's background plates | free |
| Local shots (`local` tag) | Cut-out animation: hop-ins, pose changes, camera shake, idle bob, and a **mouth flap** that swaps matching open/closed heads in time with the voice | free |
| LTX talking shots | **LTX-2.3 Pro audio-to-video**: keyframe + the line's audio, so the mouth moves with the voice | $0.06/s (720p), $0.10/s (1080p) |
| LTX action shots | **LTX-2.3 Pro image-to-video**, silent, 6/8/10 s | $0.04/s (720p), $0.08/s (1080p) |
| Music / SFX | Your files in `library/audio/`, else ElevenLabs (approved run only). SFX fall back to free synthesized effects | free / ≈ $0.15 per min of music |
| Assembly | FFmpeg: our own voice track always replaces any AI audio; −14 LUFS; captions; 9:16 + 4:5 | free |

EP001 (≈ 45 s, 5 LTX shots) is estimated at about **$1.85 at 720p**.

## Setup (once)

```sh
brew install ffmpeg                        # 9.x; `ffprobe -version` must work
python3 -m venv .venv && .venv/bin/pip install Pillow numpy PyYAML requests pytest
cp .env.example .env                       # LTX_API_KEY, ELEVENLABS_API_KEY (ELEVEN_LABS_API_KEY also accepted)
./bbtb audit                               # confirms the 91 originals are untouched
```

The ElevenLabs key needs these permissions (ElevenLabs > Developers > API keys > edit): **Text to Speech, Voices
(read + write), User (read), Models (read)**. Without *User read* the tool can't check your remaining credits first.

Optional, free, local: `.venv-voice` (Python 3.11) with `chatterbox-tts openai-whisper resemblyzer demucs`. It provides
the same-speaker check in `voices assess`, transcription, vocal/music separation, and an optional local voice clone.

## Voices (one-time setup, then reused by every episode)

```sh
./bbtb voices status                       # recordings, verdict, voice ID, rights, approval per character
./bbtb voices assess                       # measures each clip: speech length, noise, clipping, same-speaker score
./bbtb voices account                      # plan, credits left, cloning allowed (free check)
./bbtb voices clone bad_billy --confirm-rights      # ONCE per character; reused while its recordings don't change
./bbtb voices set narrator <voice_id>              # or use a voice already in your ElevenLabs account
./bbtb voices verify                       # saved voice IDs still exist (free)
./bbtb voices test bad_billy "Silly little worm!"   # the ONE test line: shows credits, file path, code; add --approve CODE 💲
./bbtb voices approve bad_billy --confirm-rights   # after LISTENING to the test file: the voice becomes FINAL
./bbtb voices forget <request_hash> [--script S]   # clear an 'unknown' row after checking ElevenLabs > History
```

- **Registry:** `library/voices.yaml` stores, per character: provider, ElevenLabs voice ID, source files and their hash, settings, assessment, rights confirmation, and approval. Each character always uses its own ID. Cloning is skipped while the source audio hash is unchanged.
- **Script speech:** `./bbtb voices render <script>` estimates characters and credits, checks credits left, and gives an approval code.
  - With `--approve CODE` it sends **one request per character**: that character's new lines, joined with short `<break>` pauses, to `/with-timestamps`.
  - It **slices** the result by ElevenLabs' character timings into `productions/<ep>/audio/lines/`.
  - The full batch and its timings are kept in `audio/lines/_batches/`, so re-slicing never costs anything.
  - Folder layout by source (ElevenLabs / LTX / local / original): see `docs/STRUCTURE.md` section 2.
  - The cache is keyed by content (voice ID + model + settings + text), so renumbered or reordered lines are never paid for twice.
- **Credit rules:**
  - one test line per character;
  - any ElevenLabs failure is logged `unknown`, stops, and is never retried;
  - only voices approved after listening are used.
- **Original recordings win:** a line whose words match a recorded clip uses the original (e.g. "Silly little worm!").
- **Narration is separate:** if no narrator voice is configured, production stops and asks you; no character voice is borrowed.
- **No silent fallbacks:** if speech is missing or the API fails, `make` **stops at the voice stage** and says why.
  - `--placeholder-voices` gives a free timing preview with **silent** placeholders of estimated length. They are never final, QA fails them, and LTX is blocked.
- **Final means approved:** a cloned voice is used in exports and LTX shots only after `voices approve`. The LTX mouth is animated to that exact audio, so changing a voice later would mean paying for those shots again.
- **Characters with too little audio:**
  - Under 5 s of clean speech, `clone` refuses (override with `--allow-short`) and tells you what to record.
  - ElevenLabs advises about 60 s, so all current characters are below that and marked *limited*.
- **Tuning:** `./bbtb voices tune <char> --stability 0.4 --similarity 0.9 --style 0.4`. This resets approval, and changed lines regenerate.

## Make a video

1. Write `productions/<name>/script.md`. Copy `productions/ep001-big-guy/script.md` as a starting point.
2. **Voices:** `./bbtb voices render productions/<name>/script.md`, then repeat with `--approve CODE` 💲 (ElevenLabs credits).
3. **Free run:** `./bbtb make productions/<name>/script.md`
   - Prints the shot list, the exact cost, and an **approval code**.
   - Writes a free **animatic** (keyframes + voices + captions) to `productions/<name>/preview/`.
   - **Nothing is spent.**
4. Watch the animatic. Edit the script and re-run as often as you like; only changed lines cost voice credits.
5. **Generate:** `./bbtb make productions/<name>/script.md --approve CODE` 💲 (LTX)
   - Spends up to the shown amount, never more than `budget:`.
   - Writes `exports/<name>_vN_9x16.mp4` and `_4x5.mp4`.
   - Writes a QA report and a frame sheet to `reviews/`.
   - To test a few shots cheaply first, add `--only S04,S07`. Its approval code covers only those shots.
6. Check the QA report and the video. If a shot looks wrong, change its line in the script and run steps 2 and 4 again. Only the changed shots are paid for again; finished shots are reused.

### Making an episode (pipeline v3.0, from EP003)
1. **Script:** write `productions/<ep>/script.md` and get the owner's approval. Use header `elements: on`,
   `negatives: billy_hands,saul_body` and `shot_cap: 0.70`.
2. **Voices:** `./bbtb voices render <script>`, then the owner approves with the code.
3. **References:** write `productions/<ep>/references.yaml`, then run `./bbtb references <script>` (free).
4. **Prompt notes:** write `productions/<ep>/prompt_notes.yaml` (emotion, action, background, avoid, preserve).
5. **Quality sheet:** run `./bbtb preprod <script>` (free). Fix every **NO-GO** for free, then rerun.
6. **Generate:** `./bbtb make <script>` gives the free animatic and the approval code. The owner approves, then
   `./bbtb make <script> --approve CODE` runs the shots, lowest risk first.
7. **Review:** check every frame by eye (auto-QA is a helper, not the judge), then export.

### Script format

```markdown
# EP002 Title
format: 9:16   resolution: 720p   music: playful-adventure   budget: 10   captions: on

## SCENE STUMP_GRASS                 ← a background from library/backgrounds.yaml (or END_CARD)
ACTION [wide]: Bad Billy lands next to the stump.        ← image-to-video shot
BILLY [tophat, suspicious]: Who dares talk to me?        ← talking shot (close-up: expression tag)
SAUL [holding-scroll]: It is I, from down under the tree. ← talking shot (medium: pose tag)
NARRATOR: Billy leaned in close...                       ← voice-over on the next ACTION (or a hold)
SFX [at 2]: whoosh                                       ← sound at 2 s into the next shot
ACTION [wide, end: BIG GUY arms-up]: The Big Guy bursts out.  ← character appears by the last frame
```

**Tags**
- Character variant (`tophat`, `goggles`), a **pose**, or an **expression**, as listed in `library/characters/<id>.yaml`.
- A pose tag gives a medium full-body shot.
- An expression tag gives a close-up, built from that exact head art on a body.
- `local` makes a shot free cut-out animation instead of LTX.
  - Talking: mouth flap, available where open/closed heads exist (Billy's front and 3/4-right heads).
  - Action: add `enter-left`/`enter-right` (hop-in), `pose-a>pose-b` (pose change) and `shake`.
- **End-card moments** (scene `END_CARD`, narrator lines, free): `card:tease` = Billy's face (official head art) over
  the previous scene, with the line shown as a question; `card:book` = book cover + the line as the CTA (a sentence with
  "link in bio" becomes a yellow pill) + a Follow button with a tapping hand. `emoji:🐛` puts an emoji in the pill
  (on screen only, never spoken). Without a `card:` tag you get the classic title + cover end card.
- **Character references (EP003 on):** header `elements: on` plus `productions/<ep>/references.yaml`. Kling 3.0
  Standard (`kling3std` talking lines and action shots) then receives the official sheets as `@Element` reference
  images. Build them for free with `./bbtb references <script.md>`. Turbo (`kling3`) can't take references.
- **Finished episodes:** header `keyframes: locked` keeps the exact keyframes the paid clips were made from, so
  rebuilt cut-outs never orphan a clip.
- **Reuse (free):** `ACTION [reuse:EP001_S07, from:2.5]: …` plays a library clip under the narration;
  `BILLY [reuse:EP001_S08, canon:p31]: Oh POOP!` reuses a talking clip WITH its own approved line (same words required).
  See `library/clips/CLIP_INVENTORY.md`.
- **Owner frame review:** `./bbtb review <script>` writes `reviews/<shot>_frames.jpg` (every 0.5 s);
  `./bbtb approve-clip <script> S01,S04` records the owner's approval. The final can't be assembled before it.
- **Edit tags:** `cut:<s>` (use a clip up to <s>, then hold the end frame), `secs:<s>` (minimum length), `silent`
  (card text on screen only), `show:<text>` (card's on-screen text differs from the spoken line), `noend`
  (Kling 3.0 Standard talk without the end frame).
- **Source** of every line: `canon:p29` (the book's exact words), `adapted:p31` (the book's words, shortened) or `production` (new). Keep adaptations honest: never re-word a canon line.
- Anything else, such as `(whispering)`, becomes acting direction.

## Spending safety

- Nothing paid runs without the approval code. The code is a hash of the exact jobs and the budget, so any change needs a new code.
- `productions/<name>/ledger.jsonl` records every paid call **before** it is sent, so a shot is never paid for twice.
- If a submit gets no answer, it is marked `unknown` and never retried automatically. Check the LTX console. If the job isn't there, run `./bbtb ltx forget <script> <hash>`.
- `./bbtb status <script>` shows progress and the next step. `./bbtb resume <script>` re-checks submitted jobs without resubmitting.
- Plain-language stops:
  - out of credits (402)
  - safety filter (422)
  - queue full (429, wait and re-run)

## Where things are

| Path | What |
|---|---|
| `Al-Oose-content/` | **Originals: read-only.** Book PDF, art, voices, old videos |
| `library/assets.yaml` / `asset_notes.yaml` | Hash registry / provenance, misfiles, duplicates |
| `library/characters/*.yaml` | Character bible: variants, poses, expressions, facing, voices, identity prompts |
| `library/cutlist.yaml` → `library/derived/cutouts/` | How each cut-out is cut from a sheet (`./bbtb cutouts` rebuilds) |
| `library/backgrounds.yaml` | Scene names → background plates |
| `library/voices.yaml` | **Voice registry**: ElevenLabs voice ID per character, source hash, settings, rights, approval |
| `studio/bbtb/` | Code: `script_parser`, `shots` (staging rules), `voices`, `keyframes`, `ltx`, `assemble`, `audio_bed`, `qa`, `pipeline`, `cli` |
| `docs/PROMPT.md` | **Start here:** goal, approach, what is done, what is left, what the owner must provide |
| `docs/DECISIONS.md` | Owner decisions and known limitations |

## Troubleshooting

| Problem | Fix |
|---|---|
| `ffmpeg … Library not loaded` | `brew upgrade ffmpeg` |
| "unknown character" / "has no art yet" | Add aliases or poses in `library/characters/*.yaml` |
| "STOPPED at the voice stage" | Follow the listed step: clone or set the voice, or run `voices render` for the script |
| ElevenLabs "missing permission …" | Edit the API key's permissions in ElevenLabs (see Setup) |
| QA FAIL "voice that is not final" | Listen to the generated lines, then `./bbtb voices approve <char> --confirm-rights` (or record more audio) |
| "Not generating: … voices that are not final" | Approve the voices after listening, or use `--only` for shots whose voices are already final |
| A character drifts off-model in an LTX shot | Use a closer framing or simpler ACTION wording, then re-generate that shot (the old clip is kept in the ledger) |

Docs: [LTX API](https://docs.ltx.io) · [ElevenLabs API](https://elevenlabs.io/docs/api-reference) · [Claude Code skills](https://code.claude.com/docs/en/skills)
