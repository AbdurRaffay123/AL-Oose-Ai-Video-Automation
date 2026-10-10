# AL-Oose Studio - rules for Claude

**Follow docs/PRODUCTION_FLOW.md step by step. Never skip or reorder a step. Read it at the start of every session.**

Script -> finished Bad Billy the Bird video. Read docs/PROMPT.md (goal, status, plan) and README.md first; the workflow is the `/bbtb-make-video` skill.

**Default pipeline:**
recordings -> one-time ElevenLabs clone per character (`library/voices.yaml`) -> script -> `./bbtb voices render`
(approved) -> `./bbtb make` (free animatic + LTX cost) -> `./bbtb make --approve` (LTX) -> QA -> export.

## ElevenLabs credit rules (owner, 2026-10-03; enforced in code)
1. Never generate audio line by line: `voices render` sends ONE `/with-timestamps` request per character (lines joined with
   short break tags) and slices it by the returned timings. Saved batches are re-sliced, never re-bought.
2. One short test line per character (`voices test`). A second test needs the owner's explicit `--retest`.
3. Never use Chatterbox or macOS `say` for anything the owner hears. Previews without voices are SILENT placeholders.
4. Never auto-retry a failed ElevenLabs call: it is logged `unknown` and production stops (`voices forget` after the
   owner checks ElevenLabs > History).
5. The owner listens to the test line and runs/authorises `voices approve` before a voice is used in any render.
Voice status lives in `library/voices.yaml`. Do not clone young_saul, narrator, big_pea or snail unless the owner says so
in the current session (Saul has only 2.3 s of audio: warn first).

## Never
- Modify, move or rename anything in `Al-Oose-content/` (originals; SHA-256 in `library/assets.yaml`). Run `./bbtb audit` if in doubt.
- Spend money or credits without the owner's approval code. Paid steps:
  - `voices render --approve` and `voices test --approve` (ElevenLabs credits);
  - `make --approve` (LTX).
  Codes come only from the free run; never compute, guess or reuse one.
- Clone a voice (`voices clone ... --confirm-rights`) or approve one (`voices approve ...`) unless the owner has explicitly confirmed, in this conversation, that the project holds the rights and the performer's consent, and (for approve) that they have listened to the result.
- Re-clone a character that already has a voice ID (the tool reuses it); never create clones while testing.
- Substitute voices: no macOS placeholder (except the explicit `--placeholder-voices` preview), no borrowing another character's voice, no picking a narrator voice yourself. If a voice is missing, stop and report it.
- Retry a paid request automatically, or "forget" a ledger row without the owner confirming it in the provider's console/history.
- Print, log or commit API keys (`.env` is git-ignored; read keys via `bbtb.env` / `bbtb.elevenlabs.api_key`).
- Mirror Bad Billy (monocle must stay on his LEFT eye) or redraw a character. Art comes only from `library/derived/cutouts/` (built from the sheets).
- Present new or shortened lines as book text. Tag every line `canon:p<N>`, `adapted:p<N>` or `production`.

## Always
- Use an original voice clip when a line matches it exactly (automatic in `voices.py`).
- One speaker per talking shot. No text inside AI shots (captions are overlaid locally).
- Prefer `local` shots (free) for simple moves; use LTX only where it clearly adds value. Keep within the script's `budget:`.
- Keep the 4:5 safe area (the middle 70% of a 9:16 frame) for faces and captions.
- After changing code: `PYTHONPATH=studio .venv/bin/python -m pytest studio/tests -q` (offline; no API calls).

## Grounding (owner, 2026-10-06)
GROUNDING RULE (owner, repeated 5+ times): every standing character's feet must sit on the flat walkable ground defined in ground_zones.yaml. Never on rims, ledges, edges, leaves or dark areas. Pre-flight blocks any keyframe that fails. Check the FEET panel on every approval card before approving.
`library/backgrounds/ground_zones.yaml`; overlays `./bbtb grounds`; tags `pos:`/`endpos:` (`x/top/height[/air]`).

## Moving video, voices, whole-animatic review (owner, 2026-10-07)
- **Every shot is real moving video.** Art-animated cut-outs are only allowed for text overlays and the end card
  background, never for a character on screen.
- **Every story beat has a voice or a strong sound.** A character who reacts says something.
- **Review the WHOLE animatic with sound** before calling any piece done, not just each clip.

## Location continuity (owner, 2026-10-06)
LOCATION CONTINUITY: consecutive shots set in the same place use the same background plate (or plates showing the same landmark from the same side). A character who arrives somewhere stays there in the next shots. Show a continuity board before approval.

## Quality first (owner, 2026-10-06)
Do not mention cost savings or reusability unless the owner asks. Focus on quality. The best shot is always the right shot.
Cost is secondary: never sacrifice quality to save money (the approval-code and spend rules above still apply).

## Jason's two top complaints: never ship them again (owner, 2026-10-06)
Details: `docs/CHARACTER_BIBLE.md`, `docs/LESSONS_LEARNED.md`.
1. **White under Billy's chin** (sheet white trapped inside the right moustache curl). Every cut-out must pass the
   red-background test (`./bbtb cutouts`) before any generation; pre-flight blocks it otherwise. White already baked
   into a paid clip is removed for free at render time (`productions/<ep>/clip_fixes.yaml`), never by regenerating.
2. **Saul's eyes shrinking or his face flattening.** Every Saul prompt includes `{identity_young_saul}`, every Saul shot
   uses the `saul_eyes` negative set, and his references lead with a large face close-up (`./bbtb preprod` blocks
   the shot otherwise).
3. **Talking Saul drifts on every Kling model** (owner, 2026-10-06, after testing): Turbo is worst (EP002 S01: droopy
   eyes ~5 s; pre-flight FAILS Turbo/Wan for Saul), Standard is worse than Avatar (37% droopy frames even with references
   and `saul_eyes`), Avatar is currently the least bad (EP003 S05: one 0.5 s squint). Silent Saul shots hold well on
   Kling 3.0 Standard + references. Never fake a talking Saul by enlarging the small sheet faces (rejected: blurry). The
   real fix needs high-resolution Saul expression art from Jason.

## Kling 3.0 Turbo: permanently retired (owner, 2026-10-10)
Never use Kling 3.0 Turbo (`kling3` talking tag / `fal-ai/kling-video/v3/turbo/...`) for any new shot. Record: 3 of 8
generations rejected (38%), wings turned into fists, Saul's eyes drooped ~5 s (EP002 S01), and its re-voice step garbled
lines (EP001 S08). Talking shots: Kling AI Avatar. Action: Kling 3.0 Standard (+ references, negative, end frame).
Existing Turbo clips (EP001 S04/S08/S09, EP002 S01/S06) may still be reused or fixed for free.

## Paid-request discipline (owner, 2026-10-06)
- Tell the video model everything: the exact moves in order, tied to the words; the official look; the negatives; the
  start and end frames. Never rely on the AI to guess. Re-read prompt + negative together for contradictions.
- Don't regenerate to fix a background flaw: a retake changes the performance (EP003 S01 needed two retakes and
  never matched). Fix it for free at render time.
- Run `./bbtb audit` after every change; all tests must pass before any generation; report the balance (or the
  ledger spend, when the key can't read it) after every paid call.

## Production rules from EP004 on (owner, 2026-10-06)
- **Before proposing ANY concept**, read `docs/IDEAS_LOG.md` (every concept and why it was rejected),
  `docs/JASON_VIDEOS.md` (what Jason already animated: never recreate it) and `docs/STORY_MAP.md` (the whole book and
  our coverage). Log every new, approved or rejected idea in `docs/IDEAS_LOG.md`.
- **Asset audit first:** check `library/clips/CLIP_INVENTORY.md` before writing a script; reuse existing clips
  (`reuse:<CLIP_ID>`, free) wherever one fits. Target: at least 2–3 reused clips per episode.
- **No static images:** every shot moves. Narrator holds with a character render as layered parallax; a still with no
  character is NO-GO in `bbtb preprod`. Never a flat zoom into a still.
- **No clip is assembled without the owner's frame review:** after generation, `reviews/<shot>_frames.jpg` (every
  0.5 s) is shown to the owner; the final is blocked until `./bbtb approve-clip <script> <shots>` records the owner's
  approval of that exact take (`--auto-approve` is for tests only).
- **End cards are dynamic** (the static YES/NO tease card is rejected).

## One shot = one approval = one generation (owner, 2026-10-06, MANDATORY)
Before sending ANY shot to Kling, show the owner for THAT shot: the keyframe(s) being sent (start/end), every
reference image (@Element1, @Element2 …), the background plate, the full prompt word for word, the negative prompt word
for word (or "none" for Avatar), the exact cost and the engine. The approval card is
`productions/<ep>/reviews/approval/<shot>_approval.jpg`. The owner types "approved" for that one shot; only then run
`./bbtb make <script> --only <SHOT> --approve <CODE>`. Never batch-approve several shots.
