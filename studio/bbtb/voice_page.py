"""Build reviews/voice_test/index.html: originals next to clones, with the objective scores.

Open it in a browser and listen. Approve a character only if the clone sounds like the original.
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


def build(test_dir: Path, plan: dict) -> Path:
    res = json.loads((test_dir / "results.json").read_text())
    orig_dir = test_dir / "originals"
    orig_dir.mkdir(exist_ok=True)
    parts = ["<!doctype html><meta charset=utf-8><title>Voice test</title>",
             "<style>body{font:15px system-ui;margin:24px;max-width:1100px}td,th{padding:6px 10px;border-bottom:1px solid #ddd;"
             "text-align:left}audio{height:32px}.bad{color:#b00}.ok{color:#070}h2{margin-top:36px}</style>",
             "<h1>Voice clone test (local Chatterbox, free)</h1>",
             "<p><b>similarity</b>: how close the clone is to the character's real recordings (1.0 = identical). "
             "<b>baseline</b> is how similar the real clips are to each other; a good clone is near or above it. "
             "<b>WER</b>: share of words Whisper mis-heard (0 = perfectly understandable).</p>"]
    for char, r in res.items():
        base = r["baseline_similarity"]
        parts.append(f"<h2>{html.escape(char)}</h2><p>baseline similarity: {base}</p><p>Originals: ")
        for o in plan[char]["originals"]:
            dst = orig_dir / f"{char}_{Path(o).stem[:40].replace(' ', '_')}.wav"
            if not dst.exists():
                shutil.copy(o, dst)
            parts.append(f"<span title='{html.escape(Path(o).name)}'><audio controls src='originals/{dst.name}'></audio></span> ")
        parts.append("</p><table><tr><th>settings</th><th>line</th><th>heard as</th><th>similarity</th><th>WER</th><th></th></tr>")
        for row in r["rows"]:
            good_sim = base is None or row["similarity"] >= base - 0.05
            st = row["settings"]
            parts.append(
                f"<tr><td>exag {st['exaggeration']} / cfg {st['cfg']}</td><td>{html.escape(row['text'])}</td>"
                f"<td>{html.escape(row['heard'])}</td><td class={'ok' if good_sim else 'bad'}>{row['similarity']}</td>"
                f"<td class={'ok' if row['wer'] <= 0.15 else 'bad'}>{row['wer']}</td>"
                f"<td><audio controls src='{row['file']}'></audio></td></tr>")
        parts.append("</table>")
    out = test_dir / "index.html"
    out.write_text("\n".join(parts))
    return out
