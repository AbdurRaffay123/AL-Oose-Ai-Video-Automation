# Script format (parsed by studio/bbtb/script_parser.py)

```
# EP00N Title
format: 9:16|16:9   resolution: 720p|1080p   music: <mood>   budget: <USD>   captions: on|off
## SCENE <BACKGROUND or END_CARD>
ACTION [wide|medium, <pose>, end: <CHARACTER> <pose>]: what happens (image-to-video)
<NAME> [<variant>, <pose> or <expression>, <direction>]: (acting) spoken line
NARRATOR: voice-over (rides on the next ACTION, otherwise holds the previous shot)
SFX [at <seconds>]: <name>      MUSIC: <mood>      <!-- comments -->
```

**Names.** `BILLY` / `BAD BILLY`, `SAUL` / `YOUNG SAUL`, `BIG GUY` / `BIG WORM`, `BIG PEA`, `SNAIL`, `NARRATOR`.

**Billy top-hat**
- Poses: front, 34left, sideleft, back, sideright, 34right, scroll-pickup, scroll-reading, scroll-stepback, scroll-recover, scroll-faceright.
- Expressions: neutral, suspicious, happy, angry, surprised, scared, wink, lookdown, lookup, laugh, talking, thinking, skeptical, shock.

**Saul poses:** ball-front, ball-side, idle, wave, holding-scroll, cheerful, standing-tall.

**Big Guy poses:** front-wave, arms-up, talking, laughing, reaching.

**Scenes** (`library/backgrounds.yaml`): BIG_WORM_HOLE, STUMP_GRASS, STUMP_SIGN, FLOATING_TREE, TUNNELS, SKY_CLOUDS, SKY_CLEAR, END_CARD.

**Limits**
- One talking line can be at most 20 s; split longer lines.
- Big Pea, Snail and goggles-Billy have no cut-outs yet, so add poses before using them.
- Keep each ACTION to one simple, clear motion. Fast, chaotic action makes AI video warp the characters.
