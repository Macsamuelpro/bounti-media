"""Open Peeps (CC0 art by Pablo Stanley, MIT package by Jens Horstmann) character builder + 2D puppet animation.
Characters are composed at the library's native 1:1 unit scale: head + face (+ facial hair) placed on a full-body pose."""
import os, glob, io, math, random
import numpy as np, cv2, resvg_py
from PIL import Image
A = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib/open-peeps/packages/open_peeps/assets/atoms")
U = 567/48.0                          # svg units per avatar unit (head is 567 units tall at 48 avatar units)
def _png(path, recolor=None):
    svg = open(path).read()
    if recolor:
        for a, b in recolor.items(): svg = svg.replace(a, b)
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert("RGBA")
def parts(kind): return sorted(glob.glob(os.path.join(A, kind, "*.svg")))
def _first_row(im):
    a = np.array(im)[..., 3]; rows = np.nonzero(a.max(1) > 40)[0]; return rows.min() if len(rows) else 0
def build(pose, head, face, facial_hair=None, ink=(13, 13, 13), paper=(255, 255, 255)):
    """Returns an RGBA PIL image of a full character. Parts are file paths."""
    P = _png(pose); H = _png(head); F = _png(face); FH = _png(facial_hair) if facial_hair else None
    hd = Image.new("RGBA", H.size, (0, 0, 0, 0)); hd.alpha_composite(H)
    fx, fy = int(13.5*U), int(15.75*U); hd.alpha_composite(F, (min(fx, hd.size[0] - F.size[0]), min(fy, hd.size[1] - F.size[1])))
    if FH is not None:
        hx, hy = int(10.25*U), int(28.5*U)
        if hx + FH.size[0] <= hd.size[0] and hy + FH.size[1] <= hd.size[1]: hd.alpha_composite(FH, (hx, hy))
    # neck: centre of the topmost opaque row of the pose
    a = np.array(P)[..., 3]; top = _first_row(P); cols = np.nonzero(a[top + 25] > 40)[0]
    neck_x = int(cols.mean()) if len(cols) else P.size[0]//2
    W = max(P.size[0], neck_x + hd.size[0]); Ht = P.size[1] + hd.size[1]
    out = Image.new("RGBA", (W + 200, Ht), (0, 0, 0, 0))
    hx = neck_x - int(hd.size[0]*0.47) + 100; hy = 0
    py = hd.size[1] - top - int(hd.size[1]*0.10)
    out.alpha_composite(P, (100, py)); out.alpha_composite(hd, (hx, hy))
    bb = out.getbbox(); out = out.crop(bb)
    arr = np.array(out).astype(np.float32)
    # recolour: black ink -> brand ink, white fill -> paper tone
    lum = arr[..., :3].mean(2, keepdims=True)/255
    arr[..., :3] = np.array(ink, np.float32)*(1 - lum) + np.array(paper, np.float32)*lum
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))
def random_peep(seed, standing=True, ink=(13, 13, 13), paper=(255, 255, 255)):
    r = random.Random(seed)
    import json
    good = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "peeps_good_heads.json"))))
    heads = [h for h in parts("head") if os.path.basename(h) in good]
    pose = r.choice(parts("pose/standing" if standing else "pose/sitting")); head = r.choice(heads); face = r.choice(parts("face"))
    fh = r.choice(parts("facial-hair") + [None]*14)
    return build(pose, head, face, fh, ink, paper)
def to_rgba_array(im, height):
    w = int(im.size[0]*height/im.size[1]); return np.array(im.resize((w, height), Image.LANCZOS)).astype(np.float32)

# ---------------- puppet motion ----------------
def walk_offset(t, speed=1.0, step=0.42, bob=10, sway=2.5):
    """Bob + sway for a walking/arriving character (no limb rig: whole-body hop is the illustrated-style convention)."""
    ph = t*2*math.pi/step*speed; return abs(math.sin(ph))*-bob, math.sin(ph)*sway
def idle_offset(t, seed=0, amp=3, rot=1.2):
    return math.sin(t*2.1 + seed)*amp, math.sin(t*1.7 + seed*2)*rot
def pop_scale(u):
    if u <= 0: return 0.0
    u = min(u/0.35, 1.0); return 1 - math.exp(-6*u)*math.cos(u*math.pi*2.2) if u < 1 else 1.0
