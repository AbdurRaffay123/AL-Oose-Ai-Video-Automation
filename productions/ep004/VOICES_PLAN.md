# EP004 v5: voices first (step 1). Nothing generated

Owner 2026-10-07: animatic v2 rejected. New shot list (S01a, S01b, S02, S03, S05, S06, S07, S08, S09; S04 dropped).
**Voices come first: their lengths set every shot's length.**

## Every line in the new shot list
| Shot | Who | Line | Tag | Source | Length | Cost |
|---|---|---|---|---|---|---|
| S01a | Narrator | "Finally they made it to the grass under the tree. The little worms were playing ball as happy as can be." | canon:p12 | **NEW** ElevenLabs (narrator clone, approved) | ~5.5 s est. | ~104 credits |
| S01a | Young Saul? | "Ball time, everybody!" | production | reuse EP003 `L026_young_saul.wav` (paid already) | 1.30 s | free. **See question 1** |
| S01b | Narrator | "An eye that belonged to a bird with a beak, who had not had a meal in over a week." | canon:p13 | **NEW** ElevenLabs (narrator) | ~4.5 s est. | ~82 credits |
| S01b | Bad Billy | growl (no words) | production | ORIGINAL `BadBilly - GRUNCHY GROWL - Arrrrrr.wav` | 3.77 s (trim to taste) | free |
| S02 | Snail | "WATCH OUT!" | canon:p14 speech bubble | **NEW** ElevenLabs (Snail clone, NOT approved yet: test first) | ~1 s est. | ~10 credits |
| S03 | worms | "Aaah!" | production | **NEW** ElevenLabs (Saul's clone?) | ~0.8 s est. | ~5 credits. **See question 1** |
| S03 | Narrator | "He dived to the ground. He could take it no more!" | canon:p14 | rendered 2026-10-06 | 2.15 s | done |
| S06 | Narrator | "And he gobbled those worms. One, two, three... four!" | canon:p15 | rendered + free re-cut (`audio/retimed/count_punch.wav`) | 3.04 s | done |
| S07 | Bad Billy | "Mmm... delicious!" | production | **NEW** ElevenLabs (Billy clone, approved) | ~1.5 s est. | ~17 credits |
| S08 | Snail | "Ah, these birds are big trouble makers, mun." | production | ORIGINAL `34.Snail - Ah - These Birds are big trouble makers mun...wav` (denoised) | 3.39 s | free |

**New ElevenLabs lines:** about 218 characters, so about **218 credits**, in one request per character (narrator,
bad_billy, snail, plus young_saul if used). About 36,900 credits are left this month.

## Step 1a: the Snail clone test (render first, play to the owner)
`./bbtb voices test snail "WATCH OUT!" --episode ep004 --approve EF26DED8` (about 10 credits). Saved to
`reviews/voice_test/elevenlabs/pending/`.
- **Warning:** his clone is built from only 4.4 s of noisy speech (verdict "insufficient"). It may only loosely match his
  original voice.
- He is approved (`voices approve snail`) only after the owner has listened and says so.

## Step 1b: one approval code for all new lines
Comes from `./bbtb voices render productions/ep004/script.md` once the script has the new lines and the Snail is
approved (the tool blocks unapproved voices).

## Questions for the owner
1. **Saul's voice for the four worms.** The four worms of pp.12-15 are not Young Saul: Saul is the one who survives
   (he appears later, in EP003 and EP002). Giving these worms Saul's voice (his own EP003 line "Ball time, everybody!"
   and an "Aaah!") would make viewers think Saul is one of the worms Billy eats. It also breaks the "never borrow another
   character's voice" rule. Options:
   - (a) the worms giggle and scream as **sound effects** (ElevenLabs SFX: children-like cartoon giggles and a group
     "aaah", no cloned voice);
   - (b) use Saul's voice anyway (owner's call);
   - (c) no worm voices; the narrator carries S01a.
2. Billy's growl is 3.8 s: use it whole under the p.13 line, or only the last ~1.5 s "Arrrr" after it?

## Owner answers (2026-10-07)
- Q1: option (a). Worm giggles (S01a) and a group "aaah!" (S03) as ElevenLabs SOUND EFFECTS. Saul's line is removed.
- Q2: only the last ~1.5 s "Arrrr" of the growl, after the p.13 line, on Billy's eyes narrowing.
- Snail: his clone used both clips but undenoised. Rebuild from both, denoised (`voices reclone snail
  --confirm-rights`), then test "WATCH OUT!" next to his original. Fallback if it doesn't sound like him: bubble + alarm.

## 2026-10-07: Snail voice rebuilt + APPROVED; one code for everything new
- Snail clone rebuilt from both clips, denoised (voice yhIWNEcHGKN35cMcxZxi; no credits); test "WATCH OUT!" 10 credits
  (similarity 0.78 / 0.73 to his originals; originals vs each other 0.88). Owner listened and APPROVED.
- Script v5 written (`script.md`; v4 kept in `_v3_superseded/script_v4_animatic_rejected.md`).
- `./bbtb voices render productions/ep004/script.md --approve A734A549`: narrator p.12 + p.13 (209 chars), Snail
  "WATCH OUT!" (10), Billy "Mmm... delicious!" (17) = 236 credits; SFX aaah 40, alarm 60, burp 40, giggles 80, gulp 40 =
  260 credits; total ~496 credits (37,007 left). Free: Billy growl tail (original), Snail "trouble makers" (original),
  narrator p.14 + count (rendered).
