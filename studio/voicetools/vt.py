"""Local voice tools (run with .venv-voice/bin/python). Free; no network after the first model download.

  vt.py transcribe <audio...>                  Whisper transcripts (+ word timings) as JSON
  vt.py similarity --ref <wav...> --test <wav...>   Resemblyzer speaker similarity (cosine)
  vt.py synth --ref <wav> --text "..." --out <wav> [--exaggeration 0.5 --cfg 0.5 --temperature 0.8]
                                               Chatterbox zero-shot voice clone (MIT licence)
  vt.py convert --ref <wav> --src <wav> --out <wav>   Chatterbox voice conversion (keeps timing/acting)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

warnings.filterwarnings("ignore")


def cmd_transcribe(a):
    import whisper
    model = whisper.load_model(a.model)
    out = {}
    for path in a.audio:
        r = model.transcribe(path, language="en", word_timestamps=True, fp16=False)
        out[path] = {"text": r["text"].strip(),
                     "words": [{"w": w["word"].strip(), "start": round(w["start"], 2), "end": round(w["end"], 2),
                                "p": round(w.get("probability", 0), 2)} for seg in r["segments"] for w in seg.get("words", [])]}
    json.dump(out, sys.stdout, indent=1)


def cmd_similarity(a):
    import numpy as np
    from resemblyzer import VoiceEncoder, preprocess_wav
    enc = VoiceEncoder(verbose=False)
    refs = {p: enc.embed_utterance(preprocess_wav(p)) for p in a.ref}
    centroid = np.mean(list(refs.values()), axis=0)
    centroid /= np.linalg.norm(centroid)
    res = {}
    for p in a.test:
        e = enc.embed_utterance(preprocess_wav(p))
        res[p] = round(float(np.dot(e, centroid)), 3)
    json.dump(res, sys.stdout, indent=1)


def _device():
    import torch
    return "mps" if torch.backends.mps.is_available() else "cpu"


def cmd_synth(a):
    """Generate each job; with "takes" > 1 and "originals", score every take (speaker similarity to the
    original clips + Whisper word error rate) and keep the best one. Prints one JSON line per job."""
    import numpy as np
    import torchaudio
    from chatterbox.tts import ChatterboxTTS
    from eval_voices import wer
    model = ChatterboxTTS.from_pretrained(device=_device())
    jobs = json.load(open(a.batch)) if a.batch else [{"ref": a.ref, "text": a.text, "out": a.out}]
    enc = asr = None
    centroids = {}
    for j in jobs:
        takes = int(j.get("takes", 1))
        best = None
        for k in range(takes):
            path = j["out"] if takes == 1 else j["out"].replace(".wav", f".take{k}.wav")
            wav = model.generate(j["text"], audio_prompt_path=j["ref"],
                                 exaggeration=j.get("exaggeration", a.exaggeration),
                                 cfg_weight=j.get("cfg", a.cfg), temperature=j.get("temperature", a.temperature))
            torchaudio.save(path, wav.cpu(), model.sr)
            score = {"file": path}
            if j.get("originals"):
                if enc is None:
                    import whisper
                    from resemblyzer import VoiceEncoder, preprocess_wav
                    enc, asr = VoiceEncoder(verbose=False), whisper.load_model("small.en")
                key = tuple(j["originals"])
                if key not in centroids:
                    c = np.mean([enc.embed_utterance(preprocess_wav(o)) for o in key], axis=0)
                    centroids[key] = c / np.linalg.norm(c)
                from resemblyzer import preprocess_wav
                score["similarity"] = round(float(np.dot(enc.embed_utterance(preprocess_wav(path)), centroids[key])), 3)
                score["heard"] = asr.transcribe(path, language="en", fp16=False)["text"].strip()
                score["wer"] = wer(j["text"], score["heard"])
                score["rank"] = score["similarity"] - 0.5 * score["wer"]
            if best is None or score.get("rank", 0) > best.get("rank", 0):
                best = score
        if takes > 1:
            import shutil
            shutil.copy(best["file"], j["out"])
        print(json.dumps({"out": j["out"], **{k: v for k, v in best.items() if k != "file"}, "takes": takes}), flush=True)


def cmd_convert(a):
    import torchaudio
    from chatterbox.vc import ChatterboxVC
    model = ChatterboxVC.from_pretrained(device=_device())
    wav = model.generate(a.src, target_voice_path=a.ref)
    torchaudio.save(a.out, wav.cpu(), model.sr)
    print(a.out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcribe"); t.add_argument("audio", nargs="+"); t.add_argument("--model", default="small.en")
    t.set_defaults(f=cmd_transcribe)
    s = sub.add_parser("similarity"); s.add_argument("--ref", nargs="+", required=True); s.add_argument("--test", nargs="+", required=True)
    s.set_defaults(f=cmd_similarity)
    y = sub.add_parser("synth")
    for k, d in (("--ref", None), ("--text", None), ("--out", None), ("--batch", None)):
        y.add_argument(k, default=d)
    y.add_argument("--exaggeration", type=float, default=0.5); y.add_argument("--cfg", type=float, default=0.5)
    y.add_argument("--temperature", type=float, default=0.8); y.set_defaults(f=cmd_synth)
    c = sub.add_parser("convert"); c.add_argument("--ref", required=True); c.add_argument("--src", required=True)
    c.add_argument("--out", required=True); c.set_defaults(f=cmd_convert)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
