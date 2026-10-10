"""bbtb - AL-Oose studio command line.

  bbtb make <script.md>                 free run: voices, keyframes, cost + approval code, animatic
  bbtb make <script.md> --approve CODE  generate (spends money, within the script's budget)
  bbtb make <script.md> --only S04,S07  same, but only those shots (cheap tests)
  bbtb make ... --max-cost 0.20         hard ceiling for this run (refuses, never trims)
  bbtb status <script.md>               where a production is and what to do next
  bbtb resume <script.md>               re-check LTX jobs that were submitted (never resubmits)
  bbtb export <script.md>               free re-export from existing clips (e.g. after a trim:<s> edit)
bbtb review <script.md>               free: frame sheets (every 0.5 s) + owner-approval status of each generated clip
bbtb approve-clip <script.md> S01,S04 record the OWNER's approval after they looked at the sheets (gate for assembly)
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
  bbtb grounds [--only PREFIX]          overlays of each plate's walkable ground / forbidden areas (ground_zones.yaml)
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
                          placeholder_voices=a.placeholder_voices, max_cost=a.max_cost,
                          assemble=not a.no_assemble, auto_approve=a.auto_approve)
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
        for p in s.get("review_sheets", []):
            print(f"Frame sheet for review: {p}")
        if s.get("final"):
            print(f"\nFinal video: {s['final']}\nQA: {s['qa']}  ->  {s['qa_report']}")
        elif s.get("unreviewed"):
            print(f"\nNOT ASSEMBLED - waiting for the owner to approve: {', '.join(s['unreviewed'])} "
                  f"(look at the frame sheets, then ./bbtb approve-clip {a.script} {','.join(s['unreviewed'])})")
        else:
            print("\nNot assembled (--no-assemble): the new clip is in shots/<id>/; run `bbtb export` when ready.")
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


def cmd_review(a):
    from . import pipeline, review
    prod = pipeline.prepare(Path(a.script))
    js = [j for j in pipeline.jobs(prod) if pipeline.is_done(j)]
    for j, p in zip(js, pipeline.review_sheets(prod, js)):
        ok = review.approved(prod.root, j.shot_id, j.request_hash())
        print(f"  {j.shot_id}: {'APPROVED' if ok else 'waiting for owner'}  {p}")


def cmd_approve_clip(a):
    from . import pipeline, review
    prod = pipeline.prepare(Path(a.script))
    wanted = {x.strip().upper() for x in a.shots.split(",")}
    for j in pipeline.jobs(prod):
        if j.shot_id.upper() in wanted:                  # case-insensitive: pinned ids like S01b
            if not pipeline.is_done(j):
                sys.exit(f"{j.shot_id}: no generated clip to approve")
            review.approve(prod.root, j.shot_id, j.request_hash(), a.note)
            print(f"  {j.shot_id}: approved (this exact take)")
            wanted.discard(j.shot_id.upper())
    if wanted:
        sys.exit(f"no generated clip for: {', '.join(sorted(wanted))}")


def cmd_export(a):
    from . import pipeline
    try:
        s = pipeline.export(Path(a.script), auto_approve=a.auto_approve, no_music=a.no_music)
    except RuntimeError as exc:
        sys.exit(str(exc))
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
    from .paths import DERIVED
    if not a.review:
        done = cutout.run(a.only)
        print(f"{len(done)} cut-outs written to library/derived/cutouts/ (status: draft until approved)")
    fails = []
    for p in sorted((DERIVED / "cutouts").glob(f"{a.review or a.only or ''}*.png")):
        r = cutout.red_test(p.stem)
        if a.review or not r["ok"]:
            cutout.red_review(p.stem, DERIVED / "cutout_review" / f"{p.stem}.png")
        if not r["ok"]:
            fails.append(f"  FAIL {p.stem}: undecided white {r['undecided'][:4]}, edge white {r['edge_white']}px")
    print(f"red-background test: {'all pass' if not fails else str(len(fails)) + ' fail (blocked from keyframes)'}")
    print("\n".join(fails))
    if fails:
        print("Review images: library/derived/cutout_review/<id>.png (blue = undecided). In library/cutlist.yaml add a "
              "`holes:` sheet point to clear trapped background, or a `keep_white:` point to approve white art.")


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
    from .script_parser import load_characters, parse_file
    if a.characters:
        for b in references.build_characters():
            print(f"  {b}")
        return
    only = [x.strip().upper() for x in a.only.split(",")] if a.only else None
    if parse_file(Path(a.script)).meta.get("keyframes") == "locked" and not only:
        sys.exit("This episode is `keyframes: locked` (finished): rebuilding its reference images would orphan its paid "
                 "clips. To remake specific shots use --only S01[,S07] (only those shots' images are rebuilt).")
    for b in references.build(Path(a.script).resolve().parent, load_characters(), only=only):
        print(f"  {b}")
    print("element images in productions/<ep>/scene_references/elements/ (used with header `elements: on`)")


def cmd_plates(a):
    from . import bgplates
    for d in bgplates.build(a.only):
        print(f"{d['scene']:<16} {d['size'][0]}x{d['size'][1]}  -> {d['file']}")


def cmd_sfx(a):
    import hashlib, json
    from . import audio_bed
    from .ledger import Ledger
    names = [n.strip() for n in a.names.split(",") if n.strip()]
    plan = audio_bed.sfx_plan(names)
    if not plan:
        print("Nothing to buy: every named sound already exists (local or cached).")
        return
    code = hashlib.sha256(("sfx|" + json.dumps([[p["name"], p["prompt"], p["seconds"]] for p in plan])).encode()
                          ).hexdigest()[:8].upper()
    for p in plan:
        print(f"  {p['name']:<8} {p['seconds'] or 'auto'} s  ~{p['credits']} credits   \"{p['prompt']}\"")
    print(f"Total: ~{sum(p['credits'] for p in plan)} ElevenLabs credits (one request per sound, never retried).")
    if a.approve is None:
        print(f"NOTHING SPENT. To generate: ./bbtb sfx {a.script} {a.names} --approve {code}")
        return
    if a.approve.strip().upper() != code:
        sys.exit(f"Approval code {a.approve} does not match the current plan ({code}).")
    led = Ledger(Path(a.script).resolve().parent / "ledger.jsonl")
    for p in plan:
        print(p["name"], "->", audio_bed.sfx(p["name"], led, allow_paid=True))


def cmd_grounds(a):
    from . import grounding
    for p in grounding.build_overlays(a.only):
        print(p)
    print("green = walkable ground, red = forbidden (library/backgrounds/ground_zones.yaml)")


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
    m.add_argument("--no-assemble", action="store_true", help="generate + clip QA only; do not build the final video")
    m.add_argument("--auto-approve", action="store_true", help="TESTS ONLY: skip the owner's frame-review gate")
    m.add_argument("--placeholder-voices", action="store_true",
                   help="free timing preview with macOS voices where speech is missing (never final)")
    m.set_defaults(f=cmd_make)
    s = sub.add_parser("status"); s.add_argument("script"); s.set_defaults(f=cmd_status)
    ex = sub.add_parser("export", help="free re-export from existing clips (no paid calls)")
    ex.add_argument("script"); ex.add_argument("--auto-approve", action="store_true", help="TESTS ONLY: skip the review gate")
    ex.add_argument("--no-music", action="store_true", help="delivery copy for Jason: voices + SFX only, *_nomusic.mp4")
    ex.set_defaults(f=cmd_export)
    rv = sub.add_parser("review", help="free: frame sheets (every 0.5 s) + approval status of every generated clip")
    rv.add_argument("script"); rv.set_defaults(f=cmd_review)
    ap = sub.add_parser("approve-clip", help="record the OWNER's approval of reviewed clips (after they saw the sheets)")
    ap.add_argument("script"); ap.add_argument("shots"); ap.add_argument("--note", default="")
    ap.set_defaults(f=cmd_approve_clip)
    r = sub.add_parser("resume"); r.add_argument("script"); r.set_defaults(f=cmd_resume)
    voice_cli.register(sub)
    au = sub.add_parser("audit"); au.add_argument("--rebuild", action="store_true"); au.set_defaults(f=cmd_audit)
    cu = sub.add_parser("cutouts"); cu.add_argument("--only"); cu.add_argument("--review", metavar="PREFIX")
    cu.set_defaults(f=cmd_cutouts)
    mu = sub.add_parser("music", help="free: analyse Jason's tracks in library/audio/music/jason/")
    mu.set_defaults(f=cmd_music)
    pp = sub.add_parser("preprod", help="free: PRE_PRODUCTION.md (GO/NO-GO, cost plan) + PROMPTS.md")
    pp.add_argument("script"); pp.set_defaults(f=cmd_preprod)
    rf = sub.add_parser("references", help="build scene reference boards + Kling element images (free)")
    rf.add_argument("--only", help="rebuild only these shots (allowed on a locked episode, to remake them)")
    rf.add_argument("script", nargs="?"); rf.add_argument("--characters", action="store_true",
                                                         help="build reusable sets in library/scene_references/<char>/")
    rf.set_defaults(f=cmd_references)
    pl = sub.add_parser("plates", help="crop background plates from the originals (free)")
    pl.add_argument("--only"); pl.set_defaults(f=cmd_plates)
    sx = sub.add_parser("sfx", help="price (free) or buy (--approve) named ElevenLabs sound effects")
    sx.add_argument("script"); sx.add_argument("names"); sx.add_argument("--approve"); sx.set_defaults(f=cmd_sfx)
    gz = sub.add_parser("grounds", help="draw each plate's walkable ground (green) and forbidden areas (red) (free)")
    gz.add_argument("--only"); gz.set_defaults(f=cmd_grounds)
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
