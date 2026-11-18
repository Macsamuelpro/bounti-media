"""Colour grading and light adjustments. Work in float BGR 0..255.
adjust(img, **controls) for primary corrections; LOOKS for creative presets; match_reference() for matching a still;
load_cube()/apply_lut() for .cube LUTs; finishing: vignette, bloom, halation, grain, sharpen."""
import numpy as np, cv2

def _lab(img): return cv2.cvtColor(np.clip(img, 0, 255).astype(np.float32)/255, cv2.COLOR_BGR2LAB)
def _bgr(lab): return np.clip(cv2.cvtColor(lab.astype(np.float32), cv2.COLOR_LAB2BGR)*255, 0, 255)
def _curve(x, pts):
    xs, ys = zip(*pts); return np.interp(x, xs, ys)

def adjust(img, exposure=0.0, contrast=0.0, highlights=0.0, shadows=0.0, whites=0.0, blacks=0.0,
           temp=0.0, tint=0.0, saturation=0.0, vibrance=0.0, clarity=0.0, pivot=0.45):
    """Lightroom-style primaries. exposure in stops; others roughly -1..1."""
    lab = _lab(img); L = lab[..., 0]/100.0
    L = np.clip(L*2**exposure, 0, 1.2)
    L = pivot + (L - pivot)*(1 + contrast)
    hm = np.clip((L - 0.5)/0.5, 0, 1); sm = np.clip((0.5 - L)/0.5, 0, 1)
    L = L - highlights*0.25*hm**1.5 + shadows*0.25*sm**1.5
    L = L + whites*0.12*np.clip((L - 0.75)/0.25, 0, 1) + blacks*0.10*np.clip((0.25 - L)/0.25, 0, 1)
    if clarity:
        base = cv2.GaussianBlur(L.astype(np.float32), (0, 0), 12); L = L + (L - base)*clarity*0.8
    lab[..., 0] = np.clip(L, 0, 1)*100
    a, b = lab[..., 1], lab[..., 2]
    b += temp*12; a += tint*8
    C = np.hypot(a, b); sat = 1 + saturation; vib = 1 + vibrance*np.clip(1 - C/40, 0, 1)
    lab[..., 1] = a*sat*vib; lab[..., 2] = b*sat*vib
    return _bgr(lab)

def split_tone(img, shadow_ab=(0, 0), highlight_ab=(0, 0), balance=0.0):
    lab = _lab(img); L = lab[..., 0]/100
    ws = np.clip((0.5 + balance - L)/0.5, 0, 1); wh = np.clip((L - 0.5 + balance)/0.5, 0, 1)
    lab[..., 1] += ws*shadow_ab[0] + wh*highlight_ab[0]; lab[..., 2] += ws*shadow_ab[1] + wh*highlight_ab[1]
    return _bgr(lab)
def curves(img, pts=((0, 0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1, 1)), channel=None):
    x = np.clip(img/255, 0, 1)
    if channel is None: return _curve(x, pts)*255
    out = x.copy(); out[..., channel] = _curve(x[..., channel], pts); return out*255
def matte(img, lift=0.06, roll=0.95): return curves(img, ((0, lift), (0.5, 0.5 + lift*0.3), (1, roll)))
def monochrome(img, contrast=0.1, tone=(0, 0)):
    g = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    out = np.dstack([g]*3); out = adjust(out, contrast=contrast); return split_tone(out, tone, tone) if any(tone) else out

# ---------------- finishing ----------------
def vignette(img, amount=0.25, roundness=0.7, feather=0.6):
    h, w = img.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - w/2)/(w/2), (yy - h/2)/(h/2)*roundness); m = 1 - amount*np.clip((d - (1 - feather))/feather, 0, 1)**2
    return img*m[..., None]
def bloom(img, threshold=200, radius=30, amount=0.35):
    hi = np.clip(img - threshold, 0, 255)*(255/(256 - threshold)); return np.clip(img + cv2.GaussianBlur(hi, (0, 0), radius)*amount, 0, 255)
def halation(img, threshold=190, radius=12, color=(40, 80, 255), amount=0.35):
    L = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    m = cv2.GaussianBlur(np.clip(L - threshold, 0, 255)/(255 - threshold), (0, 0), radius)
    return np.clip(img + m[..., None]*np.array(color, np.float32)*amount, 0, 255)
def grain(img, amount=4.0, size=1.0, seed=None):
    rng = np.random.default_rng(seed); h, w = img.shape[:2]
    n = rng.normal(0, amount, (int(h/size), int(w/size), 1)).astype(np.float32)
    if size != 1.0: n = cv2.resize(n, (w, h))[..., None]
    L = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]/255
    return np.clip(img + n*(0.5 + 0.8*L*(1 - L)*2), 0, 255)
def sharpen(img, amount=0.4, radius=1.2): return np.clip(img + (img - cv2.GaussianBlur(img, (0, 0), radius))*amount, 0, 255)
def denoise_luma(img, strength=3):
    lab = _lab(img); lab[..., 0] = cv2.bilateralFilter(lab[..., 0], 5, strength, 3); return _bgr(lab)

# ---------------- LUTs ----------------
def load_cube(path):
    size = None; data = []
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("TITLE") or s.startswith("DOMAIN"): continue
        if s.startswith("LUT_3D_SIZE"): size = int(s.split()[1]); continue
        p = s.split()
        if len(p) == 3: data.append([float(v) for v in p])
    return np.array(data, np.float32).reshape(size, size, size, 3)   # [b][g][r] -> rgb
def apply_lut(img, lut, strength=1.0):
    n = lut.shape[0]; rgb = np.clip(img[..., ::-1]/255, 0, 1)*(n - 1)
    i0 = np.floor(rgb).astype(int); i1 = np.minimum(i0 + 1, n - 1); f = rgb - i0
    def g(r, gg, b): return lut[b, gg, r]
    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                r = i1[..., 0] if dr else i0[..., 0]; gg = i1[..., 1] if dg else i0[..., 1]; b = i1[..., 2] if db else i0[..., 2]
                wgt = (f[..., 0] if dr else 1 - f[..., 0])*(f[..., 1] if dg else 1 - f[..., 1])*(f[..., 2] if db else 1 - f[..., 2])
                out = out + g(r, gg, b)*wgt[..., None]
    res = out[..., ::-1]*255; return img*(1 - strength) + res*strength

# ---------------- reference matching ----------------
def stats(img, face_box=None):
    lab = _lab(img); L = lab[..., 0]
    s = dict(pct=[float(np.percentile(L, p)) for p in range(0, 101, 5)], a=float(np.median(lab[..., 1])), b=float(np.median(lab[..., 2])),
             chroma=float(np.hypot(lab[..., 1], lab[..., 2]).mean()))
    if face_box is not None:
        x, y, w, h = [int(v) for v in face_box]; r = lab[y + h//3:y + 2*h//3, x + w//4:x + 3*w//4].reshape(-1, 3)
        s["skin"] = r.mean(0).tolist()
    return s
def match_reference(img, src_stats, ref_stats, strength=0.6):
    """Map tone distribution, white balance and saturation of a clip toward a reference still."""
    lab = _lab(img); x = np.array(src_stats["pct"]); y = np.array(ref_stats["pct"]); x = np.maximum.accumulate(x + np.arange(len(x))*1e-3)
    Lm = np.interp(lab[..., 0], x, y); lab[..., 0] = lab[..., 0]*(1 - strength) + Lm*strength
    lab[..., 1] += (ref_stats["a"] - src_stats["a"])*strength*0.8; lab[..., 2] += (ref_stats["b"] - src_stats["b"])*strength*0.8
    k = 1 + (ref_stats["chroma"]/max(src_stats["chroma"], 1) - 1)*strength; lab[..., 1] *= k; lab[..., 2] *= k
    if "skin" in src_stats and "skin" in ref_stats:
        sk = np.clip((np.minimum(lab[..., 1], lab[..., 2]) - 4)/8, 0, 1)
        for c in (1, 2): lab[..., c] += sk*(ref_stats["skin"][c] - src_stats["skin"][c])*strength*0.6
    return _bgr(lab)

# ---------------- creative looks ----------------
LOOKS = {
 "natural":        lambda x: adjust(x, contrast=0.04, shadows=0.15, vibrance=0.1),
 "clean_commercial": lambda x: sharpen(adjust(x, exposure=0.15, contrast=0.08, shadows=0.2, highlights=0.2, vibrance=0.2, temp=0.05), 0.25),
 "bright_airy":    lambda x: adjust(x, exposure=0.3, contrast=-0.1, shadows=0.35, highlights=0.25, saturation=-0.05, temp=0.05),
 "warm_golden":    lambda x: split_tone(adjust(x, contrast=0.08, temp=0.35, vibrance=0.15), (2, 6), (4, 14)),
 "teal_orange":    lambda x: split_tone(adjust(x, contrast=0.12, saturation=0.05), (-4, -10), (5, 14)),
 "cool_blue":      lambda x: split_tone(adjust(x, contrast=0.1, temp=-0.35, saturation=-0.1), (0, -10), (-2, -4)),
 "moody_dark":     lambda x: vignette(split_tone(adjust(x, exposure=-0.25, contrast=0.2, highlights=0.3, saturation=-0.25), (-2, -6), (3, 8)), 0.35),
 "film_kodak":     lambda x: grain(halation(split_tone(matte(adjust(x, contrast=0.1, saturation=-0.05), 0.04), (-3, -6), (4, 12))), 3.5),
 "film_fuji":      lambda x: grain(split_tone(matte(adjust(x, contrast=0.06, saturation=-0.08), 0.05), (-6, -2), (-2, 8)), 3.0),
 "bleach_bypass":  lambda x: adjust(x, contrast=0.35, saturation=-0.55, clarity=0.3),
 "matte_fade":     lambda x: matte(adjust(x, contrast=-0.05, saturation=-0.15), 0.09),
 "vintage":        lambda x: grain(vignette(split_tone(matte(adjust(x, saturation=-0.25, temp=0.25), 0.1), (4, 8), (6, 16)), 0.3), 6),
 "pastel":         lambda x: adjust(x, exposure=0.2, contrast=-0.2, saturation=-0.25, shadows=0.3, highlights=0.2, temp=0.08),
 "high_contrast":  lambda x: adjust(x, contrast=0.3, blacks=-0.3, whites=0.3, clarity=0.2),
 "cinematic_crush": lambda x: vignette(split_tone(adjust(x, contrast=0.22, blacks=-0.4, highlights=0.25, saturation=-0.1), (-3, -8), (4, 10)), 0.3),
 "night_neon":     lambda x: bloom(split_tone(adjust(x, contrast=0.2, saturation=0.3, temp=-0.2), (8, -14), (10, -4)), 190, 25, 0.4),
 "sunset":         lambda x: bloom(split_tone(adjust(x, temp=0.5, tint=0.1, saturation=0.15), (6, 4), (8, 20)), 200, 30, 0.3),
 "bw_classic":     lambda x: grain(monochrome(x, 0.15), 3),
 "bw_high":        lambda x: monochrome(adjust(x, contrast=0.35, clarity=0.3), 0.25),
 "sepia":          lambda x: monochrome(x, 0.05, (3, 14)),
 "documentary":    lambda x: adjust(x, contrast=0.06, saturation=-0.15, shadows=0.1),
 "luxury":         lambda x: vignette(split_tone(adjust(x, contrast=0.12, blacks=-0.2, saturation=-0.1, clarity=0.1), (0, -4), (3, 10)), 0.25),
}
