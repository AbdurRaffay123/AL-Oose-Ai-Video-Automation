# EP004 Two Hungry Villains: prompts per shot
Exactly what each paid request sends (free to regenerate with `./bbtb preprod`). Talking lines show the script text; Kling 3.0 speaks it, then ElevenLabs re-voices it.

## S01 (fal-ai/kling-video/ai-avatar/v2/standard, 2s, $0.11)
- **Emotion:** villainous glee (the hook)
- **Action:** leans forward with a sly grin, evil laugh, body shakes with each ha, goggles glint (Avatar, his ORIGINAL laugh)
- **Background:** cave tunnel with signpost and mine cart (BG_CAVE_TUNNEL, book p.37) - new location
- **Must not happen:** Avatar takes no negative prompt - keep the prompt simple; check frames for a melting body or a lost crest
- **Must be preserved:** aviator helmet, blue goggles, orange beak, crest, green sneakers
- **Visual inputs:** image_url: S01_first.jpg, audio_url: kling_voice.wav; elements: none (engine takes no references)
- **Reviewed:** claude; owner sign-off: pending

**Prompt (712 chars):**
> Static camera. Big Pea: a round, chubby yellow cartoon bird with a brown leather aviator helmet, round blue-lens goggles, a small orange beak, sleepy half-closed eyes, a yellow head crest, small yellow wings with feather tips and green sneakers, facing right, in a dim underground cave. He leans forward slowly with a sly, villainous grin and gives a big evil laugh in the rhythm of the audio: his beak opens and closes on every 'ha', his round body shakes with each laugh and his shoulders bounce. His goggles catch the light. He stays on the ground. Flat 2D picture-book cartoon style throughout, same colours, same line weight and same proportions from the first to the last frame. No new characters, no text.

**Negative prompt:** (engine takes none)

## S02 (fal-ai/kling-video/v3/standard/image-to-video, 5s, $0.42)
- **Emotion:** two hungry villains searching, grumpy
- **Action:** Big Pea pushes his goggles up and peers into the dark corners, then shakes his head (no mine cart in frame); Billy looks behind the signpost left/right then frowns; both end in their start poses (end frame = start frame, tag loop)
- **Background:** cave tunnel (same as S01, wider two-shot)
- **Must not happen:** Billy hands/fists (billy_hands negative), monocle on the right eye, extra characters, text on the signpost
- **Must be preserved:** Billy's LEFT-eye monocle, badge, folded wings; Big Pea's goggles and helmet
- **Visual inputs:** start_image_url: S02_first.jpg, end_image_url: S02_first.jpg; elements: @Element1: S02_big_pea_frontal.png + 3 sheet images, @Element2: S02_bad_billy_frontal.png + 3 sheet images
- **Reviewed:** claude; owner sign-off: pending

**Prompt (1354 chars):**
> Static camera. Two cartoon villains search a cave for food. On the left, Big Pea: a round, chubby yellow cartoon bird with a brown leather aviator helmet, round blue-lens goggles, a small orange beak, sleepy half-closed eyes, a yellow head crest, small yellow wings with feather tips and green sneakers, facing right; on the right, Bad Billy, a cartoon bird villain with a black top hat (silver badge with a red letter B), a monocle on his LEFT eye, an orange beak, teal moustache curls, a dark red vest and teal-and-red sneakers, facing left. The performance, in order: Big Pea pushes his goggles up, bends forward and peers into the dark corners, then straightens up and shakes his head; at the same time Billy leans to look behind the wooden signpost, his head turning left and right, then turns back with a grumpy frown. Both end exactly in their starting poses. Neither speaks. Billy's wings stay folded at his sides: no hands, no fingers. The monocle stays on Billy's LEFT eye. Both keep their feet on the ground. Flat 2D picture-book cartoon style throughout, same colours, same line weight and same proportions from the first to the last frame. No new characters, no text. Character references: @Element1 is Big Pea, @Element2 is Bad Billy. Keep every character exactly as in their reference images: same design, colours, proportions and details.

**Negative prompt:** floating, hovering, sliding, feet off the ground, flickering, morphing, melting, smearing, extra limbs, extra characters, text, captions, watermark, logo, blur, distortion, 3D render, realistic, style change, monocle on the right eye, mirrored character, human hands, human fingers, fists, clenched hands, fingers spread, arms, human limbs, hand gestures

## S04 (fal-ai/kling-video/ai-avatar/v2/standard, 3s, $0.17)
- **Emotion:** annoyed
- **Action:** Big Pea glares to the right, says "You are very annoying." grumpily, folds wings, taps a sneaker (Avatar, ORIGINAL line)
- **Background:** underground study (BG_CAVE_STUDY, book p.36) - new location
- **Must not happen:** no negative possible on Avatar; frames checked by the owner
- **Must be preserved:** helmet, goggles, beak
- **Visual inputs:** image_url: S04_first.jpg, audio_url: kling_voice.wav; elements: none (engine takes no references)
- **Reviewed:** claude; owner sign-off: pending

**Prompt (717 chars):**
> Static camera. Big Pea: a round, chubby yellow cartoon bird with a brown leather aviator helmet, round blue-lens goggles, a small orange beak, sleepy half-closed eyes, a yellow head crest, small yellow wings with feather tips and green sneakers, facing right, in an underground study with bookshelves. He glares to the right at someone annoying him, his eyes narrowing, and says the words in the audio grumpily: his beak opens and closes in the rhythm of the words. He folds his little wings across his tummy, taps one green sneaker and gives a small huff. Flat 2D picture-book cartoon style throughout, same colours, same line weight and same proportions from the first to the last frame. No new characters, no text.

**Negative prompt:** (engine takes none)

## S05 (fal-ai/kling-video/ai-avatar/v2/standard, 3s, $0.17)
- **Emotion:** fed up
- **Action:** Big Pea, front view, "Why are you still here?" with a huff (Avatar, ORIGINAL line)
- **Background:** underground study
- **Must not happen:** as S04
- **Must be preserved:** as S04
- **Visual inputs:** image_url: S05_first.jpg, audio_url: kling_voice.wav; elements: none (engine takes no references)
- **Reviewed:** claude; owner sign-off: pending

**Prompt (722 chars):**
> Static camera. Big Pea: a round, chubby yellow cartoon bird with a brown leather aviator helmet, round blue-lens goggles, a small orange beak, sleepy half-closed eyes, a yellow head crest, small yellow wings with feather tips and green sneakers, facing the camera, in an underground study with bookshelves. He glares to the right at someone annoying him, his eyes narrowing, and says the words in the audio grumpily: his beak opens and closes in the rhythm of the words. He folds his little wings across his tummy, taps one green sneaker and gives a small huff. Flat 2D picture-book cartoon style throughout, same colours, same line weight and same proportions from the first to the last frame. No new characters, no text.

**Negative prompt:** (engine takes none)

## S07 (fal-ai/kling-video/ai-avatar/v2/standard, 3s, $0.17)
- **Emotion:** scolding, grumpy old snail
- **Action:** the Snail's blue lips flap with the words, googly eyes bulge, stretches up on "Go ON!" and settles (Avatar, ORIGINAL line, denoised)
- **Background:** cave tunnel
- **Must not happen:** fast movement (he is a snail); no extra characters
- **Must be preserved:** orange shell, green face, googly eyes, tiny top hat, blue lips
- **Visual inputs:** image_url: S07_first.jpg, audio_url: kling_voice.wav; elements: none (engine takes no references)
- **Reviewed:** claude; owner sign-off: pending

**Prompt (641 chars):**
> Static camera. the Snail: a cartoon snail with a big orange spiral shell, a green face, two huge pale-green googly eyes on stalks, a tiny black top hat and big shiny blue lips, facing right, in a cave tunnel. He scolds someone off to the right, in the rhythm of the audio: his big blue lips open and close on every word, his googly eyes bulge and his eye stalks wobble, and his body stretches up out of the shell on 'Go ON!' and settles back. He does not move fast: he is a snail. Flat 2D picture-book cartoon style throughout, same colours, same line weight and same proportions from the first to the last frame. No new characters, no text.

**Negative prompt:** (engine takes none)
