import sys, os, json, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../v3"))
from segmask import person_mask
E = json.load(open("edit7.json")); need = {}
for g in E["segs"]:
    a = int(g["s0"]*24) - 2; b = int((g["s1"] + g["hold"])*24) + 3; need.setdefault(g["c"], set()).update(range(max(a, 0), b))
for c in sorted(need):
    out = f"masks/{c}.npz"
    if os.path.exists(out): continue
    cap = cv2.VideoCapture(f"src/{c}.mp4"); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    ks = sorted(k for k in need[c] if k < len(fr) and k % 3 == 0)
    ms = np.stack([cv2.resize((person_mask(fr[k])*255).astype(np.uint8), (360, 640), interpolation=cv2.INTER_AREA) for k in ks])
    np.savez_compressed(out, idx=np.array(ks), m=ms); print(c, len(ks), flush=True)
