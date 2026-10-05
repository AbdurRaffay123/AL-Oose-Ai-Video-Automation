# LTX API facts (verified 2026-10-03, https://docs.ltx.io)

## Endpoints
- V2 async only; V1 is deprecated after 2026-10-26.
- Submit with `POST https://api.ltx.io/v2/{image-to-video|audio-to-video}`; it returns 202 `{id}`.
- Poll with `GET /v2/<endpoint>/<id>`. Status: pending → processing → completed | failed.
- Download from `result.video_url` straight away, because the URL expires. Job status is kept for only 24 h.

## Models and limits
- image-to-video with ltx-2-3-pro: duration must be 6, 8 or 10 s; output is 16:9 or 9:16 only.
  - We always send `generate_audio:false`.
  - `last_frame_uri` sets the end frame; `camera_motion:static` keeps the camera still.
- audio-to-video with ltx-2-3-pro: output length follows the audio, up to 20 s at 720p/1080p.
  - Audio is billed per second.
  - Send MP3, not PCM. Our master voice track always replaces whatever audio LTX returns.

## Prices (USD per second)

| Endpoint | 720p | 1080p |
|---|---|---|
| i2v pro | 0.04 | 0.08 |
| a2v pro | 0.06 | 0.10 |

## Inputs
- Data URIs: images up to 7 MB, audio up to 15 MB.
- Default concurrency is 2.

## Errors
- 402 = out of credits; 422 = safety filter. Neither is retryable.
- 429 = queue full; honour `Retry-After`. 500/503/529 are retryable when polling.
- The API has no idempotency key and no documented cancel, and it doesn't say whether failed jobs are billed. Hence the ledger-before-POST rule.
