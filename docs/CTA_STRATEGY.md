# End-card / CTA strategy (owner, 2026-10-05)

**Goal:** build an **audience first**, then sell the book to a warm audience. People must trust and enjoy the channel
before they are asked to buy. A sales pitch on every episode trains viewers to scroll past the ending.

## Rotation
| Episode | CTA type | End card | Status |
|---|---|---|---|
| EP001 The Scroll and The Big Guy | Book | "What happens next? Find out in Bad Billy the Bird!" | done ✅ |
| EP002 The Deal | Book | Title video + "What did Saul do to Bad Billy? Find out in Bad Billy the Bird — link in bio!" | done ✅ |
| EP003 Rule Number One | **Engagement / cliffhanger** | Billy's face + "Uh oh... Did Saul forget Rule Number One?!" + on screen "YES or NO? Comment below!" | in production |
| EP004 | Engagement bait | A question with a one-word answer ("Comment below!") | planned |
| EP005 | Follow hook | "Follow for part 2" (a two-part story) | planned |
| EP006 | Book | Rotate back to the book CTA (title video) | planned |
| EP007 | Humour punch | No words: a funny final image + a short on-screen joke | planned |
| EP008 | Engagement bait | Question / poll | planned |

## Rules
1. **Never use the book CTA in two episodes in a row.** EP001 and EP002 already did; the next book CTA is EP006.
2. **Alternate between curiosity, engagement and sales.** At most 1 sales ending in every 3 episodes.
3. **Cliffhanger episodes NEVER end with a sales pitch.** The open question is the hook; selling over it breaks it.
4. **Engagement questions must have an easy answer:** YES/NO, a name or an emoji. Kids and parents both answer.
5. **Never contradict the story** (e.g. "Bad Billy 1, Worms 0" when nobody was eaten), and never spoil the next episode.
6. **On-screen text is short** (two lines at most), inside the 4:5 safe area, and drawn locally, never by the AI.
7. **The spoken CTA is a narrator line** (ElevenLabs credits). A purely visual CTA (on-screen text only, `silent` or `show:`)
   is free to change after the voices are rendered.

## How to build each type (script syntax)
- **Engagement / cliffhanger:** `NARRATOR [production, card:tease, show:YES or NO? | Comment below!, secs:6]: <question>`
  shows Billy's official face over the blurred last scene. `|` is a line break in the on-screen text.
- **Book:** `NARRATOR [production, card:title, show:Link in bio 🐛, secs:8]: <line>` uses the BBTB title video, video only.
- **Humour punch:** `NARRATOR [production, card:tease, silent, secs:4]: <on-screen joke>` has no narrator and costs no credits.
- **Follow hook:** as an engagement card, with "Follow for part 2" on screen.
