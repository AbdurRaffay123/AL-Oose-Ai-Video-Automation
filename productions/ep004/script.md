# EP004 WATCH OUT!
format: 9:16   resolution: 720p   music: playful-adventure   budget: 6   captions: off   talking_engine: kling
action_engine: kling3   spend_cap: 6   session_cap: 6   shot_cap: 0.70   negatives: billy_hands   elements: on

<!-- EP004 v5 (owner 2026-10-07, after animatic v2 was rejected as a slideshow). Rules: every shot is real moving -->
<!-- video (no art-animated characters), every beat has a voice or a strong sound, review the whole animatic WITH -->
<!-- sound. Shot ids are pinned with id: so the approved paid clips (S02, S05, S06, S07) keep their folders and    -->
<!-- approvals; S04 (the launch) is DROPPED (hard cut from S03 to S05 on a whoosh). Worms never speak in another   -->
<!-- character's voice: they giggle / scream as sound effects. Book lines: canon:p12-p15; the rest is production. -->
<!-- Geography as before: oak LEFT/high (Billy), the landing spot on GRASS_STUMP (worms, then Billy), the Snail in  -->
<!-- the flower bush nearby (GRASS_FLOWERS). Grounding gate on every keyframe.                                    -->

## SCENE GRASS_STUMP
<!-- S01a: the four naughty worms play ball AT THE LANDING SPOT. Kling 3.0 Standard, silent, worm references (card -->
<!-- next). Giggles (SFX) + the narrator's p.12 line. Real motion: the ball bounces between them.                  -->
SFX [at 0.2, vol 0.1]: giggles
NARRATOR [canon:p12]: Finally they made it to the grass under the tree. The little worms were playing ball as happy as can be.
ACTION [wide, kling3std, refs, id:S01a, prompt:worms_play_v5, neg:worms_body+worms_keep_monocle+worms_no_legs+worms_happy, group-ball>group-ball, pos:0.5/0.0/1.0, endpos:0.5/0.0/1.0, loop, gen:4]: The four naughty worms play ball on the grass, bouncing it between them.

## SCENE BG_OAK_TREEHOUSE
<!-- S01b: Billy watching from the oak, standing on the treehouse porch (grounded), facing the meadow. Kling 3.0      -->
<!-- Standard, small motion: eyes narrow, a slow sly smile, wings folded; start = end frame. Narrator p.13, THEN    -->
<!-- his original growl tail "Arrrr" (never under the narration), on his eyes narrowing.                           -->
NARRATOR [canon:p13]: An eye that belonged to a bird with a beak, who had not had a meal in over a week.
BILLY [tophat, over, say:3.95, production]: Arrrr!
ACTION [medium, avatar, id:S01b, prompt:billy_watch_avatar, 34right>34right, zoom:1.55, pos:0.42/0.30/0.66, endpos:0.42/0.30/0.66]: High in the oak, Bad Billy watches the meadow below, his eyes narrowing into a sly smile.

## SCENE GRASS_FLOWERS
<!-- S02 (approved take, out 1.8 s): the Snail's shout, now VOICED in his approved clone; the bubble is the only     -->
<!-- WATCH OUT on screen (the starburst is gone). The alarm rings under the cut into this shot.                    -->
SFX [at 0.0, vol 0.06]: alarm
SNAIL [over, say:0.32, canon:p14 speech bubble]: WATCH OUT!
ACTION [id:S02, medium, kling3std, refs, prompt:snail_watchout_v2, neg:snail_body, side>side, pos:0.45/0.54/0.30, endpos:0.45/0.54/0.30, loop, bubble:WATCH OUT!!!!@0.35@x0.24/y0.24/s0.85/tail0.45/0.295, out:1.8, canon:p14 speech bubble]: The Snail looks up at the tree, his eyes snap wide open and he shouts a silent warning.

## SCENE GRASS_STUMP
<!-- S03: the worms panic AT THE SPOT. Kling 3.0 Standard, silent, worm references: they jump, look up, scramble in  -->
<!-- place (never leave the spot), the ball drops. A group "aaah!" (SFX) + the narrator's p.14 line.               -->
SFX [at 0.15, vol 0.05]: aaah
NARRATOR [canon:p14]: He dived to the ground. He could take it no more!
ACTION [wide, kling3std, refs, id:S03, prompt:worms_panic_v3, neg:worms_body+worms_still+worms_keep_monocle+worms_alarm_face+worms_no_legs, group-ball>group-ball-down, pos:0.5/0.0/1.0, endpos:0.5/0.0/1.0]: The four naughty worms look up, jump and scramble in panic on the spot as the ball drops.

## SCENE GRASS_STUMP
<!-- S05 (approved take, trim 0.79 / out 2.0): hard cut from S03 on a whoosh, straight into the impact puff.       -->
SFX [at 0.0]: whoosh
SFX [at 0.05]: thud
ACTION [id:S05, wide, kling3std, refs, prompt:billy_land_soft, neg:billy_model+billy_dive+billy_softland, landing-approach4>landing-touchdown, pos:0.585/0.222/0.426/air, endpos:0.60/0.28/0.38, trim:0.79, out:2.0]: Bad Billy's sneakers touch down on the grass with a small puff of dust and he skids to a stop, wings out for balance.

## SCENE GRASS_FLOWERS
<!-- S06 (approved punch-in rebuild): the count. CHOMPs on the cuts, a proper GULP on FOUR!                         -->
SFX [at 1.625]: chomp
SFX [at 2.042]: chomp
SFX [at 2.542]: chomp
SFX [at 2.875, vol 0.35]: gulp
NARRATOR [canon:p15]: And he gobbled those worms. One, two, three... four!
ACTION [id:S06, medium, kling3std, refs, prompt:snail_cutaway_v2, neg:snail_body+snail_cutaway, side>side, pos:0.38/0.58/0.26, endpos:0.38/0.58/0.26, loop, numbers:1@1.625|2@2.042|3@2.542|4!@2.875@x0.85/y0.66/pop1.4, secs:6]: The Snail watches off screen, flinching at every chomp, and gasps in horror on the last one.

## SCENE GRASS_STUMP
<!-- S07 (approved take, out 4.375): the burp on the real beak opening (3.05 s), then Billy's new line in his clone. -->
SFX [at 3.05]: burp
BILLY [tophat, over, say:0.85, production]: Mmm... delicious!
ACTION [id:S07, wide, kling3std, refs, prompt:billy_full_v3, neg:billy_model, 34left>34left, pos:0.60/0.18/0.48, endpos:0.60/0.18/0.48, loop, secs:5, out:4.375, ball:stop@2.9]: Bad Billy stands alone, full and satisfied, pats his tummy with his wing, and the ball rolls to a stop at his feet.

## SCENE GRASS_FLOWERS
<!-- S08: the Snail's closing button, his ORIGINAL recording (free). Picture: see the owner's options (a Kling      -->
<!-- Avatar shot of him saying it, or a reused calm Snail slice). Pending the owner's choice.                       -->
SNAIL [side, kling, prompt:snail_closing_v2, production]: Ah, these birds are big trouble makers, mun.

## SCENE END_CARD
<!-- S09: 4 s, moving: "RULE NUMBER ONE... LOOK UP!" slams in, then "Tag a friend who'd be worm #5".               -->
SFX [at 0.15]: whoosh
SFX [at 0.75]: thud
SFX [at 1.9]: pop
NARRATOR [production, card:rule, id:S09, backdrop:GRASS_SIGN_LOW, show:RULE NUMBER ONE... | LOOK UP! 👆 | Tag a friend who'd be worm #5 🐛, head:BILLY suspicious, secs:4]: Rule number one: look up! Tag a friend who'd be worm number five.
