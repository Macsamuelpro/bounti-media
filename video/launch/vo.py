"""Generate the voiceover for each launch video, one clip per beat, with local Kokoro TTS.
usage: vo.py [video ...]  -> wav/<video>/bNN.wav + wav/<video>/vo.json (durations)"""
import os, sys, json
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from scripts import V
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = Kokoro(os.path.join(S, "models/kokoro/kokoro-v1.0.onnx"), os.path.join(S, "models/kokoro/voices-v1.0.bin"))
for name in (sys.argv[1:] or V):
    v = V[name]; d = os.path.join("wav", name); os.makedirs(d, exist_ok=True); out = []
    for i, b in enumerate(v["beats"]):
        x, sr = K.create(b["vo"], voice=v["voice"], speed=v.get("speed", 1.05), lang="en-us" if not v["voice"].startswith("b") else "en-gb")
        x = np.asarray(x, np.float32); e = np.abs(x) > 0.01; idx = np.where(e)[0]
        a, z = (max(idx[0] - int(0.03*sr), 0), min(idx[-1] + int(0.08*sr), len(x))) if len(idx) else (0, len(x))
        x = x[a:z]; f = os.path.join(d, f"b{i:02d}.wav"); sf.write(f, x, sr); out.append(dict(file=f, dur=len(x)/sr, sr=sr))
    json.dump(out, open(os.path.join(d, "vo.json"), "w"), indent=1); print(name, [round(o["dur"], 2) for o in out], "total %.1f" % sum(o["dur"] for o in out))
