# Production flow: the single, mandatory order for every episode

**Follow it step by step. Never skip or reorder a step. Read this file at the start of every session.**
(Owner, 2026-10-06, after the 5th "floating character" report and a rejected paid take.)

| # | Step | What happens | Gate |
|---|---|---|---|
| 1 | **Read the docs first** | `docs/STORY_MAP.md`, `docs/JASON_VIDEOS.md`, `docs/IDEAS_LOG.md`, `docs/CHARACTER_BIBLE.md`, `docs/LESSONS_LEARNED.md`, this file | – |
| 2 | **Concept** | One paragraph: the story moment, who, where, hook, ending. Never re-propose what Jason already made or what was rejected (`IDEAS_LOG.md`) | Owner approves |
| 3 | **Storyboard** | Who is WHERE in every shot: height (tree top / ground), side of frame, and **which ground they stand on** | Owner approves |
| 4 | **Script** | Every line, shot, background, engine; line tags `canon:` / `adapted:` / `production` | Owner approves |
| 5 | **Voices first** | Render all dialogue and narration (`./bbtb voices render`, ElevenLabs approval code). Voice timing sets every shot's length, so **no video is generated before its voice exists** | Owner approves the code |
| 6 | **Keyframes and backgrounds (free)** | Build them, then check: red test (no white under Billy's chin or anywhere), **GROUNDING** (feet on the flat walkable ground of `library/backgrounds/ground_zones.yaml`), **LOCATION CONTINUITY** (rule below; continuity board `reviews/CONTINUITY_BOARD.jpg`), spatial geography, facing, no text or lettering in AI shots | Pre-flight: any FAIL blocks |
| 7 | **Approval card per paid shot** | `productions/<ep>/reviews/approval/<shot>_approval.jpg`: start frame, end frame, background, references, **FEET / GROUND zoom panel**, full prompt, negative prompt, engine, cost | Owner approves EACH card individually |
| 8 | **Generate ONE shot** | Free run for that shot's code, confirm the request equals the approved card, generate, show its frame sheet (`reviews/<shot>_frames.jpg`) | Owner approves or rejects; only then the next shot |
| 9 | **Full animatic WITH SOUND** | Overlays and cards only (no art-animated characters); the owner watches the whole animatic as a video with sound, plus a 1 fps strip | Owner approves |
| 10 | **Assemble the final, run QA: TWO versions** | `./bbtb export` = WITH music (`_FINAL_<fmt>.mp4`: our internal review only); then `./bbtb export --no-music` = WITHOUT music (`_FINAL_<fmt>_nomusic.mp4`: voices + SFX, the version delivered to Jason, who adds BG music last in his own edit). The owner watches both | Owner approves |
| 11 | **Update the records** | `docs/EPISODE_LOG.md`, `docs/LESSONS_LEARNED.md`, `docs/SESSION_BRIEF.md`, `docs/IDEAS_LOG.md` | – |

## Hard rules (each one repeated by the owner)
- **Every shot is real moving video.** Art-animated cut-outs are only allowed for text overlays and the end card
  background, never for a character on screen.
- **Every story beat has a voice or a strong sound.** A character who reacts says something.
- **Review the WHOLE animatic with sound** before calling any piece done, not just each clip.
- **Voices before video, always.**
- **Every export comes in two versions** (Jason, 2026-10-10): WITH music for our internal review; WITHOUT music
  (voices + SFX only, `--no-music`) for delivery to Jason. Never deliver the music version.
- **Feet on the ground in every keyframe** (GROUNDING RULE below).
- **Show prompts and references BEFORE any generation.**
- **One approval = one generation.** Never batch-approve.
- **Quality first; cost is secondary.**
- **No worms, text or lettering in AI shots.** Worms are Jason's art, animated locally.
- **Location continuity:** same place = same plate (same landmark, same side); a character who arrives stays there.
- **Spatial geography:** establish where each character is; never two characters in the same screen position in
  consecutive shots unless they are physically together.
- **Billy:** wings never hands, monocle on the LEFT eye only, no white under the chin, never mirrored, never hatless.
- **Saul:** big round eyes in every frame.

## LOCATION CONTINUITY (owner, 2026-10-06)
LOCATION CONTINUITY: consecutive shots set in the same place use the same background plate (or plates showing the same landmark from the same side). A character who arrives somewhere stays there in the next shots. Show a continuity board before approval.

EP004 example: the worms play, scatter and get eaten, Billy lands and burps, all at ONE spot (GRASS_STUMP, flat grass
behind the stump, Billy at x 0.60 / soles y 0.66, same scale); the Snail watches from the flower bush nearby
(GRASS_FLOWERS). Before the fix the ground shots jumped between GRASS_SIGN, GRASS_STUMP and GRASS_FLOWERS.

## GROUNDING RULE (owner, repeated 5+ times)
Every standing character's feet must sit on the flat walkable ground defined in
`library/backgrounds/ground_zones.yaml`. Never on rims, ledges, edges, leaves or dark areas. Pre-flight blocks any
keyframe that fails. Check the FEET panel on every approval card before approving.

**How the tool enforces it:**
- `library/backgrounds/ground_zones.yaml`: per plate, `ground` (green) and `forbidden` (red) polygons.
  `./bbtb grounds` draws them on every plate (`library/backgrounds/ground_overlays/`).
- **Pre-flight `grounding` check** (start AND end frame, every character). It finds the soles (the lowest opaque
  pixels of the cut-out) and FAILs when they are:
  - outside the ground;
  - over a forbidden area;
  - cut off by the frame;
  - on a surface darker than, or a different colour from, the ground around them.
- **Exemptions:** only poses the script tags airborne (`pos:x/top/height/air`) and close-up busts.
- **Exact placement:** `pos:` / `endpos:` place the start and end frames. Every standing character gets a soft
  contact shadow under its soles.
- **Choosing a plate:** a plate whose foreground is a stump, rocks or leaves (for example `GRASS_SIGN_LOW`,
  `BG_MEADOW_SIGN_FLOWERS`) has no flat ground for a full-size standing character. Pick a plate with open flat
  ground (`GRASS_FLOWERS`, `GRASS_STUMP`).
