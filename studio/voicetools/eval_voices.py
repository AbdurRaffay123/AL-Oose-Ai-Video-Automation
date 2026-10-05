"""Objective clone test (run with .venv-voice/bin/python). Free and local.

For each character x settings x test line: Chatterbox generates the line from the character's
reference, then we score it:
  similarity  Resemblyzer cosine to the centroid of the character's ORIGINAL clips
  baseline    the same score for the originals themselves (leave-one-out) - what "sounds like
              this character" means numerically
  wer         Whisper word error rate against the intended text (intelligibility)
Writes <out>/results.json and the WAVs, for a human listening check.
"""
from __future__ import annotations

import argparse
import json
import re
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def words(t: str) -> list[str]:
    return re.sub(r"[^a-z0-9' ]+", " ", t.lower().replace("gunna", "gonna")).split()


def wer(ref: str, hyp: str) -> float:
    r, h = words(ref), words(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev, d[j] = d[j], cur
    return round(d[len(h)] / max(len(r), 1), 3)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True, help="JSON: {char: {ref, originals:[...], lines:[...]}}")
    p.add_argument("--out", required=True)
    p.add_argument("--settings", default='[{"exaggeration":0.5,"cfg":0.5},{"exaggeration":0.8,"cfg":0.3}]')
    a = p.parse_args()
    import numpy as np
    import torch
    import torchaudio
    import whisper
    from chatterbox.tts import ChatterboxTTS
    from resemblyzer import VoiceEncoder, preprocess_wav

    plan = json.load(open(a.plan))
    settings = json.loads(a.settings)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    tts = ChatterboxTTS.from_pretrained(device=dev)
    asr = whisper.load_model("medium.en")
    enc = VoiceEncoder(verbose=False)

    def embed(path):
        return enc.embed_utterance(preprocess_wav(path))

    results = {}
    for char, spec in plan.items():
        orig = [embed(o) for o in spec["originals"]]
        centroid = np.mean(orig, axis=0)
        centroid /= np.linalg.norm(centroid)
        loo = []
        for i, e in enumerate(orig):
            if len(orig) > 1:
                rest = np.mean([x for j, x in enumerate(orig) if j != i], axis=0)
                loo.append(float(np.dot(e, rest / np.linalg.norm(rest))))
        rows = []
        for si, st in enumerate(settings):
            for li, text in enumerate(spec["lines"]):
                path = out / f"{char}_s{si}_l{li}.wav"
                wav = tts.generate(text, audio_prompt_path=spec["ref"], exaggeration=st["exaggeration"],
                                   cfg_weight=st["cfg"], temperature=st.get("temperature", 0.8))
                torchaudio.save(str(path), wav.cpu(), tts.sr)
                hyp = asr.transcribe(str(path), language="en", fp16=False)["text"].strip()
                rows.append({"settings": st, "text": text, "file": path.name, "heard": hyp, "wer": wer(text, hyp),
                             "similarity": round(float(np.dot(embed(path), centroid)), 3),
                             "seconds": round(wav.shape[-1] / tts.sr, 2)})
                print(char, si, li, rows[-1]["similarity"], rows[-1]["wer"], flush=True)
        results[char] = {"baseline_similarity": round(float(np.mean(loo)), 3) if loo else None,
                         "reference": spec["ref"], "rows": rows}
    (out / "results.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
