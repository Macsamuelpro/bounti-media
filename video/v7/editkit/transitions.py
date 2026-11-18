"""Transition library. Every transition: fn(A, B, t, **params) -> frame.
A = outgoing frame, B = incoming frame (float32 BGR, same size), t in [0, 1] across the transition window.
Parameters (direction, colour, strength, seed...) turn each family into many variants."""
import math
import numpy as np, cv2

def _s(t): t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def _io(t): t = min(max(t, 0.0), 1.0); return 4*t**3 if t < 0.5 else 1 - (-2*t + 2)**3/2
def _out(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t)**3
def _in(t): t = min(max(t, 0.0), 1.0); return t**3
EASE = {"smooth": _s, "inout": _io, "out": _out, "in": _in, "linear": lambda t: min(max(t, 0.0), 1.0)}
DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1),
        "upleft": (-1, -1), "upright": (1, -1), "downleft": (-1, 1), "downright": (1, 1)}
def _shift(img, dx, dy, mode=cv2.BORDER_REFLECT):
    M = np.float32([[1, 0, dx], [0, 1, dy]]); h, w = img.shape[:2]
    return cv2.warpAffine(img, M, (w, h), borderMode=mode)
def _zoom(img, z, cx=None, cy=None, rot=0.0):
    h, w = img.shape[:2]; cx = w/2 if cx is None else cx; cy = h/2 if cy is None else cy
    M = cv2.getRotationMatrix2D((cx, cy), rot, z)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
def _mix(A, B, m):
    m = m if m.ndim == 3 else m[..., None]; return A*(1 - m) + B*m
def _noise(h, w, scale, seed, octaves=3):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        gh, gw = max(2, int(h/scale*2**o)), max(2, int(w/scale*2**o))
        out += cv2.resize(rng.random((gh, gw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)*amp; tot += amp; amp *= 0.5
    out /= tot; return (out - out.min())/(out.max() - out.min() + 1e-6)
def _motion_blur(img, dx, dy, n=9):
    if abs(dx) + abs(dy) < 1: return img
    acc = np.zeros_like(img)
    for k in range(n): f = (k/(n - 1) - 0.5); acc += _shift(img, dx*f, dy*f)
    return acc/n
def _radial_blur(img, strength, n=8, cx=None, cy=None):
    if strength < 1e-3: return img
    acc = np.zeros_like(img)
    for k in range(n): acc += _zoom(img, 1 + strength*k/(n - 1), cx, cy)
    return acc/n
def _gauss(img, s): return img if s < 0.3 else cv2.GaussianBlur(img, (0, 0), s)

# ---------------- basic ----------------
def cut(A, B, t, at=0.5): return A if t < at else B
def dissolve(A, B, t, ease="smooth"): k = EASE[ease](t); return A*(1 - k) + B*k
def additive_dissolve(A, B, t):
    k = _s(t); return np.clip(A*(1 - k) + B*k + (A + B)*0.35*math.sin(math.pi*k), 0, 255)
def dip(A, B, t, color=(0, 0, 0), hold=0.15):
    c = np.array(color, np.float32)
    if t < 0.5 - hold/2: k = _s(t/(0.5 - hold/2)); return A*(1 - k) + c*k
    if t < 0.5 + hold/2: return np.broadcast_to(c, A.shape).copy()
    k = _s((t - 0.5 - hold/2)/(0.5 - hold/2)); return c*(1 - k) + B*k
def blackout(A, B, t, hold=0.25): return dip(A, B, t, (0, 0, 0), hold)
def flash(A, B, t, color=(255, 255, 255), peak=0.5, width=0.35, ease="out"):
    """Flash / camera flash: hard cut under a bright burst. color: white, warm (200,230,255) BGR..."""
    base = A if t < peak else B; d = abs(t - peak)/width; k = max(0.0, 1 - d)**2
    return np.clip(base + (np.array(color, np.float32) - base)*k, 0, 255)
def camera_flash(A, B, t):
    out = flash(A, B, t, (255, 255, 255), 0.5, 0.18)
    if 0.5 <= t < 0.62: out = np.clip(out*1.15 + 20, 0, 255)       # overexposed after-glow
    return out
def blur_dissolve(A, B, t, max_blur=18):
    s = max_blur*math.sin(math.pi*t); return dissolve(_gauss(A, s), _gauss(B, s), t)
def exposure_dissolve(A, B, t, stops=1.6):
    g = 2**(stops*math.sin(math.pi*t)); return np.clip(dissolve(A, B, t)*g, 0, 255)

# ---------------- motion ----------------
def whip_pan(A, B, t, direction="left", blur=1.0, ease="inout"):
    """Fast camera swing; motion-blurred push of both frames, cut on the blur."""
    h, w = A.shape[:2]; dx, dy = DIRS[direction]; k = EASE[ease](t)
    off = k*(w if dx else h); speed = math.sin(math.pi*t)*blur*(w*0.35)
    a = _shift(A, -dx*off, -dy*off); b = _shift(B, dx*((w if dx else h) - off), dy*((w if dx else h) - off))
    img = a if t < 0.5 else b
    return _motion_blur(img, dx*speed, dy*speed, 13)
def push(A, B, t, direction="left", ease="inout"):
    h, w = A.shape[:2]; dx, dy = DIRS[direction]; k = EASE[ease](t); L = w if dx else h
    out = np.zeros_like(A)
    a = _shift(A, -dx*k*L, -dy*k*L, cv2.BORDER_CONSTANT); b = _shift(B, dx*(1 - k)*L, dy*(1 - k)*L, cv2.BORDER_CONSTANT)
    mb = _shift(np.ones(A.shape[:2], np.float32), dx*(1 - k)*L, dy*(1 - k)*L, cv2.BORDER_CONSTANT)
    return _mix(a, b, mb)
def slide_over(A, B, t, direction="left", ease="out"):
    h, w = A.shape[:2]; dx, dy = DIRS[direction]; k = EASE[ease](t); L = w if dx else h
    b = _shift(B, dx*(1 - k)*L, dy*(1 - k)*L, cv2.BORDER_CONSTANT)
    mb = _shift(np.ones(A.shape[:2], np.float32), dx*(1 - k)*L, dy*(1 - k)*L, cv2.BORDER_CONSTANT)
    return _mix(A*(1 - 0.35*k), b, mb)
def zoom_in(A, B, t, amount=1.8, blur=0.25):
    """Punch/zoom-through: A zooms into the cut, B lands from a slight over-zoom."""
    if t < 0.5:
        k = _in(t/0.5); return _radial_blur(_zoom(A, 1 + (amount - 1)*k), blur*k)
    k = _out((t - 0.5)/0.5); return _radial_blur(_zoom(B, amount - (amount - 1)*k), blur*(1 - k))
def zoom_out(A, B, t, amount=1.8, blur=0.25):
    if t < 0.5:
        k = _in(t/0.5); return _radial_blur(_zoom(A, 1/(1 + (amount - 1)*k)), blur*k)
    k = _out((t - 0.5)/0.5); return _radial_blur(_zoom(B, 1/(amount - (amount - 1)*k)), blur*(1 - k))
def zoom_blur(A, B, t, strength=0.35):
    """CapCut 'zoom blur': radial blur peaks at the cut, slight scale bump."""
    s = strength*math.sin(math.pi*t); img = A if t < 0.5 else B
    return _radial_blur(_zoom(img, 1 + 0.08*math.sin(math.pi*t)), s, 10)
def punch_in(A, B, t, amount=1.18):
    """Hard cut into a tighter crop of the incoming shot that settles (energy without a transition look)."""
    if t < 0.5: return A
    return _zoom(B, amount - (amount - 1)*0.15*_out((t - 0.5)/0.5))
def spin(A, B, t, degrees=180, amount=1.4, blur=0.2):
    if t < 0.5:
        k = _in(t/0.5); return _radial_blur(_zoom(A, 1 + (amount - 1)*k, rot=-degrees/2*k), blur*k)
    k = _out((t - 0.5)/0.5); return _radial_blur(_zoom(B, amount - (amount - 1)*k, rot=degrees/2*(1 - k)), blur*(1 - k))
def shake(A, B, t, px=40, seed=1):
    rng = np.random.default_rng(seed + int(t*100)); e = math.sin(math.pi*t)
    img = A if t < 0.5 else B
    return _motion_blur(_shift(img, rng.normal()*px*e, rng.normal()*px*e), rng.normal()*px*e*0.6, rng.normal()*px*e*0.6, 7)
def squeeze(A, B, t, direction="horizontal"):
    h, w = A.shape[:2]
    if t < 0.5:
        k = 1 - _in(t/0.5); img = A
    else:
        k = _out((t - 0.5)/0.5); img = B
    k = max(k, 0.02)
    sx, sy = (k, 1) if direction == "horizontal" else (1, k)
    M = np.float32([[sx, 0, w/2*(1 - sx)], [0, sy, h/2*(1 - sy)]])
    return cv2.warpAffine(img, M, (w, h), borderValue=(0, 0, 0))
def stretch(A, B, t, direction="horizontal", amount=3.0):
    h, w = A.shape[:2]; e = 1 + (amount - 1)*math.sin(math.pi*t)**2; img = A if t < 0.5 else B
    sx, sy = (e, 1) if direction == "horizontal" else (1, e)
    M = np.float32([[sx, 0, w/2*(1 - sx)], [0, sy, h/2*(1 - sy)]])
    return _motion_blur(cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT), (sx - 1)*40, (sy - 1)*40, 9)

# ---------------- wipes & masks ----------------
def wipe(A, B, t, direction="right", soft=0.06, ease="inout"):
    h, w = A.shape[:2]; dx, dy = DIRS[direction]; k = EASE[ease](t)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); xx /= w; yy /= h
    p = (xx if dx > 0 else 1 - xx)*abs(dx) + (yy if dy > 0 else 1 - yy)*abs(dy)
    p = p/(abs(dx) + abs(dy)); edge = k*(1 + soft) - soft
    return _mix(A, B, np.clip((edge - p)/soft + 1, 0, 1) if soft > 0 else (p < edge).astype(np.float32))
def iris(A, B, t, cx=0.5, cy=0.45, soft=0.04, reverse=False):
    h, w = A.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - cx*w)/h, (yy - cy*h)/h); R = 1.2*_io(t)
    m = np.clip((R - d)/soft, 0, 1)
    return _mix(B, A, 1 - m) if not reverse else _mix(A, B, 1 - np.clip((1.2*(1 - _io(t)) - d)/soft, 0, 1))
def clock_wipe(A, B, t, start_deg=-90, soft=0.03):
    h, w = A.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = (np.degrees(np.arctan2(yy - h/2, xx - w/2)) - start_deg) % 360/360
    return _mix(A, B, np.clip((_io(t) - ang)/soft, 0, 1))
def split(A, B, t, direction="vertical"):
    h, w = A.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); k = _io(t)
    d = np.abs(xx/w - 0.5) if direction == "vertical" else np.abs(yy/h - 0.5)
    return _mix(A, B, (d < k*0.5).astype(np.float32))
def blinds(A, B, t, n=8, direction="vertical"):
    h, w = A.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    p = ((xx/w*n) % 1) if direction == "vertical" else ((yy/h*n) % 1)
    return _mix(A, B, (p < _io(t)).astype(np.float32))
def luma_fade(A, B, t, soft=0.12, invert=False):
    """Luma wipe: the brightest areas of A reveal B first (or darkest, inverted)."""
    L = cv2.cvtColor(np.clip(A, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    L = 1 - L if invert else L; k = _io(t)*(1 + soft)
    return _mix(A, B, np.clip((k - (1 - L))/soft, 0, 1))
def ink(A, B, t, seed=3, scale=180, soft=0.08):
    """Organic ink/paint reveal driven by fractal noise."""
    h, w = A.shape[:2]; n = _noise(h, w, scale, seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); radial = np.hypot(xx/w - 0.5, yy/h - 0.5)/0.71
    field = 0.55*n + 0.45*radial; k = _io(t)*(1 + soft)
    return _mix(A, B, np.clip((k - field)/soft, 0, 1))
def brush(A, B, t, seed=5, direction="right"):
    h, w = A.shape[:2]; rng = np.random.default_rng(seed)
    rows = cv2.resize(rng.random((24, 1)).astype(np.float32), (1, h), interpolation=cv2.INTER_CUBIC)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); p = xx/w if direction == "right" else 1 - xx/w
    field = p*0.8 + rows*0.2; k = _io(t)*1.1
    return _mix(A, B, np.clip((k - field)/0.03, 0, 1))
def mask_reveal(A, B, t, mask_fn):
    """Generic: mask_fn(t) -> HxW float alpha for B. Use for body/object wipes (person mask), shape reveals."""
    return _mix(A, B, mask_fn(t))
def body_wipe(A, B, t, maskA):
    """Wipe hidden by a person/object crossing frame: maskA (HxW 0..1) of the foreground in A."""
    k = _s((t - 0.35)/0.3); return _mix(A, _mix(B, A, maskA), k)
def heart_or_shape(A, B, t, shape="circle", cx=0.5, cy=0.45):
    h, w = A.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x = (xx - cx*w)/h; y = (yy - cy*h)/h; R = 1.3*_io(t)
    if shape == "diamond": d = np.abs(x) + np.abs(y)
    elif shape == "square": d = np.maximum(np.abs(x), np.abs(y))
    elif shape == "heart": d = (x**2 + (y + 0.0)**2 - 0.01)**3 - x**2*(-y)**3; d = np.cbrt(np.maximum(d + 1e-9, 0))*3 + np.hypot(x, y)*0.6
    else: d = np.hypot(x, y)
    return _mix(A, B, np.clip((R - d)/0.03, 0, 1))

# ---------------- light & film ----------------
def light_leak(A, B, t, palette="warm", seed=2, strength=0.55):
    """Organic light leak swept across the cut (screen blend)."""
    h, w = A.shape[:2]; base = dissolve(A, B, _s((t - 0.35)/0.3))
    cols = {"warm": [(60, 150, 255), (80, 110, 255), (170, 220, 255)], "cool": [(255, 200, 120), (255, 160, 140), (255, 235, 210)],
            "neutral": [(230, 230, 240), (200, 215, 235), (255, 255, 255)]}[palette]
    yy, xx = np.mgrid[0:h:4, 0:w:4].astype(np.float32); rng = np.random.default_rng(seed); img = np.zeros(yy.shape + (3,), np.float32)
    for i, c in enumerate(cols):
        cx = w*(rng.uniform(-0.2, 0.3) + 0.9*t + 0.2*i); cy = h*rng.uniform(0.2, 0.8); r = w*rng.uniform(0.35, 0.7)
        img += np.exp(-(((xx - cx)**2 + (yy - cy)**2)/(2*r*r)))[..., None]*np.array(c, np.float32)
    img = cv2.resize(img, (w, h))*math.sin(math.pi*t)**1.4*strength
    return 255 - (255 - base)*(255 - np.clip(img, 0, 255))/255
def film_burn(A, B, t, seed=7, palette="warm"):
    """Film burn: hot orange/white burn that blooms over the cut with grain and flicker."""
    h, w = A.shape[:2]; n = _noise(h, w, 260, seed, 4)
    e = math.sin(math.pi*t); base = A if t < 0.5 else B
    heat = np.clip((n - (1 - e*0.85))/0.4, 0, 1)*0.85
    col = np.array((40, 120, 255) if palette == "warm" else (255, 160, 60), np.float32)
    burn = heat[..., None]*col + np.clip(heat - 0.55, 0, 1)[..., None]*255*0.9
    rng = np.random.default_rng(seed + int(t*97)); grain = rng.normal(0, 10*e, (h, w, 1)).astype(np.float32)
    out = 255 - (255 - base)*(255 - np.clip(burn, 0, 255))/255
    return np.clip(out*(1 + 0.15*e*rng.uniform(-1, 1)) + grain, 0, 255)
def bloom_flash(A, B, t):
    base = A if t < 0.5 else B; e = math.sin(math.pi*t)**2
    glow = _gauss(np.clip(base - 140, 0, 255)*3, 25)
    return np.clip(base + glow*e + 120*e, 0, 255)
def lens_flare_sweep(A, B, t, color=(200, 230, 255)):
    h, w = A.shape[:2]; base = dissolve(A, B, _s((t - 0.4)/0.2)); x = w*(-0.2 + 1.4*t)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    streak = np.exp(-((yy - h*0.42)**2)/(2*(h*0.012)**2))*np.exp(-((xx - x)**2)/(2*(w*0.6)**2))
    core = np.exp(-((xx - x)**2 + (yy - h*0.42)**2)/(2*(w*0.08)**2))
    f = (streak*0.8 + core)[..., None]*np.array(color, np.float32)*math.sin(math.pi*t)
    return 255 - (255 - base)*(255 - np.clip(f, 0, 255))/255

# ---------------- digital ----------------
def glitch(A, B, t, seed=11, intensity=1.0):
    """RGB split + displaced slices + blocks, peaking at the cut."""
    h, w = A.shape[:2]; e = math.sin(math.pi*t)*intensity; img = (A if t < 0.5 else B).copy()
    rng = np.random.default_rng(seed + int(t*60))
    for _ in range(int(12*e)):
        y0 = rng.integers(0, h - 10); hh = rng.integers(4, max(6, int(h*0.08))); dx = int(rng.normal(0, w*0.08*e))
        img[y0:y0 + hh] = np.roll(img[y0:y0 + hh], dx, 1)
    s = int(w*0.02*e)
    if s: img[..., 2] = np.roll(img[..., 2], s, 1); img[..., 0] = np.roll(img[..., 0], -s, 1)
    if e > 0.5:
        for _ in range(int(6*e)):
            x0, y0 = rng.integers(0, w - 40), rng.integers(0, h - 40); bw, bh = rng.integers(20, 120), rng.integers(10, 60)
            src = (B if t < 0.5 else A)[y0:y0 + bh, x0:x0 + bw]; img[y0:y0 + src.shape[0], x0:x0 + src.shape[1]] = src
    return img
def mask_glitch(A, B, t, seed=13):
    """Mask glitch: B appears through glitching horizontal bands with a warm over-exposure."""
    h, w = A.shape[:2]; rng = np.random.default_rng(seed + int(t*48)); m = np.zeros((h, w), np.float32)
    k = _io(t)
    for _ in range(int(4 + 30*math.sin(math.pi*t))):
        y0 = rng.integers(0, h); hh = rng.integers(3, max(4, int(h*0.07))); m[y0:y0 + hh] = 1
    m = np.maximum(m*(1 - k), 0) + (k > 0.55)*1.0
    out = _mix(A, B, np.clip(m, 0, 1))
    e = math.sin(math.pi*t); return np.clip(out*(1 + 0.6*e) + np.array((10, 60, 120), np.float32)*e, 0, 255)
def pixelate(A, B, t, max_block=0.045):
    h, w = A.shape[:2]; b = int(1 + max_block*w*math.sin(math.pi*t)); img = dissolve(A, B, _s((t - 0.4)/0.2))
    if b <= 1: return img
    small = cv2.resize(img, (max(1, w//b), max(1, h//b)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
def vhs(A, B, t, seed=17):
    h, w = A.shape[:2]; e = math.sin(math.pi*t); img = glitch(A, B, t, seed, 0.6)
    rng = np.random.default_rng(seed + int(t*50))
    lines = (np.sin(np.arange(h)*0.9 + t*40)*0.5 + 0.5)[:, None, None]*18*e
    noise = rng.normal(0, 18*e, (h, w, 1)).astype(np.float32)
    return np.clip(img - lines + noise, 0, 255)
def rgb_split(A, B, t, px=0.012):
    img = A if t < 0.5 else B; s = int(px*img.shape[1]*math.sin(math.pi*t)); o = img.copy()
    if s: o[..., 2] = _shift(img, s, 0)[..., 2]; o[..., 0] = _shift(img, -s, 0)[..., 0]
    return o
def mosaic_tiles(A, B, t, n=6, seed=19):
    h, w = A.shape[:2]; rng = np.random.default_rng(seed); order = rng.random((n*2, n))
    m = cv2.resize((order < _io(t)).astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST)
    return _mix(A, B, m)

# ---------------- optical / continuity ----------------
_dis = None
def morph_cut(A, B, t):
    """Optical-flow morph: hides a jump cut inside one talking-head take."""
    global _dis
    if _dis is None: _dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    a8, b8 = [np.clip(x, 0, 255).astype(np.uint8) for x in (A, B)]; h, w = a8.shape[:2]; sc = 0.5
    ga = cv2.resize(cv2.cvtColor(a8, cv2.COLOR_BGR2GRAY), None, fx=sc, fy=sc); gb = cv2.resize(cv2.cvtColor(b8, cv2.COLOR_BGR2GRAY), None, fx=sc, fy=sc)
    fab = cv2.resize(_dis.calc(ga, gb, None), (w, h))/sc; fba = cv2.resize(_dis.calc(gb, ga, None), (w, h))/sc
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)); k = _s(t)
    Aw = cv2.remap(A, gx - k*fab[..., 0], gy - k*fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(B, gx - (1 - k)*fba[..., 0], gy - (1 - k)*fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Aw*(1 - k) + Bw*k
def match_cut(A, B, t, H=None):
    """Match cut: cut between shots aligned on the same shape/motion. H = homography aligning B to A (optional, eases out)."""
    if t < 0.5 or H is None: return cut(A, B, t)
    k = _out((t - 0.5)/0.5); h, w = B.shape[:2]; Hk = np.eye(3)*(k) + H*(1 - k)
    return cv2.warpPerspective(B, Hk, (w, h), borderMode=cv2.BORDER_REFLECT)

# ---------------- registry ----------------
CATALOG = {
 "cut": cut, "dissolve": dissolve, "additive_dissolve": additive_dissolve, "dip_black": lambda A, B, t: dip(A, B, t, (0, 0, 0)),
 "dip_white": lambda A, B, t: dip(A, B, t, (255, 255, 255)), "blackout": blackout, "flash": flash, "warm_flash": lambda A, B, t: flash(A, B, t, (190, 225, 255)),
 "camera_flash": camera_flash, "blur_dissolve": blur_dissolve, "exposure_dissolve": exposure_dissolve,
 "whip_pan": whip_pan, "push": push, "slide_over": slide_over, "zoom_in": zoom_in, "zoom_out": zoom_out, "zoom_blur": zoom_blur,
 "punch_in": punch_in, "spin": spin, "shake": shake, "squeeze": squeeze, "stretch": stretch,
 "wipe": wipe, "iris": iris, "clock_wipe": clock_wipe, "split": split, "blinds": blinds, "luma_fade": luma_fade, "ink": ink,
 "brush": brush, "shape_diamond": lambda A, B, t: heart_or_shape(A, B, t, "diamond"), "shape_square": lambda A, B, t: heart_or_shape(A, B, t, "square"),
 "light_leak": light_leak, "film_burn": film_burn, "bloom_flash": bloom_flash, "lens_flare_sweep": lens_flare_sweep,
 "glitch": glitch, "mask_glitch": mask_glitch, "pixelate": pixelate, "vhs": vhs, "rgb_split": rgb_split, "mosaic_tiles": mosaic_tiles,
 "morph_cut": morph_cut, "match_cut": match_cut,
}
# Sound pairing (sfx-kit ids) and when to use each, learned from the references
SOUND = {"whip_pan": "whoosh-fast-hard", "zoom_in": "whoosh-fast-medium", "zoom_out": "reverse-whoosh-short-soft", "zoom_blur": "click-mouse-medium",
         "flash": "swish-medium", "camera_flash": "mechanical-shutter-light", "blackout": "boom-hit-soft", "film_burn": "whoosh-slow-soft",
         "glitch": "digital-glitch-clear", "mask_glitch": "digital-glitch-clear", "light_leak": "whoosh-slow-soft", "spin": "whoosh-medium-medium",
         "push": "swipe-fast-soft", "slide_over": "swipe-fast-soft", "wipe": "whoosh-medium-soft", "ink": "whoosh-slow-soft",
         "blur_dissolve": "whoosh-medium-soft", "shake": "impact-heavy-hard", "punch_in": None, "cut": None, "morph_cut": None, "match_cut": None,
         "dissolve": None, "dip_black": None}
