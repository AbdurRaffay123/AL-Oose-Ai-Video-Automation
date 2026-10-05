# Background inventory

21 backgrounds in `library/backgrounds.yaml`: 16 rated ⭐⭐⭐ and 5 rated ⭐⭐.
- **Visual check:** `INVENTORY.jpg` shows every background as the pipeline frames it at 9:16.
- **Rebuild:** `./bbtb plates` rebuilds all cropped plates from the originals, for free (crop only, never painted).
- **Book plates:** cut from the painting embedded in each page of `Book/BAD BILLY THE BIRD-story.pdf` (300 ppi, art only:
  the verse is a separate text layer, so it never appears).

**Ratings**
- ⭐⭐⭐ clean, no characters, ready to use.
- ⭐⭐ tiny far-away figures (or a crew on an airship), usable with care.
- ⭐ characters painted in, not extracted.

| Filename | Scene | Source | Characters in it? | Usable as-is? | Scene types | Rating |
|---|---|---|---|---|---|---|
| `BIG_WORM_HOLE` | rocks, hatch, waterfall (book pp.29-31) | big-worm-hole | No | Yes | rocks, tension, conversation | ⭐⭐⭐ |
| `STUMP_GRASS` | flowers + stump with ladder (pp.17-22) | stump-grass | No | Yes | meadow, conversation, happy | ⭐⭐⭐ |
| `STUMP_SIGN` | stump + 'Look UP in the tree' sign, portrait | bg | No | Yes | meadow, conversation | ⭐⭐⭐ |
| `FLOATING_TREE` | floating island, windmill | tree-bg-sky | Tiny / far | Yes, with care | flying, sky, island | ⭐⭐ |
| `TUNNELS` | underground cross-section, tall | grass-n-dirt | No | Yes | underground | ⭐⭐⭐ |
| `SKY_CLOUDS` |  | sky-cloudfs | No | Yes | flying, sky | ⭐⭐⭐ |
| `SKY_CLEAR` |  | sky-no-clouds | No | Yes | flying, sky | ⭐⭐⭐ |
| `GRASS_STUMP` | stump + ladder, two-shot / establishing (pp.17-22) | stump-grass | No | Yes | conversation, meadow, happy | ⭐⭐⭐ |
| `GRASS_FLOWERS` | big smiling flowers: Billy's reverse angle | stump-grass | No | Yes | conversation, meadow, happy | ⭐⭐⭐ |
| `GRASS_SIGN` | 'Look UP in the tree' sign + stump + pink sky: Saul's side (Avatar only: the sign has text) | bg | No | Yes | conversation, meadow | ⭐⭐⭐ |
| `FLOATING_ISLAND` | printed-book pp.22-23 spread, right half: floating tree island + windmill (characters are outside the crop) | bad-billy-jumping-off-with-saul | Tiny / far | Yes, with care | flying, sky, island | ⭐⭐ |
| `SKY_SHIP` | printed-book p.7 spread, left: rainbows, floating islands, airship (characters are outside the crop) | sky-and-fly-2 | Tiny / far | Yes, with care | flying, sky, happy, opening | ⭐⭐ |
| `BG_SKY_RAINBOW` | p.6: pastel sky, rainbows, floating islets (the airship with its tiny crew is below the window; Billy and Big Pea are on p.7) | book p.6 | No | Yes | flying, sky, happy, opening | ⭐⭐⭐ |
| `BG_FLOATING_TREE_ISLAND` | p.8: floating tree island with windmill; two tiny figures on the island edge (the inset panel is outside the window) | book p.8 | Tiny / far | Yes, with care | flying, sky, island | ⭐⭐ |
| `BG_OAK_TREEHOUSE` | p.12: the big oak with the treehouse, pink sky (owls above and worms below the window) | book p.12 | No | Yes | tree, conversation, happy | ⭐⭐⭐ |
| `BG_MEADOW_SIGN_FLOWERS` | p.17: smiling flowers + 'Look UP in the tree' sign (painted lettering is canon) over the meadow | book p.17 | No | Yes | conversation, meadow, happy | ⭐⭐⭐ |
| `BG_ISLAND_WINDMILL_SKY` | p.23: floating island underside, windmill, lilac clouds (OH WOW, Billy and the tiny worms on the island top are above the window) | book p.23 | No | Yes | flying, sky, island | ⭐⭐⭐ |
| `BG_SKY_CASTLE` | p.24: rock-pillar castle with crane and wrecked ship in the clouds (the flying birds are outside the window) | book p.24 | No | Yes | flying, sky, adventure | ⭐⭐⭐ |
| `BG_SKY_ISLAND_AIRSHIP` | p.26: blue sky, island underside with pipes, airship (tiny worms on the airship deck; the birds on top of the island are above the window) | book p.26 | Tiny / far | Yes, with care | flying, sky, adventure | ⭐⭐ |
| `BG_CAVE_STUDY` | p.36: underground study, bookshelves, desk, lamp (the worm at the desk and THE END are outside) | book p.36 | No | Yes | underground, home, tension | ⭐⭐⭐ |
| `BG_CAVE_TUNNEL` | p.37: cave floor, blank signpost, glass tube, mine cart (THE END lettering and the publisher logo are above) | book p.37 | No | Yes | underground, tension, ending | ⭐⭐⭐ |

## Scene type → backgrounds (automatic matching)
In a script, `## SCENE <TYPE>` (or `type:<type>`) picks the best-rated background of that type, never the same one
as the previous shot. An exact name, e.g. `## SCENE GRASS_FLOWERS`, is always used as written.

| Scene type | Use for | Backgrounds |
|---|---|---|
| `conversation` | Dialogue, shot/reverse-shot | GRASS_STUMP, GRASS_FLOWERS, GRASS_SIGN, STUMP_GRASS, STUMP_SIGN, BG_MEADOW_SIGN_FLOWERS, BG_OAK_TREEHOUSE, BIG_WORM_HOLE |
| `flying` / `sky` | Flight, travel | BG_SKY_RAINBOW, BG_ISLAND_WINDMILL_SKY, BG_SKY_CASTLE, BG_SKY_ISLAND_AIRSHIP, BG_FLOATING_TREE_ISLAND, SKY_SHIP, FLOATING_ISLAND, SKY_CLOUDS, SKY_CLEAR |
| `underground` | Worm homes, tunnels | BG_CAVE_STUDY, BG_CAVE_TUNNEL, TUNNELS |
| `opening` | Book opening, title | BG_SKY_RAINBOW, SKY_SHIP (also the marketing title video, see the EP002 end card) |
| `tension` | Danger | BIG_WORM_HOLE, BG_CAVE_TUNNEL, BG_CAVE_STUDY |
| `happy` / `meadow` | Bright, fun | GRASS_FLOWERS, BG_MEADOW_SIGN_FLOWERS, GRASS_STUMP, STUMP_GRASS, BG_SKY_RAINBOW |
| `tree` | Treehouse life | BG_OAK_TREEHOUSE |
| `adventure` / `island` | Sky world | BG_SKY_CASTLE, BG_SKY_ISLAND_AIRSHIP, BG_ISLAND_WINDMILL_SKY, BG_FLOATING_TREE_ISLAND |
| `ending` | Last shot | BG_CAVE_TUNNEL |

## Every book page (6–37) and why it was or wasn't extracted
| Pages | Scene | Characters painted in | Result |
|---|---|---|---|
| 6–7 | Pastel sky, rainbows, airship | Billy and Big Pea on p.7 | p.6 → **BG_SKY_RAINBOW** ⭐⭐⭐ (the airship crew is below the window; SKY_SHIP keeps the airship) |
| 8 | Floating tree island, windmill | Inset panel, two tiny figures | **BG_FLOATING_TREE_ISLAND** ⭐⭐ |
| 9 | Meadow, periscope, "POP!" | Billy, Big Pea | ⭐ not extracted |
| 10 | Worm house interior, "DANGER" poster | Many worms | ⭐ not extracted (poster lettering too) |
| 11 | Inside the hollow tree, rope bridges | Worms on every level | ⭐ not extracted |
| 12 | Oak tree island with treehouse | Worms at the foot, owls in the canopy | **BG_OAK_TREEHOUSE** ⭐⭐⭐ (window between them) |
| 13, 16 | Big tree with owls, treehouse | Owls, Billy, "LUNCH" / "CHA HOO" | ⭐ not extracted |
| 14 | Tree trunk, snail | Snail, worms, "WATCH OUT!!!!" | ⭐ not extracted |
| 15, 17–21 | The stump meadow: flowers, sign, stump | Billy, worms, Saul | p.17 → **BG_MEADOW_SIGN_FLOWERS** ⭐⭐⭐. The others are the same place, already covered by GRASS_* / STUMP_* |
| 22 | Cliff edge, stump, sign | Billy, Saul, numbers | ⭐ (same place as FLOATING_ISLAND's spread) |
| 23 | Floating island, windmill | "OH WOW", Billy, tiny worms | **BG_ISLAND_WINDMILL_SKY** ⭐⭐⭐ (the lower half) |
| 24 | Sky castle, wrecked ship | Flying birds | **BG_SKY_CASTLE** ⭐⭐⭐ (left part) |
| 25 | Blue sky, rainbow | Billy, Saul, "PREPARE FOR LANDING" | ⭐ not extracted |
| 26–27 | Blue sky, island, airship, cutaway | Birds, Billy, "THUD!" | p.26 → **BG_SKY_ISLAND_AIRSHIP** ⭐⭐ (tiny crew on the airship) |
| 28 | Rocks above, juice bar underground | Billy, Saul, worms | ⭐ not extracted |
| 29 | Rocks, scroll, hatch | Billy, Saul, arrows | ⭐ (same place as BIG_WORM_HOLE) |
| 30–35 | The Big Guy's eruption and "Big Guy Country" | The Big Guy fills the page | ⭐ not extracted |
| 36–37 | Underground study, cave, signpost | Worm at the desk, "THE END" | **BG_CAVE_STUDY** ⭐⭐⭐ (p.36) and **BG_CAVE_TUNNEL** ⭐⭐⭐ (p.37) |

**Not in the book:** a bedroom, an underground classroom, or a book-opening page. These would need new art (or a
paid generation the owner approves). The closest stand-ins are BG_CAVE_STUDY (an indoor, homely underground room)
and BG_SKY_RAINBOW or the title video for an opening.

**No painted-in character was removed.** That would need AI inpainting, which is generation. Each book plate is a
window between the painted characters, chosen on a measured grid, recorded in `backgrounds.yaml` and checked by eye.
