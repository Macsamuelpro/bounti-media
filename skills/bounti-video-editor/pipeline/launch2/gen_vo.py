"""Generate each line with ElevenLabs v3 through OpenRouter (/audio/speech), 2 takes, keep the take whose
Whisper transcript matches best (then shorter). usage: gen_vo.py [video...] -> vo/<video>/lNN.wav + vo.json"""
import os, sys, json, re, subprocess, urllib.request, difflib, wave
import numpy as np
from vo_scripts import S
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
from pywhispercpp.model import Model
W = Model(os.path.join(SP, "models/ggml-base.en.bin") if os.path.exists(os.path.join(SP, "models/ggml-base.en.bin")) else "base.en", print_progress=False, print_realtime=False)
def tts(text, voice):
    body = json.dumps({"model": "elevenlabs/eleven-v3", "input": text, "voice": voice}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/audio/speech", data=body, headers={"Authorization": "Bearer sk-or-dummy", "Content-Type": "application/json"})
    return np.frombuffer(urllib.request.urlopen(req, timeout=300).read(), np.int16).astype(np.float32)/32768
def plain(t): return re.sub(r"[^a-z ]", "", re.sub(r"\[[^\]]*\]", "", t).lower().replace("dot com", "com")).split()
for name in (sys.argv[1:] or S):
    v = S[name]; d = os.path.join(HERE, "vo", name); os.makedirs(d, exist_ok=True); meta = []
    for i, line in enumerate(v["lines"]):
        best = None
        for take in range(2):
            x = tts(line, v["voice"]); e = np.where(np.abs(x) > 0.012)[0]
            if len(e): x = x[max(e[0] - 600, 0):min(e[-1] + 2400, len(x))]
            tmp = os.path.join(d, f"_t{take}.wav")
            with wave.open(tmp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes((np.clip(x, -1, 1)*32767).astype(np.int16).tobytes())
            r16 = os.path.join(d, "_16.wav"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ar", "16000", r16])
            hyp = " ".join(s.text for s in W.transcribe(r16))
            sc = difflib.SequenceMatcher(None, plain(line), plain(hyp)).ratio()
            if best is None or sc > best[0] + 0.02 or (abs(sc - best[0]) <= 0.02 and len(x) < best[2]): best = (sc, hyp, len(x), take, x)
        sc, hyp, n, take, x = best; out = os.path.join(d, f"l{i:02d}.wav")
        with wave.open(out, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes((np.clip(x, -1, 1)*32767).astype(np.int16).tobytes())
        meta.append(dict(file=out, dur=n/24000, text=line, heard=hyp.strip(), match=round(sc, 2)))
        print(name, i, f"{n/24000:.2f}s match={sc:.2f}", "|", hyp.strip()[:90], flush=True)
    json.dump(meta, open(os.path.join(d, "vo.json"), "w"), indent=1)
