"""Bounti-style animated scenes (1080x1920). Paper #F1F0EC, ink #0D0D0D, grey #5E5E5E, gold accent, Inter Black + Kalam,
Open Peeps characters (CC0) and real Bounti UI cards captured from earnbounti.com. scene(name)(u, dur) -> BGR float frame."""
import os, sys, math, random, glob
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, "editkit"))
import peeps, captions as CAP
W, H = 1080, 1920
PAPER = (241, 240, 236); INK = (13, 13, 13); GREY = (94, 94, 94); GOLD = (196, 158, 82); WHITE = (255, 255, 255)
def inter(size, w=900): return CAP.font("Inter", size, w)
def kalam(size): return CAP.font("Kalam", size, 700)
def s_(t): t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def out_(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t)**3
def pop(u, d=0.35): return peeps.pop_scale(u) if u > 0 else 0.0

# ---------------- canvas helpers (RGBA PIL canvas, composited at the end) ----------------
_grain = None
def paper():
    global _grain
    if _grain is None:
        rng = np.random.default_rng(4); g = rng.normal(0, 3.2, (H//2, W//2)).astype(np.float32)
        _grain = cv2.resize(cv2.GaussianBlur(g, (0, 0), 0.7), (W, H))[..., None]
    return np.clip(np.array(PAPER[::-1], np.float32)[None, None, :] + _grain, 0, 255)
def paste(frame, rgba, cx, cy, scale=1.0, alpha=1.0, rot=0.0): CAP.composite(frame, rgba, cx, cy, scale, alpha, rot)
def text_img(txt, f, col=INK, tracking=-0.055, align="center"):
    d = ImageDraw.Draw(Image.new("L", (1, 1))); lines = txt.split("\n"); size = f.size
    ws = [sum(d.textlength(ch, font=f) + tracking*size for ch in l) for l in lines]; lh = int(size*1.02)
    im = Image.new("RGBA", (int(max(ws)) + 40, lh*len(lines) + int(size*0.4)), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = 20 + ((max(ws) - ws[i])/2 if align == "center" else 0); y = 10 + i*lh
        c = col if not isinstance(col, list) else col[i]
        for ch in l: dr.text((x, y), ch, font=f, fill=c + (255,)); x += d.textlength(ch, font=f) + tracking*size
    return np.array(im).astype(np.float32)
_cache = {}
def T(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]
def peep(seed, h=520, standing=True): return T(("peep", seed, h, standing), lambda: peeps.to_rgba_array(peeps.random_peep(seed, standing), h))
def card(name, width=700):
    def mk():
        im = cv2.imread(os.path.join(HERE, "web", f"card_{name}.png"), cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 3: im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
        h, w = im.shape[:2]; r = int(w*0.065); m = np.zeros((h, w), np.uint8)
        cv2.rectangle(m, (r, 0), (w - r, h), 255, -1); cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
        for cx, cy in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)): cv2.circle(m, (cx, cy), r, 255, -1)
        im[..., 3] = np.minimum(im[..., 3], m); s = width/w
        im = cv2.resize(im, (width, int(h*s)), interpolation=cv2.INTER_AREA).astype(np.float32)
        rgba = im[..., [2, 1, 0, 3]]
        sh = cv2.GaussianBlur(rgba[..., 3], (0, 0), 18)*0.30; pad = 50
        out = np.zeros((rgba.shape[0] + 2*pad, rgba.shape[1] + 2*pad, 4), np.float32)
        out[pad + 14:pad + 14 + sh.shape[0], pad:pad + sh.shape[1], 3] = sh
        a = rgba[..., 3:4]/255; reg = out[pad:pad + rgba.shape[0], pad:pad + rgba.shape[1]]
        reg[..., :3] = reg[..., :3]*(1 - a) + rgba[..., :3]*a; reg[..., 3:4] = np.maximum(reg[..., 3:4], rgba[..., 3:4])
        return out
    return T(("card", name, width), mk)
def coin(size=260):
    def mk():
        im = cv2.imread(os.path.join(HERE, "web", "sec_06.png")); h, w = im.shape[:2]
        crop = im[int(h*0.48):int(h*0.98), int(w*0.18):int(w*0.82)]
        d = np.abs(crop.astype(np.float32) - np.array(PAPER[::-1], np.float32)).max(2)
        a = np.clip((d - 18)*6, 0, 255).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats((a > 0).astype(np.uint8))
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); x, y, ww, hh = st[k, :4]; keep = (lab == k).astype(np.uint8)
        keep = cv2.dilate(keep, np.ones((5, 5), np.uint8)); a = a*keep
        rgba = np.dstack([crop[..., ::-1], a])[y:y + hh, x:x + ww].astype(np.float32)
        s = size/max(ww, hh); return cv2.resize(rgba, (int(ww*s), int(hh*s)), interpolation=cv2.INTER_AREA)
    return T(("coin", size), mk)
LOGO_PATH = os.path.join(ROOT, "v3/gfx/bounti_logo.png")
def logo(width, ink=True):
    def mk():
        im = cv2.imread(LOGO_PATH, cv2.IMREAD_UNCHANGED).astype(np.float32); s = width/im.shape[1]
        im = cv2.resize(im, (width, int(im.shape[0]*s)), interpolation=cv2.INTER_AREA); rgba = im[..., [2, 1, 0, 3]].copy()
        if ink: rgba[..., :3] = np.array(INK, np.float32)
        return rgba
    return T(("logo", width, ink), mk)
def lucide(name, px, col=INK, stroke=2.2):
    import resvg_py, io
    def mk():
        svg = open(os.path.join(ROOT, "lib/icons/package/icons", name + ".svg")).read().replace('stroke="currentColor"', 'stroke="#%02x%02x%02x"' % col)
        svg = svg.replace('stroke-width="2"', f'stroke-width="{stroke}"').replace('width="24"', f'width="{px}"').replace('height="24"', f'height="{px}"')
        return np.array(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert("RGBA")).astype(np.float32)
    return T(("icon", name, px, col), mk)
def ink_line(frame, pts, width=7, col=INK, progress=1.0):
    """Hand-drawn style line that draws on with progress."""
    pts = np.array(pts, np.float32); seg = np.hypot(*np.diff(pts, axis=0).T); L = seg.sum()*progress; out = [pts[0]]; acc = 0
    for p0, p1, s in zip(pts[:-1], pts[1:], seg):
        if acc + s <= L: out.append(p1); acc += s
        else: out.append(p0 + (p1 - p0)*max(L - acc, 0)/max(s, 1e-6)); break
    cv2.polylines(frame, [np.array(out, np.int32)], False, col[::-1], width, cv2.LINE_AA)
def label(txt, size=56, col=INK, rot=0): return T(("lab", txt, size, col), lambda: text_img(txt, kalam(size), col, 0.0))

# ---------------- store illustration ----------------
def store(frame, cx, base_y, prog=1.0, name="GRAND OPENING", open_sign=True):
    w, h = 760, 520; x0, y0 = int(cx - w/2), int(base_y - h)
    k = s_(prog)
    ink_line(frame, [(x0, base_y), (x0, y0 + 110), (x0 + w, y0 + 110), (x0 + w, base_y)], 9, INK, k)
    ink_line(frame, [(x0 - 30, y0 + 110), (x0 + w/2, y0 + 10), (x0 + w + 30, y0 + 110)], 9, INK, k)
    if k > 0.6:
        a = s_((k - 0.6)/0.4)
        for i in range(8):
            xa = x0 + i*w/8; col = INK if i % 2 == 0 else WHITE
            pts = np.array([[xa, y0 + 110], [xa + w/8, y0 + 110], [xa + w/8 - 8, y0 + 170], [xa + 8, y0 + 170]], np.int32)
            ov = frame.copy(); cv2.fillPoly(ov, [pts], col[::-1]); cv2.polylines(ov, [pts], True, INK[::-1], 5, cv2.LINE_AA)
            frame[:] = frame*(1 - a) + ov*a
        dx = int(cx - 110); cv2.rectangle(frame, (dx, base_y - 300), (dx + 220, base_y), INK[::-1], 7, cv2.LINE_AA)
        cv2.rectangle(frame, (x0 + 60, base_y - 290), (x0 + 270, base_y - 120), INK[::-1], 6, cv2.LINE_AA)
        cv2.rectangle(frame, (x0 + w - 270, base_y - 290), (x0 + w - 60, base_y - 120), INK[::-1], 6, cv2.LINE_AA)
        if name: paste(frame, T(("store", name), lambda: text_img(name, inter(64), INK)), cx, y0 - 70, 1.0, a)
        if open_sign: paste(frame, label("open", 44), dx + 110, base_y - 240, 1.0, a)

# ---------------- scenes ----------------
def sc_poof(u, d):
    f = paper(); rng = np.random.default_rng(5)
    for i in range(7):                                               # stack of bills + coins, then puff
        k = 1 - s_((u - 0.55 - i*0.03)/0.35)
        if k <= 0: continue
        y = 1120 - i*40; bill = T(("bill",), lambda: _bill())
        paste(f, bill, W/2 + rng.uniform(-14, 14), y, 1.5*k, k, rng.uniform(-4, 4))
    if u > 0.45:
        pu = (u - 0.45)/0.9
        for i in range(26):
            r = rng.uniform(40, 120)*(0.6 + pu); ang = rng.uniform(0, 2*math.pi); dist = rng.uniform(40, 420)*out_(pu)
            x = W/2 + math.cos(ang)*dist; y = 1000 + math.sin(ang)*dist*0.8; a = max(0, 1 - pu)*0.9
            ov = f.copy(); cv2.circle(ov, (int(x), int(y)), int(r), (232, 231, 227), -1, cv2.LINE_AA); cv2.circle(ov, (int(x), int(y)), int(r), INK[::-1], 4, cv2.LINE_AA)
            f[:] = f*(1 - a) + ov*a
    paste(f, label("poof.", 120), W/2, 600, out_((u - 0.5)/0.3), s_((u - 0.5)/0.2))
    return f
def _bill():
    im = Image.new("RGBA", (520, 250), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, 514, 244], 18, fill=(236, 240, 228, 255), outline=INK + (255,), width=6)
    d.ellipse([200, 65, 320, 185], outline=INK + (255,), width=6); d.text((240, 82), "$", font=inter(80), fill=INK + (255,))
    d.rounded_rectangle([30, 30, 490, 220], 12, outline=INK + (255,), width=3)
    return np.array(im).astype(np.float32)
def sc_scroll_past(u, d):
    """50,000 saw it: people walk past a giant ad without stopping."""
    f = paper(); ad = T(("ad",), lambda: text_img("YOUR AD", inter(110), INK))
    cv2.rectangle(f, (300, 520), (780, 1020), INK[::-1], 8, cv2.LINE_AA); paste(f, ad, 540, 770, 1.0)
    cnt = int(50000*out_(u/max(d*0.7, 0.1)))
    paste(f, T(("cnt", cnt//500), lambda: text_img(f"{cnt:,}", inter(150), INK)), 540, 330, 1.0)
    paste(f, label("saw it", 64, GREY), 540, 440)
    for i in range(6):
        x = -200 + ((u*260 + i*240) % 1480); dy, rot = peeps.walk_offset(u + i*0.13)
        paste(f, peep(30 + i, 520), x, 1430 + dy, 1.0, 1.0, rot)
    if u > d*0.55: paste(f, label("...and kept walking", 62), 540, 1780, 1.0, s_((u - d*0.55)/0.3))
    return f
def sc_empty_store(u, d):
    f = paper(); store(f, 540, 1230, u/0.9, "GRAND OPENING")
    who = [("you", 61), ("staff", 62), ("staff", 63), ("your cousin", 64)]
    for i, (lab_, s) in enumerate(who):
        k = pop(u - 0.9 - i*0.35)
        if k <= 0: continue
        x = 180 + i*240; dy, rot = peeps.idle_offset(u, i)
        paste(f, peep(s, 470), x, 1530 + dy, k, min(1, k)); paste(f, label(lab_, 44), x, 1815, 1.0, min(1, k))
    if u > d - 1.3: paste(f, label("...a private family meeting?", 58), 540, 380, 1.0, s_((u - (d - 1.3))/0.3))
    return f
def sc_crowd_fill(u, d, title="You need people."):
    f = paper(); paste(f, T(("ct", title), lambda: text_img(title, inter(96))), 540, 330, out_(u/0.4) if u < 0.4 else 1.0, s_(u/0.25))
    rows = [(1180, 330, 7), (1450, 400, 6), (1760, 470, 5)]; i = 0
    for ry, hgt, n in rows:
        for j in range(n):
            k = pop(u - 0.25 - i*0.09); x = (j + 0.5)*W/n + (35 if ry == 1450 else 0)
            if k > 0:
                dy, rot = peeps.idle_offset(u, i); paste(f, peep(100 + i, hgt), x, ry + dy, k, min(1, k), rot)
            i += 1
    return f
def sc_rsvp(u, d):
    f = paper()
    im = T(("rsvp",), lambda: _rsvp_card()); paste(f, im, 540, 900, out_(u/0.35)*0.1 + 0.9, s_(u/0.25))
    if u > 1.2: paste(f, label("just the organizers.", 66), 540, 1420, 1.0, s_((u - 1.2)/0.3))
    return f
def _rsvp_card():
    im = Image.new("RGBA", (820, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 820, 560], 44, fill=WHITE + (255,))
    d.text((52, 46), "Attending", font=inter(54, 800), fill=INK + (255,)); d.text((52, 118), "Launch night", font=inter(36, 500), fill=GREY + (255,))
    for i, nm in enumerate(["Organizer", "Organizer"]):
        y = 220 + i*130; d.ellipse([52, y, 142, y + 90], fill=(230, 229, 225, 255)); d.text((170, y + 20), nm, font=inter(44, 700), fill=INK + (255,))
    d.text((520, 46), "2", font=inter(90, 900), fill=INK + (255,))
    return np.array(im).astype(np.float32)
def sc_spread(u, d):
    """Thousands helping spread the word: people with phones, link/heart/share icons hop between them."""
    f = paper(); pos = [(200, 1250), (540, 1180), (880, 1250), (360, 1620), (720, 1620)]
    for i, (x, y) in enumerate(pos):
        k = pop(u - i*0.12); dy, rot = peeps.idle_offset(u, i)
        if k > 0: paste(f, peep(200 + i, 400), x, y + dy, k, min(1, k), rot)
    icons = ["link", "heart", "share-2", "message-circle", "eye"]
    for j in range(10):
        a = (u*0.9 + j*0.37) % 1.0; s_i = j % len(pos); t_i = (j*3 + 1) % len(pos)
        (x0, y0), (x1, y1) = pos[s_i], pos[t_i]; x = x0 + (x1 - x0)*a; y = y0 - 330 + (y1 - y0)*a - math.sin(a*math.pi)*220
        ic = lucide(icons[j % len(icons)], 72, INK, 2.4)
        bub = T(("bub", icons[j % len(icons)]), lambda ic=ic: _bubble(ic)); paste(f, bub, x, y, 1.0, min(1, math.sin(a*math.pi)*3))
    paste(f, T(("spw",), lambda: text_img("spreading\nthe word", inter(104))), 540, 420, 1.0, s_(u/0.3))
    return f
def _bubble(ic):
    s = 120; out = np.zeros((s + 30, s + 30, 4), np.float32); c = s//2 + 15
    m = np.zeros(out.shape[:2], np.uint8); cv2.circle(m, (c, c), s//2, 255, -1)
    sh = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 6)*0.25; out[..., 3] = np.roll(sh, 5, 0)
    a = m[..., None]/255.0; out[..., :3] = out[..., :3]*(1 - a) + 255*a; out[..., 3:4] = np.maximum(out[..., 3:4], m[..., None])
    CAP.composite(out[..., :3], ic, c, c); out[..., :3] = out[..., :3]; return out
def sc_busy_store(u, d):
    f = paper(); store(f, 540, 1250, 1.0, "OPEN")
    for i in range(9):
        a = ((u*0.35 + i*0.13) % 1.0); x = -150 + a*(540 + 150); sc = 1 - 0.45*s_((a - 0.6)/0.4)
        dy, rot = peeps.walk_offset(u + i*0.2)
        if a < 0.97: paste(f, peep(300 + i, 420), x, 1520 + dy - 80*s_((a - 0.6)/0.4), sc, min(1, (1 - a)*6), rot)
    for i, (x, y) in enumerate([(820, 1560), (960, 1600)]):
        dy, rot = peeps.idle_offset(u, i + 4); paste(f, peep(320 + i, 400), x, y + dy, 1.0, 1.0, rot)
    if u > 0.8:
        for j in range(3):
            k = pop(u - 0.8 - j*0.25)
            if k > 0: paste(f, T(("camb",), lambda: _bubble(lucide("camera", 64))), 760 + j*110, 1150 - j*40, k)
    return f
def sc_bounti_reveal(u, d):
    f = paper(); k = pop(u - 0.05); paste(f, logo(820), 540, 720, k*0.98 + 0.02*out_(u), min(1, k))
    paste(f, coin(240), 540, 420, pop(u - 0.25), min(1, pop(u - 0.25)))
    if u > 0.55: paste(f, label("go get it.", 70), 540, 940, 1.0, s_((u - 0.55)/0.3))
    return f
def sc_pillars(u, d):
    f = paper(); items = [("users", "Crowd marketing"), ("trending-up", "Trend marketing"), ("link", "Compound affiliate\nmarketing")]
    for i, (ic, txt) in enumerate(items):
        k = pop(u - i*0.55); y = 620 + i*380
        if k <= 0: continue
        im = T(("pill", txt), lambda ic=ic, txt=txt: _pill(ic, txt)); paste(f, im, 540, y, 0.9 + 0.1*k, min(1, k))
    return f
def _pill(ic, txt):
    im = Image.new("RGBA", (900, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, 900, 300], 60, fill=INK + (255,))
    arr = np.array(im).astype(np.float32); icn = lucide(ic, 120, WHITE, 2.2); CAP.composite(arr[..., :3], icn, 150, 150)
    tx = text_img(txt, inter(62 if "\n" in txt else 70), WHITE, -0.04, "left"); CAP.composite(arr[..., :3], tx, 270 + tx.shape[1]/2, 150)
    arr[..., [0, 2]] = arr[..., [2, 0]]
    return arr
def sc_partners(u, d):
    """Real partners.earnbounti.com page in a phone, URL beneath."""
    f = paper(); ph = T(("phone",), lambda: _phone(os.path.join(HERE, "web", "partners_top.png")))
    k = out_(u/0.5); paste(f, ph, 540, 860 + 120*(1 - k), 0.96 + 0.04*k, s_(u/0.3))
    paste(f, T(("url",), lambda: text_img("partners.earnbounti.com", inter(64, 800))), 540, 1720, 1.0, s_((u - 0.4)/0.3))
    return f
def _phone(path):
    sc = cv2.imread(path); sw = 620; sh = int(sc.shape[0]*sw/sc.shape[1]); sc = cv2.resize(sc, (sw, sh), interpolation=cv2.INTER_AREA)
    bz = 26; out = np.zeros((sh + 2*bz + 60, sw + 2*bz + 60, 4), np.float32); x0 = y0 = 30
    m = np.zeros(out.shape[:2], np.uint8); cv2.rectangle(m, (x0 + 60, y0), (x0 + sw + 2*bz - 60, y0 + sh + 2*bz), 255, -1)
    cv2.rectangle(m, (x0, y0 + 60), (x0 + sw + 2*bz, y0 + sh + 2*bz - 60), 255, -1)
    for cx, cy in ((x0 + 60, y0 + 60), (x0 + sw + 2*bz - 60, y0 + 60), (x0 + 60, y0 + sh + 2*bz - 60), (x0 + sw + 2*bz - 60, y0 + sh + 2*bz - 60)): cv2.circle(m, (cx, cy), 60, 255, -1)
    sh_ = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 16)*0.35; out[..., 3] = np.roll(sh_, 16, 0)
    a = m[..., None]/255.0; out[..., :3] = out[..., :3]*(1 - a) + np.array(INK, np.float32)*a; out[..., 3:4] = np.maximum(out[..., 3:4], m[..., None])
    sm = np.zeros((sh, sw), np.uint8); r = 40; cv2.rectangle(sm, (r, 0), (sw - r, sh), 255, -1); cv2.rectangle(sm, (0, r), (sw, sh - r), 255, -1)
    for cx, cy in ((r, r), (sw - r, r), (r, sh - r), (sw - r, sh - r)): cv2.circle(sm, (cx, cy), r, 255, -1)
    reg = out[y0 + bz:y0 + bz + sh, x0 + bz:x0 + bz + sw]; sa = sm[..., None]/255.0
    reg[..., :3] = reg[..., :3]*(1 - sa) + sc[..., ::-1]*sa
    return out
def sc_end(u, d):
    f = paper(); paste(f, logo(640), 540, 820, 0.96 + 0.04*out_(u/0.5), s_(u/0.3))
    paste(f, T(("end1",), lambda: text_img("Put a crowd behind\nyour next big thing.", inter(70), [INK, GREY])), 540, 1020, 1.0, s_((u - 0.3)/0.3))
    paste(f, T(("end2",), lambda: text_img("partners.earnbounti.com", inter(48, 700), GREY)), 540, 1200, 1.0, s_((u - 0.6)/0.3))
    return f
SCENES = dict(poof=sc_poof, scroll_past=sc_scroll_past, empty_store=sc_empty_store, crowd=sc_crowd_fill, rsvp=sc_rsvp, spread=sc_spread,
              busy_store=sc_busy_store, bounti=sc_bounti_reveal, pillars=sc_pillars, partners=sc_partners, end=sc_end)
