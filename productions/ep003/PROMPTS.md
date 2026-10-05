# EP003 Rule Number One: prompts per shot
Exactly what each paid request sends (free to regenerate with `./bbtb preprod`). Talking lines show the script text; Kling 3.0 speaks it, then ElevenLabs re-voices it.

## S01 (fal-ai/kling-video/v3/standard/image-to-video, 4s, $0.50)
- **Emotion:** theatrical self-pity turning into outrage at his own empty tummy (comic hook)
- **Action:** droops, looks down at his tummy, head snaps up on "EMPTY", eyes pop; settles back (end frame = start frame)
- **Background:** big oak trunk + treehouse, pink sky (BG_OAK_TREEHOUSE, p.12); close-up so no floating feet
- **Must not happen:** wings as hands/fists (S02 EP002 lesson), teeth in the beak, monocle switching eye, floating
- **Must be preserved:** monocle LEFT eye, silver B badge + crack, teal moustache curls, orange beak with no teeth
- **Visual inputs:** start_image_url: S01_first.jpg, end_image_url: S01_first.jpg; elements: @Element1: S01_bad_billy_frontal.png + 3 sheet images, @Element2: S01_background.jpg + 1 sheet images
- **Reviewed:** claude; owner sign-off: pending

**Prompt (2162 chars):**
> Bad Billy: a cartoon bird villain with a yellow feathered body; wild dark-brown head feathers with orange eyebrow feathers; a tall black top hat with one lightning-bolt crack near the top that never overlaps the badge, and a round silver badge with a white rim and a red script letter B; a round monocle with a thin black frame and a thin chain on his LEFT eye only; a long orange beak with NO teeth inside when it opens; teal curly moustache whiskers with the same spiral shape on both sides; a dark red vest, a brown belt with a gold square buckle and red-and-black striped shorts; teal-and-red high-top sneakers with a white star and pink-white soles; three long yellow tail feathers. His wings act as his arms: each wing ends in five long yellow primary feathers, never human hands or fingers, never fists. facing left, close up, half hidden against the trunk of a giant old oak tree, pink sky behind. He is theatrically hungry and sorry for himself: he slumps, his head droops low and he looks down at his own empty tummy, then his head snaps up in outrage and he says: "My tummy... it's EMPTY again!" On "EMPTY" his eyes pop wide and his beak flies open wide (no teeth inside) and snaps shut between words, in the rhythm of the words. His body sags, then puffs up indignantly, then settles back into his starting pose. His wings stay folded flat against his sides the whole clip: they do not spread or gesture. Only his HEAD and BODY act. Both feet stay planted; when he shifts his weight one foot stays down. He never floats. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Only Billy is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. Character references: @Element1 is Bad Billy. Keep every character exactly as in their reference images: same design, colours, proportions and details. @Element2 is the location: keep this background exactly as it is; it is scenery, not a character.

**Negative prompt:** floating, hovering, sliding, feet off the ground, flickering, morphing, melting, smearing, extra limbs, extra characters, text, captions, watermark, logo, blur, distortion, 3D render, realistic, style change, monocle on the right eye, mirrored character, human hands, human fingers, fists, clenched hands, fingers spread, arms, human limbs, hand gestures

## S04 (fal-ai/kling-video/v3/standard/image-to-video, 3s, $0.25)
- **Emotion:** carefree joy
- **Action:** empty stump -> Saul pops up out of the hollow stump with his ball and lands in front of it (start = empty scene, end = Saul pose)
- **Background:** stump meadow two-shot plate (GRASS_STUMP, pp.17-22 art), no text in frame
- **Must not happen:** legs/feet on Saul, coloured gloves, a deformed ball, a second worm
- **Must be preserved:** white gloves, pale-blue eyes, yellow ball, plum tail rings
- **Visual inputs:** start_image_url: S04_first.jpg, end_image_url: S04_last.jpg; elements: @Element1: S04_young_saul_frontal.png + 2 sheet images, @Element2: S04_background.jpg + 1 sheet images
- **Reviewed:** claude; owner sign-off: pending

**Prompt (1265 chars):**
> Young Saul: a small light-pink cartoon worm with no legs and no feet, dark plum rings near his tail, huge round pale-blue eyes with black pupils and white highlights, small brown eyebrows, two little buck teeth when he smiles, and white cartoon gloves on his tiny hands (always white). Happy, curious, playful and loyal. A grassy meadow with a hollow tree stump and a little ladder; static camera. Saul pops straight up out of the hollow stump with a happy bounce, holding his round yellow ball in his white gloves, looks around with big curious eyes and lands in front of the stump, smiling, ending exactly in the pose of the last frame. Real cartoon weight: the pop has a quick squash and stretch. The ball stays round and yellow; his gloves stay white; he has no legs. No other characters. No new text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. Character references: @Element1 is Young Saul. Keep every character exactly as in their reference images: same design, colours, proportions and details. @Element2 is the location: keep this background exactly as it is; it is scenery, not a character.

**Negative prompt:** floating, hovering, sliding, feet off the ground, flickering, morphing, melting, smearing, extra limbs, extra characters, text, captions, watermark, logo, blur, distortion, 3D render, realistic, style change, monocle on the right eye, mirrored character, legs, feet, shoes, human hands, bare hands, coloured gloves, extra fingers, deformed ball

## S05 (fal-ai/kling-video/ai-avatar/v2/standard, 2s, $0.11)
- **Emotion:** excitement
- **Action:** shouts "Ball time, everybody!", bounces once, lifts the ball (Kling Avatar drives the mouth with OUR audio)
- **Background:** Saul's side of the meadow (GRASS_SIGN); the canon sign lettering is painted art (Avatar keeps it static)
- **Must not happen:** Avatar takes no references or negative prompt - kept short and simple, low risk
- **Must be preserved:** white gloves, ball, eyes
- **Visual inputs:** image_url: S05_first.jpg, audio_url: kling_voice.wav; elements: none (engine takes no references)
- **Reviewed:** claude; owner sign-off: pending

**Prompt (875 chars):**
> Young Saul: a small light-pink cartoon worm with no legs and no feet, dark plum rings near his tail, huge round pale-blue eyes with black pupils and white highlights, small brown eyebrows, two little buck teeth when he smiles, and white cartoon gloves on his tiny hands (always white). Happy, curious, playful and loyal. facing right, in a sunny meadow, holding his round yellow ball. Bursting with excitement, he shouts: "Ball time, everybody!" His mouth opens WIDE and clearly on every word and closes between words, in the exact rhythm of the voice; his eyes sparkle, his body bounces once with joy and he lifts the ball. Only Saul is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame.

**Negative prompt:** (engine takes none)

## S07 (fal-ai/kling-video/v3/standard/image-to-video, 3s, $0.38)
- **Emotion:** sly, menacing glee (lunch spotted)
- **Action:** eyes narrow, slow wicked smile, leans slowly toward camera, one eyebrow rises; settles back (end frame = start frame)
- **Background:** same oak close-up as S01 (continuity - he never left the tree)
- **Must not happen:** wing gestures (they become hands), teeth, monocle drift
- **Must be preserved:** monocle LEFT eye, badge, moustache, beak
- **Visual inputs:** start_image_url: S07_first.jpg, end_image_url: S07_first.jpg; elements: @Element1: S07_bad_billy_frontal.png + 3 sheet images, @Element2: S07_background.jpg + 1 sheet images
- **Reviewed:** claude; owner sign-off: pending

**Prompt (2136 chars):**
> Bad Billy: a cartoon bird villain with a yellow feathered body; wild dark-brown head feathers with orange eyebrow feathers; a tall black top hat with one lightning-bolt crack near the top that never overlaps the badge, and a round silver badge with a white rim and a red script letter B; a round monocle with a thin black frame and a thin chain on his LEFT eye only; a long orange beak with NO teeth inside when it opens; teal curly moustache whiskers with the same spiral shape on both sides; a dark red vest, a brown belt with a gold square buckle and red-and-black striped shorts; teal-and-red high-top sneakers with a white star and pink-white soles; three long yellow tail feathers. His wings act as his arms: each wing ends in five long yellow primary feathers, never human hands or fingers, never fists. facing left, close up, half hidden against the trunk of a giant old oak tree, pink sky behind. A sly, menacing villain who has just spotted his lunch on the ground below: his eyes narrow, a slow wicked smile spreads across his beak, he leans slowly forward and down toward the camera and purrs: "Lunch... is served!" The beak opens slowly and clearly on each word (no teeth inside) and closes between them; one eyebrow rises. Then he settles back into his starting pose with a smug look. His wings stay folded flat against his sides the whole clip: they do not spread or gesture. Only his HEAD and BODY act. Both feet stay planted; when he shifts his weight one foot stays down. He never floats. The monocle is a small round lens on his LEFT eye only — it NEVER moves to the right eye, NEVER disappears, NEVER changes size. Only Billy is in the frame. Static camera. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. Character references: @Element1 is Bad Billy. Keep every character exactly as in their reference images: same design, colours, proportions and details. @Element2 is the location: keep this background exactly as it is; it is scenery, not a character.

**Negative prompt:** floating, hovering, sliding, feet off the ground, flickering, morphing, melting, smearing, extra limbs, extra characters, text, captions, watermark, logo, blur, distortion, 3D render, realistic, style change, monocle on the right eye, mirrored character, human hands, human fingers, fists, clenched hands, fingers spread, arms, human limbs, hand gestures

## S08 (fal-ai/kling-video/v3/standard/image-to-video, 5s, $0.42)
- **Emotion:** dawning fear (the cliffhanger)
- **Action:** Saul looks up at the tree, eyes widen, gulps, trembles; stays silent; ends in the start pose (end frame)
- **Background:** stump meadow (GRASS_STUMP), the same place EP002 opens
- **Must not happen:** legs, coloured gloves, extra worms, any text
- **Must be preserved:** Saul's face, gloves, plum rings
- **Visual inputs:** start_image_url: S08_first.jpg, end_image_url: S08_last.jpg; elements: @Element1: S08_young_saul_frontal.png + 2 sheet images, @Element2: S08_background.jpg + 1 sheet images
- **Reviewed:** claude; owner sign-off: pending

**Prompt (1237 chars):**
> Young Saul: a small light-pink cartoon worm with no legs and no feet, dark plum rings near his tail, huge round pale-blue eyes with black pupils and white highlights, small brown eyebrows, two little buck teeth when he smiles, and white cartoon gloves on his tiny hands (always white). Happy, curious, playful and loyal. facing right, in a grassy meadow by a hollow tree stump, looking up toward a big tree. He slowly realises he is being watched: his huge eyes go even wider, his eyebrows shoot up, he gulps, and his whole body trembles with fear in small quick shivers, leaning back a little, then he freezes, ending exactly in the pose of the last frame. He stays silent, mouth closed in a nervous wobble. His gloves stay white; he has no legs. No other characters. No text. No smearing. The art style stays flat 2D picture-book cartoon throughout — no 3D rendering, no photorealism, no style drift. Same colors, same line weight, same character proportions from first to last frame. Character references: @Element1 is Young Saul. Keep every character exactly as in their reference images: same design, colours, proportions and details. @Element2 is the location: keep this background exactly as it is; it is scenery, not a character.

**Negative prompt:** floating, hovering, sliding, feet off the ground, flickering, morphing, melting, smearing, extra limbs, extra characters, text, captions, watermark, logo, blur, distortion, 3D render, realistic, style change, monocle on the right eye, mirrored character, legs, feet, shoes, human hands, bare hands, coloured gloves, extra fingers, deformed ball
