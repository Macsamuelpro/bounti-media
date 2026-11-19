# ======================= UGC v2 style engines (exec'd inside ugc_render2.py) =======================
from ugc_styles2 import ST as _ST
import dev3d, cards as CARDS
SV = _ST[NAME]; STY = SV["style"]
CREAM = np.array((230, 246, 252), np.float32)
_det = cv2.FaceDetectorYN.create(os.path.join(S, "models/yunet.onnx"), "", (270, 480), 0.6); _face = {}; _last_face = [(390.0, 420.0, 300.0, 380.0)]
def face_box(t):
    i, g = seg_at(max(t, PRE_ROLL)); fr_all = raw(g["c"]); k = min(src_k(g, max(t, PRE_ROLL)), len(fr_all) - 1); key = (g["c"], k//4)
    if key not in _face:
        fr = fr_all[k]; sm = cv2.resize(fr, (270, 480)); _, fs = _det.detect(sm)
        if fs is not None and len(fs):
            x, y, w, h = [float(v)*4 for v in fs[0][:4]]; _face[key] = (x, y, w, h); _last_face[0] = _face[key]
        else: _face[key] = _last_face[0]
    return _face[key]
def app_at(t):
    for x in SCREEN_INS:
        if x["a"] <= t < x["b"]: return x
    return None
def app_frame(x, t): return live_img(x["live"], x["spd"], t - x["a"], (860, 1864))
def kin(x, t, d=0.3): return min(s_((t - x["a"])/d), s_((x["b"] - t)/d))
def rr_mask(h, w, r): return dev3d.rrect(h, w, r)
def paste(f, img, x, y, mask=None, al=1.0):
    """paste BGR img with optional float mask at top-left x,y (clipped)"""
    h, w = img.shape[:2]; xa, ya, xb, yb = max(int(x), 0), max(int(y), 0), min(int(x) + w, OW), min(int(y) + h, OH)
    if xa >= xb or ya >= yb: return
    src = img[ya - int(y):yb - int(y), xa - int(x):xb - int(x)].astype(np.float32); m = (mask[ya - int(y):yb - int(y), xa - int(x):xb - int(x)] if mask is not None else np.ones(src.shape[:2], np.float32))[..., None]*al
    f[ya:yb, xa:xb] = f[ya:yb, xa:xb]*(1 - m) + src*m
def drop_shadow(f, x, y, w, h, r=40, k=0.3, blur=30, dy=24):
    m = np.zeros((OH, OW), np.float32); cv2.rectangle(m, (int(x) + 10, int(y) + dy), (int(x + w) - 10, int(y + h) + dy), 1, -1); m = cv2.GaussianBlur(m, (0, 0), blur)*k; f *= (1 - m[..., None])
def fit_screen(fr, H):
    W = int(H*fr.shape[1]/fr.shape[0]); return cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
def safe_y(t, want="below", h=200):
    """a y centre for text that keeps clear of the face"""
    x, y, w, hh = face_box(t)
    if want == "above" and y - h - 40 > 120: return y - h/2 - 50
    return min(max(y + hh + h/2 + 70, 1180), 1720)
def big_text(lines, sz, col, box=None, w=900):
    imgs = [text_rgba(l, inter(sz, w), col, track=-0.04) for l in lines]; W = max(i.shape[1] for i in imgs); H = sum(i.shape[0] for i in imgs) - 20*(len(imgs) - 1)
    pad = 36 if box else 0; out = np.zeros((H + 2*pad, W + 2*pad, 4), np.float32)
    if box: out[..., :3] = box; out[..., 3] = rr_mask(out.shape[0], out.shape[1], 26)*255
    y = pad
    for im in imgs:
        h_, w_ = im.shape[:2]; x = pad + (W - w_)//2; a = im[..., 3:4]/255; reg = out[y:y + h_, x:x + w_]; reg[..., :3] = reg[..., :3]*(1 - a) + im[..., :3]*a; reg[..., 3:4] = np.maximum(reg[..., 3:4], im[..., 3:4]); y += h_ - 20
    return out
_hk = {}
def hook_img(key, maker):
    if key not in _hk: _hk[key] = maker()
    return _hk[key]
H0, H1 = SV["hook_t"]
def hook_alpha(t): return min(s_((t - H0)/0.2), s_((H1 - t)/0.25)) if H0 <= t < H1 else 0.0
# ---------------- captions per style ----------------
_cs, _ca = SV["cap"]
CPT2 = CAP.Captioner(CH, dict(CAP.STYLES[_cs]), _ca, y=1500, max_words=3 if STY in ("punch", "contrast", "vlog", "gs_float") else 5, max_chars=18 if STY in ("punch", "contrast") else 28, hidden=[(MAIN, DUR), (H0, H1)])
def caps(f, t, x=None, y=None, maxw=900):
    CPT2.x = OW/2 if x is None else x; CPT2.y = safe_y(t) if y is None else y; CPT2.max_w = maxw; CPT2.draw(f, t)
# ---------------- shared overlays ----------------
def logo_moments(f, t, y=None):
    for y_ in INS:
        if y_["kind"] == "logo" and y_["a"] <= t < y_["b"]:
            k = spring(t - y_["a"], 0.35); al = s_((y_["b"] - t)/0.25); yy = y if y is not None else safe_y(t, "above", 160)
            fx.composite(f, LOGO_POP, OW/2, yy, 0.85 + 0.15*k, min(1, k)*al)
def url_moment(f, t, y=1660, scale=1.0):
    for y_ in INS:
        if y_["kind"] == "url" and y_["a"] <= t < y_["b"]:
            k = spring(t - y_["a"], 0.35); fx.composite(f, url_pill(), OW/2, y, (0.85 + 0.15*k)*scale, min(1, k))
def person_layer(f, m, s, cx, bottom=OH):
    """presenter cut out with the person mask, scaled s, anchored at the bottom edge (torso framing)"""
    M = np.float32([[s, 0, cx - s*OW/2], [0, s, bottom - s*OH]]); pf = cv2.warpAffine(f, M, (OW, OH)); pm = cv2.warpAffine(m, M, (OW, OH)); return pf, cv2.GaussianBlur(pm, (0, 0), 1.2)
def torso_layer(f, m, t, face_w, cx, cy):
    """scale the presenter so the face is face_w px wide and centred at (cx, cy); the rest falls off the bottom edge (torso framing)"""
    fxb, fyb, fw, fh = face_box(t); s = min(max(face_w/max(fw, 1), 0.45), 1.8); fcx, fcy = fxb + fw/2, fyb + fh/2
    M = np.float32([[s, 0, cx - s*fcx], [0, s, cy - s*fcy]]); pf = cv2.warpAffine(f, M, (OW, OH)); pm = cv2.warpAffine(m, M, (OW, OH)); return pf, cv2.GaussianBlur(pm, (0, 0), 1.2)
def blurfill(fr):
    """full 9:16 frame: app screen fitted to height over a blurred, dimmed copy of itself"""
    sc = fit_screen(fr, OH).astype(np.float32); bgf = cv2.GaussianBlur(cv2.resize(fr, (OW, OH)), (0, 0), 40).astype(np.float32)*0.55
    paste(bgf, sc, (OW - sc.shape[1])/2, 0); return bgf
# ---------------- style engines ----------------
def st_punch(t):
    x = app_at(t); f, m = footage(t)
    i, g = seg_at(t); fxb, fyb, fw, fh = face_box(t); z = 1.0 if i % 2 == 0 else 1.15     # jump-cut punch-ins, centred on the face
    cx, cy = fxb + fw/2, fyb + fh/2; f = cv2.warpAffine(f, np.float32([[z, 0, cx*(1 - z)], [0, z, cy*(1 - z)]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
    if x:
        k = kin(x, t, 0.12); f = f*(1 - k) + blurfill(app_frame(x, t))*k
    a = hook_alpha(t)
    if a: fx.composite(f, hook_img("h", lambda: big_text(SV["hook"], 96, (13, 13, 13), box=(226, 178, 84))), OW/2, safe_y(t, "below", 260), 0.9 + 0.1*spring(t - H0, 0.3), a, -3)
    logo_moments(f, t); caps(f, t, y=1690 if x else None); url_moment(f, t, 1500); return f
_card_ts = None
def st_cards(t):
    global _card_ts
    if _card_ts is None:
        _card_ts = [(0.0, H1, "hook")] + [(at(a_) - 0.1, at(a_) + 2.2, kind) for a_, kind in SV["cards"]] + [(x["a"], x["b"], "app") for x in SCREEN_INS]
    f, m = footage(t); cam = f.copy(); active = [c for c in _card_ts if c[0] <= t < c[1]]
    if not active: caps(cam, t); url_moment(cam, t); return cam
    a0, a1, kind = active[0]; k = min(s_((t - a0)/0.45), s_((a1 - t)/0.45)); lt = t - a0
    if kind == "app":
        card = np.empty_like(f); card[:] = CREAM
        tile = CARDS.shrink_to_tile(f, 1.0, tile=(0.26, 0.18, 0.34)); tm = np.zeros((OH, OW), np.float32)
        tw = int(OW*0.34); th = int(tw*OH/OW); x0, y0 = int(OW*0.26 - tw/2), int(OH*0.18 - th/2); tm[y0:y0 + th, x0:x0 + tw] = rr_mask(th, tw, 42)
        card = card*(1 - tm[..., None]) + tile*tm[..., None]
        x = app_at(t); ph = phone(None, 0, None, cv2.resize(app_frame(x, t), (SW_, SH_), interpolation=cv2.INTER_AREA))
        fx.composite(card, ph, OW*0.6, OH*0.58, 0.82, 1.0); caps(card, t, x=OW*0.6, y=OH*0.93, maxw=800)
    else:
        card = CARDS.shrink_to_tile(f, eout(lt/0.5), tile=(0.5, 0.36, 0.46))
        if kind == "hook": CARDS.letter_reveal(card, SV["hook"][0], lambda c, col: text_rgba(c, inter(150, 900), col), lt - 0.3, OW/2, OH*0.69, col=(13, 13, 13))
        elif kind == "logo": fx.composite(card, logo_rgba(520), OW/2, OH*0.69, 0.9 + 0.1*eout((lt - 0.3)/0.4), eout((lt - 0.3)/0.4))
        else: CARDS.letter_reveal(card, kind.split(":")[1], lambda c, col: text_rgba(c, inter(140, 900), col), lt - 0.3, OW/2, OH*0.69, col=(13, 13, 13))
    out = CARDS.fog_dissolve(cam, card, k) if 0 < k < 1 else (card if k >= 1 else cam)
    if k < 0.5: caps(out, t)
    url_moment(out, t); return out
def eout(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x)**3
def st_split(t):
    f, m = footage(t); x = app_at(t)
    if x:
        k = kin(x, t, 0.35); fxb, fyb, fw, fh = face_box(t); y0 = int(min(max(fyb + fh/2 - 430, 0), OH - 960))
        out = np.empty_like(f); out[:960] = f[y0:y0 + 960]
        scr = cv2.resize(app_frame(x, t), (OW, int(OW*1864/860)), interpolation=cv2.INTER_AREA).astype(np.float32); sy = int((scr.shape[0] - 960)*SV.get("ay", 0.4))
        out[960:] = scr[sy:sy + 960]; out[954:966] = 13
        slide = int((1 - eout(k))*960); 
        if slide: out[960:] = np.vstack([f[960 + 0:960 + slide] if slide else f[0:0], out[960:OH - slide]])[:960]
        f = out; caps(f, t, y=900, maxw=860)
    else: caps(f, t)
    a = hook_alpha(t)
    if a: fx.composite(f, hook_img("h", lambda: big_text(SV["hook"], 70, (255, 255, 255), w=600)), OW/2, safe_y(t, "below", 160), 1.0, a)
    logo_moments(f, t); url_moment(f, t); return f
def st_loom(t):
    f, m = footage(t); x = app_at(t)
    if x:
        k = kin(x, t, 0.14); out = np.empty_like(f); out[:] = PAPER
        sc = fit_screen(app_frame(x, t), 1760); w = sc.shape[1]; xx = (OW - w)/2; drop_shadow(out, xx, 80, w, 1760); paste(out, sc, xx, 80, rr_mask(1760, w, 44))
        fxb, fyb, fw, fh = face_box(t); side = int(fh*2.3); cx, cy = fxb + fw/2, fyb + fh*0.62
        sq = cv2.warpAffine(f, np.float32([[1, 0, side/2 - cx], [0, 1, side/2 - cy]]), (side, side), borderMode=cv2.BORDER_REFLECT); bub = cv2.resize(sq, (340, 340)).astype(np.float32)
        cm = np.zeros((340, 340), np.float32); cv2.circle(cm, (170, 170), 168, 1, -1, cv2.LINE_AA); ring = np.zeros((360, 360, 3), np.float32) + 255
        rm = np.zeros((360, 360), np.float32); cv2.circle(rm, (180, 180), 180, 1, -1, cv2.LINE_AA); paste(out, ring, 40, OH - 420, rm); paste(out, bub, 50, OH - 410, cm)
        f = f*(1 - k) + out*k; caps(f, t, x=700, y=OH - 160, maxw=560)
    else: caps(f, t)
    a = hook_alpha(t)
    if a:
        note = hook_img("h", lambda: big_text(SV["hook"], 62, (13, 13, 13), box=(246, 226, 160), w=700)); fxb, fyb, fw, fh = face_box(t)
        fx.composite(f, note, OW/2, safe_y(t, "above", 150) if fyb > 380 else safe_y(t), 1.0, a, 4)
    logo_moments(f, t); url_moment(f, t); return f
def _backdrop_spec(t):
    xs = SCREEN_INS
    for x in xs:
        if x["a"] <= t < x["b"]: return x, t
    prev = [x for x in xs if x["b"] <= t]; nxt = [x for x in xs if x["a"] > t]
    if prev: return prev[-1], prev[-1]["b"] - 0.01
    return nxt[0], nxt[0]["a"]
def st_gs_side(t):
    f, m = footage(t, True); x, tt = _backdrop_spec(t)
    scr = cv2.resize(app_frame(x, tt), (OW, int(OW*1864/860)), interpolation=cv2.INTER_AREA).astype(np.float32); bgf = scr[:OH]*0.94
    pf, pm = torso_layer(f, m, t, 210, OW*0.70, OH*0.66); out = bgf*(1 - pm[..., None]) + pf*pm[..., None]
    for k_, (trig, num, lab) in enumerate(SV["steps"]):
        t0 = at(trig) - 0.1; t1 = at(SV["steps"][k_ + 1][0]) - 0.1 if k_ + 1 < len(SV["steps"]) else at("And that's") - 0.1
        if t0 <= t < t1:
            kk = spring(t - t0, 0.35); badge = hook_img("b" + num, lambda: big_text([num + "  " + lab], 54, (255, 255, 255), box=(13, 13, 13), w=800))
            fx.composite(out, badge, 50 + badge.shape[1]/2, 210, kk, min(1, kk))
    a = hook_alpha(t)
    if a: fx.composite(out, hook_img("h", lambda: big_text(SV["hook"], 84, (13, 13, 13), box=(241, 240, 236))), OW/2, 330, 0.9 + 0.1*spring(t - H0, 0.3), a)
    caps(out, t, x=OW*0.36, y=1060, maxw=600); logo_moments(out, t, 330); url_moment(out, t, 1200); return out
def st_cinema(t):
    f, m = footage(t); i, g = seg_at(t); u = (t - g["t0"])/max(g["s1"] - g["s0"] + g["hold"], 0.5); z = 1.02 + 0.06*u
    fxb, fyb, fw, fh = face_box(t); cx, cy = fxb + fw/2, fyb + fh/2
    f = cv2.warpAffine(f, np.float32([[z, 0, cx*(1 - z)], [0, z, cy*(1 - z)]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
    f = f*np.array([0.92, 0.99, 1.07], np.float32); f = np.clip((f - 128)*1.06 + 128, 0, 255)
    f += np.random.default_rng(int(t*24)).normal(0, 5, (OH//4, OW//4, 1)).repeat(4, 0).repeat(4, 1).astype(np.float32)
    x = app_at(t)
    if x:
        k = kin(x, t, 0.4); sc = cv2.resize(app_frame(x, t), (520, int(520*1864/860)), interpolation=cv2.INTER_AREA)[:640].astype(np.float32)
        pol = np.zeros((780, 600, 4), np.float32); pol[..., :3] = 247; pol[..., 3] = 255; pol[40:680, 40:560, :3] = sc[..., ::-1]
        side = 300 if cx > OW/2 else 780; fx.composite(f, pol, side + (1 - eout(k))*(300 if side > 540 else -300), OH*0.48, 0.9, k, -5 if side > 540 else 5)
    f[:300] = 13; f[OH - 300:] = 13
    a = hook_alpha(t)
    if a:
        full = SV["hook"][0]; n = int(len(full)*min(1, (t - H0)/1.4)); img = text_rgba(full[:max(n, 1)], CAP.font("Cormorant Garamond", 76, 600) if hasattr(CAP, "font") else inter(70), (236, 240, 241))
        fx.composite(f, img, OW/2, 150, 1.0, a)
    caps(f, t, y=OH - 150, maxw=940); logo_moments(f, t, 150); url_moment(f, t, OH - 150, 0.8); return f
def st_contrast(t):
    f, m = footage(t); turn = at(SV["turn"]) - 0.1; x = app_at(t)
    sat = 0.15 + 0.85*s_((t - turn)/0.6); g_ = cv2.cvtColor(np.clip(f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]
    f = g_*(1 - sat) + f*sat
    if t < turn: f *= 0.92
    for trig, word in SV["words"]:
        tw = at(trig) - 0.05
        if tw <= t < tw + 0.55:
            card = np.empty_like(f); card[:] = PAPER; fx.composite(card, hook_img("w" + word, lambda: text_rgba(word, inter(190, 900), (13, 13, 13))), OW/2, OH/2, 1.0 + 0.05*(t - tw)); f = card
    if x:
        k = kin(x, t, 0.35); card = np.empty_like(f); card[:] = PAPER; lt = t - x["a"]; dur = x["b"] - x["a"]
        yaw = -30 + 22*s_(lt/dur); dev3d.phone3d(card, app_frame(x, t), dict(x=OW/2, y=OH*0.60, s=1.6, yaw=yaw, pitch=6 - 4*s_(lt/dur), roll=-3))
        f = f*(1 - k) + card*k; caps(f, t, y=OH*0.075)
    else: caps(f, t)
    a = hook_alpha(t)
    if a:
        card = np.empty_like(f); card[:] = PAPER; fx.composite(card, hook_img("h", lambda: big_text(SV["hook"], 92, (13, 13, 13))), OW/2, OH/2, 0.95 + 0.05*spring(t - H0, 0.3)); f = f*(1 - a) + card*a
    logo_moments(f, t); url_moment(f, t); return f
def st_duet(t):
    f, m = footage(t); x = app_at(t)
    if x:
        k = kin(x, t, 0.35); out = cv2.GaussianBlur(f, (0, 0), 30)*0.45; pw, ph_ = 500, 900; y0 = (OH - ph_)//2 - 60
        fxb, fyb, fw, fh = face_box(t); cx, cy = fxb + fw/2, fyb + fh*1.6
        crop = cv2.warpAffine(f, np.float32([[1, 0, pw/2 - cx], [0, 1, ph_/2 - cy]]), (pw, ph_), borderMode=cv2.BORDER_REFLECT)
        drop_shadow(out, 30, y0, pw, ph_); paste(out, crop, 30, y0, rr_mask(ph_, pw, 34))
        panel = np.empty((ph_, pw, 3), np.float32); panel[:] = PAPER; sc = fit_screen(app_frame(x, t), ph_ - 40); paste(panel, sc, (pw - sc.shape[1])/2, 20, rr_mask(sc.shape[0], sc.shape[1], 30))
        drop_shadow(out, OW - 30 - pw, y0, pw, ph_); paste(out, panel, OW - 30 - pw, y0, rr_mask(ph_, pw, 34))
        for lab, xx in (("Me", 30 + pw/2), ("Bounti", OW - 30 - pw/2)): fx.composite(out, hook_img("l" + lab, lambda: text_rgba(lab, inter(40, 800), (255, 255, 255))), xx, y0 - 46)
        f = f*(1 - k) + out*k; caps(f, t, y=y0 + ph_ + 130, maxw=980)
    else: caps(f, t)
    a = hook_alpha(t)
    if a: fx.composite(f, hook_img("h", lambda: big_text(SV["hook"], 78, (255, 255, 255), box=(13, 13, 13))), OW/2, safe_y(t, "below", 220), 0.9 + 0.1*spring(t - H0, 0.3), a)
    logo_moments(f, t); url_moment(f, t); return f
def st_vlog(t):
    f, m = footage(t); i, g = seg_at(t)
    if i > 0 and segs[i - 1]["c"] != g["c"] and t - g["t0"] < 0.16:      # whip into a new take
        k = (t - g["t0"])/0.16; f = cv2.blur(np.roll(f, int((1 - k)*OW*0.25), 1), (int(50*(1 - k)) + 1, 1))
    fxb, fyb, fw, fh = face_box(t); x = app_at(t)
    if x:
        k = kin(x, t, 0.35); ph = phone(None, 0, None, cv2.resize(app_frame(x, t), (SW_, SH_), interpolation=cv2.INTER_AREA))
        side = 790 if fxb + fw/2 < OW/2 else 290; fx.composite(f, ph, side, OH*0.86 + (1 - eout(k))*700, 0.92, 1.0, 6 if side > 540 else -6)
    p = min(1, t/MAIN); hud = hook_img("hud", lambda: big_text(["DAY 1"], 40, (255, 255, 255), box=(13, 13, 13), w=900))
    fx.composite(f, hud, 40 + hud.shape[1]/2, 80); cv2.rectangle(f, (40, 140), (300, 150), (90, 90, 90), -1); cv2.rectangle(f, (40, 140), (40 + int(260*p), 150), (84, 178, 226), -1)
    items = SV["checklist"]; cw, chh = 420, 74*len(items) + 30; card = np.zeros((chh, cw, 4), np.float32); card[..., :3] = 255; card[..., 3] = rr_mask(chh, cw, 24)*235
    for j, (trig, lab) in enumerate(items):
        done = t >= at(trig) + 1.0; y = 30 + j*74; cv2.rectangle(card, (24, y), (66, y + 42), (13, 13, 13, 255), 3)
        if done: cv2.polylines(card, [np.int32([(30, y + 22), (44, y + 36), (62, y + 6)])], False, (84, 178, 226, 255), 6, cv2.LINE_AA)
        tx = text_rgba(lab, inter(32, 700), (13, 13, 13)); fx.composite(card[..., :3], tx[..., [2, 1, 0, 3]], 90 + tx.shape[1]/2, y + 22)
    card[..., :3] = card[..., [2, 1, 0]] if False else card[..., :3]
    fx.composite(f, card[..., [2, 1, 0, 3]], OW - 40 - cw/2, 80 + chh/2, 1.0, 1.0 if t < MAIN else 0)
    a = hook_alpha(t)
    if a: fx.composite(f, hook_img("h", lambda: big_text(["ONE DAY.", "HOW MANY BOUNTIES?"], 74, (13, 13, 13), box=(226, 178, 84))), OW/2, safe_y(t, "below", 220), 0.9 + 0.1*spring(t - H0, 0.3), a, -2)
    caps(f, t, x=(270 if (x and (fxb + fw/2) < OW/2) is False else OW/2) if not x else (300 if fxb + fw/2 >= OW/2 else 780), maxw=520 if x else 900)
    logo_moments(f, t); url_moment(f, t); return f
GS_SEQ = [(at("Look at this") - 0.1, [("signup", 0.0, 1.2)]), (at("And the idea") - 0.1, [("partner_create", 0.5, 1.38), ("partner_create", 3.05, 13.5)]), (at("Then people can join") - 0.1, [("browse_feed", 0.5, 8.7)]), (at("And for hunters") - 0.1, [("find_claim", 4.6, 9.0), ("find_claim", 12.9, 15.6)])] if NAME == "UGC12" else []
def st_gs_float(t):
    f, m = footage(t, True); out = np.empty_like(f); out[:] = PAPER
    cur = [g for g in GS_SEQ if g[0] <= t]
    if cur:
        t0, spec = cur[-1]; lt = t - t0; kin_ = s_(lt/0.5); fr = live_img(spec, 1.0, lt, (860, 1864))
        yaw = 18*math.sin(lt*0.5) - 6; zoom = 1.0 + 0.12*s_((lt - 1.5)/2.0)
        dev3d.phone3d(out, fr, dict(x=OW/2, y=OH*0.36 + (1 - kin_)*300, s=1.28*zoom, yaw=yaw, pitch=8, roll=-2), alpha=kin_)
    pf, pm = torso_layer(f, m, t, 230, OW/2, OH*0.70); out = out*(1 - pm[..., None]) + pf*pm[..., None]
    a = hook_alpha(t)
    if a: fx.composite(out, hook_img("h", lambda: big_text(SV["hook"], 96, (13, 13, 13))), OW/2, 330, 0.9 + 0.1*spring(t - H0, 0.3), a)
    caps(out, t, y=OH - 190); url_moment(out, t, OH - 330); return out
def st_chat(t):
    f, m = footage(t); dx, dy, r = 7*math.sin(t*2.3) + 4*math.sin(t*5.1), 6*math.sin(t*1.7 + 1), 0.35*math.sin(t*1.3)
    M = cv2.getRotationMatrix2D((OW/2, OH/2), r, 1.03); M[0, 2] += dx; M[1, 2] += dy; f = cv2.warpAffine(f, M, (OW, OH), borderMode=cv2.BORDER_REFLECT)
    fxb, fyb, fw, fh = face_box(t); side_left = fxb + fw/2 > OW/2
    def bubble(lines, tail_left):
        b = big_text(lines, 64, (13, 13, 13), box=(255, 255, 255), w=700); return b
    a = hook_alpha(t)
    if a: fx.composite(f, hook_img("h", lambda: bubble(SV["hook"], True)), OW/2, safe_y(t, "above", 140) if fyb > 380 else safe_y(t), 0.85 + 0.15*spring(t - H0, 0.3), a)
    lt0 = at(SV["bubbles"][0][0]) - 0.1; x = app_at(t)
    card = hook_img("link", lambda: _link_card())
    if lt0 <= t < lt0 + 2.4 and not x:
        k = spring(t - lt0, 0.35); fx.composite(f, card, OW/2, safe_y(t, "below", 260), 0.85 + 0.15*k, min(1, k)*s_((lt0 + 2.4 - t)/0.25))
    if x:
        k = kin(x, t, 0.4); out = np.empty_like(f); out[:] = PAPER; sc = fit_screen(app_frame(x, t), 1700); w = sc.shape[1]
        drop_shadow(out, (OW - w)/2, 110, w, 1700); paste(out, sc, (OW - w)/2, 110, rr_mask(1700, w, 50))
        z = 0.4 + 0.6*eout(k); out = cv2.warpAffine(out, np.float32([[z, 0, OW/2*(1 - z)], [0, z, OH*0.55*(1 - z)]]), (OW, OH), borderValue=(241, 240, 236))
        f = f*(1 - k) + out*k
    caps(f, t, y=OH - 170 if x else None); url_moment(f, t); return f
def _link_card():
    W_, H_ = 700, 230; c = np.zeros((H_, W_, 4), np.float32); c[..., :3] = 255; c[..., 3] = rr_mask(H_, W_, 34)*255
    cv2.rectangle(c, (24, 24), (206, 206), (13, 13, 13, 255), -1); lg = logo_rgba(160, (241, 240, 236)); fx.composite(c[..., :3], lg, 115, 115)
    t1 = text_rgba("Bounti", inter(54, 900), (13, 13, 13)); t2 = text_rgba("earnbounti.com", inter(36, 600), (110, 110, 110))
    fx.composite(c[..., :3], t1, 240 + t1.shape[1]/2, 90); fx.composite(c[..., :3], t2, 240 + t2.shape[1]/2, 150); c[..., :3] = c[..., [2, 1, 0]]; return c
ENGINES = {"punch": st_punch, "cards": st_cards, "split": st_split, "loom": st_loom, "gs_side": st_gs_side, "cinema": st_cinema, "contrast": st_contrast,
           "duet": st_duet, "vlog": st_vlog, "gs_float": st_gs_float, "chat": st_chat}
END_INK = STY in ("cinema", "contrast")
def frame_at(t):
    if t >= MAIN:
        u = t - MAIN; f = np.empty((OH, OW, 3), np.float32); f[:] = (13 if END_INK else PAPER)
        col = (241, 240, 236) if END_INK else INK
        imgs = (logo_rgba(600, col), text_rgba("Become a Bounti hunter.", inter(64, 900), col, track=-0.05), text_rgba("earnbounti.com", inter(48, 700), (150, 150, 150)))
        for img, y, d0 in zip(imgs, (820, 1000, 1090), (0.1, 0.35, 0.55)): fx.composite(f, img, OW/2, y + 14*(1 - out_((u - d0)/0.4)), 1.0, s_((u - d0)/0.3))
        if u < 0.3: g = ENGINES[STY](MAIN - 0.02); f = g*(1 - u/0.3) + f*(u/0.3)
        return f
    return ENGINES[STY](max(t, 0.0))
