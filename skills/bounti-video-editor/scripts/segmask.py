import cv2, numpy as np, onnxruntime as ort, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sess = ort.InferenceSession(os.path.join(HERE, "../models/u2net_human_seg.onnx"), providers=["CPUExecutionProvider"])
iname = sess.get_inputs()[0].name
MEAN = np.array([0.485, 0.456, 0.406]); STD = np.array([0.229, 0.224, 0.225])

def person_mask(bgr):
    h, w = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    x = cv2.resize(rgb, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    x = ((x / x.max()) - MEAN) / STD
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    d = sess.run(None, {iname: x})[0][0, 0]
    d = (d - d.min()) / (d.max() - d.min() + 1e-8)
    m = cv2.resize(d, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    # edge-aware refinement with the frame as guide
    g = cv2.ximgproc.guidedFilter(guide=bgr, src=m, radius=6, eps=1e-3)
    return np.clip((g - 0.15) / 0.7, 0, 1).astype(np.float32)

def frames_needed(ranges, fps=24):
    out = {}
    for c, a, b in ranges:
        out.setdefault(c, set()).update(range(int(a*fps), int(np.ceil(b*fps)) + 1))
    return out

if __name__ == "__main__":
    ranges = [("d08", 3.25, 5.95), ("d07", 4.20, 5.95), ("d01", 7.60, 8.75), ("d02", 6.45, 7.85),
              ("d06", 5.20, 6.85), ("d06", 7.35, 9.99)]
    need = frames_needed(ranges)
    os.makedirs(os.path.join(HERE, "masks"), exist_ok=True)
    for c, ks in need.items():
        cap = cv2.VideoCapture(os.path.join(HERE, f"src/{c}.mp4")); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(f)
        ks = sorted(k for k in ks if k < len(fr))
        ms = np.stack([person_mask(fr[k]) for k in ks])
        np.savez_compressed(os.path.join(HERE, f"masks/{c}.npz"), idx=np.array(ks), m=(ms*255).astype(np.uint8))
        print(c, len(ks), "masks", file=sys.stderr)
