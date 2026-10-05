# MiniMax H3 Max: free manual test (owner)

**What this tests:** whether MiniMax H3 Max animates Billy with more energy and better consistency than Kling and Wan,
using the same shot as every other test (EP001 S02). Score the result in `docs/model_comparison.md`.

**Cost: $0. Free, as long as you use the sandbox.**
- fal gives signed-in users **5 free MiniMax H3 Max videos a day** (up to 15 s each; the allowance resets every 24 h) in
  the **fal sandbox**.
- The playground on the model's own page (`fal.ai/models/minimax/h3-max/image-to-video`) is **paid**: $0.08/s at 768p,
  charged to the fal balance.
- **Before you press Generate, check that the page says free.** If it asks for credits or a payment, stop.

## Step 1: Open the free sandbox
Go to **https://fal.ai/minimax-h3-max** and click **"Generate free videos"**. It opens the sandbox:
`https://fal.ai/sandbox?op=video.text_to_video&free=true&models=da5j8ccregja812b831g`

*(Correction to the original plan: searching fal.ai for "MiniMax H3 Max" and clicking the model leads to the paid model
page, not the free sandbox.)*

## Step 2: Sign in
The free allowance needs a fal account. Sign in with the same account as the studio's fal key, or any account.

## Step 3: Attach the image (this switches to image-to-video)
The sandbox starts in text-to-video. Attach an image and it runs image-to-video from that picture. Use this exact file
(in the file picker press **⇧⌘G** and paste the path):

```
/Users/abdurraffay/Documents/Al-oose-Ai-video/productions/ep001-big-guy/keyframes/S02_first.jpg
```

**Optional:** if the sandbox shows an **audio** upload (the API calls it `target_audio_url`), attach Billy's approved
line:

```
/Users/abdurraffay/Documents/Al-oose-Ai-video/productions/test-wan27-ep001-s02/shots/S01/wan_voice.wav
```

Without it, H3 makes its own soundtrack. That's fine for judging body movement, energy and on-model, but not lip sync to
Billy's voice. Whether the audio upload moves the beak, or only replaces the soundtrack, is unverified.

## Step 4: Paste this exact prompt
This is the owner's prompt with one correction. "standing in a meadow of big smiling flowers" became "standing on
rocky ground beside the worm hole", because the EP001 S02 picture is the rocky worm-hole scene, and a meadow prompt
would make H3 repaint the background.

```
2D cartoon villain bird character with orange beak, black top hat with B badge, monocle on his LEFT eye, facing left, standing on rocky ground beside the worm hole. MAXIMUM villain energy: throws whole body into performance, leans far forward neck stretched, wings sweep out wide like a showman's cape, beak flies open and snaps shut on every word, head jabs and bobs to the rhythm, stomps one foot, bounces on knees. Feathered yellow wings at all times — no hands no fingers no arms. Static camera. Consistent 2D cartoon style. No smearing.
```

## Step 5: Set the duration to 5 seconds
5 s is H3's shortest clip, and the result may run up to 0.7 s longer. Billy's line is 4.74 s.

## Step 6: Set the resolution to 768P
H3 has no 720p; it offers 480P, **768P** and 1080P. Pick 768P, the closest to our 720p.
- **Prompt expansion:** if offered, set it to **disabled**, so H3 doesn't rewrite away the LEFT-eye monocle and wing
  rules.
- **Aspect ratio:** leave it alone. The output follows the image, which is 9:16.
- **End image:** leave it empty.

## Step 7: Generate
Confirm that it says free (5 per day), then generate. It usually takes a minute or two.

## Step 8: Download the result
Click **Download** under the preview and save the clip as:
```
/Users/abdurraffay/Documents/Al-oose-Ai-video/productions/test-h3max-ep001-s02/H3MAX_free_1.mp4
```
Create the `test-h3max-ep001-s02` folder first. For a second try with a different prompt, use `H3MAX_free_2.mp4`.

## Step 9: Compare in Finder
Open `productions/test-wan27-ep001-s02/compare/`, which holds the Kling Avatar take, Wan test 1 and a side-by-side, and
play them next to the H3 clip. Then tell Claude: it will put H3 into the labelled side-by-side and check every frame.

## What to look for (score each 1–10 in `docs/model_comparison.md`)
- **On model:** the monocle stays on Billy's **LEFT** eye (the screen-right side, as in the picture) in every frame;
  the hat keeps the B badge and crack and does not melt or fall off; the moustache curls stay.
- **Wings:** feathered yellow wings all the time, with no hands, fingers or arms.
- **Beak:** opens and closes clearly, on the words if you attached the audio.
- **Body movement and energy:** does he lean, sweep his wings and stomp, or just stand?
- **Consistency:** no morphing, no 3D or realistic look, same colours, no extra characters, text or watermark. Watch
  the **last second** for snaps (Wan test 1 snapped at 4.6 s).
