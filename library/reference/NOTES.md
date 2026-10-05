# Reference clips: what makes them look natural

The owner's own clips live in `Al-Oose-content/CONTENT/BBTB MARKETING/Video/`. They are originals: read only, never copied or moved.
- **Analyse a clip** (free): `./bbtb refs analyze <video or folder>`.
- **Output:** a contact sheet (4 frames per second) and `stats.json` (camera motion, motion level, cuts) in `library/reference/<name>/`.
- **New references:** drop them anywhere outside `Al-Oose-content/` (e.g. `library/reference/inbox/`) and run the same command.

## Findings (2026-10-03, from the contact sheets)

| Clip | Source | What works | What fails |
|---|---|---|---|
| `5. HELP WORM FILE.mp4` | Kling (edited) | The worm crawls with a **dust cloud**, sits up, waves; the **mouth opens wide** and changes shape constantly. Wide action shot, then a **close-up** for talking. Arms gesture all the time. | Nothing major; this is the target look. |
| `BILLY landing FUNny.mp4` | Kling | The landing **smoke cloud** and settle are lively; once still, Billy's pose is on-model. | **Fast motion smears Billy**: hat, face and body melt for about 1 s. Fast moves need short shots or a softer action. |
| `SNAIL - kling_...mp4` | Kling 3.0 (web, has audio) | Small, believable idle moves; eyes blink. | **"KlingAI 3.0" watermark** (web app). Mouth movement is subtle. |
| `2. If there was a bird.mp4` | Cut-out (paper-puppet) | n/a | Billy is a flat sticker sliding around (white outline). This is the "floating / flipbook" look the owner rejected. |

## Patterns to copy
1. **One clear physical action per shot**, with contact and reaction: dust where feet or the body hit the ground, a settle after stopping.
2. **Talking = a closer shot plus big mouth shapes plus gestures.** The mouth opens wide and the hands/wings never stop moving.
3. **Static camera** in almost every Kling clip; the life comes from the character and small background motion.
4. **Keep fast moves short (≤ 1 s) or slow them down.** Kling smears Billy's detailed design at speed.
5. **The API has no watermark** (the web app adds one), so generate through fal, not the Kling website.
