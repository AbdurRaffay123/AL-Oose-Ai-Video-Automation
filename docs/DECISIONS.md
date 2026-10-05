# Decisions and known limitations

## 2026-10-03: owner decisions
- Goal: one automated workflow from script to published video. Approximate lip-sync is fine; the characters must visibly talk. Outputs are production, not experiments.
- Voice clips are clone references. New and adapted lines are allowed (marked PRODUCTION). An original clip is used whenever its text matches a line.
- Billy top-hat and goggles are both canon, chosen per script. Expressions and theme must stay on-model.
- No layered PSDs exist. Work from flattened art, using cut-outs extracted from the reference sheets.
- Video engine: LTX-2.3 Pro, V2 API. Voice: Inworld instant clone. Music/SFX: local files or ElevenLabs.

## Known limitations
- Source art is small (full-body Billy is about 355 px tall). At 720p the art is upscaled 2–3× and at 1080p 3–4.5×, so it looks soft.
  - **Recommended next step:** a local cartoon upscaler (Real-ESRGAN anime model), with owner approval to install.
- Cut-outs are draft until approved. Leg gaps were removed by hand-placed seeds in `library/cutlist.yaml`.
- No cut-outs yet for Big Pea, Snail or goggles-Billy.
- How LTX audio-to-video handles 2D cartoon birds is unproven. The first paid test answers this.
- Saul's voice reference is only 4.2 s.
- Loudness is measured and corrected to about −14/−15 LUFS with a −3 dBFS limiter.

## 2026-10-03: owner requests (v2)
- Final videos must not contain placeholder or unverified voices. Enforced: QA fails, and LTX talking shots are blocked until every voice is final.
- Target duration under 50 s (ideally 40–45 s). EP001 was rewritten to about 45 s; dropped and shortened lines are tagged `adapted:`.
- Budget under $3 at 720p. Simple movement uses free local animation; LTX only where it adds value (EP001: 4 talking shots + 1 eruption).
- No paid call of any kind (LTX, Inworld, ElevenLabs) without an explicit approval code.

## Voice findings (measured locally; free)
- **Transcripts** (Whisper medium.en) of all 15 clips are clear speech.
  - `BigPea_Go_Away_Stop_following_me.wav` actually says "Go away, I'm hungry!". The filename is wrong, so the mapping was corrected.
  - `bad-billy-voice.wav` is a compilation of Billy's other clips plus screams, so it adds no new material.
- **Usable speech per character** (active voice, not file length): Billy ~5–6 s of words, Big Pea ~5.6 s, Snail ~4.4 s, **Saul ~2.3 s**.
- **Speaker similarity** (Resemblyzer):
  - Billy and Big Pea are near-identical voices (0.93), and the Snail is close (0.77–0.80): probably one performer. Saul is distinct.
  - The narrator in marketing videos 2, 3 and 5 is one consistent voice (0.92–0.95). It was recovered as a 9.7 s clean reference from `5. HELP WORM FILE.mp4` using Demucs vocal separation (music sits only 2–5 dB under the speech).
- **Saul has too little audio** for any clone to be trustworthy: about 2.3 s of speech, below Inworld's 3 s minimum. Best fix: record 20–30 s of new Saul lines with the original performer (any content, varied emotion). Fallback: a performer reads Saul's lines and Chatterbox voice conversion maps them onto Saul's timbre.

## 2026-10-03: ElevenLabs is the primary voice engine (owner decision)
- **Workflow:** recordings → one-time ElevenLabs Instant Voice Clone per character → voice IDs saved in `library/voices.yaml` → every script reuses them.
- **Paid steps:** speech generation is a paid step with its own approval code (`voices render`), done before the free animatic, because audio length drives shot timing.
- **No silent fallback:** placeholders are explicit-preview only. Inworld support was removed (it was never used); Chatterbox stays as an optional, explicitly selected local provider.
- **Narrator:** must be configured by the owner. Options:
  - clone the marketing narrator (Demucs-cleaned reference, rights required);
  - `voices set narrator <voice_id>`.
- **API key:** stored in `.env` as `ELEVEN_LABS_API_KEY`; both spellings are accepted. As of 2026-10-03 it lacks the `user_read`, `models_read` and `voices_read` permissions; `voices_write` and `text_to_speech` are unverified.
- **Cloning is on hold** until the owner confirms the rights and performer consent (owner rule).

## 2026-10-03: ElevenLabs credit rules (owner) and key status
- **Key:** all permissions are now enabled. Starter plan, 39,482 credits (reset 2026-11-03).
  - 10 voice slots: 2 used, by "BBTB Bad Billy" (fFaS1yzAqPneDXnQ0rbL) and a personal "raffay khan" clone. The latter is not part of the project.
  - Rate: eleven_multilingual_v2 = 1.0 credit per character (read from /v1/models).
- **Rules now enforced in code:**
  - one `/with-timestamps` request per character, sliced by timings;
  - one test line per character;
  - no Chatterbox or macOS audio for anything the owner hears (silent previews);
  - any failure → `unknown` and stop, never retried;
  - an approved voice is required before any render, and approval requires a test line.
- **Cache:** speech is now cached by content key (`audio/lines/by_key/`), which fixes the "renumbering re-bills" issue from STRUCTURE.md. The "LTX clip reused by shot number" issue is still open.

## 2026-10-04: Billy keeps his top hat in the EP002 crash (owner)
- **Finding:** the landing sheet's "8. Fall 1" frame (cut-out `billy_tophat_landing_fall`) draws Billy's head without the
  hat as a bald yellow dome with hair sticking out sideways. The owner says it looks wrong. No other top-hat-edition art shows him hatless.
  The hatless Billy on `BBTB-Expression-sheet.png` is the goggles edition (crest, goggles, no monocle or moustache), a different design.
- **Rule:** top-hat Billy is never shown without his hat. `landing-fall` stays in the library but is not used.
- **EP002 S07:** ends on the sheet's "7. Trip 2" frame (`landing-trip2`), where one wing clamps the hat on. The hat-flying-off
  beat is dropped (it was production, not book text: p.27 says only "CRASH! and a THUD!"). Continuity with EP001 is
  preserved: Billy wears the hat there.

## 2026-10-04: EP002 animatic "frozen from 33 s", and Saul not seen in S05
- **Frozen picture (a bug, now fixed):** the file was fine. AVFoundation decoded all 1,083 frames, and every shot changes.
  The cause was that `assemble.mux` rewrote `animatic.mp4` in place while QuickTime still had the previous version open.
  QuickTime kept the old frame index, so from the first changed shot (S07, 32.25 s) it read the wrong bytes and froze.
  `open` on a file that is already open only brings the old window to the front.
  **Fix:** mux writes `animatic.tmp.mp4` and then renames it over the old file (new inode; test `test_mux_replaces_the_animatic...`).
  Before reopening, close the old QuickTime window.
- **Saul in S05:** both S05 frames always used the "flying with Saul" sheet (Saul riding on Billy). At `far` framing he
  was a small pink head against a pink sky. S05 is now `wide` (Billy and Saul are about 1.6x bigger).
  `Scenes/Bad Billy jumping off With Saul_.jpg` is the take-off beat: Billy crouches on the cliff while Saul climbs on
  in four ghosted steps with large numbers "1-4". It does not show Saul riding in flight, and the numbers are baked-in text, so it
  is not used for the characters. Its right half is already the FLOATING_ISLAND background of S05.

## 2026-10-04: EP002 end card sells the book (owner)
- **Change:** the end card is now two moments.
  - **Tease (S08):** Billy's eye twitches at the camera over the crash site, with the line "Did a tiny worm just outsmart the
    baddest bird around?"
  - **Book (S09):** the real cover from `Images/Marketing/COVER.png`, the CTA, a "LINK IN BIO 🐛" pill and a Follow button with a
    tapping hand.
- **CTA:** the owner chose **version D** of the four offered (A curiosity, B kids, C urgent, D parent + child).
  The narrator line is "Bedtime just got WAY more fun. Bad Billy the Bird — grab your copy! Link in bio!" (production).
- **Art:** the twitch alternates the expression sheet's `neutral` and `wink` heads (same angle, no redraw).
  There is no art of Billy holding the book, so the cover appears on its own. No "buy now" graphic exists.

## 2026-10-05: Official character sheets become visual inputs (Jason)
- **Diagnosis (Jason):** we described the characters in words only. Kling must SEE them.
- **Sheets:** 8 files in `Al-Oose-content/CONTENT/BBTB MARKETING/Character-Facials-sheet/`, now registered (99
  originals):
  - Billy 01 Turnaround, 02 Head Expressions (each sent at two sizes), 03 Scroll, 04 Landing.
  - Saul Character Bible.
  - Old Wise Worm sign-board sequence.
- **Kling:** 3.0 Standard i2v takes `elements` (frontal + 1–3 references per character, `@ElementN` in the prompt,
  combinable with start/end frames, no price change). 3.0 Turbo does not.
- **Built:**
  - `library/sheet_crops.yaml`: named, label-free crops of the official sheets.
  - `productions/<ep>/references.yaml` plus `bbtb references`: per-shot review boards (`S0X_reference.jpg`) and
    element images.
  - Opt-in header `elements: on`.
  - `{identity_bad_billy}` / `{identity_young_saul}` official descriptions.
- **Cut-outs:** an automatic defringe in `cutout.extract` removes the white halo on the silhouette edge (38,896 →
  654 edge-white pixels across 46 files). Interior whites are kept: eyes, gloves, soles, monocle.
- **Not done, on purpose:** automatic removal of "enclosed white islands". On inspection those were eye whites,
  gloves and soles, so it would have damaged the characters. Real background gaps need a `holes:` seed in
  `cutlist.yaml`.
- **Finished episodes (EP001, EP002, the Wan tests):** marked `keyframes: locked`, so their paid clips still match.
- **Wings:** the official design is wings acting as hands with feather fingers. Only smooth human hands or fists are
  off model.
