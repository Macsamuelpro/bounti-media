"""Render one UGC project. usage: ugc_render.py UGCn  [PREVIEW=t1,t2 -> strip png]"""
import os, sys, json, re, math, subprocess
import numpy as np, cv2
S = os.path.dirname(os.path.abspath(__file__))
for p in (S, os.path.join(S, "editkit"), os.path.join(S, "v3"), os.path.join(S, "v7")): sys.path.insert(0, p)
import fx, captions as CAP, grade as GR, transitions as TR
from segmask import person_mask
from ugc_projects import P as PROJ, SCREENS
from PIL import Image, ImageDraw
NAME = sys.argv[1]; CFG = PROJ[NAME]; D = os.path.join(S, "ugc", NAME); FPS = 24; R = 48000; OW, OH = 1080, 1920
PIECES = json.load(open(os.path.join(D, "pieces.json")))
def s_(t): t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def out_(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t)**3
def spring(u, d=0.35):
    if u <= 0: return 0.0
    u = min(u/d, 1.0); return 1 - math.exp(-6*u)*math.cos(u*math.pi*2.2) if u < 1 else 1.0
PAPER = np.array((236, 240, 241), np.float32)       # BGR of #F1F0EC
INK = (13, 13, 13)
# ---------------- timeline ----------------
pcs = []
for item in CFG["pieces"]:
    c, i, txt = item[:3]; a, b = PIECES[c]["pieces"][i][:2]
    if len(item) > 3: a, b = item[3]
    pcs.append(dict(c=c, a=a, b=b, txt=txt))
NEW = ("So ", "Now", "Then", "Basically", "And the", "Head over", "head over", "Check out", "Visit", "Go to", "You can check", "You can try", "Anyway", "Okay", "Oh,",
       "Honestly", "Well", "It's called", "That's", "Let's", "First", "When you", "If everything", "Once", "I like", "Instead", "Maybe", "Turns out", "At first", "But what")
PRE_ROLL = CFG["hook"].get("dur", 0.0) if CFG["hook"]["kind"] == "screen_open" else 0.0
t = PRE_ROLL; segs = []; carry = 0.0
for k, p in enumerate(pcs):
    nxt = pcs[k + 1] if k + 1 < len(pcs) else None
    gap = 0.30 if p["txt"].rstrip()[-1:] in ".?!" else 0.12
    if nxt and nxt["txt"].startswith(NEW): gap = max(gap, 0.42)
    if nxt is None: gap = 0.5
    s0 = max(p["a"] - 0.05 - carry, 0.0); carry = 0.0
    if k == 0 and "lead0" in CFG: s0 = CFG["lead0"]
    s1 = p["b"] + 0.08
    contig = nxt is not None and nxt["c"] == p["c"] and nxt["a"] > p["b"]
    avail = (nxt["a"] - 0.05 - s1) if contig else 9.9
    cend = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(D, f"src/{p['c']}.mp4")], capture_output=True, text=True).stdout) - 0.06
    extra = max(min(gap, max(avail, 0), cend - s1), 0); s1 += extra; hold = max(gap - extra, 0)
    if hold > 0 and nxt and not contig and nxt["a"] - 0.05 - hold >= 0: carry = hold; hold = 0.0
    segs.append(dict(c=p["c"], s0=s0, s1=s1, t0=t, a=p["a"], b=p["b"], hold=hold, txt=p["txt"])); t += (s1 - s0) + hold
MAIN = t; END = 2.4; DUR = MAIN + END; N = int(round(DUR*FPS))
def find(txt):
    for g in segs:
        if g["txt"].startswith(txt): return g
    raise KeyError(f"{NAME}: no line starts with {txt!r}")
def at(txt, end=False): g = find(txt); return g["t0"] + (g["b"] if end else g["a"]) - g["s0"]
def seg_at(t):
    for i, g in enumerate(segs):
        if g["t0"] - 1e-6 <= t < g["t0"] + g["s1"] - g["s0"] + g["hold"] - 1e-6: return i, g
    return len(segs) - 1, segs[-1]
# ---------------- footage + masks ----------------
_raw = {}
def raw(c):
    if c not in _raw:
        if len(_raw) > 3: _raw.pop(next(iter(_raw)))
        cap = cv2.VideoCapture(os.path.join(D, f"src/{c}.mp4")); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(f)
        _raw[c] = fr
    return _raw[c]
_mask = {}
def mask_of(c, k):
    key = (c, k//2*2)
    if key not in _mask:
        fr = raw(c)[min(key[1], len(raw(c)) - 1)]; _mask[key] = cv2.resize((person_mask(fr)*255).astype(np.uint8), (360, 640), interpolation=cv2.INTER_AREA)
    return cv2.resize(_mask[key], (OW, OH), interpolation=cv2.INTER_LINEAR).astype(np.float32)/255
def src_k(g, t):
    loc = t - g["t0"]; sp = g["s1"] - g["s0"]
    s = g["s0"] + loc if loc <= sp else g["s1"] + (loc - sp)*0.25
    return int(round(s*FPS))
def footage(t, want_mask=False):
    i, g = seg_at(max(t, PRE_ROLL)); fr = raw(g["c"]); k = min(src_k(g, max(t, PRE_ROLL)), len(fr) - 1); f = fr[k].astype(np.float32)
    if i + 1 < len(segs) and segs[i + 1]["c"] == g["c"]:
        n2 = segs[i + 1]; jb = n2["t0"]
        if jb - 3/FPS <= t:
            k2 = int(round((n2["s0"] + t - jb)*FPS))
            if abs(k2 - k) > 2: f = TR.morph_cut(f, fr[min(k2, len(fr) - 1)].astype(np.float32), s_((t - (jb - 3/FPS))*FPS/6 + 1/12))
    f = cv2.resize(f, (OW, OH), interpolation=cv2.INTER_LANCZOS4)
    f = GR.adjust(f, exposure=0.05, contrast=0.05, shadows=0.12, vibrance=0.08)
    return f, (mask_of(g["c"], k) if want_mask else None)
# ---------------- graphics ----------------
def inter(size, w=900): return CAP.font("Inter", size, w)
def text_rgba(txt, f, col, stroke=0, scol=(0, 0, 0), shadow=0.0, track=-0.04):
    d = ImageDraw.Draw(Image.new("L", (1, 1))); lines = txt.split("\n"); sz = f.size
    ws = [sum(d.textlength(ch, font=f) + track*sz for ch in l) for l in lines]; lh = int(sz*1.0)
    im = Image.new("RGBA", (int(max(ws)) + 60 + 2*stroke, lh*len(lines) + int(sz*0.35) + 40 + 2*stroke), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = 30 + stroke + (max(ws) - ws[i])/2; y = 20 + stroke + i*lh
        for ch in l: dr.text((x, y), ch, font=f, fill=col + (255,), stroke_width=stroke, stroke_fill=scol + (255,)); x += d.textlength(ch, font=f) + track*sz
    a = np.array(im).astype(np.float32)
    if shadow:
        sh = cv2.GaussianBlur(a[..., 3], (0, 0), 14)*shadow; o = np.zeros_like(a); o[..., 3] = np.roll(sh, 8, 0)
        al = a[..., 3:4]/255; o[..., :3] = a[..., :3]; o[..., 3:4] = np.maximum(o[..., 3:4], a[..., 3:4]); return o
    return a
LOGO = cv2.imread(os.path.join(S, "v3/gfx/bounti_logo.png"), cv2.IMREAD_UNCHANGED)
def logo_rgba(w, col=INK):
    im = cv2.resize(LOGO, (w, int(LOGO.shape[0]*w/LOGO.shape[1])), interpolation=cv2.INTER_AREA).astype(np.float32)[..., [2, 1, 0, 3]].copy()
    im[..., :3] = np.array(col, np.float32); return im
def sticker(rgba, pad=22, r=40):
    h, w = rgba.shape[:2]; out = np.zeros((h + 2*pad, w + 2*pad, 4), np.float32); m = np.zeros(out.shape[:2], np.uint8)
    cv2.rectangle(m, (r, 0), (out.shape[1] - r, out.shape[0]), 255, -1); cv2.rectangle(m, (0, r), (out.shape[1], out.shape[0] - r), 255, -1)
    for cx, cy in ((r, r), (out.shape[1] - r, r), (r, out.shape[0] - r), (out.shape[1] - r, out.shape[0] - r)): cv2.circle(m, (cx, cy), r, 255, -1)
    out[..., :3] = 255; out[..., 3] = m; a = rgba[..., 3:4]/255
    out[pad:pad + h, pad:pad + w, :3] = out[pad:pad + h, pad:pad + w, :3]*(1 - a) + rgba[..., :3]*a; return out
LOGO_POP = sticker(logo_rgba(460), 34, 46)
URL_PILL = None
def url_pill():
    global URL_PILL
    if URL_PILL is None:
        t = text_rgba("earnbounti.com", inter(58, 800), (255, 255, 255), track=-0.02); h, w = t.shape[:2]
        out = np.zeros((h + 20, w + 50, 4), np.float32); m = np.zeros(out.shape[:2], np.uint8); rr = out.shape[0]//2
        cv2.rectangle(m, (rr, 0), (out.shape[1] - rr, out.shape[0]), 255, -1); cv2.circle(m, (rr, rr), rr, 255, -1); cv2.circle(m, (out.shape[1] - rr, rr), rr, 255, -1)
        out[..., :3] = np.array(INK, np.float32); out[..., 3] = m; a = t[..., 3:4]/255; y0, x0 = 10, 25
        out[y0:y0 + h, x0:x0 + w, :3] = out[y0:y0 + h, x0:x0 + w, :3]*(1 - a) + t[..., :3]*a; URL_PILL = out
    return URL_PILL
# phone with scrolling app screen
_scr = {}
def screen_img(name):
    if name not in _scr:
        f, a, b = SCREENS[name]; im = cv2.imread(os.path.join(S, f)); W = 1170
        if im.shape[1] != W: im = cv2.resize(im, (W, int(im.shape[0]*W/im.shape[1])), interpolation=cv2.INTER_AREA)
        _scr[name] = (im, a, b)
    return _scr[name]
SW_, BZ = 690, 22; SH_ = int(SW_*844/390)
def phone(name, u, tap=None):
    im, a, b = screen_img(name); H = im.shape[0]; win = int(1170*844/390); span = max(H - win, 0)
    y = int(span*min(1, (a + (b - a)*s_(u)))) if b > a else int(span*min(1, a))
    crop = im[y:y + win] if H >= win else np.vstack([im, np.full((win - H, 1170, 3), 245, np.uint8)])
    scr = cv2.resize(crop, (SW_, SH_), interpolation=cv2.INTER_AREA).astype(np.float32)
    W2, H2 = SW_ + 2*BZ, SH_ + 2*BZ; out = np.zeros((H2 + 60, W2 + 60, 4), np.float32); x0 = y0 = 30
    def rr(img, x, y, w, h, r, val):
        cv2.rectangle(img, (x + r, y), (x + w - r, y + h), val, -1); cv2.rectangle(img, (x, y + r), (x + w, y + h - r), val, -1)
        for cx, cy in ((x + r, y + r), (x + w - r, y + r), (x + r, y + h - r), (x + w - r, y + h - r)): cv2.circle(img, (cx, cy), r, val, -1)
    m = np.zeros(out.shape[:2], np.uint8); rr(m, x0, y0, W2, H2, 70, 255)
    sh = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 18)*0.35; out[..., 3] = np.roll(sh, 18, 0)
    am = m[..., None]/255; out[..., :3] = out[..., :3]*(1 - am) + 13*am; out[..., 3:4] = np.maximum(out[..., 3:4], m[..., None])
    sm = np.zeros((SH_, SW_), np.uint8); rr(sm, 0, 0, SW_ - 1, SH_ - 1, 52, 255); sa = sm[..., None]/255
    reg = out[y0 + BZ:y0 + BZ + SH_, x0 + BZ:x0 + BZ + SW_]; reg[..., :3] = reg[..., :3]*(1 - sa) + scr*sa
    if tap is not None and 0 <= u - tap < 0.35:                      # tap ripple
        k = (u - tap)/0.35; cx, cy = x0 + BZ + SW_//2, y0 + BZ + int(SH_*0.62); r = int(30 + 60*k)
        ov = out.copy(); cv2.circle(ov, (cx, cy), r, (255, 255, 255, 255), -1, cv2.LINE_AA); out = out*(1 - 0.35*(1 - k)) + ov*0.35*(1 - k)
    return out
# ---------------- inserts ----------------
INS = []
for ins in CFG["inserts"]:
    a0 = at(ins["at"]) - 0.12
    if ins["kind"] == "screen":
        b0 = at(ins["until"]) - 0.12 if ins.get("until") else at(ins["at"], True) + 0.3
        if INS and INS[-1]["kind"] == "screen" and abs(INS[-1]["b"] - a0) < 0.6: a0 = INS[-1]["b"]
        INS.append(dict(ins, a=a0, b=b0))
    elif ins["kind"] == "logo": INS.append(dict(ins, a=a0 + 0.1, b=a0 + 1.9))
    elif ins["kind"] == "url": INS.append(dict(ins, a=a0 + 0.1, b=MAIN))
if CFG["hook"]["kind"] == "cutout_pop" and INS and INS[0]["kind"] == "screen": INS[0]["a"] = PRE_ROLL
SCREEN_INS = [x for x in INS if x["kind"] == "screen"]
def ins_at(t):
    for x in SCREEN_INS:
        if x["a"] <= t < x["b"]: return x
    return None
TR_F = 0.30
def cutout_layer(f, m, k_small):
    """presenter frame -> scaled sticker cutout in the bottom-left corner. k_small 0 = full frame, 1 = corner."""
    sc = 1 - 0.56*out_(k_small); M = np.float32([[sc, 0, 0], [0, sc, OH*(1 - sc)]])
    return cv2.warpAffine(f, M, (OW, OH)), cv2.warpAffine(m, M, (OW, OH))
def compose_screen(t, x, f, m):
    name = x["screen"]; u = (t - x["a"])/max(x["b"] - x["a"], 0.1)
    if x.get("then") and u >= x["then"][1]: name = x["then"][0]; u = (u - x["then"][1])/(1 - x["then"][1])
    bg = np.broadcast_to(PAPER, (OH, OW, 3)).copy()
    first = not any(y["b"] == x["a"] for y in SCREEN_INS); last = not any(y["a"] == x["b"] for y in SCREEN_INS)
    kin = out_((t - x["a"])/TR_F) if first else 1.0; kout = out_((x["b"] - t)/TR_F) if last else 1.0; k = min(kin, kout)
    if CFG["hook"]["kind"] == "cutout_pop" and x is SCREEN_INS[0]: k = 1.0
    pk = spring(t - x["a"], 0.4) if first else 1.0
    ph = phone(name, u, x.get("tap")); fx.composite(bg, ph, 600, 820 + 60*(1 - pk), 0.92 + 0.08*min(pk, 1), min(1, pk*1.5) if first else 1.0)
    if x.get("layout") == "full": return bg*k + f*(1 - k) if k < 1 else bg
    pres_k = k
    if CFG["hook"]["kind"] == "cutout_pop" and x is SCREEN_INS[0]: pres_k = 1.0; pop = spring(t - (segs[0]["t0"] + segs[0]["a"] - segs[0]["s0"]) + 0.1, 0.35)
    else: pop = 1.0
    cf, cm = cutout_layer(f, m, pres_k)
    if pop < 1:
        M = np.float32([[pop, 0, 0], [0, pop, OH*(1 - pop)]]); cf = cv2.warpAffine(cf, M, (OW, OH)); cm = cv2.warpAffine(cm, M, (OW, OH))
    edge = np.clip(cv2.dilate(cm, np.ones((15, 15), np.uint8)) - cm, 0, 1)[..., None]*min(1, pres_k*2)
    base = bg*pres_k + f*(1 - pres_k)
    base = base*(1 - edge) + 255*edge
    mm = cv2.GaussianBlur(cm, (0, 0), 1.0)[..., None]
    return base*(1 - mm) + cf*mm
# ---------------- captions ----------------
CH = [(g["t0"] + g["a"] - g["s0"], g["t0"] + g["b"] - g["s0"], g["txt"]) for g in segs]
hook = CFG["hook"]; hide = [(MAIN, DUR)]
if hook["kind"] in ("text", "text_small"): hide.append((hook["t0"], hook["t1"]))
st = dict(CAP.STYLES[CFG["style"]])
CPT = CAP.Captioner(CH, st, CFG["anim"], y=1330, max_words=4, max_chars=20, hidden=hide)
_cd = CPT.draw
def draw_caps(f, t):
    if ins_at(t): CPT.x, CPT.y, CPT.max_w = 715, 1790, 640
    else: CPT.x, CPT.y, CPT.max_w = OW/2, 1330, 920
    _cd(f, t)
HOOK_IMG = None
if hook["kind"] == "text": HOOK_IMG = text_rgba(hook["text"], inter(150 if len(hook["text"]) < 16 else 120), (255, 255, 255), stroke=0, shadow=0.8, track=-0.05)
if hook["kind"] == "text_small": HOOK_IMG = text_rgba(hook["text"], inter(64, 800), (255, 255, 255), shadow=0.8)
ICONS = [(at(a), name) for a, name in CFG.get("icons", [])]
def icon_bubble(name):
    import resvg_py, io
    svg = open(os.path.join(S, "lib/icons/package/icons", name + ".svg")).read().replace('stroke="currentColor"', 'stroke="#0d0d0d"').replace('width="24"', 'width="110"').replace('height="24"', 'height="110"').replace('stroke-width="2"', 'stroke-width="2.2"')
    ic = np.array(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert("RGBA")).astype(np.float32)
    s = 190; out = np.zeros((s, s, 4), np.float32); cv2.circle(out, (s//2, s//2), s//2 - 6, (255, 255, 255, 255), -1, cv2.LINE_AA)
    fx.composite(out[..., :3], ic, s/2, s/2); out[..., [0, 2]] = out[..., [2, 0]]; return out
END_LOGO = logo_rgba(600); END_T1 = text_rgba("Become a Bounti hunter.", inter(64, 900), INK, track=-0.05); END_T2 = text_rgba("earnbounti.com", inter(48, 700), (94, 94, 94))
def bg_screen(name, t):
    im, a, b = screen_img(name); sc = OW/im.shape[1]; img = cv2.resize(im, (OW, int(im.shape[0]*sc)), interpolation=cv2.INTER_AREA)
    span = max(img.shape[0] - OH, 0); y = int(span*min(1, a + (b - a)*min(1, t/max(MAIN, 1)))); crop = img[y:y + OH]
    if crop.shape[0] < OH: crop = np.vstack([crop, np.full((OH - crop.shape[0], OW, 3), 240, np.uint8)])
    return crop.astype(np.float32)
# ---------------- frame ----------------
def frame_at(t):
    if t >= MAIN:
        u = t - MAIN; f = np.broadcast_to(PAPER, (OH, OW, 3)).copy()
        for img, y, d0 in ((END_LOGO, 820, 0.1), (END_T1, 1000, 0.35), (END_T2, 1090, 0.55)): fx.composite(f, img, OW/2, y + 14*(1 - out_((u - d0)/0.4)), 1.0, s_((u - d0)/0.3))
        if u < 0.25:
            g, _ = footage(MAIN - 0.02); f = g*(1 - u/0.25) + f*(u/0.25)
        return f
    if t < PRE_ROLL:
        f = np.broadcast_to(PAPER, (OH, OW, 3)).copy(); fx.composite(f, phone(hook["screen"], t/PRE_ROLL), OW/2, OH/2, 1.06, 1.0); return f
    x = ins_at(t); gs = CFG.get("greenscreen")
    f, m = footage(t, want_mask=bool(x) or bool(gs))
    if gs:
        name = gs
        for at_txt, nm in CFG.get("bg_switch", []):
            if t >= at(at_txt) - 0.1: name = nm
        b = bg_screen(name, t); b = cv2.GaussianBlur(b, (0, 0), 1.2)*0.92; mm = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
        f = b*(1 - mm) + f*mm
    if hook["kind"] == "punch" and t < hook["t0"] + 1.2:
        z = 1 + 0.14*out_((t - hook["t0"])/0.18)*(1 - s_((t - hook["t0"] - 0.6)/0.6)); f = cv2.warpAffine(f, np.float32([[z, 0, OW/2*(1 - z)], [0, z, OH*0.35*(1 - z)]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
    for i, (ti, nm) in enumerate(ICONS):
        if ti - 0.05 <= t < ti + 0.55:
            z = 1.08; f = cv2.warpAffine(f, np.float32([[z, 0, OW/2*(1 - z)], [0, z, OH*0.35*(1 - z)]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
    if x: f = compose_screen(t, x, f, m)
    for i, (ti, nm) in enumerate(ICONS):
        k = spring(t - ti, 0.3); al = s_((ti + 0.9 - t)/0.2)
        if k > 0 and t < ti + 0.9: fx.composite(f, icon_bubble(nm), 790 - 60*(i % 2), 560 + 40*i, k, min(1, k)*al)
    if hook["kind"] in ("text", "text_small") and hook["t0"] <= t < hook["t1"]:
        u = t - hook["t0"]; k = spring(u, 0.32); al = s_((hook["t1"] - t)/0.18)
        rot = 6*math.sin(u*14)*max(0, 1 - u/0.8) if hook.get("wobble") else 0
        y = 560 if hook["kind"] == "text" else 300
        if hook.get("punch"):
            z = 1 + 0.12*out_(u/0.2); f = cv2.warpAffine(f, np.float32([[z, 0, OW/2*(1 - z)], [0, z, OH*0.3*(1 - z)]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
        fx.composite(f, HOOK_IMG, OW/2, y, k, min(1, k)*al, rot)
    for y_ in INS:
        if y_["kind"] == "logo" and y_["a"] <= t < y_["b"] and not ins_at(t):
            k = spring(t - y_["a"], 0.35); al = s_((y_["b"] - t)/0.25); fx.composite(f, LOGO_POP, OW/2, 330, 0.85 + 0.15*k, min(1, k)*al)
        if y_["kind"] == "url" and y_["a"] <= t < y_["b"]:
            k = spring(t - y_["a"], 0.35); fx.composite(f, url_pill(), OW/2, 1580 if not ins_at(t) else 1680, 0.85 + 0.15*k, min(1, k))
    if CFG.get("timer"):
        p = min(1, t/MAIN); bar = np.zeros((96, 360, 4), np.float32)
        tx = text_rgba("DAY 1", inter(30, 800), (255, 255, 255)); fx.composite(bar[..., :3], tx, 72, 48); bar[..., 3] = 215
        cv2.rectangle(bar, (140, 43), (330, 53), (90, 90, 90, 255), -1); cv2.rectangle(bar, (140, 43), (140 + int(190*p), 53), (82, 158, 196, 255), -1)
        bar[..., [0, 2]] = bar[..., [2, 0]]; fx.composite(f, bar, 200, 150, 1.0, 1.0)
    draw_caps(f, t)
    if t < 0.2 and PRE_ROLL == 0: pass
    return f
prev = os.environ.get("PREVIEW")
if prev:
    ts = [float(x) for x in prev.split(",")]
    cv2.imwrite(os.path.join(D, "preview.png"), np.hstack([cv2.resize(np.clip(frame_at(t), 0, 255).astype(np.uint8), (216, 384)) for t in ts]))
    print("preview", NAME, "dur %.1f" % DUR, [(x["kind"], round(x["a"], 1), round(x["b"], 1)) for x in INS]); sys.exit(0)
# ---------------- audio ----------------
BD = os.path.join(S, "lib/rnn/rnnoise-models/beguiling-drafter-2018-08-30/bd.rnnn")
CLEAN = ("highpass=f=80,bandreject=f=100:width_type=q:w=8,bandreject=f=200:width_type=q:w=8,"
         f"arnndn=m={BD}:mix=0.9,equalizer=f=220:t=q:w=1:g=-1.2,equalizer=f=3200:t=q:w=1.3:g=1.5")
os.makedirs(os.path.join(D, "clean"), exist_ok=True)
def rd(path, a, b, ch=1):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(a,0):.4f}", "-t", f"{b-max(a,0):.4f}", "-i", path, "-f", "f32le", "-ac", str(ch), "-ar", str(R), "-"], capture_output=True).stdout
    x = np.frombuffer(r, np.float32).copy(); return x if ch == 1 else x.reshape(-1, 2)
gains = {}
for c in sorted({g["c"] for g in segs}):
    cp = os.path.join(D, f"clean/{c}.wav")
    if not os.path.exists(cp): subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(D, f"src/{c}.mp4"), "-vn", "-af", CLEAN, "-ac", "1", "-ar", str(R), cp])
    x = np.concatenate([rd(cp, g["a"], g["b"]) for g in segs if g["c"] == c])
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "1", "-ar", str(R), "-i", "-", "-af", "ebur128", "-f", "null", "-"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err = p.communicate(x.tobytes()); gains[c] = 10**((-19 - float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", err.decode())[-1]))/20)
NS = int((DUR + 1)*R); voice = np.zeros(NS, np.float32); speech = []
for g in segs:
    x = rd(os.path.join(D, f"clean/{g['c']}.wav"), g["s0"], g["s1"])*gains[g["c"]]; n = len(x); fw = np.ones(n, np.float32); kk = min(int(0.012*R), n//2)
    if kk: fw[:kk] = np.linspace(0, 1, kk); fw[-kk:] = np.linspace(1, 0, kk)
    s = int(round(g["t0"]*R)); voice[s:s + n] += (x*fw)[:max(0, min(n, NS - s))]; speech.append((g["t0"] + g["a"] - g["s0"], g["t0"] + g["b"] - g["s0"]))
tracks = {"lofi": "lib/ccmusic/freemusicarchive.org/HoliznaCC0 - Not It (Lofi).mp3.mp3", "beat": "lib/ccmusic/freepd.com/Beat One.mp3"}
mus = rd(os.path.join(S, tracks[CFG["music"]]), 0, DUR + 1, 2); mus = np.pad(mus, ((0, max(0, NS - len(mus))), (0, 0)))[:NS]
tt = np.arange(NS)/R; mus *= (10**(-21/20)*np.clip(tt/1.2, 0, 1)*np.clip((DUR - tt)/1.5, 0, 1))[:, None]
sfx = np.zeros((NS, 2), np.float32)
for trig, sid in CFG.get("sfx", []): fx.place_sfx(sfx, sid, at(trig) - 0.05, -8, speech, R)
if CFG.get("whoosh0"): fx.place_sfx(sfx, "whoosh-fast-medium", 0.35, -10, speech, R)
if PRE_ROLL: fx.place_sfx(sfx, "whoosh-fast-medium", PRE_ROLL, -10, speech, R)
for x in SCREEN_INS:
    if not any(y["b"] == x["a"] for y in SCREEN_INS): fx.place_sfx(sfx, "whoosh-fast-soft", x["a"] + 0.1, -12, speech, R)
for ti, _ in ICONS: fx.place_sfx(sfx, "pop-small-in", ti + 0.02, -10, speech, R)
if CFG.get("timer"):
    for tk in np.arange(2.5, at("Well,") - 0.5, 1.0): fx.place_sfx(sfx, "time-clock", tk, -22, speech, R)
fx.place_sfx(sfx, "sting-minimal-short", MAIN + 0.15, -8, speech, R)
def wr(path, x, ch):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", str(ch), "-ar", str(R), "-i", "-", "-c:a", "pcm_f32le", path], stdin=subprocess.PIPE)
    p.stdin.write(x.astype(np.float32).tobytes()); p.stdin.close(); p.wait()
wr(os.path.join(D, "_v.wav"), voice, 1); wr(os.path.join(D, "_m.wav"), mus, 2); wr(os.path.join(D, "_s.wav"), sfx, 2)
# ---------------- video + mux ----------------
raw_mp4 = os.path.join(D, "raw.mp4")
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", raw_mp4], stdin=subprocess.PIPE)
for n in range(N):
    ff.stdin.write(np.clip(frame_at(n/FPS) + 0.5, 0, 255).astype(np.uint8).tobytes())
    if n % 240 == 0: print(NAME, n, "/", N, flush=True)
ff.stdin.close(); ff.wait()
outdir = os.path.join(S, "final/ugc"); os.makedirs(outdir, exist_ok=True)
OUTV = os.path.join(outdir, f"Bounti-{NAME}-{CFG['title'].replace(' ', '-').replace('/', '').replace('(', '').replace(')', '').replace('--', '-')}.mp4")
FG = ("[1]acompressor=threshold=-22dB:ratio=2.5:attack=6:release=120:makeup=2,deesser=i=0.3,asplit[v][k];"
      "[2][k]sidechaincompress=threshold=0.03:ratio=4:attack=25:release=450:knee=6[md];[v][md][3]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_mp4, "-i", os.path.join(D, "_v.wav"), "-i", os.path.join(D, "_m.wav"), "-i", os.path.join(D, "_s.wav"),
                "-filter_complex", FG, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", OUTV], check=True)
json.dump(dict(duration=DUR, segs=segs, inserts=INS), open(os.path.join(D, "edit.json"), "w"), indent=1)
print("DONE", NAME, OUTV, "%.1fs" % DUR)
