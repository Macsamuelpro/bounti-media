"""Shared effects for the Bounti edits: captions, props, SFX placement, morph cuts, speed ramps."""
import os, json, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OW, OH = 1080, 1920
FONT_VAR = os.path.join(HERE, "lib/fonts/Montserrat[wght].ttf")

def ease_out(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t)**3
def ease_io(t):
    t = min(max(t, 0.0), 1.0); return 4*t**3 if t < 0.5 else 1 - (-2*t + 2)**3/2
def smooth(t):
    t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def spring(t, dur=0.32, overshoot=0.12):
    """0 -> 1 with one damped overshoot (bouncy pop)."""
    if t <= 0: return 0.0
    u = min(t/dur, 1.0)
    return 1 - math.exp(-6*u)*math.cos(u*math.pi*(1.5 + overshoot*8)) if u < 1 else 1.0

def mfont(size, weight=900):
    f = ImageFont.truetype(FONT_VAR, size); f.set_variation_by_axes([weight]); return f
def ifont(style, size):
    p = subprocess.run(["fc-match", "-f", "%{file}", f"Inter Display:style={style}"], capture_output=True, text=True).stdout
    return ImageFont.truetype(p, size)

# ---------------------------------------------------------------- compositing
def composite(frame_bgr_f32, rgba, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    """Paste an RGBA (RGB order, float or uint8) image centred at cx,cy onto a float BGR frame."""
    if alpha <= 0.003 or scale <= 0.01: return
    im = rgba.astype(np.float32)
    if scale != 1.0 or rot != 0.0:
        h, w = im.shape[:2]
        M = cv2.getRotationMatrix2D((w/2, h/2), rot, scale)
        nw, nh = int(w*scale*1.2) + 4, int(h*scale*1.2) + 4
        M[0, 2] += nw/2 - w/2; M[1, 2] += nh/2 - h/2
        im = cv2.warpAffine(im, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    h, w = im.shape[:2]; x0, y0 = int(round(cx - w/2)), int(round(cy - h/2))
    FH, FW = frame_bgr_f32.shape[:2]
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, FW), min(y0 + h, FH)
    if xa >= xb or ya >= yb: return
    src = im[ya - y0:yb - y0, xa - x0:xb - x0]; a = src[..., 3:4]/255*alpha
    dst = frame_bgr_f32[ya:yb, xa:xb]
    dst[:] = dst*(1 - a) + src[..., 2::-1]*a

def shadowed(img_rgba, blur=14, opacity=0.45, dy=8):
    """Add a soft drop shadow under an RGBA PIL image (returns PIL)."""
    pad = blur*3
    W, H = img_rgba.size[0] + 2*pad, img_rgba.size[1] + 2*pad
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = img_rgba.split()[3].point(lambda v: int(v*opacity))
    sh.paste((0, 0, 0, 255), (pad, pad + dy), a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.alpha_composite(sh); out.alpha_composite(img_rgba, (pad, pad))
    return out

# ---------------------------------------------------------------- captions
class Captions:
    """Bold, slanted, word-by-word captions: active word bigger with a black bar under it.
    chunks: list of (t0, t1, text) on the output timeline."""
    FONT = os.path.join(HERE, "lib/fonts/Rubik-Italic[wght].ttf")
    def __init__(self, chunks, y=1250, size=80, big=1.34, max_w=980, bar=(14, 14, 14), hidden=(), y_fn=None):
        self.y, self.size, self.big, self.max_w, self.bar, self.y_fn = y, size, big, max_w, bar, y_fn
        self.f = ImageFont.truetype(self.FONT, size); self.f.set_variation_by_axes([900])
        self.fb = ImageFont.truetype(self.FONT, int(size*big)); self.fb.set_variation_by_axes([900])
        self.cache = {}; self.chunks = []; self.hidden = hidden
        split = []
        for t0, t1, text in chunks:
            ws = text.split(); groups, cur = [], []
            for w in ws:
                if cur and (len(cur) >= 3 or len(" ".join(cur + [w])) > 17): groups.append(cur); cur = []
                cur.append(w)
            if cur: groups.append(cur)
            lens = np.array([len(" ".join(g)) + 3 for g in groups], float); edges = t0 + np.concatenate([[0], np.cumsum(lens)])/lens.sum()*(t1 - t0)
            for g, a, b in zip(groups, edges[:-1], edges[1:]): split.append((a, b, " ".join(g)))
        for t0, t1, text in split:
            words = text.upper().split()
            wts = np.array([len(w.strip(",.?!")) + 2.5 for w in words], float); wts /= wts.sum()
            starts = t0 + np.concatenate([[0], np.cumsum(wts)[:-1]])*(t1 - t0)
            self.chunks.append(dict(t0=t0, t1=t1, words=words, ws=starts))
        for i, c in enumerate(self.chunks):
            nxt = self.chunks[i + 1]["t0"] if i + 1 < len(self.chunks) else c["t1"] + 0.3
            c["contig"] = nxt - c["t1"] < 0.35
            c["hold"] = nxt if c["contig"] else c["t1"] + 0.12
    def _render(self, ci, active):
        key = (ci, active)
        if key in self.cache: return self.cache[key]
        words = self.chunks[ci]["words"]
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        fonts = [self.fb if i == active else self.f for i in range(len(words))]
        widths = [d.textlength(w, font=fonts[i]) for i, w in enumerate(words)]
        sp = d.textlength(" ", font=self.f)*1.1
        lines, cur, cw = [], [], 0
        for i, w in enumerate(widths):
            if cur and cw + sp + w > self.max_w: lines.append(cur); cur, cw = [], 0
            cw = cw + (sp if cur else 0) + w; cur.append(i)
        if cur: lines.append(cur)
        stroke = max(7, self.size//10); lh = int(self.size*self.big*1.08)
        W = int(max(sum(widths[i] for i in l) + sp*(len(l) - 1) for l in lines)) + 6*stroke + 40
        H = lh*len(lines) + 6*stroke + 40
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        for li, l in enumerate(lines):
            lw = sum(widths[i] for i in l) + sp*(len(l) - 1); x = (W - lw)/2
            base = 3*stroke + 20 + (li + 1)*lh - int(self.size*0.18)
            for i in l:
                if i == active:
                    cap = self.size*self.big*0.72
                    dr.rounded_rectangle([x - 18, base - cap*0.42, x + widths[i] + 12, base + cap*0.36], radius=int(cap*0.30), fill=self.bar + (245,))
                dr.text((x, base), words[i], font=fonts[i], fill=(255, 255, 255, 255), anchor="ls",
                        stroke_width=stroke + (2 if i == active else 0), stroke_fill=(0, 0, 0, 255))
                x += widths[i] + sp
        out = np.array(shadowed(im, blur=10, opacity=0.5, dy=6)).astype(np.float32)
        self.cache[key] = out; return out
    def draw(self, frame, t):
        for ci, c in enumerate(self.chunks):
            if c["t0"] <= t < c["hold"]:
                if any(a <= t < b for a, b in self.hidden): return
                k = int(np.searchsorted(c["ws"], t, side="right") - 1)
                active = min(max(k, 0), len(c["words"]) - 1) if t < c["t1"] + 0.05 else -1
                img = self._render(ci, active)
                u = t - c["t0"]; s = 0.70 + 0.30*spring(u, 0.30, 0.16)
                if active >= 0:                       # small bounce each time a new word lights up
                    uw = t - c["ws"][active]; s *= 1 + 0.035*math.sin(min(uw/0.16, 1)*math.pi)
                a = min(1.0, u/0.06)
                if not c["contig"] and t > c["hold"] - 0.08: a *= max(0.0, (c["hold"] - t)/0.08)
                if "y" not in c: c["y"] = self.y_fn(c["t0"] + 0.05) if self.y_fn else self.y
                composite(frame, img, OW/2, c["y"] + (1 - smooth(u/0.18))*18, s, a, rot=0)
                return

# ---------------------------------------------------------------- props (premium design system)
import resvg_py, io
ICON_DIR = os.path.join(HERE, "lib/icons/package/icons")
INK = (10, 10, 10); MUTED = (107, 114, 128); GREEN = (22, 163, 74); RED = (225, 29, 72); BLUE = (37, 99, 235)
SS = 3
_ICON = {}
def icon(name, px, color, stroke=2.25):
    key = (name, px, color, stroke)
    if key not in _ICON:
        svg = open(os.path.join(ICON_DIR, name + ".svg")).read()
        hexc = "#%02x%02x%02x" % color
        svg = svg.replace('stroke="currentColor"', f'stroke="{hexc}"').replace('stroke-width="2"', f'stroke-width="{stroke}"')
        svg = svg.replace('width="24"', f'width="{px}"').replace('height="24"', f'height="{px}"')
        png = bytes(resvg_py.svg_to_bytes(svg_string=svg))
        _ICON[key] = Image.open(io.BytesIO(png)).convert("RGBA")
    return _ICON[key]
def tint(c, a):
    k = a/255*0.55; return tuple(int(255 - (255 - v)*k) for v in c) + (255,)
def card(w, h, r=34):
    im = Image.new("RGBA", (w*SS, h*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w*SS - 1, h*SS - 1], r*SS, fill=(255, 255, 255, 255), outline=(0, 0, 0, 16), width=2*SS)
    return im, d
def tile(im, x, y, size, name, color, r=22):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x*SS, y*SS, (x + size)*SS, (y + size)*SS], r*SS, fill=tint(color, 30))
    ic = icon(name, int(size*0.5*SS), color); o = int((size*SS - ic.size[0])/2)
    im.alpha_composite(ic, (x*SS + o, y*SS + o))
def finish(im):
    im = im.resize((im.size[0]//SS, im.size[1]//SS), Image.LANCZOS)
    pad = 60; W, H = im.size[0] + 2*pad, im.size[1] + 2*pad
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = im.split()[3]
    for blur, op, dy in ((30, 0.22, 20), (7, 0.16, 4)):
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.paste((0, 0, 0, 255), (pad, pad + dy), a.point(lambda v: int(v*op)))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(im, (pad, pad))
    return np.array(out).astype(np.float32)
def F(style, size): return ifont(style, size*SS)
def fmt(n): return f"{int(n):,}"
_CUR = None
def cursor_img():
    global _CUR
    if _CUR is None:
        ic = icon("mouse-pointer-2", 56*SS, (10, 10, 10), 2.0)
        fill = Image.new("RGBA", ic.size, (0, 0, 0, 0))
        svg = open(os.path.join(ICON_DIR, "mouse-pointer-2.svg")).read().replace('fill="none"', 'fill="#ffffff"').replace('stroke="currentColor"', 'stroke="#0a0a0a"').replace('width="24"', f'width="{56*SS}"').replace('height="24"', f'height="{56*SS}"').replace('stroke-width="2"', 'stroke-width="1.6"')
        im = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert("RGBA").resize((56, 56), Image.LANCZOS)
        out = Image.new("RGBA", (96, 96), (0, 0, 0, 0)); sh = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        sh.paste((0, 0, 0, 255), (22, 25), im.split()[3].point(lambda v: int(v*0.35))); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
        out.alpha_composite(im, (20, 20)); _CUR = np.array(out).astype(np.float32)
    return _CUR

class Prop:
    """One timed overlay. kind picks the design; (cx, cy) its centre; set later by place() if None."""
    SIZES = {"social": (420, 150), "signup": (440, 136), "signups_count": (330, 150), "search": (600, 124),
             "results": (440, 250), "event": (330, 150), "verified": (330, 112), "owe": (330, 150), "views": (360, 150)}
    def __init__(self, kind, t0, t1, cx=None, cy=None, scale=1.0, **kw):
        self.kind, self.t0, self.t1, self.cx, self.cy, self.scale, self.kw = kind, t0, t1, cx, cy, scale, kw
    @property
    def size(self):
        w, h = self.SIZES[self.kind]; return int(w*self.scale), int(h*self.scale)
    def active(self, t): return self.t0 <= t <= self.t1 + 0.25
    def draw(self, frame, t):
        if not self.active(t) or self.cx is None: return
        u = t - self.t0
        k = spring(u, 0.42, 0.10); a = min(1.0, u/0.12); dy = (1 - ease_out(u/0.35))*36
        if t > self.t1:
            v = ease_io((t - self.t1)/0.25); a *= 1 - v; k *= 1 - 0.04*v; dy -= 10*v
        img, extra = getattr(self, "_" + self.kind)(u)
        s = (0.9 + 0.1*k)*self.scale
        composite(frame, img, self.cx, self.cy + dy, s, a)
        if extra: extra(frame, s, a, dy)
    # ---- designs
    def _social(self, u):
        W, H = 420, 150; im = Image.new("RGBA", (W*SS, H*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for i, (name, col) in enumerate((("heart", RED), ("message-circle", BLUE), ("user-plus", GREEN))):
            k = spring(u - i*0.12, 0.34, 0.18)
            if k <= 0.01: continue
            cx, cy, r = 70 + i*140, 75, 62*min(k, 1.12)
            d.ellipse([(cx - r)*SS, (cy - r)*SS, (cx + r)*SS, (cy + r)*SS], fill=(255, 255, 255, 255), outline=(0, 0, 0, 16), width=2*SS)
            ic = icon(name, int(52*SS*min(k, 1.1)), col, 2.4)
            if name == "heart":
                svg = open(os.path.join(ICON_DIR, "heart.svg")).read().replace('fill="none"', '').replace('<path', f'<path fill="#{col[0]:02x}{col[1]:02x}{col[2]:02x}"', 1).replace('stroke="currentColor"', f'stroke="#{col[0]:02x}{col[1]:02x}{col[2]:02x}"').replace('width="24"', f'width="{int(52*SS*min(k,1.1))}"').replace('height="24"', f'height="{int(52*SS*min(k,1.1))}"')
                ic = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert("RGBA")
            im.alpha_composite(ic, (int(cx*SS - ic.size[0]/2), int(cy*SS - ic.size[1]/2)))
        return finish(im), None
    def _stat(self, u, label, value, name, col, value_col=INK):
        W, H = self.SIZES[self.kind]; im, d = card(W, H, r=30)
        ts = 76; tile(im, 22, (H - ts)//2, ts, name, col, 22)
        d.text((116*SS, (H/2 - 42)*SS), label, font=F("SemiBold", 24), fill=MUTED)
        d.text((114*SS, (H/2 - 12)*SS), value, font=F("Bold", 54), fill=value_col)
        return finish(im)
    def _signups_count(self, u):
        clicks = self.kw.get("clicks", [0.35, 0.75]); n = sum(1 for c in clicks if u >= c)
        img = self._stat(u, "Sign-ups", str(n), "user-plus", GREEN)
        def extra(frame, s, a, dy):
            k = ease_out((u - 0.05)/0.28); press = any(0 <= u - c < 0.08 for c in clicks)
            sd = -1 if self.cx < OW/2 else 1
            composite(frame, cursor_img(), self.cx + sd*(130*self.scale + (1 - k)*110), self.cy + 40*self.scale + dy + (1 - k)*60, 0.9 if press else 1.0, a)
        return img, extra
    def _event(self, u): return self._stat(u, "Event attendees", "0", "calendar-x", RED, RED), None
    def _owe(self, u): return self._stat(u, "Amount due", "$0.00", "receipt", GREEN, GREEN), None
    def _views(self, u): return self._stat(u, "Views", fmt(self.kw.get("target", 24815)*ease_out((u - 0.1)/1.1)), "eye", BLUE), None
    def _verified(self, u):
        W, H = self.SIZES["verified"]; im, d = card(W, H, r=H//2)
        k = spring(u - 0.12, 0.32, 0.2)
        if k > 0.01:
            ic = icon("badge-check", int(64*SS*min(k, 1.1)), GREEN, 2.4)
            im.alpha_composite(ic, (int(58*SS - ic.size[0]/2), int(H/2*SS - ic.size[1]/2)))
        d.text((104*SS, (H/2 - 29)*SS), "Verified", font=F("Bold", 48), fill=INK)
        return finish(im), None
    def _signup(self, u):
        c = self.kw.get("click", 0.55); done = u >= c + 0.06; press = 0 <= u - c < 0.1
        W, H = self.SIZES["signup"]; im = Image.new("RGBA", (W*SS, H*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        col = GREEN if done else INK
        d.rounded_rectangle([0, 0, W*SS - 1, H*SS - 1], (H//2)*SS, fill=col + (255,))
        txt = "Signed up" if done else "Sign up"; f = F("Bold", 50); tw = d.textlength(txt, font=f)/SS
        x0 = (W - tw - (64 if done else 0))/2
        if done:
            ic = icon("check", 50*SS, (255, 255, 255), 3.0); im.alpha_composite(ic, (int(x0*SS), int((H/2 - 25)*SS))); x0 += 64
        d.text((x0*SS, (H/2 - 31)*SS), txt, font=f, fill=(255, 255, 255))
        img = finish(im)
        if press: img = cv2.resize(img, None, fx=0.96, fy=0.96)
        def extra(frame, s, a, dy):
            k = ease_io((u - 0.05)/max(c - 0.05, 0.01)); sd = -1 if self.cx < OW/2 else 1
            x = self.cx + sd*(230 - 120*k)*self.scale; y = self.cy + (150 - 120*k)*self.scale + dy
            composite(frame, cursor_img(), x, y, 0.9 if press else 1.0, a)
        return img, extra
    def _search(self, u):
        text = self.kw.get("text", "your business"); n = int(max(0, (u - 0.25)*15)); shown = text[:n]
        W, H = self.SIZES["search"]; im = Image.new("RGBA", (W*SS, H*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, W*SS - 1, H*SS - 1], (H//2)*SS, fill=(255, 255, 255, 255), outline=(0, 0, 0, 16), width=2*SS)
        ic = icon("search", 46*SS, MUTED, 2.6); im.alpha_composite(ic, (int(38*SS), int((H/2 - 23)*SS)))
        f = F("Medium", 46); d.text((106*SS, (H/2 - 29)*SS), shown, font=f, fill=INK)
        if int(u*2.4) % 2 == 0 or n < len(text):
            x = 106*SS + d.textlength(shown, font=f) + 5*SS; d.rounded_rectangle([x, (H/2 - 26)*SS, x + 4*SS, (H/2 + 26)*SS], 2*SS, fill=BLUE)
        return finish(im), None
    def _results(self, u):
        W, H = self.SIZES["results"]; im, d = card(W, H)
        tile(im, 26, 24, 72, "trending-up", GREEN, 22)
        d.text((116*SS, 26*SS), "Results", font=F("Bold", 36), fill=INK)
        d.text((116*SS, 68*SS), "Campaign live", font=F("Medium", 24), fill=MUTED)
        vals = (0.28, 0.42, 0.38, 0.6, 0.74, 1.0); n = len(vals); base, top = H - 26, 120; bw = 48; gap = (W - 52 - n*bw)/(n - 1)
        for i, v in enumerate(vals):
            k = ease_out((u - 0.2 - i*0.08)/0.35); h = (base - top)*v*k
            if h > 3:
                x = 26 + i*(bw + gap)
                d.rounded_rectangle([x*SS, (base - h)*SS, (x + bw)*SS, base*SS], 12*SS, fill=GREEN if i == n - 1 else tint(GREEN, 150))
        return finish(im), None

def place_prop(prop, masks, face=None, cap_top=1140, scales=(1.0, 0.88, 0.78), max_ov=0.02):
    """Choose a centre inside the platform safe zone where the prop's box stays clear of the person in EVERY
    sampled frame (masks at output res), the caption band and the right-hand UI column. Prefers the height of the
    face and the side with more room. Tries smaller sizes if needed. Returns (score, cx, cy, worst_overlap, scale)."""
    stack = [cv2.dilate((m > 0.3).astype(np.uint8), np.ones((41, 41), np.uint8)) for m in masks]
    iis = [m.cumsum(0).cumsum(1).astype(np.float64) for m in stack]
    def ov(ii, x0, y0, x1, y1):
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, OW - 1), min(y1, OH - 1)
        return ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]
    fy = face[1] if face is not None else OH*0.33
    best_any = None
    for sc in scales:
        prop.scale = sc; w, h = prop.size; best = None
        for cy in range(250 + h//2, cap_top - h//2 - 20, 10):
            for cx in range(60 + w//2, OW - 60 - w//2 + 1, 10):
                if cy + h//2 > 840 and cx + w//2 > 880: continue
                box = (cx - w//2 - 16, cy - h//2 - 16, cx + w//2 + 16, cy + h//2 + 16)
                o = max(ov(ii, *box) for ii in iis)/((w + 32)*(h + 32))
                score = o*100 + abs(cy - fy)/OH*3 + abs(cx - OW/2)/OW*0.6
                if best is None or score < best[0]: best = (score, cx, cy, o, sc)
        if best_any is None or best[3] < best_any[3]: best_any = best
        if best[3] <= max_ov: break
    _, prop.cx, prop.cy, _, prop.scale = best_any
    return best_any

# ---------------------------------------------------------------- SFX library
SFX_DIR = os.path.join(HERE, "lib/sfx-kit")
_SND = {x["id"]: x for x in json.load(open(os.path.join(SFX_DIR, "sounds.json")))["sounds"]}
_CACHE = {}
def sfx_audio(sid, R=48000):
    if sid not in _CACHE:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(SFX_DIR, _SND[sid]["file"]), "-f", "f32le", "-ac", "2", "-ar", str(R), "-"], capture_output=True).stdout
        _CACHE[sid] = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    return _CACHE[sid]
def place_sfx(buf, sid, moment, gain_db=0.0, speech=(), R=48000, pan=0.0):
    """Start the sound at moment - sync.at; duck by its under_voiceover_db if its body overlaps speech."""
    m = _SND[sid]; x = sfx_audio(sid, R)
    start = moment - m["sync"]["at"]
    body = (start + m["timing"]["onset"], start + m["timing"]["body_end"])
    g = gain_db
    if any(a < body[1] and b > body[0] for a, b in speech): g += m["under_voiceover_db"]
    x = x*10**(g/20)
    if pan: a = (pan + 1)*np.pi/4; x = x*np.array([np.cos(a), np.sin(a)])*np.sqrt(2)
    s = int(round(start*R))
    if s < 0: x = x[-s:]; s = 0
    e = min(s + len(x), len(buf))
    if e > s: buf[s:e] += x[:e - s]
    return start

# ---------------------------------------------------------------- morph cut
_dis = None
def morph_frames(A, B, t):
    """Optical-flow morph between BGR uint8 frames A and B at fraction t (0=A, 1=B)."""
    global _dis
    if _dis is None: _dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    h, w = A.shape[:2]; sc = 0.5
    ga = cv2.resize(cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), None, fx=sc, fy=sc)
    gb = cv2.resize(cv2.cvtColor(B, cv2.COLOR_BGR2GRAY), None, fx=sc, fy=sc)
    fab = cv2.resize(_dis.calc(ga, gb, None), (w, h))/sc
    fba = cv2.resize(_dis.calc(gb, ga, None), (w, h))/sc
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    Aw = cv2.remap(A, gx - t*fab[..., 0], gy - t*fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    Bw = cv2.remap(B, gx - (1 - t)*fba[..., 0], gy - (1 - t)*fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.addWeighted(Aw, 1 - t, Bw, t, 0)

# ---------------------------------------------------------------- speed ramp
def ramp_times(a, b, zones, fps=24, ramp=0.30):
    """Source times (s) for each output frame of a segment a..b, speeding up to vmax inside each zone
    (z0, z1, vmax) with smooth ramps; 1x elsewhere. Zones must sit inside speech pauses."""
    def v(s):
        out = 1.0
        for z0, z1, vm in zones:
            if z0 <= s <= z1:
                k = min(smooth((s - z0)/ramp), smooth((z1 - s)/ramp))
                out = max(out, 1 + (vm - 1)*k)
        return out
    ts, s = [], a
    while s < b - 1e-6:
        ts.append(s); s += v(s)/fps
    return ts


# ---------------------------------------------------------------- caption height that avoids the hoodie logo
def caption_y(frame_bgr, default=1240, half=72, detector=None):
    """If the white hoodie print sits in the caption band, lift the captions above it (and below the chin)."""
    f = np.clip(frame_bgr, 0, 255).astype(np.uint8)
    reg = f[880:1520, 240:840]
    mn = reg.min(2).astype(int); mx = reg.max(2).astype(int)
    white = (mn > 170) & (mx - mn < 45)
    dark = cv2.boxFilter((mx < 60).astype(np.float32), -1, (41, 41))
    rows = (white & (dark > 0.25)).sum(1)            # white print on the black hoodie only
    hit = np.nonzero(rows > 18)[0] + 880
    if len(hit) == 0: return default
    groups, cur = [], [hit[0]]
    for r in hit[1:]:
        if r - cur[-1] <= 14: cur.append(r)
        else: groups.append(cur); cur = [r]
    groups.append(cur)
    big = [(g[0], g[-1]) for g in groups if g[-1] - g[0] >= 35 and not (g[-1] < default - half - 10 or g[0] > default + half + 10)]
    if not big: return default
    top, bot = min(b[0] for b in big), max(b[1] for b in big)
    chin = 0
    if detector is not None:
        _, fs = detector.detect(cv2.resize(f, (720, 1280)))
        if fs is not None: x, y, w, h = fs[0][:4]*1.5; chin = y + h*1.12
    y = top - half - 18
    return int(max(y, chin + half + 10)) if max(y, chin + half + 10) < top - 20 else default
