"""Reference-matched grade: brightness distribution, skin and white balance taken from the user's reference frame."""
import cv2, numpy as np, os, json
from scipy.interpolate import PchipInterpolator
HERE = os.path.dirname(os.path.abspath(__file__))
REF = json.load(open(os.path.join(HERE, "ref_look.json")))
det = cv2.FaceDetectorYN.create(os.path.join(HERE, "../models/yunet.onnx"), "", (720, 1280), 0.6)
def analyse(frames):
    Ls, faces, skins, neus, chroma = [], [], [], [], []
    for f in frames:
        lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
        L, a, b = lab[..., 0]/2.55, lab[..., 1] - 128, lab[..., 2] - 128
        Ls.append(L[::4, ::4].ravel()); chroma.append(np.hypot(a, b).mean())
        m = (L > 25) & (L < 85) & (np.hypot(a, b) < 12)
        if m.sum() > 500: neus.append((a[m].mean(), b[m].mean()))
        _, fs = det.detect(f)
        if fs is not None:
            x, y, w, h = fs[0][:4].astype(int); x = max(x, 0); y = max(y, 0)
            r = lab[y + h//3:y + 2*h//3, x + w//4:x + 3*w//4].reshape(-1, 3)
            if len(r): faces.append(r[:, 0].mean()/2.55); skins.append((r[:, 1].mean() - 128, r[:, 2].mean() - 128))
    Lall = np.concatenate(Ls)
    return dict(L_pct=[float(np.percentile(Lall, p)) for p in range(0, 101, 5)],
                face=float(np.median(faces)) if faces else None,
                skin=np.median(np.array(skins), 0).tolist() if skins else None,
                neutral=np.median(np.array(neus), 0).tolist() if neus else [0, 0], chroma=float(np.mean(chroma)))
def make_grade(st, strength=0.55):
    src = np.array(st["L_pct"]); dst = np.array(REF["L_pct"])
    src = np.maximum.accumulate(src + np.arange(len(src))*1e-3)
    f = PchipInterpolator(src, dst, extrapolate=True)
    x = np.arange(256)/2.55
    y = (1 - strength)*x + strength*np.clip(f(np.clip(x, src[0], src[-1])), 0, 100)
    if st["face"]:                                   # anchor skin to the reference skin brightness
        fy = float(np.interp(st["face"], x, y)); tgt = REF["skin"][0] + 1.5
        k = np.clip(tgt/max(fy, 1), 0.85, 1.35)
        w = np.exp(-((x - st["face"])/22)**2)        # only around skin tones
        y = y*(1 + (k - 1)*w)
    y = np.clip(y, 0, 100)
    # limit the slope so shadows are never stretched hard (that is what exposes compression blocks)
    dy = np.diff(y, prepend=y[0]); dx = np.diff(x, prepend=0)
    dy = np.clip(dy, 0.45*dx, 1.45*dx); y2 = y[0] + np.cumsum(dy) - dy[0]
    if st["face"]:                                   # re-anchor: keep skin where the reference has it
        fy = float(np.interp(st["face"], x, y2)); y2 = y2 + (REF["skin"][0] + 1.5 - fy)*np.exp(-((x - st["face"])/30)**2)*0.0 + (REF["skin"][0] + 1.5 - fy)*0.6
    y = np.clip(y2, 0, 100); y = np.maximum.accumulate(y)
    y = np.minimum(y, 97 + 0.03*x)
    da, db = (REF["neutral"][0] - st["neutral"][0])*0.75, (REF["neutral"][1] - st["neutral"][1])*0.75
    sk = st["skin"] or [REF["skin"][1], REF["skin"][2]]
    return dict(lut=(y*2.55).astype(np.float32), da=da, db=db,
                sa=(REF["skin"][1] - (sk[0] + da))*0.85, sb=(REF["skin"][2] - (sk[1] + db))*0.85,
                csat=float(np.clip((REF["chroma_mean"] + 2.0)/max(st["chroma"], 1), 0.70, 1.10)))
def apply(f, g):
    lab = cv2.cvtColor(f.astype(np.float32)/255.0, cv2.COLOR_BGR2LAB)          # float: L 0..100, no banding
    L0 = cv2.bilateralFilter(lab[..., 0], 5, 2.5, 3)                           # calm compression noise before lifting
    L = np.interp(L0, np.arange(256)/2.55, g["lut"]/2.55) + (lab[..., 0] - L0)*0.6
    a = lab[..., 1] + g["da"]; b = lab[..., 2] + g["db"]
    skin = np.clip((np.minimum(a, b) - 4)/8, 0, 1)*np.clip((L - 12)/15, 0, 1)*np.clip((72 - L)/15, 0, 1)
    cs = g["csat"]*(1 - skin) + 1.08*skin
    a = a*cs + g["sa"]*skin; b = b*cs + g["sb"]*skin
    out = cv2.cvtColor(np.dstack([L, a, b]).astype(np.float32), cv2.COLOR_LAB2BGR)
    return np.clip(out*255 + 0.5, 0, 255).astype(np.uint8)
