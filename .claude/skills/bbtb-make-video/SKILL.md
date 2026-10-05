---
name: bbtb-make-video
description: Turn a Bad Billy the Bird script into a finished video (voices, LTX animation, music, captions). Use when the owner gives or asks for a script, a new episode, a retake of a shot, or wants to know a production's status/cost.
disable-model-invocation: true
argument-hint: "[path/to/script.md or idea]"
---

# Make a Bad Billy video

Follow CLAUDE.md rules. Everything runs through `./bbtb` from the repo root.

## 1. Script
- If the owner gave an idea instead of a script, draft `productions/<slug>/script.md` in the format in
  [script-format.md](reference/script-format.md). Book text = canon. Mark new lines `<!-- PRODUCTION -->`.
  Show the draft and wait for the owner's OK.
- Only use characters, variants, poses and expressions listed in `library/characters/*.yaml`, and scenes in `library/backgrounds.yaml`.

## 2. Voices (ElevenLabs)
- `./bbtb voices status`. Every speaking character in the script needs a saved voice ID. Big Guy has no dialogue.
- A character with no voice: report it, and ask the owner to confirm rights/consent before running
  `./bbtb voices clone <char> --confirm-rights` (once ever). For the narrator, ask the owner which voice to use:
  `voices set narrator <voice_id>`, or clone the marketing narrator with rights confirmed. Never choose one yourself.
- `./bbtb voices render <script>`: show the owner the lines, characters and credits, and wait for their approval code.
- After generation, ask the owner to listen. Only they run or authorise `./bbtb voices approve <char> --confirm-rights`.

## 3. Free run
`./bbtb make productions/<slug>/script.md`
- If it errors, fix the script (the message names the line) and re-run.
- Show the owner the cost table, the approval code, and the animatic path
  `productions/<slug>/preview/animatic.mp4`. Ask them to watch it.
- If it stops at the voice stage, go back to step 2. Don't use `--placeholder-voices` except for a preview
  the owner asked for (those voices are never final).
- Report the **Voices** table. Lines are FINAL only if original, or from a voice the owner has approved.

## 4. Generate (spends money)
Only after the owner replies with the approval code themselves (generation refuses to start while any
selected talking shot has a non-final voice):
`./bbtb make productions/<slug>/script.md --approve <CODE>`
Never invent, reuse or compute a code. Never re-run on failure without telling the owner what failed.

## 5. Review
Read `productions/<slug>/reviews/qa.md`, then look at `reviews/frames.jpg`. Report to the owner:
- the verdict and any FAIL/WARN lines;
- which shots look off-model;
- the export paths.

For a retake, change only that shot's script line, then go back to step 2. Finished shots are reused, so only the change costs money.

## If something is pending or unclear
- `./bbtb status <script>` shows where the production is and the next action.
- `./bbtb resume <script>` re-checks submitted LTX jobs and never resubmits.
- For a ledger row in state `unknown`, ask the owner to check the LTX console before anything else.

Details: [ltx-api.md](reference/ltx-api.md) · [voice.md](reference/voice.md) · [script-format.md](reference/script-format.md)
