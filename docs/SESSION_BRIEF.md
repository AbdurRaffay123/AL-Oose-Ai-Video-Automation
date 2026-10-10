# Session brief (2026-10-06)

**Follow docs/PRODUCTION_FLOW.md step by step. Never skip or reorder a step. Read it at the start of every session.**

## GROUNDING RULE
GROUNDING RULE (owner, repeated 5+ times): every standing character's feet must sit on the flat walkable ground defined in ground_zones.yaml. Never on rims, ledges, edges, leaves or dark areas. Pre-flight blocks any keyframe that fails. Check the FEET panel on every approval card before approving.

## QUALITY FIRST (owner, 2026-10-06)
QUALITY FIRST. Cost is secondary. Never sacrifice quality to save $0.50. Jason's approval = more business. Bad quality =
losing the client. Spend what is needed to get it right.

## Money
- **fal.ai balance:** about **$47.44** (owner's figure; this API key can't read billing, so check fal.ai > Billing).
- **EP003 fal spend:** **$3.05** (ledger): first run $1.67, S01 retakes $1.00 (unused), S05 Standard retake $0.38 (unused).
- **ElevenLabs:** about 37,000 credits left this month (resets 2026-11-03).
- **Clip library:** 30 paid clips ($12.46) in `library/clips/CLIP_INVENTORY.md`; 8 are freely reusable (rating A).

## Episodes
| Episode | Status | Known issues |
|---|---|---|
| EP001 The Scroll and The Big Guy | Complete | White under Billy's chin is still in its Billy clips (a free clip fix is possible) |
| EP002 The Deal | Complete (35.2 s) | Saul's droopy eyes in S01; Billy's pointing hand in S04; chin white in its Billy clips |
| EP003 Rule Number One | Complete (36.5 s), best quality so far (~7.8/10) | Owner: narrator stills look bad; the YES/NO end card is too static |
| EP004 "WATCH OUT!" (pp.14–15) | **Complete (33.0 s), FINAL exported 2026-10-07** (`productions/ep004/exports/ep004_FINAL_9x16.mp4`). QA pass. Re-exported 2026-10-07: SFX rebalance + S02 bubble moved off the Snail's eyes (old finals in `exports/_previous_2026-10-07/`); end-card CTA voiced by the narrator (code 06859FDB, 65 credits); final 33.2 s | S08 Snail barely moves (Avatar); Snail eyes tinted pale green in S06. Spend $5.38 fal + ~210 credits |

## Next (in order)
1. Asset audit: **done** (`library/clips/CLIP_INVENTORY.md`).
2. EP004 concept: **shown to the owner**.
3. Owner approves the concept.
4. Script written.
5. Pre-production quality sheet (`./bbtb preprod`).
6. Owner approves every prompt.
7. Generate, then the owner approves each clip's frame sheet (`./bbtb approve-clip`) before anything is assembled.

## Permanent rules (also in CLAUDE.md)
1. Red-background test before any Billy generation.
2. `{identity_young_saul}` in every Saul prompt.
3. Saul references lead with a face close-up.
4. `saul_eyes` in every Saul shot's negatives.
5. Explain the EXACT movements in the prompt.
6. Never rely on the AI to guess.
7. Fix artifacts for free at render time; don't regenerate to fix a background flaw.
8. `./bbtb audit` after every change.
9. All tests pass before generation.
10. Report the balance after every paid call.
12. Asset audit first; reuse clips (`reuse:<ID>`); no static stills; owner approves every clip's frame sheet before assembly; dynamic end cards.
11. Saul talking shots: currently the best option is Kling Avatar (0.5 s squint only). Standard is worse (37% droopy
    frames); Turbo is worst. The art-based approach needs high-res files from Jason.

## ASK JASON
> "High resolution Saul expression art files (vector or 300 dpi minimum) for close-up shots. The character sheet images
> are too low resolution for close-up animation." (His expression faces are only about 100 px on the sheets we have.)

## Saul eye drift (2026-10-06)
| Shot | Engine | Drift | Fix |
|---|---|---|---|
| EP003 S05 "Ball time" | Avatar | squint ~60% for 0.5 s mid-line (17.1–17.6 s) | **Kept (owner).** Std retake ($0.38) was worse (37% droopy); art-based close-up rejected (blurry) |
| EP002 S01 "Excuse me…" | Turbo | droopy half-closed eyes ~5 s | Std retake set up ($0.76), blocked by EP002 spend_cap 4.5 (owner must raise it) |
| EP002 S05 riding | Turbo | two short laughing squints | needs the riding cut-out reviewed (red test) first |
| EP001 S03, EP002 S03 | Avatar | none measured | keep |
