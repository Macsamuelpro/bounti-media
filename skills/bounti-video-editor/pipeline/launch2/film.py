"""Bounti premium launch film engine v2.
3D devices (phone, laptop) as perspective planes with keyframed poses, shadows and glass sheen; exploded UI layers;
masked line-reveal type; whip transitions; camera moves; beat-snapped cuts; ElevenLabs VO; Lyria music.
usage: film.py <video> <V|H>   (PREVIEW=t1,t2,... for a strip)"""
import os, sys, json, math, io, subprocess
import numpy as np, cv2, soundfile as sf
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
for p in (SP, os.path.join(SP, "editkit")): sys.path.insert(0, p)
import fx, captions as CAP
from shots import FILMS
NAME, FMT = sys.argv[1], sys.argv[2]; F = FILMS[NAME]; VERT = FMT == "V"
OW, OH = (1080, 1920) if VERT else (1920, 1080); FPS = 30; R = 48000; U = min(OW, OH)
PAPER = np.array((236, 240, 241), np.float32); INK = np.array((14, 14, 14), np.float32); GOLD = (84, 178, 226); GREY = (110, 110, 110)
def clamp(x, a=0.0, b=1.0): return min(max(x, a), b)
def ease(t): t = clamp(t); return t*t*t*(t*(6*t - 15) + 10)          # smootherstep
def eout(t): t = clamp(t); return 1 - (1 - t)**4
def ein(t): t = clamp(t); return t**3
# ---------------- text ----------------
_fc = {}
def font(sz, w=900):
    if (sz, w) not in _fc: _fc[(sz, w)] = CAP.font("Inter", sz, w)
    return _fc[(sz, w)]
def text_rgba(txt, sz, col, w=900, track=-0.045):
    f = font(sz, w); d = ImageDraw.Draw(Image.new("L", (1, 1))); wd = sum(d.textlength(c, font=f) + track*sz for c in txt) - track*sz
    im = Image.new("RGBA", (int(wd) + 30, int(sz*1.3)), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); x = 15
    for c in txt: dr.text((x, int(sz*0.04)), c, font=f, fill=(col[2], col[1], col[0], 255)); x += d.textlength(c, font=f) + track*sz
    return np.array(im).astype(np.float32)
def line_rgba(line, sz, col, hcol=GOLD, w=900):
    """'*word*' marks gold words. Returns RGBA (RGB order) of the whole line."""
    parts = []; f = font(sz, w)
    for i, tok in enumerate(line.split(" ")):
        hi = tok.startswith("*"); parts.append(text_rgba(tok.replace("*", ""), sz, hcol if hi else col, w))
    gap = int(sz*0.22); W = sum(p.shape[1] for p in parts) + gap*(len(parts) - 1) - 30*(len(parts) - 1); H = max(p.shape[0] for p in parts)
    out = np.zeros((H, W + 30, 4), np.float32); x = 0
    for p in parts:
        h, w_ = p.shape[:2]; reg = out[:h, x:x + w_]; a = p[..., 3:4]/255; reg[:] = reg*(1 - a) + p*a; x += w_ - 30 + gap
    return out
_lc = {}
def draw_lines(f, lines, t, cx, cy, sz, col, align="c", t_in=0.0, t_out=None, stagger=0.07, maxw=None):
    """masked slide-up reveal per line; lines may be pre-scaled to fit maxw"""
    key = (tuple(lines), sz, col, maxw)
    if key not in _lc:
        imgs = [line_rgba(l, sz, col) for l in lines]
        if maxw:
            wmax = max(i.shape[1] for i in imgs)
            if wmax > maxw:
                s2 = int(sz*maxw/wmax*0.97); imgs = [line_rgba(l, s2, col) for l in lines]; sz = s2
        _lc[key] = (imgs, sz)
    imgs, sz = _lc[key]; lh = sz*1.0; y0 = cy - (len(lines) - 1)*lh/2
    for i, im in enumerate(imgs):
        h, w = im.shape[:2]; k_in = eout((t - t_in - i*stagger)/0.55); k_out = ein((t - t_out - i*stagger*0.6)/0.35) if t_out is not None else 0
        if k_in <= 0 or k_out >= 1: continue
        dy = (1 - k_in)*h*0.95 - k_out*h*0.95
        x = cx - w/2 if align == "c" else (cx if align == "l" else cx - w)
        ly = int(y0 + i*lh - h/2)                         # mask band = the line's own box
        src = np.zeros_like(im); sh = int(round(dy))
        if abs(sh) < h: 
            if sh >= 0: src[sh:] = im[:h - sh]
            else: src[:h + sh] = im[-sh:]
        fx.composite(f, src, x + w/2, ly + h/2)
# ---------------- media ----------------
LIVE = os.path.join(SP, "ugc/live")
class Clip:
    def __init__(s, n): s.n = n; s.cap = None; s.pos = -1; s.cur = None; s.fps = 24; s.meta = json.load(open(os.path.join(LIVE, n + ".json")))
    def at(s, sec):
        k = max(int(sec*s.fps), 0)
        if s.cap is None or k < s.pos: s.cap = cv2.VideoCapture(os.path.join(LIVE, s.n + ".mp4")); s.pos = -1
        while s.pos < k:
            ok, fr = s.cap.read()
            if not ok: break
            s.pos += 1; s.cur = fr
        return s.cur
_cl = {}
def clip(n):
    if n not in _cl: _cl[n] = Clip(n)
    return _cl[n]
LOGO = cv2.imread(os.path.join(SP, "v3/gfx/bounti_logo.png"), cv2.IMREAD_UNCHANGED)
def logo_rgba(w, col):
    im = cv2.resize(LOGO, (w, int(LOGO.shape[0]*w/LOGO.shape[1])), interpolation=cv2.INTER_AREA).astype(np.float32)[..., [2, 1, 0, 3]].copy()
    im[..., :3] = np.array(col[::-1], np.float32); return im
# ---------------- 3D ----------------
FOC = 2.2*U
def rot(yaw, pitch, roll):
    y, p, r = map(math.radians, (yaw, pitch, roll))
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return Ry @ Rx @ Rz
def project(P, pose):
    """P: Nx3 points in object space (px). pose: x,y (canvas px), z (depth px), s (scale), yaw, pitch, roll"""
    Rm = rot(pose.get("yaw", 0), pose.get("pitch", 0), pose.get("roll", 0)); Q = (P*pose.get("s", 1)) @ Rm.T
    z = Q[:, 2] + pose.get("z", 0) + FOC; return np.stack([pose["x"] + Q[:, 0]*FOC/z, pose["y"] + Q[:, 1]*FOC/z], 1)
def warp_plane(canvas, tex, quad2d, alpha=1.0):
    """tex RGBA float (BGR order), quad2d 4x2 target corners (tl,tr,br,bl)"""
    h, w = tex.shape[:2]; x0, y0 = np.floor(quad2d.min(0)).astype(int) - 2; x1, y1 = np.ceil(quad2d.max(0)).astype(int) + 2
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x1, OW), min(y1, OH)
    if xa >= xb or ya >= yb: return
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad2d - [xa, ya]))
    out = cv2.warpPerspective(tex, M, (xb - xa, yb - ya), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = out[..., 3:4]/255*alpha; reg = canvas[ya:yb, xa:xb]; reg[:] = reg*(1 - a) + out[..., :3]*a
def shadow(canvas, quad2d, strength=0.35, blur=None, dy=None):
    blur = blur or U*0.035; dy = U*0.03 if dy is None else dy
    q = quad2d.copy(); q[:, 1] += dy; x0, y0 = np.floor(q.min(0)).astype(int) - int(3*blur); x1, y1 = np.ceil(q.max(0)).astype(int) + int(3*blur)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x1, OW), min(y1, OH)
    if xa >= xb or ya >= yb: return
    m = np.zeros((yb - ya, xb - xa), np.float32); cv2.fillConvexPoly(m, np.int32(q - [xa, ya]), 1.0, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), blur)*strength; canvas[ya:yb, xa:xb] *= (1 - m[..., None])
def rrect_mask(h, w, r):
    m = np.zeros((h, w), np.float32); cv2.rectangle(m, (r, 0), (w - r, h), 1, -1); cv2.rectangle(m, (0, r), (w, h - r), 1, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 1, -1, cv2.LINE_AA)
    return m
PW = 430; PH = int(PW*1864/860)                       # phone screen texture size (object px)
def phone_tex(fr, sheen=None):
    bz = 14; r = 62; W, H = PW + 2*bz, PH + 2*bz; t = np.zeros((H, W, 4), np.float32)
    outer = rrect_mask(H, W, r + bz); t[..., :3] = 18; t[..., 3] = outer*255
    edge = outer - cv2.erode(outer, np.ones((5, 5), np.uint8)); t[..., :3] += edge[..., None]*70        # thin metal rim highlight
    scr = cv2.resize(fr, (PW, PH), interpolation=cv2.INTER_AREA).astype(np.float32); sm = rrect_mask(PH, PW, r)[..., None]
    reg = t[bz:bz + PH, bz:bz + PW, :3]; reg[:] = reg*(1 - sm) + scr*sm
    if sheen is not None:                               # diagonal glass reflection band
        yy, xx = np.mgrid[0:H, 0:W]; band = np.exp(-((xx + yy*0.6 - sheen*(W + H*0.6))/(W*0.18))**2)*0.10
        t[..., :3] = t[..., :3]*(1 - band[..., None]) + 255*band[..., None]*outer[..., None]
    return t
LW = 900; LH = int(LW*900/1440)                       # laptop screen texture size
def laptop_tex(fr):
    bz = 22; bt = 30; W, H = LW + 2*bz, LH + bz + bt; t = np.zeros((H, W, 4), np.float32)
    m = rrect_mask(H, W, 26); t[..., :3] = 20; t[..., 3] = m*255
    cv2.circle(t, (W//2, bt//2 + 2), 4, (60, 60, 60, 255), -1, cv2.LINE_AA)
    t[bt:bt + LH, bz:bz + LW, :3] = cv2.resize(fr, (LW, LH), interpolation=cv2.INTER_AREA).astype(np.float32); return t
def deck_tex():
    W, H = LW + 2*22 + 60, 420; t = np.zeros((H, W, 4), np.float32); t[..., 3] = rrect_mask(H, W, 30)*255
    g = np.linspace(205, 168, H)[:, None, None]; t[..., :3] = g
    cv2.rectangle(t, (W//2 - 150, H - 150), (W//2 + 150, H - 40), (185, 185, 185, 255), -1)            # trackpad
    for i in range(5): cv2.rectangle(t, (60, 40 + i*44), (W - 60, 74 + i*44), (178, 178, 178, 255), -1)  # key rows
    return t
DECK = None
def draw_phone(canvas, fr, pose, sheen=None, shadow_k=0.38, alpha=1.0):
    tex = phone_tex(fr, sheen); h, w = tex.shape[:2]
    P = np.array([[-w/2, -h/2, 0], [w/2, -h/2, 0], [w/2, h/2, 0], [-w/2, h/2, 0]], np.float32); q = project(P, pose)
    if shadow_k: shadow(canvas, q, shadow_k)
    warp_plane(canvas, tex, q, alpha); return q
def draw_laptop(canvas, fr, pose, alpha=1.0):
    global DECK
    if DECK is None: DECK = deck_tex()
    lid = laptop_tex(fr); h, w = lid.shape[:2]; dh, dw = DECK.shape[:2]
    # hinge at y = h/2 (bottom of lid); lid leans back 8 degrees, deck extends towards camera
    lean = math.radians(8); hy = h/2
    Lid = np.array([[-w/2, hy - h*math.cos(lean), -h*math.sin(lean)], [w/2, hy - h*math.cos(lean), -h*math.sin(lean)], [w/2, hy, 0], [-w/2, hy, 0]], np.float32)
    Deck = np.array([[-dw/2, hy, 0], [dw/2, hy, 0], [dw/2, hy + 6, -dh], [-dw/2, hy + 6, -dh]], np.float32)
    Deck[:, 2] *= -1                                    # deck comes forward (towards camera = negative z in our projection)
    qd = project(Deck, pose); ql = project(Lid, pose)
    shadow(canvas, qd, 0.30, dy=U*0.01)
    warp_plane(canvas, DECK, qd[[3, 2, 1, 0]] if False else qd, alpha); warp_plane(canvas, lid, ql, alpha); return ql
def lerp_pose(keys, t):
    """keys: list of (t, pose dict). eased between keys"""
    if t <= keys[0][0]: return dict(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease((t - t0)/max(t1 - t0, 1e-3)); return {q: a.get(q, 0)*(1 - k) + b.get(q, 0)*k for q in set(a) | set(b)}
    return dict(keys[-1][1])
def P(x, y, s=1.0, **k):
    """pose in canvas fractions; s relative to the frame's short side"""
    return dict(x=x*OW, y=y*OH, s=s*U/1080, **k)
# ---------------- timeline ----------------
VO = json.load(open(os.path.join(HERE, "vo", NAME, "vo.json")))
GAP = F.get("gaps", {}); t = F.get("lead", 0.45); LINES = []
for i, v in enumerate(VO):
    LINES.append(dict(t0=t, t1=t + v["dur"], text=v["text"], file=v["file"])); t += v["dur"] + GAP.get(i, 0.32)
END_HOLD = 2.6; DUR = t + END_HOLD
MA = json.load(open(os.path.join(HERE, "music/analysis.json")))[F["music"]]
REVEAL = LINES[F["reveal_line"]]["t0"]; MOFF = MA["drop"] - REVEAL          # music time = film time + MOFF
BEATS = [b - MOFF for b in MA["beats"] if 0 < b - MOFF < DUR]
def snap(tt, win=0.22):
    if not BEATS: return tt
    b = min(BEATS, key=lambda x: abs(x - tt)); return b if abs(b - tt) <= win else tt
SH = []
for s in F["shots"]:
    li, off = s["at"]; st = LINES[li]["t0"] + off if li >= 0 else 0.0
    SH.append(dict(s, t0=snap(st) if s.get("snap", True) and li >= 0 else st))
SH.sort(key=lambda s: s["t0"]); SH[0]["t0"] = 0.0
for a, b in zip(SH, SH[1:]): a["t1"] = b["t0"]
SH[-1]["t1"] = DUR
def word_time(li, word):
    L_ = LINES[li]; txt = L_["text"]; import re
    clean = re.sub(r"\[[^\]]*\]\s*", "", txt); j = clean.lower().find(word.lower())
    return L_["t0"] + (L_["t1"] - L_["t0"])*(j/max(len(clean), 1) if j >= 0 else 0)
# ---------------- shot renderers ----------------
def bg(f, kind, t, sh):
    f[:] = INK if kind == "ink" else PAPER
    if sh.get("glow", True):                               # very soft vignette for depth
        k = 0.10 if kind == "ink" else 0.06
        yy, xx = np.ogrid[0:OH, 0:OW]; v = ((xx - OW/2)/(OW*0.75))**2 + ((yy - OH*0.45)/(OH*0.75))**2
        f *= (1 - k*np.clip(v, 0, 1.4))[..., None]
def media_time(sh, t, spec, spd=None):
    if isinstance(spec, str): spec = (spec, 0.4, 1e9)
    lt = t - sh["t0"]; rec, a, b = spec; spd = spd or sh.get("spd", 1.0); return rec, min(a + lt*spd, b)
def r_type(f, sh, t):
    bg(f, sh.get("bg", "paper"), t, sh); col = (241, 240, 236) if sh.get("bg") == "ink" else (14, 14, 14)
    lt = t - sh["t0"]; sz = sh.get("size", 170 if VERT else 150)*(U/1080)
    t_out = (sh["t1"] - sh["t0"]) - 0.32 if sh.get("out", True) else None
    lines = sh["lines_v"] if VERT and "lines_v" in sh else sh["lines"]
    draw_lines(f, lines, lt, OW/2, OH/2 + sh.get("dy", 0)*OH, sz, col, t_in=sh.get("delay", 0.0), t_out=t_out, maxw=OW*0.86, stagger=sh.get("stagger", 0.07))
    if sh.get("logo_under"):
        k = eout((lt - 0.5)/0.5); lg = logo_rgba(int(U*0.32), col); fx.composite(f, lg, OW/2, OH/2 + sz*len(lines)*0.6 + U*0.08, 0.9 + 0.1*k, k)
def r_phones(f, sh, t):
    """one or more phones with pose keys (relative to shot start), optional headline"""
    bg(f, sh.get("bg", "paper"), t, sh); lt = t - sh["t0"]; dur = sh["t1"] - sh["t0"]
    items = sh["phones_v"] if VERT and "phones_v" in sh else sh["phones"]
    order = sorted(range(len(items)), key=lambda i: -items[i].get("z", 0))
    for i in order:
        it = items[i]; keys = [(k*dur if k <= 1 else k, P(**p)) for k, p in it["keys"]]
        pose = lerp_pose(keys, lt); rec, rt = media_time(sh, t, it["rec"], it.get("spd")); fr = clip(rec).at(rt)
        if fr is None: continue
        layers = it.get("explode")
        if layers:                                      # exploded view: screen bands lift towards camera
            e = ease((lt - layers[0])/layers[1]) if lt > layers[0] else 0.0
            draw_phone(f, fr, pose, sheen=None, shadow_k=0.38)
            hgt = fr.shape[0]; bands = [(0, 0.12), (0.62, 1.0)]
            for j, (a, b) in enumerate(bands):
                if e <= 0: break
                y0, y1 = int(a*hgt), int(b*hgt); part = fr[y0:y1]; tex = np.zeros((int(part.shape[0]*PH/hgt), PW, 4), np.float32)
                tex[..., :3] = cv2.resize(part, (PW, tex.shape[0]), interpolation=cv2.INTER_AREA); tex[..., 3] = rrect_mask(tex.shape[0], PW, 26)*255
                h_, w_ = tex.shape[:2]; cyo = ((a + b)/2 - 0.5)*PH
                Pq = np.array([[-w_/2, cyo - h_/2, 0], [w_/2, cyo - h_/2, 0], [w_/2, cyo + h_/2, 0], [-w_/2, cyo + h_/2, 0]], np.float32)
                lift = dict(pose); lift["z"] = pose.get("z", 0) - e*U*0.22*(1 + j*0.4); lift["x"] = pose["x"] + e*U*0.05*(1 if j else -1)
                q = project(Pq, lift); shadow(f, q, 0.25*e, blur=U*0.03, dy=U*0.04*e); warp_plane(f, tex, q)
        else:
            sheen = clamp((lt - 0.1)/max(dur, 0.5)) if it.get("sheen", True) else None
            draw_phone(f, fr, pose, sheen=sheen)
    head(f, sh, t)
def r_duo(f, sh, t):
    """laptop + phone (desktop and mobile)"""
    bg(f, sh.get("bg", "paper"), t, sh); lt = t - sh["t0"]; dur = sh["t1"] - sh["t0"]
    L_ = sh["laptop_v"] if VERT and "laptop_v" in sh else sh["laptop"]; Ph = sh["phone_v"] if VERT and "phone_v" in sh else sh["phone"]
    lp = lerp_pose([(k*dur if k <= 1 else k, P(**p)) for k, p in L_["keys"]], lt); rec, rt = media_time(sh, t, L_["rec"], L_.get("spd")); draw_laptop(f, clip(rec).at(rt), lp)
    pp = lerp_pose([(k*dur if k <= 1 else k, P(**p)) for k, p in Ph["keys"]], lt); rec, rt = media_time(sh, t, Ph["rec"], Ph.get("spd")); draw_phone(f, clip(rec).at(rt), pp, sheen=clamp(lt/max(dur, 0.5)))
    head(f, sh, t)
def head(f, sh, t):
    hd = sh.get("head_v" if VERT else "head") or sh.get("head")
    if not hd: return
    lt = t - sh["t0"]; col = (241, 240, 236) if sh.get("bg") == "ink" else (14, 14, 14); sz = hd.get("size", 112 if VERT else 104)*(U/1080)
    x, y = hd.get("x", 0.5)*OW, hd.get("y", 0.12 if VERT else 0.5)*OH; al = hd.get("align", "c")
    draw_lines(f, hd["lines"], lt, x, y, sz, col, align=al, t_in=hd.get("delay", 0.15), t_out=(sh["t1"] - sh["t0"]) - 0.3, maxw=OW*(0.86 if VERT else 0.40))
def r_logo(f, sh, t):
    bg(f, sh.get("bg", "paper"), t, sh); lt = t - sh["t0"]; col = (241, 240, 236) if sh.get("bg") == "ink" else (14, 14, 14)
    lw = int(U*0.62); cy = OH/2 - U*0.07
    k = eout(lt/0.7); lg = logo_rgba(lw, col)
    # mask wipe reveal left to right, slight scale settle
    w = lg.shape[1]; cut = int(w*k); lg2 = lg.copy(); lg2[:, cut:, 3] = 0
    fx.composite(f, lg2, OW/2, cy, 1.06 - 0.06*k)
    p = eout((lt - 0.45)/0.5)
    if p > 0:
        ww = lw*0.86; x0 = OW/2 - ww/2; y = cy + lg.shape[0]*0.66
        pts = [(x0 + ww*p*s, y + 10*math.sin(s*math.pi) - 6*s) for s in np.linspace(0, 1, 32)]; cv2.polylines(f, [np.int32(pts)], False, GOLD, max(6, int(U*0.009)), cv2.LINE_AA)
    if sh.get("sub"): draw_lines(f, [sh["sub"]], lt, OW/2, cy + U*0.19, int(U*0.052), GREY, t_in=0.75)
    if sh.get("url"):
        u = lt - 1.05; kk = eout(u/0.4)
        if kk > 0:
            key = ("url", sh["url"])
            if key not in _lc:
                tx = text_rgba(sh["url"], int(U*0.046), (241, 240, 236) if sh.get("bg") != "ink" else (14, 14, 14), 800, -0.02); h, w2 = tx.shape[:2]
                pill = np.zeros((h + 34, w2 + 80, 4), np.float32); pill[..., 3] = rrect_mask(h + 34, w2 + 80, (h + 34)//2)*255
                pill[..., :3] = (14, 14, 14) if sh.get("bg") != "ink" else (241, 240, 236); fx.composite(pill[..., :3], tx, pill.shape[1]/2, pill.shape[0]/2 + 2); _lc[key] = pill
            fx.composite(f, _lc[key], OW/2, cy + U*0.31 + 30*(1 - kk), 1.0, kk)
R_ = {"type": r_type, "phones": r_phones, "duo": r_duo, "logo": r_logo}
def cam(f, sh, t):
    c = sh.get("cam")
    if not c: return f
    lt = (t - sh["t0"])/max(sh["t1"] - sh["t0"], 0.1); z = c[0] + (c[1] - c[0])*ease(lt); dx = c[2]*OW*(lt - 0.5) if len(c) > 2 else 0
    M = np.float32([[z, 0, OW/2*(1 - z) + dx], [0, z, OH/2*(1 - z)]]); return cv2.warpAffine(f, M, (OW, OH), borderMode=cv2.BORDER_REFLECT)
def render(i, t):
    sh = SH[i]; f = np.empty((OH, OW, 3), np.float32); R_[sh["kind"]](f, sh, t); return cam(f, sh, t)
TRW = 0.26
def frame_at(t):
    i = max(k for k, s in enumerate(SH) if s["t0"] <= t + 1e-6); f = render(i, t)
    if i + 1 < len(SH) and t > SH[i]["t1"] - TRW and SH[i + 1].get("tr", "whip") != "cut":
        tr = SH[i + 1].get("tr", "whip"); g = render(i + 1, max(t, SH[i + 1]["t0"])); k = ease((t - (SH[i]["t1"] - TRW))/TRW)
        if tr == "fade": return f*(1 - k) + g*k
        if tr == "zoom":                                # zoom through: current scales up and fades, next settles from 1.08
            z1 = 1 + 0.5*k; z2 = 1.08 - 0.08*k
            a = cv2.warpAffine(f, np.float32([[z1, 0, OW/2*(1 - z1)], [0, z1, OH/2*(1 - z1)]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
            b = cv2.warpAffine(g, np.float32([[z2, 0, OW/2*(1 - z2)], [0, z2, OH/2*(1 - z2)]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
            return a*(1 - k) + b*k
        d = SH[i + 1].get("dir", -1); off = int(k*OW)*d     # whip pan
        out = np.empty_like(f)
        if d < 0: out[:, :OW + off] = f[:, -off:]; out[:, OW + off:] = g[:, :-off] if off else g[:, :0]
        else: out[:, off:] = f[:, :OW - off]; out[:, :off] = g[:, OW - off:]
        bl = int(60*math.sin(k*math.pi)) + 1; return cv2.blur(out, (bl, 1))
    return f
prev = os.environ.get("PREVIEW")
if prev:
    ts = [float(x) for x in prev.split(",")]; sc = float(os.environ.get("PSC", 0.2))
    cv2.imwrite(os.path.join(HERE, f"pv_{NAME}_{FMT}.png"), np.hstack([cv2.resize(np.clip(frame_at(x), 0, 255).astype(np.uint8), (int(OW*sc), int(OH*sc))) for x in ts]))
    print("dur %.1f" % DUR, "moff %.2f" % MOFF, [(s["kind"], round(s["t0"], 2)) for s in SH]); sys.exit(0)
# ---------------- audio ----------------
NS = int((DUR + 0.5)*R); vo = np.zeros(NS, np.float32); speech = []
for L_ in LINES:
    x, sr = sf.read(L_["file"], dtype="float32")
    if sr != R: x = np.interp(np.arange(int(len(x)*R/sr))*sr/R, np.arange(len(x)), x).astype(np.float32)
    s = int(L_["t0"]*R); vo[s:s + len(x)] += x[:NS - s]; speech.append((L_["t0"], L_["t0"] + len(x)/R))
mus = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "music", F["music"] + ".mp3"), "-f", "f32le", "-ac", "2", "-ar", str(R), "-"], capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
ms = int(MOFF*R)
if ms >= 0: mus = mus[ms:]
else: mus = np.concatenate([np.zeros((-ms, 2), np.float32), mus])
mus = np.pad(mus, ((0, max(0, NS - len(mus))), (0, 0)))[:NS]; tt = np.arange(NS)/R
mus *= (10**(F.get("music_db", -13)/20)*np.clip(tt/0.25, 0, 1)*np.clip((DUR + 0.2 - tt)/1.6, 0, 1))[:, None]
sfx = np.zeros((NS, 2), np.float32)
for a, b in zip(SH, SH[1:]):
    tr = b.get("tr", "whip")
    if tr == "whip": fx.place_sfx(sfx, "whoosh-fast-medium", b["t0"] - TRW*0.4, -14, speech, R)
    elif tr == "zoom": fx.place_sfx(sfx, "whoosh-fast-soft", b["t0"] - TRW*0.5, -14, speech, R)
for s in SH:
    for tm, sid, g in s.get("sfx", []): fx.place_sfx(sfx, sid, s["t0"] + tm, g, speech, R)
def wr(path, x, ch):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", str(ch), "-ar", str(R), "-i", "-", "-c:a", "pcm_f32le", path], stdin=subprocess.PIPE); p.stdin.write(x.astype(np.float32).tobytes()); p.stdin.close(); p.wait()
tmp = os.path.join(HERE, "tmp", f"{NAME}_{FMT}"); os.makedirs(tmp, exist_ok=True)
wr(f"{tmp}/v.wav", vo, 1); wr(f"{tmp}/m.wav", mus, 2); wr(f"{tmp}/s.wav", sfx, 2)
raw = f"{tmp}/raw.mp4"; N = int(DUR*FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", raw], stdin=subprocess.PIPE)
for n in range(N):
    ff.stdin.write(np.clip(frame_at(n/FPS) + 0.5, 0, 255).astype(np.uint8).tobytes())
    if n % 300 == 0: print(NAME, FMT, n, "/", N, flush=True)
ff.stdin.close(); ff.wait()
od = os.path.join(SP, "final/launch2"); os.makedirs(od, exist_ok=True); OUT = os.path.join(od, f"Bounti-Launch-{NAME}-{'9x16' if VERT else '16x9'}.mp4")
FG = ("[1]highpass=f=70,acompressor=threshold=-20dB:ratio=2.2:attack=5:release=120:makeup=2,asplit[v][k];[2][k]sidechaincompress=threshold=0.035:ratio=5:attack=15:release=420[md];"
      "[v][md][3]amix=inputs=3:normalize=0:duration=first[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", f"{tmp}/v.wav", "-i", f"{tmp}/m.wav", "-i", f"{tmp}/s.wav", "-filter_complex", FG, "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "pcm_s16le", f"{tmp}/mix.mov"], check=True)
J = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{tmp}/mix.mov", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
m = json.loads(J[J.rindex("{"):J.rindex("}") + 1])
LN = f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/mix.mov", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-af", LN, "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", OUT], check=True)
print("DONE", OUT, "%.1fs" % DUR)
