# Ideas and decisions log: made, approved, discarded

One place for every episode idea and what happened to it, so nothing is re-proposed or re-researched.
**Before proposing a concept, read:**
1. this file;
2. `docs/JASON_VIDEOS.md` (what Jason already animated);
3. `docs/STORY_MAP.md` (the whole book, page by page, and our coverage).

Detail lives elsewhere:
- `docs/EPISODE_LOG.md`: what was generated, spent and fixed per episode.
- `library/clips/CLIP_INVENTORY.md`: every paid clip we own, with descriptions and reuse ratings.
- `docs/LESSONS_LEARNED.md` and `docs/DECISIONS.md`: technical lessons.

## Episodes made (released)
The series runs **backwards** through the book: each episode is the prequel of the one before.

| Episode | Book pages | Story | Final | Ending |
|---|---|---|---|---|
| EP001 The Scroll and The Big Guy | 28–31 | Billy reads Saul's scroll, The Big Guy erupts, "Oh POOP!" | `productions/ep001-big-guy/exports/` | Book CTA |
| EP002 The Deal | 19–23 | Saul stands tall, pitches The Big Guy, "Oh wow!" | 35.2 s | Title video + book CTA (version D) |
| EP003 Rule Number One | 16–18 (+ p.12 Rule line) | Billy hungry again, Saul pops out, Billy leaps | 36.5 s, ~7.8/10 | Tease card YES/NO (owner later called it too static) |

## EP004: concept history (all 2026-10-06)
| # | Concept | Pages | Status | Why |
|---|---|---|---|---|
| v1 | **"Swallowed!"**: The Big Guy erupts (reused EP001 clips), Billy flees, GULP | 31–34 | **Rejected** | Owner: Big Guy clips look static and bad; no Big Guy |
| v2 | **"Sneaking Out"**: Saul sneaks out of class, slides up the tunnels, pops out; Billy watches; reused EP003 clips | 10–14 | **Rejected** | Too similar to EP003: same characters, locations, stump, clips |
| ideas | Owner's fresh ideas: **A** "The Classroom" (pp.10–11, worm school chaos), **B** "Big Pea's Warning" (two villains arguing), **C** "The Snail" (slow-motion comedy), **D** "Sky Adventure" (pp.23–26, Billy in the sky castle) | – | B + C were combined into v3 | – |
| v3 | **"Two Hungry Villains"**: Big Pea's evil laugh in a dark cave, the search, "You are very annoying", the Snail shoos them, VS-poll end card | 7–9 | Approved, then **superseded** | Owner later rejected the cave plates: dark, characters float, study at the wrong scale. The book's pp.7–9 happen on a BRIGHT island meadow; the cave plates are from pp.36–37. S01 (Big Pea laugh, Avatar, $0.11) was generated, never approved; files in `productions/ep004/` |
| – | **Top 3 backgrounds** (quality-first directive): Worm Underworld cut-away (TUNNELS), Sky Castle (p.24), Smiling Meadow (p.17) | – | **Superseded** before the owner picked | Owner restarted from a full book read |
| v4 | **"WATCH OUT!" (pp.14–15 only)**: the Snail's warning, the worms panic, Billy dives, "One, two, three… FOUR!". Answers Jason's video-2 cliffhanger ("What do you think would happen next?"); pp.12–13 are NOT re-animated | 14–15 | **Direction approved by the owner** (2026-10-06); spatial storyboard + concept v4 written (`productions/ep004/CONCEPT.md`, `STORYBOARD_EXPLANATION.jpg`); owner said "understood" and chose C + speech bubble (no Snail clone) + GRASS_SIGN; **script v4 written** (`productions/ep004/script.md`); 4 approval cards + narrator code ready (`productions/ep004/APPROVAL_CARDS.md`), awaiting per-shot approval. v3 files archived in `productions/ep004/_v3_superseded/` | Owner: the eating and landing shots need PERFECTION; if AI isn't perfect, use a free book-art alternative. Mock-ups: `productions/ep004/reviews/v4/` |
| EP005 | **"Big Pea DOOF"**: Billy and Big Pea fly the rainbow sky, the DOOF landing, no worms, Big Pea storms off, periscope POP | 6–9 | **Planned** (after EP004) | Never animated by anyone; the landing needs the same perfection rule |

## Owner's perfection rule for key action shots (2026-10-06)
The eating scene (EP004) and the DOOF landing (EP005) must be perfect:
- multiple references;
- a frame-by-frame prompt;
- start AND end frames;
- a negative prompt blocking every known failure;
- the owner reviews every frame.

If the AI take isn't perfect, it is NOT used: a free book-art animation replaces it.

## Story moments never animated by anyone (as of 2026-10-06)
- **pp.6–9:** Billy and Big Pea fly the rainbow sky, the DOOF belly-flop landing, no worms, Big Pea storms off, the
  periscope POP. **Big Pea has never been animated** by Jason or us.
- **pp.10–11:** worm school; four worms sneak out and slide down the tree walkways (v2 used this; rejected for
  repetition, not for the beat itself).
- **pp.14–15:** the Snail's "WATCH OUT!!!!", the dive, the count to four. (Jason's video 2 ends on "What do you think
  would happen next?" right before it.)
- **pp.24–27:** the flight past the sky castle and the crash (our attempts were cut from EP002: they looked bad).
- **pp.32–35:** swallowed, Big Pea finds the scroll and shoes, The Big Guy's happy ending (Big Guy: owner says no).

## Discarded techniques (don't re-propose)
| Idea | Why it was dropped |
|---|---|
| Wan 2.7 for talking Billy | 5.8–6.0/10: energy OR stability, never both; hard cut back to the start pose at 4.6 s |
| Kling 3.0 Turbo for Saul | Worst eye drift (EP002 S01 droopy eyes ~5 s); pre-flight FAILS it |
| "Saul never on Avatar" rule | Reversed: the Standard retake was worse (37% droopy frames); Avatar is the least bad for talking Saul |
| Enlarging sheet faces for talking Saul | Rejected as blurry. The real fix: high-resolution Saul expression art from Jason |
| Kling without an end frame | Billy is redesigned within 0.5 s (EP002 S02 take 3) |
| Wing gestures on engines without a negative prompt | Wings turn into hands or fists |
| Regenerating to fix a background flaw | A retake changes the performance; fix it for free at render time |
| AI flight and crash shots (EP002 old S05/S07) | "Looks boring" / meltdown; cut |
| Hatless Billy (landing-sheet "Fall 1" frame) | Looks wrong; top-hat Billy never loses his hat |
| Static YES/NO tease card (EP003) | Too static; end cards must be dynamic |
| Narrator over a flat zoom into a still | Slideshow look; every shot must move (parallax at minimum) |
| Big Guy clips (EP001 S07) for new episodes | Owner: static and bad quality |
| Cave plates (BG_CAVE_TUNNEL, BG_CAVE_STUDY) for daytime story beats | Dark, characters float, wrong scale; they only fit the book's ending (pp.36–37) |
| Burned-in captions | Removed (`captions: off`) |
| Chatterbox or macOS `say` for anything the owner hears | Forbidden (CLAUDE.md) |
| Optimising for cost or clip reuse | Owner's quality-first directive, 2026-10-06 |
| Art-animated characters (bobbing cut-outs) on screen (EP004 animatic v2) | Read as a slideshow; owner rule: only overlays and the end-card background may be art-animated |
| A big fall in one 3 s Kling shot (EP004 S05 take 1) | Smeared, went upside down and face-planted into a dust cloud: the banned crash-landing (rejected 2026-10-06) |
| Showing the eating with art animation (EP004 count mock) | Beak closed in every frame, no expression change, a floating head for "4!": replaced by a Snail reaction cutaway |
| GRASS_SIGN_LOW for standing characters (EP004 S07 take) | Its foreground is all stump: feet ended on the rim ("floating"); take rejected 2026-10-06 |

## Facts that are easy to get wrong
- **Jason's landing sheet** (`billy_land`): Approach 1 and Approach 2 are almost identical; Approach 3 has an open beak.
  Use Approach 1 / Approach 4 / Touchdown as closed-beak references.
- **Big Pea** is Billy's chubby yellow bird buddy in an aviator cap and goggles, not a giant pea.
- **The whole "snail" image folder** (`images.characters.snail.*`, the sheet AND the four screenshots) is **Big Guy** art,
  misfiled. The only real Snail art is the book p.14 cut-out.
- **The only clean Snail art** is the book p.14 cut-out (`snail_side`). The Snail's original recordings: "Go on!
  Shooo, you silly birds!" and "Ah, these birds are big trouble makers, mun". He has no "WATCH OUT" recording and no
  clone.
- **The four naughty worms** (blue ball, orange bow, top hat and monocle, aviator cap) have official art:
  `images.scenes.worm-s-getting-eaten`. Saul is not one of them.
- **Old Wise Worm** (Jason's video 3) is a marketing character, not in the book.
- **Billy's edition:** the book PDF interior draws goggles Billy; the printed book (Jason's read-along) and our
  episodes use top-hat Billy.
- **Big Pea's original recordings:** evil laugh, "You are very annoying", "Why are you still here?", "Go away, stop
  following me". **Billy's:** "Go away, stop following us", "Arrrrr" growl, "I'll get you", screams in pain, "Silly
  little worm", "Who are you and what do you want?". **Saul's:** "I think we're gonna need your help", "I don't trust
  these birds".
