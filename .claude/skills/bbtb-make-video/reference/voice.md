# Voices: ElevenLabs workflow (default)

## Where things live
- **Registry:** `library/voices.yaml` holds, per character:
  - `provider` and `elevenlabs.voice_id`;
  - `source_files` and `source_sha256` (re-cloning is skipped while these are unchanged);
  - `settings` (stability, similarity_boost, style, speed);
  - `assessment`, `rights_confirmed`, `approved`.
- **Source audio:** `voice.clone_reference` in `library/characters/<id>.yaml`, plus `clone_reference_files` for derived files such as the music-free narrator.

## Choosing a source for each line (`studio/bbtb/voices.py`)
1. The original clip, if the line's words match `voice.originals`.
2. The saved, **owner-approved** ElevenLabs voice. All of a character's new lines go out as ONE request to
   `POST /v1/text-to-speech/{voice_id}/with-timestamps` (joined with `<break time="0.7s" />`), then the result is sliced by the
   returned character times. Batches are saved in `productions/<ep>/audio/batches/`, and lines are cached by content key.
3. Otherwise **stop** (VoicesNotReady). `make --placeholder-voices` uses SILENT placeholders only and they are never final.
   There is no macOS or Chatterbox audio anywhere the owner hears.

## API facts
- Cloning: `POST /v1/voices/add` (multipart; one file per clip). It uses a voice slot; Instant Voice Cloning needs the Starter plan or higher.
- Speech is billed in credits per character of text. A model's multiplier comes from `GET /v1/models`.
- Free checks: `GET /v1/user/subscription` (credits, slots, whether cloning is allowed) and `GET /v1/voices/{id}`.
- Errors explained in plain language: missing permissions, invalid key, quota exceeded, voice not found, 429 (busy).
- There's no idempotency key. The ledger row is written before each request.
- **Any** failure (timeout or error response) is marked `unknown`, stops production, and blocks the same request until the
  owner checks ElevenLabs > History and runs `bbtb voices forget <hash>`.
- Batching does not reduce credits (1 credit per character either way, plus about 21 per break tag), but it means one
  request per character and a consistent delivery.

## Measured limits (2026-10-03)
Speech per character: Billy 5.3 s, Big Pea 5.0 s, Narrator 5.8 s (from a marketing video, music removed), Snail 4.4 s, Saul 2.3 s.
ElevenLabs advises about 60 s, so every clone is "limited". Snail and Saul are below the 5 s minimum and need new recordings:
30–60 s each, varied lines and emotions, quiet room, no music.
