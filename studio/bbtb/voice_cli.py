"""`bbtb voices ...` - one-time voice setup and verification. Free unless a command says 💲.

  status                          every character: recordings, verdict, voice ID, rights, approval
  assess [character]              measure each recording (speech length, noise, clipping, pitch)
  account                         ElevenLabs plan, credits left, cloning allowed (free check)
  reclone <character> --confirm-rights          replace a clone using ALL its clone_reference clips (new first,
                                                then the old voice is deleted)
  clone <character> --confirm-rights [--allow-short]
                                  create the character's ElevenLabs voice ONCE (uses a voice slot)
  set <character> <voice_id>      use a voice already in your ElevenLabs account (e.g. a narrator)
  verify [character]              check saved voice IDs still exist (free)
  test <character> "text" [--approve CODE]       💲 the ONE short test line per character
  approve <character> --confirm-rights           owner, after listening: voice becomes FINAL
  forget <request_hash> [--script S]             clear an 'unknown' row after checking ElevenLabs History
  tune <character> [--stability N --similarity N --style N --speed N]   (resets approval)
  render <script> [--approve CODE]               💲 a script's new lines: ONE request per character, cached
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

from . import elevenlabs, media, voices
from .ledger import Ledger
from .paths import PRODUCTIONS
from .script_parser import load_characters, parse_file
from .shots import Line, lines_of

DEFAULT_EPISODE = "ep001-big-guy"


def test_dir(episode: str, state: str = "pending") -> Path:
    """ElevenLabs test samples (paid): reviews/voice_test/elevenlabs/{pending,approved,rejected}/.
    New tests land in pending/; `voices approve` moves the approved one to approved/."""
    return PRODUCTIONS / episode / "reviews" / "voice_test" / "elevenlabs" / state


def episode_ledger(episode: str) -> Path:
    return PRODUCTIONS / episode / "ledger.jsonl"


def _char(cid: str) -> dict:
    chars = load_characters()
    if cid not in chars:
        sys.exit(f"unknown character '{cid}'. Known: {', '.join(chars)}")
    return chars[cid]


def status(a):
    data = voices.registry_state()
    print(f"default provider: {data['defaults']['provider']}  model: {data['defaults']['model_id']}\n")
    print(f"{'character':<11} {'speech':>7} {'recordings':<13} {'provider':<11} {'voice id':<14} rights  approved")
    for cid, c in load_characters().items():
        cfg = data["characters"].get(cid) or {}
        files = voices.source_files(c)
        a = cfg.get("assessment") or (voices.assess(cid, c) if files else {"verdict": "none", "speech_seconds": 0})
        vid = (cfg.get("elevenlabs") or {}).get("voice_id")
        print(f"{cid:<11} {a['speech_seconds']:>6}s {a['verdict']:<13} {voices.provider_for(cid, data):<11} "
              f"{(vid[:10] + '…') if vid else 'NONE':<14} {'yes' if cfg.get('rights_confirmed') else 'NO':<7} "
              f"{'yes' if cfg.get('approved') else 'NO'}")
    need = [cid for cid, c in load_characters().items() if c.get("voice", {}).get("needed", True)
            and not ((data["characters"].get(cid) or {}).get("elevenlabs") or {}).get("voice_id")]
    print("\nNeeds a voice: " + (", ".join(need) or "none") + "   (big_guy: no dialogue, voice not needed)")


def assess(a):
    data = voices.registry_state()
    targets = [a.character] if a.character else [k for k, c in load_characters().items()
                                                 if c.get("voice", {}).get("needed", True)]
    for cid in targets:
        c = _char(cid)
        r = voices.assess(cid, c)
        print(f"\n{c['display_name']} ({cid}): {r['verdict'].upper()} - {r['note']}")
        for clip in r["clips"]:
            print(f"   {clip['file'][:58]:<58} {clip['seconds']:>5}s  speech {clip['speech_seconds']:>4}s  "
                  f"noise {clip['noise_floor_db']:>6} dB  clipped {clip['clipped_samples']:>3}  pitch {clip['pitch_median_hz']}"
                  + (f"  same-speaker {clip['same_speaker_score']}" if clip.get("same_speaker_score") is not None else ""))
        voices.char_cfg(data, cid)["assessment"] = {k: r[k] for k in ("verdict", "speech_seconds", "note")}
    voices.save_registry(data)


def account(a):
    try:
        s = elevenlabs.Client().subscription()
    except elevenlabs.ElevenLabsError as exc:
        sys.exit(str(exc))
    left = s.get("character_limit", 0) - s.get("character_count", 0)
    reset = time.strftime("%Y-%m-%d", time.localtime(s.get("next_character_count_reset_unix") or 0))
    print(f"plan {s.get('tier')} ({s.get('status')}); credits left {left} of {s.get('character_limit')} (resets {reset}); "
          f"instant cloning {'allowed' if s.get('can_use_instant_voice_cloning') else 'NOT allowed on this plan'}; "
          f"voice slots {s.get('voice_slots_used')}/{s.get('voice_limit')}")


def clone(a):
    c = _char(a.character)
    try:
        vid, created = voices.clone(a.character, c, a.confirm_rights, allow_short=a.allow_short)
    except (RuntimeError, elevenlabs.ElevenLabsError) as exc:
        sys.exit(str(exc))
    print(f"{c['display_name']}: {'cloned' if created else 'already cloned from the same recordings - reused'} "
          f"(voice id {vid}). Next: `./bbtb voices test {a.character} \"...\"`, listen, then approve.")


def reclone(a):
    c = _char(a.character)
    try:
        r = voices.reclone(a.character, c, a.confirm_rights)
    except (RuntimeError, elevenlabs.ElevenLabsError) as exc:
        sys.exit(str(exc))
    print(f"{c['display_name']}: NEW voice {r['new_voice_id']} from {len(r['files'])} clips joined into "
          f"{r['reference']} ({r['reference_seconds']} s).")
    print(f"  old voice {r['deleted_voice_id']} deleted" if r["deleted_voice_id"] else "  (no old voice to delete)")
    print("  Not approved: make ONE test line, listen, then decide.")


def set_voice(a):
    _char(a.character)
    voices.set_existing(a.character, a.voice_id, a.note or "set by owner")
    print(f"{a.character}: now uses ElevenLabs voice {a.voice_id} (not approved yet - test and listen first)")


def verify(a):
    data = voices.registry_state()
    client = elevenlabs.Client()
    for cid in ([a.character] if a.character else list(data["characters"])):
        vid = ((data["characters"].get(cid) or {}).get("elevenlabs") or {}).get("voice_id")
        if not vid:
            print(f"{cid:<11} no voice id")
            continue
        try:
            info = client.voice_exists(vid)
            print(f"{cid:<11} OK  {vid}  '{info['name']}' ({info['category']})")
            voices.char_cfg(data, cid)["elevenlabs"]["verified_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        except elevenlabs.ElevenLabsError as exc:
            print(f"{cid:<11} PROBLEM  {vid}: {exc}")
    voices.save_registry(data)


def test(a):
    """ONE short test line per character (owner rule). Free run shows the cost, code and output path."""
    c = _char(a.character)
    data = voices.registry_state()
    cfg = voices.char_cfg(data, a.character)
    el = cfg.get("elevenlabs") or {}
    if not el.get("voice_id"):
        sys.exit(f"{c['display_name']} has no ElevenLabs voice. Clone or set one first.")
    done = el.get("test") or {}
    if done.get("voice_id") == el["voice_id"] and Path(done.get("file", "")).exists() and not a.retest:
        print(f"{c['display_name']} already has its one test line (no charge): {done['file']}\n"
              f'  text: "{done["text"]}"\nListen to it; a second test needs --retest (owner decision).')
        return
    model = data["defaults"]["model_id"]
    settings = {**elevenlabs.DEFAULT_SETTINGS, **(el.get("settings") or {})}
    rh = elevenlabs.request_hash(el["voice_id"], model, settings, a.text)
    code = rh[-8:].upper()
    dst = test_dir(a.episode) / (f"{a.name}.wav" if a.name else f"{a.character}_test_{rh[3:11]}.wav")
    print(f"Test line for {c['display_name']} (voice {el['voice_id']}): \"{a.text}\"\n"
          f"  {len(a.text)} characters = about {len(a.text)} credits with {model}\n  will be saved as: {dst}")
    if a.approve is None:
        print(f"NOTHING SPENT. To generate: ./bbtb voices test {a.character} \"{a.text}\"{' --retest' if a.retest else ''} --approve {code}")
        return
    if a.approve.strip().upper() != code:
        sys.exit(f"approval code does not match ({code})")
    try:
        mp3 = elevenlabs.Client().tts(el["voice_id"], a.text, model, settings, dst.with_suffix(".mp3"),
                                      Ledger(episode_ledger(a.episode)), rh,
                                      meta={"line": "test", "speaker": a.character, "characters": len(a.text)},
                                      credits_estimate=len(a.text))
    except elevenlabs.ElevenLabsError as exc:
        sys.exit(str(exc))
    media.to_wav(mp3, dst, trim_silence=False)
    el["test"] = {"voice_id": el["voice_id"], "text": a.text, "file": str(dst),
                  "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    voices.save_registry(data)
    dst.with_suffix(".mp3").unlink(missing_ok=True)
    print(f"Saved {dst} ({media.duration(dst):.2f}s). Listen to it in Finder next to the original clips, then decide:\n"
          f"  approve: ./bbtb voices approve {a.character} --confirm-rights")


def forget(a):
    """Clear an 'unknown' ElevenLabs ledger row after checking ElevenLabs > History."""
    path = (Path(a.script).resolve().parent / "ledger.jsonl") if a.script else episode_ledger(a.episode)
    led = Ledger(path)
    row = led.find(a.request_hash)
    if not row or row.get("state") not in ("intent", "unknown"):
        sys.exit(f"no 'intent'/'unknown' row {a.request_hash} in {path}")
    led.write(a.request_hash, state="failed", error="owner checked ElevenLabs History: not delivered (forgotten)",
              credits_estimate=0.0)
    print("cleared; the request may be made again (it will need a new approval)")


def approve(a):
    if not a.confirm_rights:
        sys.exit("Add --confirm-rights to confirm the project holds the rights and the performer's consent, "
                 "and that you have listened to this voice and it is good enough for final videos.")
    data = voices.registry_state()
    cfg = voices.char_cfg(data, a.character)
    el = cfg.get("elevenlabs") or {}
    t = el.get("test") or {}
    if not el.get("voice_id"):
        sys.exit(f"{a.character} has no voice to approve.")
    if t.get("voice_id") != el["voice_id"] or not Path(t.get("file", "")).exists():
        sys.exit(f"Listen first: {a.character} has no test line for its current voice. "
                 f"Run `./bbtb voices test {a.character} \"...\"` (one short line), listen, then approve.")
    src = Path(t["file"])
    if src.parent.name == "pending":                        # keep the folder honest: pending/ -> approved/
        dst = src.parent.parent / "approved" / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        t["file"] = str(dst)
    cfg.update(approved=True, rights_confirmed=True, approved_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
               approved_after_test=t["file"])
    voices.save_registry(data)
    print(f"{a.character}: voice APPROVED for final videos")


def tune(a):
    data = voices.registry_state()
    el = voices.char_cfg(data, a.character).setdefault("elevenlabs", {})
    st = {**elevenlabs.DEFAULT_SETTINGS, **(el.get("settings") or {})}
    for k, v in (("stability", a.stability), ("similarity_boost", a.similarity), ("style", a.style), ("speed", a.speed)):
        if v is not None:
            st[k] = v
    el["settings"] = st
    voices.char_cfg(data, a.character)["approved"] = False
    voices.save_registry(data)
    print(f"{a.character}: settings {st} (approval reset; cached lines will be regenerated)")


def render(a):
    script = parse_file(Path(a.script))
    root = Path(a.script).resolve().parent
    chars, data = load_characters(), voices.registry_state()
    plan = voices.line_plan(lines_of(script), chars, data)
    problems = voices.group_problems(plan)
    if problems:
        sys.exit("Can't generate yet:\n  " + "\n  ".join(problems))
    est = voices.estimate(plan, root / "audio")
    from . import audio_bed
    import hashlib, json
    sfx_names = sorted({e.text.strip() for e in script.events if e.kind == "sfx"})
    sfx = audio_bed.sfx_plan(sfx_names)                   # owner 2026-10-07: one code for voices + sound effects
    if est["lines"] == 0 and not sfx:
        print("All lines and sound effects are already generated (cached) - nothing to pay for.")
        return
    if est["lines"]:
        print(f"{est['lines']} line(s) in {est['requests']} request(s) (one per character): {est['characters']} characters, "
              f"about {est['credits']} credits.")
        for sp, n in est["per_character"].items():
            print(f"  {sp:<12} {n} characters (lines joined with short pauses, sliced by ElevenLabs timestamps)")
    for x in sfx:
        print(f"  SFX {x['name']:<9} {x['seconds'] or 'auto'} s  ~{x['credits']} credits  \"{x['prompt']}\"")
    if sfx:
        est = dict(est, credits=est["credits"] + sum(x["credits"] for x in sfx),
                   code=hashlib.sha256((est.get("code", "") + json.dumps([[x["name"], x["prompt"], x["seconds"]] for x in sfx]))
                                       .encode()).hexdigest()[:8].upper())
        print(f"Total with sound effects: about {est['credits']} credits.")
    try:
        sub = elevenlabs.Client().subscription()
        left = sub["character_limit"] - sub["character_count"]
        print(f"Credits left this month: {left}.")
        if left < est["credits"]:
            sys.exit("Not enough credits for this script; nothing was generated.")
    except elevenlabs.ElevenLabsError as exc:
        print(f"(could not check remaining credits: {exc})")
    if a.approve is None:
        print(f"NOTHING SPENT. To generate: ./bbtb voices render {a.script} --approve {est['code']}")
        return
    if a.approve.strip().upper() != est["code"]:
        sys.exit(f"approval code does not match the current lines ({est['code']})")
    try:
        if est["lines"]:
            voices.render_lines(lines_of(script), chars, root / "audio", Ledger(root / "ledger.jsonl"),
                                allow_paid=True)
        for x in sfx:                                      # one request per sound, never retried
            print("SFX", x["name"], "->", audio_bed.sfx(x["name"], Ledger(root / "ledger.jsonl"), allow_paid=True))
    except (elevenlabs.ElevenLabsError, voices.VoicesNotReady, RuntimeError) as exc:
        sys.exit(f"Stopped: {exc}")
    print(f"Done. ElevenLabs lines are in {root / 'audio' / 'lines'}; next: `./bbtb make {a.script}` for the free animatic.")


def register(sub):
    v = sub.add_parser("voices", help="voice setup and verification")
    vs = v.add_subparsers(dest="vcmd", required=True)
    vs.add_parser("status").set_defaults(f=status)
    p = vs.add_parser("assess"); p.add_argument("character", nargs="?"); p.set_defaults(f=assess)
    vs.add_parser("account").set_defaults(f=account)
    p = vs.add_parser("clone"); p.add_argument("character"); p.add_argument("--confirm-rights", action="store_true")
    p.add_argument("--allow-short", action="store_true"); p.set_defaults(f=clone)
    p = vs.add_parser("set"); p.add_argument("character"); p.add_argument("voice_id"); p.add_argument("--note")
    p.set_defaults(f=set_voice)
    p = vs.add_parser("verify"); p.add_argument("character", nargs="?"); p.set_defaults(f=verify)
    p = vs.add_parser("test"); p.add_argument("character"); p.add_argument("text"); p.add_argument("--approve")
    p.add_argument("--retest", action="store_true", help="owner only: a second test line for this voice")
    p.add_argument("--episode", default=DEFAULT_EPISODE, help="where the sample is saved (reviews/voice_test/elevenlabs/)")
    p.add_argument("--name", help="output file name without .wav (default <char>_test_<hash>)")
    p.set_defaults(f=test)
    p = vs.add_parser("reclone"); p.add_argument("character"); p.add_argument("--confirm-rights", action="store_true")
    p.set_defaults(f=reclone)
    p = vs.add_parser("forget"); p.add_argument("request_hash"); p.add_argument("--script")
    p.add_argument("--episode", default=DEFAULT_EPISODE)
    p.set_defaults(f=forget)
    p = vs.add_parser("approve"); p.add_argument("character"); p.add_argument("--confirm-rights", action="store_true")
    p.set_defaults(f=approve)
    p = vs.add_parser("tune"); p.add_argument("character")
    for k in ("--stability", "--similarity", "--style", "--speed"):
        p.add_argument(k, type=float)
    p.set_defaults(f=tune)
    p = vs.add_parser("render"); p.add_argument("script"); p.add_argument("--approve"); p.set_defaults(f=render)
