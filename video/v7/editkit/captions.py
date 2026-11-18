"""Caption engine: style presets x animations x highlight modes.
render_chunk(words, style, anim, u, active) -> RGBA float image; Captioner draws timed chunks onto frames."""
import os, glob, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.path.join(os.path.dirname(HERE), "lib")

WNAMES = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}
def font_path(family, italic=False, weight=None):
    fam = family.replace(" ", "")
    pats = glob.glob(os.path.join(LIB, "gfonts/ofl", fam.lower(), "*.ttf")) + glob.glob(os.path.join(LIB, "fonts", fam + "*.ttf"))
    if not pats: raise FileNotFoundError(family)
    pats = [p for p in pats if ("Italic" in os.path.basename(p)) == italic] or pats
    var = [p for p in pats if "[" in p]
    if var: return var[0], True
    want = WNAMES.get(int(round((weight or 400)/100))*100, "Regular")
    for p in pats:
        nm = os.path.basename(p).split("-")[-1].replace(".ttf", "").replace("Italic", "")
        if nm == want or (want == "Regular" and nm == ""): return p, False
    return sorted(pats, key=len)[0], False
_FC = {}
def font(family, size, weight=None, italic=False):
    key = (family, size, weight, italic)
    if key not in _FC:
        p, var = font_path(family, italic, weight); f = ImageFont.truetype(p, size)
        if var and weight:
            try:
                axes = f.get_variation_axes(); vals = [a.get("default", 0) for a in axes]
                idx = next((i for i, ax in enumerate(axes) if "weight" in str(ax.get("name", b"")).lower()), 0)
                vals[idx] = max(axes[idx]["minimum"], min(axes[idx]["maximum"], weight))
                f.set_variation_by_axes(vals)
            except Exception: pass
        _FC[key] = f
    return _FC[key]

def _s(t): t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def _out(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t)**3
def _spring(t, d=0.32, o=0.14):
    if t <= 0: return 0.0
    u = min(t/d, 1.0); return 1 - math.exp(-6*u)*math.cos(u*math.pi*(1.5 + o*8)) if u < 1 else 1.0

# ---------------- style presets ----------------
P = lambda **k: k
STYLES = {
 # bold / social
 "hormozi":      P(family="Montserrat", size=86, weight=900, fill=(255, 255, 255), stroke=8, case="upper", hl="color", hl_col=(255, 214, 10), shadow=0.6),
 "bar_pop":      P(family="Rubik", size=80, weight=900, italic=True, fill=(255, 255, 255), stroke=8, case="upper", hl="bar", hl_col=(14, 14, 14), hl_scale=1.3, shadow=0.5),
 "red_bar":      P(family="Rubik", size=80, weight=900, italic=True, fill=(255, 255, 255), stroke=8, case="upper", hl="bar", hl_col=(229, 34, 34), hl_scale=1.3, shadow=0.5),
 "mrbeast":      P(family="Luckiest Guy", size=92, fill=(255, 255, 255), stroke=10, case="upper", hl="color", hl_col=(80, 255, 80), shadow=0.6),
 "comic":        P(family="Bangers", size=96, fill=(255, 240, 120), stroke=9, case="upper", hl="scale", hl_scale=1.25, shadow=0.6),
 "impact_clean": P(family="Anton", size=96, fill=(255, 255, 255), stroke=0, case="upper", hl="color", hl_col=(255, 196, 0), shadow=0.75),
 "bebas_box":    P(family="Bebas Neue", size=104, fill=(10, 10, 10), stroke=0, case="upper", box=(255, 255, 255), hl="color", hl_col=(229, 34, 34)),
 "neon":         P(family="Syne", size=78, weight=800, fill=(255, 255, 255), stroke=0, case="upper", glow=(0, 220, 255), hl="color", hl_col=(255, 60, 200)),
 "box_black":    P(family="Inter", size=64, weight=800, fill=(255, 255, 255), stroke=0, case="none", box=(0, 0, 0), box_alpha=0.75),
 "box_white":    P(family="Inter", size=64, weight=800, fill=(10, 10, 10), stroke=0, case="none", box=(255, 255, 255), box_alpha=0.95),
 "highlighter":  P(family="DM Sans", size=70, weight=800, fill=(255, 255, 255), stroke=0, case="none", hl="marker", hl_col=(255, 214, 10), shadow=0.6),
 "underline":    P(family="Plus Jakarta Sans", size=70, weight=800, fill=(255, 255, 255), stroke=0, hl="underline", hl_col=(255, 214, 10), shadow=0.6),
 "karaoke":      P(family="Montserrat", size=82, weight=900, fill=(255, 255, 255), stroke=7, case="upper", hl="karaoke", hl_col=(255, 214, 10), shadow=0.5),
 "gradient":     P(family="Outfit", size=86, weight=800, fill=(255, 255, 255), stroke=0, case="upper", grad=((255, 220, 120), (255, 120, 80)), shadow=0.6),
 "rounded":      P(family="Fredoka", size=84, weight=700, fill=(255, 255, 255), stroke=7, case="none", hl="color", hl_col=(120, 220, 255), shadow=0.5),
 "condensed":    P(family="Barlow Condensed", size=100, weight=800, fill=(255, 255, 255), stroke=0, case="upper", hl="color", hl_col=(255, 214, 10), shadow=0.7),
 # elegant / professional
 "elegant_serif":   P(family="Playfair Display", size=64, weight=500, fill=(255, 255, 255), stroke=0, case="none", hl="italic", hl_col=(236, 200, 140), shadow=0.55),
 "editorial":       P(family="Instrument Serif", size=80, fill=(255, 255, 255), stroke=0, case="none", hl="italic", hl_col=(255, 255, 255), shadow=0.5),
 "cormorant":       P(family="Cormorant Garamond", size=76, weight=600, fill=(250, 246, 238), stroke=0, case="none", hl="italic", hl_col=(236, 200, 140), shadow=0.5),
 "dm_serif":        P(family="DM Serif Display", size=72, fill=(255, 255, 255), stroke=0, case="none", hl="color", hl_col=(236, 200, 140), shadow=0.5),
 "minimal":         P(family="Inter", size=56, weight=500, fill=(255, 255, 255), stroke=0, case="none", shadow=0.5),
 "minimal_caps":    P(family="Manrope", size=50, weight=700, fill=(255, 255, 255), stroke=0, case="upper", tracking=6, shadow=0.5),
 "documentary":     P(family="Libre Baskerville", size=54, fill=(255, 255, 255), stroke=0, case="none", box=(0, 0, 0), box_alpha=0.45),
 "luxury":          P(family="Cormorant Garamond", size=70, weight=500, fill=(236, 214, 170), stroke=0, case="upper", tracking=10, shadow=0.6),
 # handwritten / playful
 "handwritten":  P(family="Caveat", size=92, weight=700, fill=(255, 255, 255), stroke=0, case="none", shadow=0.6),
 "marker":       P(family="Kalam", size=84, weight=700, fill=(255, 255, 255), stroke=0, case="none", shadow=0.6),
 "script":       P(family="Dancing Script", size=90, weight=700, fill=(255, 255, 255), stroke=0, case="none", shadow=0.6),
 "retro":        P(family="Righteous", size=82, fill=(255, 230, 160), stroke=6, stroke_col=(120, 40, 20), case="upper", shadow=0.4),
 "bungee":       P(family="Bungee", size=70, fill=(255, 214, 10), stroke=6, case="upper", shadow=0.5),
 "tech_mono":    P(family="Space Mono", size=58, fill=(140, 255, 160), stroke=0, case="none", box=(0, 0, 0), box_alpha=0.6),
}
ANIMS = ["none", "fade", "pop", "bounce", "slide_up", "slide_down", "slide_left", "blur_in", "scale_down", "drop", "typewriter",
         "word_by_word", "wave", "shake", "glow_pulse", "rise_per_word", "stamp"]

def _measure(words, fonts, sp, tracking):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return [d.textlength(w, font=f) + tracking*max(len(w) - 1, 0) for w, f in zip(words, fonts)]

def render_chunk(words, st, active=-1, reveal_chars=None, max_w=960, word_alpha=None, word_dy=None):
    """Draw one caption chunk. active: index of the spoken word; reveal_chars: typewriter count."""
    case = st.get("case", "none"); W = [w.upper() if case == "upper" else w for w in words]
    base = font(st["family"], st["size"], st.get("weight")); hl = st.get("hl")
    hit = font(st["family"], int(st["size"]*st.get("hl_scale", 1.0)), st.get("weight"), italic=(hl == "italic" or st.get("italic", False))) \
        if hl in ("italic", "scale", "bar") else base
    if st.get("italic") and hl != "italic": base = font(st["family"], st["size"], st.get("weight"), italic=True)
    fonts = [hit if (i == active and hl in ("italic", "scale", "bar")) else base for i in range(len(W))]
    tr = st.get("tracking", 0); sp = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(" ", font=base)*1.05 + 3*tr
    ws = _measure(W, fonts, sp, tr)
    lines, cur, cw = [], [], 0
    for i, w in enumerate(ws):
        if cur and cw + sp + w > max_w: lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + w; cur.append(i)
    if cur: lines.append(cur)
    stroke = st.get("stroke", 0); lh = int(st["size"]*st.get("hl_scale", 1.0)*1.15); pad = 40 + stroke*2
    Wd = int(max(sum(ws[i] for i in l) + sp*(len(l) - 1) for l in lines)) + 2*pad; Hd = lh*len(lines) + 2*pad
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    shown = reveal_chars if reveal_chars is not None else 10**9; nchar = 0
    if st.get("box") is not None:
        bx = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(bx).rounded_rectangle([pad - 24, pad - 14, Wd - pad + 24, Hd - pad + 14], 18,
            fill=tuple(st["box"]) + (int(255*st.get("box_alpha", 1.0)),)); im = Image.alpha_composite(im, bx); dr = ImageDraw.Draw(im)
    for li, l in enumerate(lines):
        lw = sum(ws[i] for i in l) + sp*(len(l) - 1); x = (Wd - lw)/2; base_y = pad + (li + 1)*lh - int(st["size"]*0.25)
        for i in l:
            w = W[i]; f = fonts[i]; col = st["fill"]
            is_hit = i == active or (hl == "karaoke" and i <= active)
            if is_hit and hl in ("color", "italic", "karaoke"): col = st.get("hl_col", col)
            a = 255 if word_alpha is None else int(255*word_alpha[i]); y = base_y + (0 if word_dy is None else word_dy[i])
            if is_hit and hl in ("bar", "marker", "underline") and i == active:
                cap = st["size"]*st.get("hl_scale", 1.0)*0.72
                if hl == "bar": dr.rounded_rectangle([x - 16, y - cap*0.45, x + ws[i] + 10, y + cap*0.34], int(cap*0.3), fill=st["hl_col"] + (240,))
                if hl == "marker": dr.rounded_rectangle([x - 8, y - cap*0.75, x + ws[i] + 8, y + cap*0.12], 8, fill=st["hl_col"] + (200,))
                if hl == "underline": dr.rounded_rectangle([x, y + 8, x + ws[i], y + 16], 4, fill=st["hl_col"] + (255,))
            vis = w[:max(0, shown - nchar)]; nchar += len(w) + 1
            if vis:
                if tr:
                    xx = x
                    for ch in vis:
                        dr.text((xx, y), ch, font=f, fill=col + (a,), anchor="ls", stroke_width=stroke, stroke_fill=st.get("stroke_col", (0, 0, 0)) + (a,))
                        xx += dr.textlength(ch, font=f) + tr
                else:
                    dr.text((x, y), vis, font=f, fill=col + (a,), anchor="ls", stroke_width=stroke, stroke_fill=st.get("stroke_col", (0, 0, 0)) + (a,))
            x += ws[i] + sp
    if st.get("grad"):
        g0, g1 = np.array(st["grad"][0], np.float32), np.array(st["grad"][1], np.float32); arr = np.array(im).astype(np.float32)
        ramp = np.linspace(0, 1, Hd)[:, None, None]; colmask = (arr[..., :3].sum(2, keepdims=True) > 600)
        arr[..., :3] = np.where(colmask, g0*(1 - ramp) + g1*ramp, arr[..., :3]); im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    if st.get("glow"):
        gl = Image.new("RGBA", im.size, tuple(st["glow"]) + (0,)); gl.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(14))); out = Image.alpha_composite(out, gl); out = Image.alpha_composite(out, gl)
    if st.get("shadow"):
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v*st["shadow"])).filter(ImageFilter.GaussianBlur(9)))
        out.alpha_composite(sh, (0, 5))
    out = Image.alpha_composite(out, im)
    return np.array(out).astype(np.float32)

def composite(frame, rgba, cx, cy, scale=1.0, alpha=1.0, rot=0.0, blur=0.0):
    if alpha <= 0.003 or scale <= 0.01: return
    im = rgba
    if blur > 0.4: im = cv2.GaussianBlur(im, (0, 0), blur)
    if scale != 1.0 or rot:
        h, w = im.shape[:2]; M = cv2.getRotationMatrix2D((w/2, h/2), rot, scale); nw, nh = int(w*max(scale, 1)*1.2) + 4, int(h*max(scale, 1)*1.2) + 4
        M[0, 2] += nw/2 - w/2; M[1, 2] += nh/2 - h/2; im = cv2.warpAffine(im, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    h, w = im.shape[:2]; x0, y0 = int(round(cx - w/2)), int(round(cy - h/2)); H, W = frame.shape[:2]
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    src = im[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4]/255*alpha
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb]*(1 - a) + src[..., 2::-1]*a

class Captioner:
    """chunks: [(t0, t1, text)] on the output timeline. style: name or dict. anim: one of ANIMS."""
    def __init__(self, chunks, style="elegant_serif", anim="fade", y=1300, max_words=3, max_chars=18, hidden=()):
        self.st = STYLES[style] if isinstance(style, str) else style; self.anim = anim; self.y = y; self.hidden = hidden; self.ch = []
        for t0, t1, text in chunks:
            ws = text.split(); groups, cur = [], []
            for w in ws:
                if cur and (len(cur) >= max_words or len(" ".join(cur + [w])) > max_chars or cur[-1][-1] in ",.?!"): groups.append(cur); cur = []
                cur.append(w)
            if cur: groups.append(cur)
            L = np.array([len(" ".join(g)) + 3 for g in groups], float); e = t0 + np.concatenate([[0], np.cumsum(L)])/L.sum()*(t1 - t0)
            for g, a, b in zip(groups, e[:-1], e[1:]):
                wl = np.array([len(w) + 2 for w in g], float); ws_ = a + np.concatenate([[0], np.cumsum(wl)[:-1]])/wl.sum()*(b - a)
                self.ch.append(dict(t0=a, t1=b, words=g, ws=ws_))
        for i, c in enumerate(self.ch):
            nx = self.ch[i + 1]["t0"] if i + 1 < len(self.ch) else c["t1"] + 1
            c["hold"] = nx if nx - c["t1"] < 0.4 else c["t1"] + 0.15
        self.cache = {}
    def draw(self, f, t):
        if any(a <= t < b for a, b in self.hidden): return
        for c in self.ch:
            if not (c["t0"] <= t < c["hold"]): continue
            u = t - c["t0"]; n = len(c["words"])
            act = int(np.searchsorted(c["ws"], t, side="right") - 1) if t < c["t1"] else -1
            A = self.anim; wa = wdy = None; reveal = None; sc = 1.0; al = 1.0; dx = dy = 0.0; blur = 0.0; rot = 0.0
            if A == "typewriter":
                total = len(" ".join(c["words"])); reveal = int(total*min(1, u/max(c["t1"] - c["t0"], 0.2)*1.2))
            elif A in ("word_by_word", "rise_per_word"):
                wa = [float(np.clip((t - s)/0.08, 0, 1)) for s in c["ws"]]
                if A == "rise_per_word": wdy = [int(18*(1 - _out((t - s)/0.2))) for s in c["ws"]]
            elif A == "wave": wdy = [int(8*math.sin(t*9 + i)) for i in range(n)]
            key = (id(c), act, reveal, None if wa is None else tuple(round(x, 1) for x in wa), None if wdy is None else tuple(wdy))
            img = self.cache.get(key)
            if img is None:
                img = render_chunk(c["words"], self.st, act, reveal, max_w=getattr(self, "max_w", 960), word_alpha=wa, word_dy=wdy)
                if len(self.cache) > 400: self.cache.clear()
                self.cache[key] = img
            if A == "fade": al = _s(u/0.15)
            elif A == "pop": sc = 0.72 + 0.28*_spring(u, 0.3, 0.14); al = min(1, u/0.06)
            elif A == "bounce": sc = 0.6 + 0.4*_spring(u, 0.4, 0.3); al = min(1, u/0.05)
            elif A == "slide_up": dy = 40*(1 - _out(u/0.25)); al = _s(u/0.15)
            elif A == "slide_down": dy = -40*(1 - _out(u/0.25)); al = _s(u/0.15)
            elif A == "slide_left": dx = 80*(1 - _out(u/0.25)); al = _s(u/0.15)
            elif A == "blur_in": blur = 12*(1 - _out(u/0.3)); al = _s(u/0.2)
            elif A == "scale_down": sc = 1.35 - 0.35*_out(u/0.25); al = _s(u/0.12)
            elif A == "drop": dy = -120*(1 - _spring(u, 0.35, 0.2)); al = min(1, u/0.05)
            elif A == "shake": dx = 6*math.sin(t*60)*max(0, 1 - u/0.3)
            elif A == "glow_pulse": sc = 1 + 0.03*math.sin(u*8)
            elif A == "stamp": sc = 1.6 - 0.6*_out(u/0.12); rot = -4*(1 - _out(u/0.12)); al = min(1, u/0.04)
            if act >= 0 and A in ("pop", "bounce"): sc *= 1 + 0.03*math.sin(min((t - c["ws"][act])/0.16, 1)*math.pi)
            if t > c["hold"] - 0.1 and c["hold"] - c["t1"] > 0.05: al *= _s((c["hold"] - t)/0.1)
            composite(f, img, getattr(self, "x", f.shape[1]/2) + dx, self.y + dy, sc, al, rot, blur); return
