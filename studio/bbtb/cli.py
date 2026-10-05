"""bbtb - AL-Oose studio command line.

  bbtb make <script.md>                 free run: voices, keyframes, cost + approval code, animatic
  bbtb make <script.md> --approve CODE  generate (spends money, within the script's budget)
  bbtb make <script.md> --only S04,S07  same, but only those shots (cheap tests)
  bbtb make ... --max-cost 0.20         hard ceiling for this run (refuses, never trims)
  bbtb status <script.md>               where a production is and what to do next
  bbtb resume <script.md>               re-check LTX jobs that were submitted (never resubmits)
  bbtb export <script.md>               free re-export from existing clips (e.g. after a trim:<s> edit)
  bbtb make <script.md> --placeholder-voices   free timing preview before voices exist (never final)
  bbtb voices ...                       voice setup: status, assess, account, clone, set, verify, test,
                                        approve, use, tune, render  (see `bbtb voices -h`)
  bbtb audit [--rebuild]                verify originals are unchanged (or rebuild the registry)
  bbtb refs analyze <video|folder>...   free: contact sheet + motion stats of reference clips
  bbtb cutouts [--only PREFIX]          rebuild character cut-outs from library/cutlist.yaml
bbtb references <script.md>           free: scene reference boards + Kling 3.0 character-reference images
bbtb music                            free: analyse Jason's music (library/audio/music/jason/MUSIC_INVENTORY.md)
bbtb preprod <script.md>              free: PRE_PRODUCTION.md (GO/NO-GO per shot, risk order, cost plan) + PROMPTS.md
  bbtb plates [--only PREFIX]           crop background plates (library/backgrounds.yaml `crop:`) to library/backgrounds/
  bbtb ltx forget <request_hash>        clear an 'unknown' ledger row after checking the LTX console
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import env, voice_cli


def cmd_make(a):
    from . import pipeline
    from .voices import VoicesNotReady
    try:
        s = pipeline.make(Path(a.script), approve=a.approve, only=a.only.split(",") if a.only else None,
                          placeholder_voices=a.placeholder_voices, max_cost=a.max_cost)
    except VoicesNotReady as exc:
        print("STOPPED at the voice stage (nothing generated, nothing spent):\n  " + "\n  ".join(exc.problems))
        if any("no ElevenLabs voice" in p for p in exc.problems):
            print("\nNext: set up the missing voices once (see `./bbtb voices status`), then re-run.")
        elif exc.estimate.get("lines"):
            print(f"\nNext: ./bbtb voices render {a.script}   (shows the cost and an approval code)")
        print(f"Or a free timing preview with obvious placeholder voices: ./bbtb make {a.script} --placeholder-voices")
        sys.exit(1)
    print(f"\n{s['title']}  |  {s['shots']} shots  |  {s['duration']:.1f}s")
    print(s["table"])
    print(f"  {'-' * 44}\n  new spend ${s['new_cost']:.2f}   already spent ${s['spent']:.2f}   budget ${s['budget']:.2f}")
    print("\nVoices:")
    print("\n".join(s["voices"]))
    if s.get("voice_blockers"):
        print(f"  -> {len(s['voice_blockers'])} talking shot(s) can't be generated until their voices are final.")
    for sid, checks in s.get("preflight", {}).items():
        print(f"\nPre-flight {sid}:")
        for c in checks:
            print(f"  {c.status:<4}  {c.name:<22} {c.detail}")
    if s.get("caps"):
        print("\nSPENDING LIMITS - this run would be refused:\n  " + "\n  ".join(s["caps"]))
    print(f"\nAnimatic (free preview): {s['animatic']}")
    if "next" in s and s.get("voice_blockers"):
        print("\nNOTHING HAS BEEN SPENT. Paid generation is not available yet: some talking shots use voices "
              "that are not final (see Voices above). Set up and approve the voices first.")
    elif "next" in s:
        print(f"\nNOTHING HAS BEEN SPENT. Approval code: {s['code']}\n{s['next']}")
    else:
        for r in s.get("clip_qa", []):
            print(f"\nClip QA {r['shot']}: {r['verdict']}  (consistency {r['consistency']}/10)  {r['clip']}")
            for row in r["rows"]:
                print(f"  {row['result']:<4}  {row['check']:<36} expected {row['expected']:<18} got {row['actual']}")
            print(f"  frames: {r['sheet']}")
            if r["consistency"] < 7:
                print("  !! consistency below 7/10 - flagged before review")
            if sys.platform == "darwin":
                import subprocess
                subprocess.run(["open", "-a", "QuickTime Player", r["clip"]], check=False)
        if "balance" in s:
            bal, note = s["balance"]
            print(f"\nfal.ai balance: " + (f"${bal:.2f} {note}" if bal is not None else note))
        print(f"Ledger spend for this episode so far: ${s.get('spent_after', 0):.2f}")
        print(f"\nFinal video: {s['final']}\nQA: {s['qa']}  ->  {s['qa_report']}")
        for f in s.get("failures", []):
            print(f"  ! {f}")


def cmd_status(a):
    from .ledger import Ledger
    root = Path(a.script).resolve().parent
    plan = root / "plan.json"
    led = Ledger(root / "ledger.jsonl")
    exports = sorted((root / "exports").glob("*_9x16.mp4")) if (root / "exports").exists() else []
    if not plan.exists():
        print(f"Not started. Next: bbtb make {a.script}")
        return
    p = json.loads(plan.read_text())
    done = [j for j in p["jobs"] if (root / "shots" / j["shot"] / "ltx.mp4").exists()]
    open_rows = [r for r in led.latest().values() if r.get("state") in ("intent", "submitted", "unknown")]
    print(f"{p['title']}: {len(p['shots'])} shots, LTX clips {len(done)}/{len(p['jobs'])}, spent ${led.spent():.2f} of ${p['meta']['budget']:.2f}")
    if open_rows:
        print(f"{len(open_rows)} paid job(s) not finished. Next: bbtb resume {a.script}")
    elif len(done) < len(p["jobs"]):
        print(f"Next: review preview/animatic.mp4, then bbtb make {a.script} --approve {p['approval_code']}")
    elif exports:
        print(f"Latest export: {exports[-1]}  (QA report in reviews/)")
    else:
        print(f"Next: bbtb make {a.script} --approve {p['approval_code']}")


def cmd_resume(a):
    from . import fal, ltx, pipeline
    prod = pipeline.prepare(Path(a.script))
    client = ltx.Client(prod.ledger)
    fal_client = fal.Client(prod.ledger)
    for j in pipeline.jobs(prod):
        row = prod.ledger.find(j.request_hash())
        if not row or pipeline.is_done(j):
            continue
        if isinstance(j, fal.Job) and row.get("state") in ("submitted", "completed"):
            print(f"{j.shot_id}: checking fal request {row.get('request_id')} ...")
            try:
                j.out_path = Path(row.get("out", j.out_path))
                fal_client.wait(j, row)
                print(f"{j.shot_id}: downloaded")
            except fal.FalError as exc:
                print(f"{j.shot_id}: {exc}")
            continue
        if row.get("state") == "submitted":
            print(f"{j.shot_id}: checking job {row['job_id']} ...")
            try:
                client.wait(j, row["job_id"])
                print(f"{j.shot_id}: downloaded")
            except ltx.LtxError as exc:
                print(f"{j.shot_id}: {exc}")
        elif row.get("state") in ("intent", "unknown"):
            print(f"{j.shot_id}: state '{row['state']}' - the submit may or may not have reached LTX. Check the "
                  f"LTX console; if it is not there, run: bbtb ltx forget {j.request_hash()}")


def cmd_export(a):
    from . import pipeline
    s = pipeline.export(Path(a.script))
    print(f"Re-exported for free ({s['duration']:.1f}s): {s['final']}")
    print(f"QA: {s['qa']}  ->  {s['qa_report']}")
    if s["missing"]:
        print(f"Local stand-ins (no generated clip): {', '.join(s['missing'])}")


def cmd_audit(a):
    from . import registry
    if a.rebuild:
        print(f"registry rebuilt: {len(registry.build())} originals hashed")
        return
    r = registry.verify()
    if any(r.values()):
        print("ORIGINALS CHANGED - stop and restore from backup before producing anything:")
        for k, v in r.items():
            for x in v:
                print(f"  {k}: {x}")
        sys.exit(1)
    print(f"all {len(registry.load())} originals unchanged")


def cmd_cutouts(a):
    from . import cutout
    done = cutout.run(a.only)
    print(f"{len(done)} cut-outs written to library/derived/cutouts/ (status: draft until approved)")


def cmd_music(a):
    from . import music_lib
    inv = music_lib.scan()
    print(f"{len(inv.get('tracks', {}))} track(s) analysed -> {music_lib.DIR / 'MUSIC_INVENTORY.md'}")


def cmd_preprod(a):
    from pathlib import Path
    from . import pipeline
    out = pipeline.preprod(Path(a.script))
    print(f"  {out}\n  {out.with_name('PROMPTS.md')}")


def cmd_references(a):
    from pathlib import Path
    from . import references
    from .script_parser import load_characters
    for b in references.build(Path(a.script).resolve().parent, load_characters()):
        print(f"  {b}")
    print("element images in productions/<ep>/scene_references/elements/ (used with header `elements: on`)")


def cmd_plates(a):
    from . import bgplates
    for d in bgplates.build(a.only):
        print(f"{d['scene']:<16} {d['size'][0]}x{d['size'][1]}  -> {d['file']}")


def cmd_refs(a):
    from . import refs
    vids = refs.collect(a.paths)
    if not vids:
        sys.exit("no videos found (.mp4/.mov/.m4v/.webm)")
    for v in vids:
        s = refs.analyze(v, a.max_seconds)
        print(f"{v.name}: {s['width']}x{s['height']} {s['fps']:g} fps {s['seconds']}s audio={s['audio']} | "
              f"camera {s['camera']} | motion {s['motion_mean']} | cuts {s['cuts'][:6]} -> {s['sheet']}")


def cmd_forget(a):
    from .ledger import Ledger
    root = Path(a.script).resolve().parent
    led = Ledger(root / "ledger.jsonl")
    row = led.find(a.request_hash)
    if not row or row.get("state") not in ("intent", "unknown"):
        sys.exit("only 'intent'/'unknown' rows can be forgotten")
    led.write(a.request_hash, state="failed", error="owner confirmed not billed (forgotten)", cost_estimate=0.0)
    print("cleared; the shot can be submitted again")


def main(argv=None):
    p = argparse.ArgumentParser(prog="bbtb", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make"); m.add_argument("script"); m.add_argument("--approve")
    m.add_argument("--only", help="comma-separated shot ids, e.g. S04,S07")
    m.add_argument("--max-cost", type=float, help="refuse the paid run if it would cost more than this (USD)")
    m.add_argument("--placeholder-voices", action="store_true",
                   help="free timing preview with macOS voices where speech is missing (never final)")
    m.set_defaults(f=cmd_make)
    s = sub.add_parser("status"); s.add_argument("script"); s.set_defaults(f=cmd_status)
    ex = sub.add_parser("export", help="free re-export from existing clips (no paid calls)")
    ex.add_argument("script"); ex.set_defaults(f=cmd_export)
    r = sub.add_parser("resume"); r.add_argument("script"); r.set_defaults(f=cmd_resume)
    voice_cli.register(sub)
    au = sub.add_parser("audit"); au.add_argument("--rebuild", action="store_true"); au.set_defaults(f=cmd_audit)
    cu = sub.add_parser("cutouts"); cu.add_argument("--only"); cu.set_defaults(f=cmd_cutouts)
    mu = sub.add_parser("music", help="free: analyse Jason's tracks in library/audio/music/jason/")
    mu.set_defaults(f=cmd_music)
    pp = sub.add_parser("preprod", help="free: PRE_PRODUCTION.md (GO/NO-GO, cost plan) + PROMPTS.md")
    pp.add_argument("script"); pp.set_defaults(f=cmd_preprod)
    rf = sub.add_parser("references", help="build scene reference boards + Kling element images (free)")
    rf.add_argument("script"); rf.set_defaults(f=cmd_references)
    pl = sub.add_parser("plates", help="crop background plates from the originals (free)")
    pl.add_argument("--only"); pl.set_defaults(f=cmd_plates)
    rf = sub.add_parser("refs"); rfs = rf.add_subparsers(dest="rcmd", required=True)
    ra = rfs.add_parser("analyze"); ra.add_argument("paths", nargs="+"); ra.add_argument("--max-seconds", type=float, default=30.0)
    ra.set_defaults(f=cmd_refs)
    l = sub.add_parser("ltx"); ls = l.add_subparsers(dest="lcmd", required=True)
    fg = ls.add_parser("forget"); fg.add_argument("script"); fg.add_argument("request_hash"); fg.set_defaults(f=cmd_forget)
    a = p.parse_args(argv)
    try:
        a.f(a)
    except Exception as exc:  # plain-language errors, secrets redacted
        sys.exit(f"error: {env.redact(str(exc))}")


if __name__ == "__main__":
    main()
