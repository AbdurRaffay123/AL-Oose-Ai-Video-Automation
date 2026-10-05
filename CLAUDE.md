# AL-Oose Studio - rules for Claude

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
