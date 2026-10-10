# TEST Kling O3 vs Kling 3.0 Standard: EP001 Billy at the rocks
format: 9:16   resolution: 720p   budget: 1   captions: off   action_engine: kling3   spend_cap: 1   session_cap: 1   shot_cap: 0.40   negatives: billy_hands   elements: on

<!-- Owner 2026-10-08: model test, two cards, one generation each. Same start/end keyframe (billy_tophat_34left,       -->
<!-- 1.55x push-in on the EP001 plate BIG_WORM_HOLE), same prompt (template test_o3_suspicious = Section 6 body), same  -->
<!-- official references. S01 = Kling O3 reference-to-video with EP004 S07 (0-3.0 s) as @Element1's reference video;  -->
<!-- O3 has no negative field, so the blocking list goes into the prompt as "Never: ...". S02 = Kling 3.0 Standard     -->
<!-- control with the same list as its negative prompt. Nothing in productions/ep001-big-guy is used or changed.       -->

## SCENE BIG_WORM_HOLE
ACTION [id:S01, medium, kling3std, refs, o3, refvideo:refs/billy_ep004_s07_0-3s.mp4, never:o3_never_billy, prompt:test_o3_suspicious, neg:billy_model+billy_watch_still, 34left>34left, zoom:1.55, loop, gen:4]: Bad Billy looks around the rocks for the worm, suspicious.
ACTION [id:S02, medium, kling3std, refs, prompt:test_o3_suspicious, neg:billy_model+billy_watch_still, 34left>34left, zoom:1.55, loop, gen:4]: Bad Billy looks around the rocks for the worm, suspicious.
