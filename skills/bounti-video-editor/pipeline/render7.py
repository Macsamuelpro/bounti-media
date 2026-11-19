"""Three versions of the Bounti crowd video. usage: render7.py A|B|C out.mp4  (PREVIEW=t1,t2,... writes a strip instead)
A = cut-out on Bounti paper with kinetic type (sample style)
B = natural studio footage, bold moving captions, text behind subject, site cards
C = editorial: footage, serif + handwritten captions, whip transitions into animated scenes"""
import os, sys, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for p in (HERE, os.path.join(ROOT, "editkit"), os.path.join(ROOT, "v3")): sys.path.insert(0, p)
import mg7, captions as CAP, transitions as TR, grade as GR
from collections import OrderedDict
V = sys.argv[1]; OUT = sys.argv[2]; FPS = 24; OW, OH, SW, SH = 1080, 1920, 720, 1280
E = json.load(open(os.environ.get("EDIT", os.path.join(HERE, "edit7.json")))); segs = E["segs"]; words = E["words"]
END = 3.0; MAIN = E["duration"]; DUR = MAIN + END; N = int(round(DUR*FPS))
def s_(t): t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def out_(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t)**3
def tl(txt_start):
    for g in segs:
        if g["txt"].startswith(txt_start): return g
    raise KeyError(txt_start)
def at(txt, end=False):
    g = tl(txt); return g["t0"] + (g["b"] if end else g["a"]) - g["s0"]
def has(txt):
    try: tl(txt); return True
    except KeyError: return False
def scene(name, start, ends, pad=0.0):
    if not has(start): return None
    a = at(start) + pad; i = [k for k, g in enumerate(segs) if g["txt"].startswith(start)][0]
    for g in segs[i + 1:]:
        if any(g["txt"].startswith(e) for e in ends): return (name, a, g["t0"] + g["a"] - g["s0"])
    return (name, a, at(start, True) + 0.3)
SCN = [("poof", 0.0, at("Poof", True) + 0.15)] if has("Poof") else []
for args in [("scroll_past", "And every month,", ["Okay, and"]), ("empty_store", "Opening day", ["Please."]),
             ("rsvp", "The only people", ["You need a crowd"]), ("crowd", "You need a crowd", ["Now, let me", "Imagine people"]),
             ("spread", "What if you could get", ["People watching"]), ("busy_store", "Imagine people already", ["Now someone passing"]),
             ("bounti", "It's called Bounti", ["We've got crowd"], -0.1), ("pillars", "We've got crowd", ["Basically,", "And the beautiful", "and the beautiful", "Head over", "head over"])]:
    sc = scene(*args)
    if sc: SCN.append(sc)
if has("Head over") or has("head over"): SCN.append(("partners", at("Head over" if has("Head over") else "head over"), MAIN))
if V == "C": SCN = [s for s in SCN if s[0] not in ("rsvp", "crowd")]
TRANS_F = 6
def scene_at(t):
    for name, a, b in SCN:
        if a <= t < b: return name, a, b
    return None
# ---------------- footage ----------------
RAW = OrderedDict(); MASK = {}
def raw(c):
    if c in RAW: RAW.move_to_end(c); return RAW[c]
    cap = cv2.VideoCapture(os.path.join(HERE, f"src/{c}.mp4")); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    RAW[c] = fr
    while len(RAW) > 3: RAW.popitem(last=False)
    return fr
def mask(c, k):
    if c not in MASK:
        d = np.load(os.path.join(HERE, f"masks/{c}.npz")); MASK[c] = {int(i): m for i, m in zip(d["idx"], d["m"])}
        if len(MASK) > 4: MASK.pop(next(iter(MASK)))
    m = MASK[c].get(k)
    if m is None: m = MASK[c][min(MASK[c], key=lambda j: abs(j - k))]
    return cv2.resize(m, (OW, OH), interpolation=cv2.INTER_LINEAR).astype(np.float32)/255
def seg_at(t):
    for i, g in enumerate(segs):
        if g["t0"] - 1e-6 <= t < g["t0"] + (g["s1"] - g["s0"]) + g["hold"] - 1e-6: return i, g
    return len(segs) - 1, segs[-1]
def src_time(g, t):
    loc = t - g["t0"]; sp = g["s1"] - g["s0"]
    if loc <= sp: return g["s0"] + loc
    avail = min(g["s1"] + g["hold"], 8.0 - 0.05) - g["s1"]
    return g["s1"] + (loc - sp)*max(avail, 0)/max(g["hold"], 1e-6)
LOOK = {"A": lambda x: GR.adjust(x, exposure=0.10, contrast=0.06, shadows=0.15, vibrance=0.08),
        "B": lambda x: GR.adjust(x, exposure=0.12, contrast=0.08, shadows=0.18, highlights=0.1, vibrance=0.12, temp=0.03),
        "C": lambda x: GR.vignette(GR.adjust(x, exposure=0.05, contrast=0.12, shadows=0.1, saturation=-0.08, temp=0.04), 0.18)}[V]
def footage(t, want_mask=False):
    i, g = seg_at(t); c = g["c"]; s = src_time(g, t); fr = raw(c); k = min(int(round(s*FPS)), len(fr) - 1)
    # morph across same-clip joins (same framing); cross-clip joins are camera-angle cuts
    if i + 1 < len(segs) and segs[i + 1]["c"] == c:
        jb = segs[i + 1]["t0"]
        if jb - 3/FPS <= t:
            n2 = segs[i + 1]; k2 = int(round((n2["s0"] + (t - jb))*FPS)); kk = (t - (jb - 3/FPS))*FPS
            if abs(k2 - k) > 2: f = TR.morph_cut(fr[k].astype(np.float32), fr[min(k2, len(fr) - 1)].astype(np.float32), s_((kk + 0.5)/6))
            else: f = fr[k].astype(np.float32)
        else: f = fr[k].astype(np.float32)
    elif i > 0 and segs[i - 1]["c"] == c and t < g["t0"] + 3/FPS:
        p = segs[i - 1]; kp = int(round((p["s1"] + p["hold"]*0 + (t - g["t0"]))*FPS)); kk = (t - g["t0"])*FPS + 3
        f = TR.morph_cut(fr[min(kp, len(fr) - 1)].astype(np.float32), fr[k].astype(np.float32), s_((kk + 0.5)/6)) if abs(kp - k) > 2 else fr[k].astype(np.float32)
    else: f = fr[k].astype(np.float32)
    f = cv2.resize(f, (OW, OH), interpolation=cv2.INTER_LANCZOS4)
    return LOOK(f), (mask(c, k) if want_mask else None), g
# ---------------- type ----------------
EMPH = {"disappeared": 0, "ads": 0, "50,000": 0, "customers": 0, "guru": 0, "targeting": 0, "people": 0, "problem": 0, "business": 0, "creator": 0,
        "app": 0, "store": 0, "perfect": 0, "you": 0, "cousin": 0, "crowd": 0, "interesting": 0, "thousands": 0, "viral": 0, "traction": 0,
        "website": 0, "link": 0, "game": 0, "Bounti": 0, "trends": 0, "actions": 0, "impressions": 0, "crisis": 0, "distribution": 0, "talk": 0}
def key_of(text):
    for w in text.replace(",", "").replace(".", "").replace("?", "").split():
        if w in EMPH: return w
    return None
CHUNKS = [(g["t0"] + g["a"] - g["s0"], g["t0"] + g["b"] - g["s0"], g["txt"].replace("partners.earnbounti.com", "").strip()) for g in segs]
CHUNKS = [c for c in CHUNKS if c[2]]
def hidden(t): return scene_at(t) is not None or t >= MAIN
if V == "B":
    CPT = CAP.Captioner(CHUNKS, "bar_pop", "pop", y=1300, max_words=3, max_chars=16, hidden=[(a, b) for _, a, b in SCN] + [(MAIN, DUR)])
elif V == "C":
    st = dict(CAP.STYLES["editorial"]); st["size"] = 78; st["shadow"] = 0.95; st["box"] = (13, 13, 13); st["box_alpha"] = 0.28
    CPT = CAP.Captioner(CHUNKS, st, "blur_in", y=1420, max_words=4, max_chars=22, hidden=[(a, b) for _, a, b in SCN] + [(MAIN, DUR)])
else:
    st = dict(CAP.STYLES["highlighter"]); st.update(family="Inter", weight=800, size=58, hl_col=(255, 214, 10), fill=(13, 13, 13), shadow=0)
    CPT = CAP.Captioner(CHUNKS, st, "word_by_word", y=1400, max_words=4, max_chars=18, hidden=[(a, b) for _, a, b in SCN] + [(MAIN, DUR)])
CPT.max_w = 560 if V == "A" else 960
if V == "A":
    st2 = dict(st); st2.update(box=(255, 255, 255), box_alpha=0.94)
    CPT2 = CAP.Captioner(CHUNKS, st2, "word_by_word", y=1400, max_words=4, max_chars=18, hidden=[(a, b) for _, a, b in SCN] + [(MAIN, DUR)]); CPT2.max_w = 700
SPOTS = {"A": [(360, 1380), (720, 1500), (380, 1560), (700, 1360)], "B": [(540, 1300), (540, 1180), (540, 1420)], "C": [(540, 1420)]}[V]
def caption_pos(ci): return SPOTS[ci % len(SPOTS)]
_orig_draw = CPT.draw
_spot = {}
CAND = [(540, 420), (300, 760), (780, 760), (300, 1250), (780, 1250), (540, 1620), (540, 1780)]
def draw_caps(f, t, m=None):
    for ci, c in enumerate(CPT.ch):
        if c["t0"] <= t < c["hold"]:
            if V == "A":
                if ci not in _spot:
                    if m is None: _spot[ci] = caption_pos(ci)
                    else:
                        big = behind_text(c["t0"] + 0.05) is not None; best = None
                        for k, (x, y) in enumerate(CAND):
                            if big and y < 520: continue
                            if y < 620 and any(a <= c["t0"] + 0.05 < b for _, a, b, _ in CARDS): continue
                            ov = (m[max(0, y - 80):y + 80, max(0, x - 290):x + 290] > 0.4).mean()
                            sc = ov + 0.02*k + (0.05 if (ci > 0 and _spot.get(ci - 1) == (x, y)) else 0)
                            if best is None or sc < best[0]: best = (sc, (x, y))
                        _spot[ci] = best[1] if best[0] < 0.06 else ("box", (540, 1560))
                if _spot[ci][0] == "box":
                    CPT2.x, CPT2.y = _spot[ci][1]; CPT2.draw(f, t); return
                CPT.x, CPT.y = _spot[ci]
            else: CPT.x, CPT.y = caption_pos(ci)
            _orig_draw(f, t); return
BIGF = CAP.font("Inter", 230, 900)
_bigcache = {}
def big_word(w, col):
    k = (w, col)
    if k not in _bigcache:
        im = mg7.text_img(w.upper() if V != "C" else w, BIGF if V != "C" else CAP.font("Instrument Serif", 220), col, -0.06 if V != "C" else -0.02)
        if im.shape[1] > 960: im = cv2.resize(im, (960, int(im.shape[0]*960/im.shape[1])), interpolation=cv2.INTER_AREA)
        _bigcache[k] = im
    return _bigcache[k]
KEYS = []
for c in CHUNKS:
    w = key_of(c[2])
    if w and w not in ("you", "people") and not any(abs(c[0] - k[0]) < 2.2 for k in KEYS): KEYS.append((c[0], min(c[1] + 0.4, c[0] + 2.0), w))
def behind_text(t):
    for a, b, w in KEYS:
        if a <= t < b and not hidden(t):
            u = t - a; al = s_(u/0.15)*(1 - s_((t - (b - 0.2))/0.2))
            col = (13, 13, 13)
            if V == "A" and w in ("Bounti", "crowd", "actions", "50,000", "thousands"): col = (196, 158, 82)
            return big_word(w, col), al, 1.0 + 0.04*(1 - out_(u/0.4)), 250 + 30*(1 - out_(u/0.35))
    return None
# ---------------- site cards (version B) ----------------
_cards = [("Follow_Bounty", "sharing your links", "Engaging with"), ("Like_a_video", "You've launched a website", "sending it to"),
          ("Your_wallet", "You decide what", "Not just sitting"), ("Your_wallet", "you decide what", "not just sitting"), ("Link_your_accounts", "Basically,", "and the beautiful")]
CARDS = []
if V in ("A", "B"):
    for nm, st_, en in _cards:
        if has(st_):
            a0 = at(st_); b0 = at(en) if has(en) else at(st_, True) + 0.6
            CARDS.append((nm, a0, b0, (820, 640)))
def draw_cards(f, t):
    for name, a, b, (x, y) in CARDS:
        if a <= t < b:
            u = t - a; k = mg7.pop(u); al = min(1, k)*(1 - s_((t - (b - 0.25))/0.25))
            mg7.paste(f, mg7.card(name, 360), 855, 470 + 20*(1 - out_(u/0.3)), 0.85 + 0.15*k, al)
# ---------------- frame ----------------
PAPER = mg7.paper()
def scene_frame(t):
    sc = scene_at(t); name, a, b = sc; return mg7.SCENES[name](t - a, b - a)
def main_frame(t):
    f, m, g = footage(t, want_mask=(V in ("A", "B")))
    if V == "A":
        cut = PAPER.copy(); bt = behind_text(t)
        if bt: mg7.paste(cut, bt[0], OW/2, bt[3], bt[2], bt[1])
        mm = cv2.GaussianBlur(np.clip((m - 0.35)/0.4, 0, 1), (0, 0), 1.2)[..., None]
        sh = cv2.GaussianBlur(m, (0, 0), 14)[..., None]; cut = cut*(1 - 0.18*np.roll(sh, 18, 0))
        f = cut*(1 - mm) + f*mm
    elif V == "B":
        bt = behind_text(t)
        if bt:
            L = np.zeros_like(f); mg7.paste(L, bt[0], OW/2, bt[3], bt[2], 1.0)
            A = np.zeros(f.shape[:2], np.float32); tmp = np.zeros_like(f); a_img = bt[0].copy(); a_img[..., :3] = 255
            mg7.paste(tmp, a_img, OW/2, bt[3], bt[2], 1.0); A = (tmp[..., 0]/255)*bt[1]*(1 - m)
            sh = cv2.GaussianBlur(A, (0, 0), 10)*0.35; f = f*(1 - np.roll(sh, 8, 0)[..., None])
            f = f*(1 - A[..., None]) + L*A[..., None]
    elif V == "C":
        bt = behind_text(t)
        if bt: mg7.paste(f, bt[0], OW/2, 330, 1.0, bt[1]*0.95)
    draw_cards(f, t)
    global LAST_M; LAST_M = m
    return f
LAST_M = None
def frame_at(t):
    if t >= MAIN:
        return mg7.sc_end(t - MAIN, END)
    sc = scene_at(t)
    base = scene_frame(t) if sc else main_frame(t)
    if not sc: draw_caps(base, t, LAST_M)
    # transitions at scene boundaries
    for name, a, b in SCN:
        for edge, into in ((a, True), (b, False)):
            if edge <= 0.01 or edge >= MAIN - 0.01: continue
            d = (t - edge)*FPS
            if -TRANS_F/2 <= d < TRANS_F/2:
                u = (d + TRANS_F/2)/TRANS_F
                tA = edge - 1/FPS; tB = edge
                A_ = (scene_frame(tA) if scene_at(tA) else main_frame(tA)); B_ = (scene_frame(tB) if scene_at(tB) else main_frame(tB))
                if V == "A": return TR.dissolve(A_, B_, u) if u < 1 else base
                if V == "B": return TR.zoom_blur(A_, B_, u, 0.25)
                if V == "C": return TR.whip_pan(A_, B_, u, "left" if into else "right", 0.8)
    return base
prev = os.environ.get("PREVIEW")
if prev:
    ts = [float(x) for x in prev.split(",")]
    cv2.imwrite(OUT, np.hstack([cv2.resize(np.clip(frame_at(t), 0, 255).astype(np.uint8), (270, 480)) for t in ts])); sys.exit(0)
import subprocess
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "13", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for n in range(N):
    t = n/FPS; f = frame_at(t)
    if t > DUR - 0.5: f = f*(1 - s_((t - (DUR - 0.5))/0.5)) + mg7.paper()*s_((t - (DUR - 0.5))/0.5)
    ff.stdin.write(np.clip(f + 0.5, 0, 255).astype(np.uint8).tobytes())
    if n % 480 == 0: print(V, "frame", n, "/", N, flush=True)
ff.stdin.close(); ff.wait()
json.dump(dict(duration=DUR, main=MAIN, scenes=SCN, cards=[(c[0], c[1]) for c in CARDS]), open(OUT + ".json", "w"), indent=1)
print("done", V)
