import subprocess, re, json, os, glob
from pywhispercpp.model import Model
U = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ugc")
m = Model(os.path.join(os.path.dirname(U), "models/ggml-base.en.bin"), n_threads=3, print_progress=False, print_realtime=False)
for d in sorted(os.listdir(U)):
    if not d.startswith("UGC"): continue
    P = os.path.join(U, d); out = {}
    for w in sorted(glob.glob(os.path.join(P, "wav/c*.wav")), key=lambda x: int(re.findall(r"c(\d+)", os.path.basename(x))[0])):
        n = os.path.basename(w)[:-4]
        o = subprocess.run(["ffmpeg", "-v", "error", "-i", w, "-af", "highpass=f=90,asetnsamples=160,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-", "-f", "null", "-"], capture_output=True, text=True).stdout
        v = [float(x) if x != "-inf" else -99 for x in re.findall(r"RMS_level=([-0-9.inf]+)", o)]
        sv = sorted(v); fl = sv[len(sv)//10]; th = max(fl + 12, -44); s = []; st = None
        for k, on in enumerate([x > th for x in v] + [False]):
            if on and st is None: st = k
            if not on and st is not None: s.append([st, k]); st = None
        mm = []
        for a, b in s:
            if mm and a - mm[-1][1] <= 22: mm[-1][1] = b
            else: mm.append([a, b])
        ps = [[round(a/100, 2), round(b/100, 2)] for a, b in mm if b - a >= 8]; res = []
        for a, b in ps:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(a - 0.06, 0)), "-to", str(b + 0.08), "-i", w, "-af", "apad=pad_dur=0.6", os.path.join(P, "wav/_p.wav")])
            res.append([a, b, " ".join(x.text.strip() for x in m.transcribe(os.path.join(P, "wav/_p.wav"))).strip()])
        out[n] = dict(floor=fl, pieces=res)
    json.dump(out, open(os.path.join(P, "pieces.json"), "w"), indent=1)
    print("==", d)
    for n, v in out.items(): print("  ", n, " | ".join(f"{a}-{b} {t}" for a, b, t in v["pieces"]))
