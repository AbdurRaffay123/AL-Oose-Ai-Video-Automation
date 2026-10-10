# EP004 WATCH OUT!
format: 9:16   resolution: 720p   music: playful-adventure   budget: 3   captions: off   talking_engine: kling
action_engine: kling3   spend_cap: 3   session_cap: 3   shot_cap: 0.70   negatives: billy_hands   elements: on

<!-- Script v4, written 2026-10-06 for owner approval. Concept + storyboard approved ("understood"):          -->
<!-- productions/ep004/CONCEPT.md, STORYBOARD_EXPLANATION.jpg. Source: book pp.14-15 (pp.12-13 were animated  -->
<!-- by Jason, video 2: here they are only the 2.5 s establishing tilt). It answers Jason's video-2 question  -->
<!-- "What do you think would happen next?". Line tags: canon:<page> = the book's exact words.               -->
<!-- Owner decisions: Option C (Kling = Billy diving ALONE, no worms in any AI shot; the count = free book-art -->
<!-- animation); Snail NOT cloned (book-style "WATCH OUT!!!!" burst + alarm, silent mouth); worms on         -->
<!-- GRASS_SIGN (real grass floor). PERFECTION shots: S04a, S04b (owner reviews every frame; if not perfect,  -->
<!-- the free fallback = the same official landing poses animated locally).                                 -->
<!-- GEOGRAPHY (whole episode): book p.12 layout = oak screen-LEFT, meadow screen-RIGHT. Billy = TREE TOP;     -->
<!-- Snail + worms = GROUND (bottom of frame). Billy dives top-left -> bottom-right and always ENTERS FROM THE -->
<!-- TOP when coming from the tree. His official landing poses face screen-right: he is never mirrored.       -->
<!-- No text in AI shots. GROUNDING (owner, 2026-10-06): every standing character's soles sit on the flat walkable  -->
<!-- ground of library/backgrounds/ground_zones.yaml (pre-flight FAILs otherwise). LOCATION CONTINUITY: the worms play,-->
<!-- scatter and get eaten, Billy lands and burps, all at ONE spot (GRASS_STUMP); the Snail watches from the flowers  -->
<!-- nearby (GRASS_FLOWERS); the dive starts in the oak (BG_OAK_TREEHOUSE).                                           -->

## SCENE GRASS_STUMP
<!-- S01 HOOK 0-4.5 s (owner 2026-10-07), ONE free shot with a hard cut inside (keeps S02-S08 numbered as approved): -->
<!-- part 1, 0-2.5 s: open LOW on the four naughty worms having fun at the spot where Billy will land (GRASS_STUMP,  -->
<!-- same layout/scale as S03 and the count): they bounce and toss the blue ball (localanim worms_play).          -->
<!-- part 2, 2.5-4.5 s: cut to the oak (BG_OAK_TREEHOUSE) and crane UP the trunk to Billy poised by the treehouse,  -->
<!-- ending EXACTLY on S04's start framing; monocle glint 3.65-3.95 s; comic "WATCH OUT!!!!" burst + alarm at 4.05 s. -->
SFX [at 4.0]: alarm
ACTION [medium, local, fx:opening, billy:0.36/0.16/0.24/air, burst:1.55, secs:4.5]: The four little worms play with their ball; high up in the oak, Bad Billy's monocle glints... WATCH OUT!!!!

## SCENE GRASS_FLOWERS
<!-- S02 2.5-5 s. CAMERA: close, GROUND LEVEL (snail eye height). GROUNDING (owner 2026-10-06): GRASS_FLOWERS has   -->
<!-- flat grass across the whole bottom; the Snail sits screen-LEFT on it (soles at y 0.84), facing right; his eyes  -->
<!-- snap UP toward the top-right (the tree, where Billy is), he rears back and opens his mouth in a SILENT shout.     -->
<!-- No voice: bubble "WATCH OUT!!!!" + alarm land on the shout (0.35 s). Owner 2026-10-06: clip ENDS at 1.8 s, on   -->
<!-- the big open-mouth shout (smear + white eyes after 2.0 s), then a hard cut to S03. Kling 3.0 Std, start = end.  -->
SFX [at 0.3]: alarm
ACTION [medium, kling3std, refs, prompt:snail_watchout_v2, neg:snail_body, side>side, pos:0.45/0.54/0.30, endpos:0.45/0.54/0.30, loop, bubble:WATCH OUT!!!!@0.35, out:1.8, canon:p14 speech bubble]: The Snail looks up at the tree, his eyes snap wide open and he shouts a silent warning.

## SCENE GRASS_STUMP
<!-- S03 5-8 s. CAMERA: medium, GROUND LEVEL. LOCATION CONTINUITY (owner 2026-10-06): the SAME spot where Billy   -->
<!-- lands in S05 = GRASS_STUMP, on the flat grass behind and left of the stump (ground_zones.yaml). The four naughty   -->
<!-- worms (Jason's official art) play there; the ball freezes in the air, then they PANIC and scramble but STAY in the -->
<!-- spot (the count needs all four). Free book-art animation; every worm's soles stay on the green ground.           -->
NARRATOR [canon:p14]: He dived to the ground. He could take it no more!
ACTION [medium, local, fx:worms_panic, secs:3.0]: The four little worms freeze, the ball drops, and they tremble and hop in panic on the spot.

## SCENE BG_OAK_TREEHOUSE
<!-- S04a 8-10 s. PERFECTION SHOT. CAMERA: HIGH, up in the tree (no ground in frame). Billy ALONE (no worms):   -->
<!-- start = sheet pose "Approach 1" by the treehouse branch (upper-left), end = sheet pose "Approach 3"       -->
<!-- dropping out of the BOTTOM-RIGHT of frame. Kling 3.0 Standard, 3 s generated, cut to 2 s. References:    -->
<!-- turnaround + landing sheet (Approach 1, 3, 4, Touchdown; never the hatless Fall frames).                -->
SFX [at 0.0]: whoosh
ACTION [wide, kling3std, refs, prompt:billy_dive_launch_v2, neg:billy_model+billy_dive, landing-approach1>landing-approach, pos:0.36/0.16/0.24/air, endpos:0.62/0.52/0.30/air, trim:1.625, out:2.125]: Bad Billy launches off the branch and dives straight down out of the bottom of the frame.

## SCENE GRASS_STUMP
<!-- S04b 10-13 s. PERFECTION SHOT, v2 (owner 2026-10-06: take 1 face-planted - Kling can't do a big fall in 3 s).    -->
<!-- S04a already shows the dive out of the tree; this shot is ONLY the last small move. Start = official "Approach 4"  -->
<!-- (signed-off landing sheet), soles just ABOVE the grass at the landing spot (x 0.60, y 0.645, tagged airborne), same -->
<!-- scale (hat width matched to the Touchdown pose). End = "Touchdown (slide)", soles on the flat grass at the yellow   -->
<!-- ring (y 0.66). Feet come down, small dust puff, a short skid of a few centimetres, wings out. No falling, tumbling, -->
<!-- head-first or rotation. Kling 3.0 Std, 3 s. Owner 2026-10-06: take 1 of v2 approved with trim:0.79 (first frame  -->
<!-- with sharp body + wings, f19 at 24 fps) and out:2.0 (after f47 the settled pose starts to drift = the 'paused    -->
<!-- video' look): 1.21 s on screen - impact puff, skid, cut to the Snail cutaway.                                        -->
SFX [at 0.0]: thud
ACTION [wide, kling3std, refs, prompt:billy_land_soft, neg:billy_model+billy_dive+billy_softland, landing-approach4>landing-touchdown, pos:0.585/0.222/0.426/air, endpos:0.60/0.28/0.38, trim:0.79, out:2.0]: Bad Billy's sneakers touch down on the grass with a small puff of dust and he skids to a stop, wings out for balance.

## SCENE GRASS_FLOWERS
<!-- OWNER 2026-10-06 (take 1 review): built as PUNCH-IN CUTS from the clean moments only (clip_fixes.yaml S06 edit):-->
<!-- 1.0x calm (intro + One, slowed 0.75x) | 1.15x another calm slice (two) | 1.3x eyes pop (three) | 1.45x the gasp,  -->
<!-- eyes tinted pale green (FOUR!). Nothing from 2.1-3.3 s or 3.55-3.95 s (eye blobs, jump, see-through eyes).     -->
<!-- Cuts at 2.042 / 2.542 / 2.875 s; 4.33 s on screen; narration re-cut for free (audio/retimed/count_punch.wav).  -->
<!-- Numbers at x 0.85 / y 0.66, pop from 1.4x: measured >= 26 px clear of his eyes and stalks in every frame.     -->
<!-- S05 13-18.5 s. THE COUNT = REACTION CUTAWAY TO THE SNAIL (owner 2026-10-06: the art-animated eating was rejected;  -->
<!-- the eating is never shown - classic cartoon cutaway, kid-friendly). The Snail in the flower bush (GRASS_FLOWERS,   -->
<!-- S02 framing family), soles on the flat grass, watching off screen RIGHT (where Billy is). On each CHOMP (sound only, -->
<!-- off screen) he flinches, eyes wider; on FOUR! + GULP a silent wide-mouth GASP (head stays out of the shell). Numbers -->
<!-- (local overlay) on the open grass to his RIGHT, in his eyeline (GRASS_FLOWERS has no clear sky: flowers fill the top). -->
<!-- Narration = the free re-timed count (audio/retimed.yaml). Kling 3.0                                                   -->
<!-- Standard, silent, start = end frame; 6 s generated, cut at 5.5 s ON THE GASP, then cut to S07. If the flinches land  -->
<!-- off 1.9/2.7/3.6 s, the CHOMPs and numbers are re-synced to the actual flinches (free).                             -->
SFX [at 1.62]: chomp
SFX [at 2.042]: chomp
SFX [at 2.542]: chomp
SFX [at 2.875]: gulp
NARRATOR [canon:p15]: And he gobbled those worms. One, two, three... four!
ACTION [medium, kling3std, refs, prompt:snail_cutaway_v2, neg:snail_body+snail_cutaway, side>side, pos:0.38/0.58/0.26, endpos:0.38/0.58/0.26, loop, numbers:1@1.625|2@2.042|3@2.542|4!@2.875@x0.85/y0.66/pop1.4, secs:6]: The Snail watches off screen, flinching at every chomp, and gasps in horror on the last one.

## SCENE GRASS_STUMP
<!-- S06 19-24 s. CAMERA: wide, GROUND LEVEL. LOCATION CONTINUITY: Billy stays EXACTLY where his S05 landing ended -->
<!-- (GRASS_STUMP, flat grass behind the stump, screen-right of centre, soles at y 0.66), same scale as the landing    -->
<!-- (hat width matched: standing 0.48 H). Full, satisfied; one wing pats his tummy (feathers, never a hand). The ball -->
<!-- rolls in from the LEFT (local) and stops at his feet at 2.9 s; BURP on the real beak opening (f73 = 3.04 s).    -->
<!-- Owner 2026-10-06: approved; out:4.375 (f104 = last sharp-badge frame after the beak closes at f101; the badge     -->
<!-- blurs again from f105), then cut to the end card. Kling 3.0 Standard, start = end frame.                          -->
SFX [at 3.05]: burp
ACTION [wide, kling3std, refs, prompt:billy_full_v3, neg:billy_model, 34left>34left, pos:0.60/0.18/0.48, endpos:0.60/0.18/0.48, loop, secs:5, out:4.375, ball:stop@2.9]: Bad Billy stands alone, full and satisfied, pats his tummy with his wing, and the ball rolls to a stop at his feet.

## SCENE END_CARD
<!-- S07 24-36 s. Dynamic share card over a blurred GRASS_SIGN: "RULE NUMBER ONE..." slams in word by word,   -->
<!-- then "LOOK UP! 👆" punches in; Billy's official suspicious head slides up from the bottom with a whoosh;   -->
<!-- then "Tag a friend who'd be worm #5 🐛". Silent (no narrator), drum hits on each word.                    -->
SFX [at 0.0]: whoosh
SFX [at 1.6]: thud
SFX [at 3.0]: whoosh
SFX [at 4.2]: pop
NARRATOR [production, card:rule, silent, backdrop:GRASS_SIGN_LOW, show:RULE NUMBER ONE... | LOOK UP! 👆 | Tag a friend who'd be worm #5 🐛, head:BILLY suspicious, secs:5.5]: Rule number one: look up! Tag a friend who'd be worm number five.
