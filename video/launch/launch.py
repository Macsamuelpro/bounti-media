"""Bounti launch video engine (kinetic type + live prototype UI + logo resolve).
usage: launch.py <video> <V|H> [PREVIEW=t1,t2]   V = 1080x1920, H = 1920x1080"""
import os, sys, json, math, io, subprocess
import numpy as np, cv2, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
L = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(L)
for p in (S, os.path.join(S, "editkit")): sys.path.insert(0, p)
import fx, captions as CAP
from scripts import V as VIDEOS
NAME, FMT = sys.argv[1], sys.argv[2]; CFG = VIDEOS[NAME]
OW, OH = (1080, 1920) if FMT == "V" else (1920, 1080); FPS = 30; R = 48000; VERT = FMT == "V"
PAPER = np.array((236, 240, 241), np.float32); INK = np.array((13, 13, 13), np.float32); GOLD = (84, 178, 226); GREY = (94, 94, 94)
def clamp(x, a=0.0, b=1.0): return min(max(x, a), b)
def ease(t): t = clamp(t); return t*t*(3 - 2*t)
def eout(t): t = clamp(t); return 1 - (1 - t)**3
def spring(u, d=0.4):
    if u <= 0: return 0.0
    u = min(u/d, 1.0); return 1 - math.exp(-6*u)*math.cos(u*math.pi*2.2) if u < 1 else 1.0
# ---------------- assets ----------------
_font = {}
def inter(sz, w=900):
    k = (sz, w)
    if k not in _font: _font[k] = CAP.font("Inter", sz, w)
    return _font[k]
def text_img(txt, sz, col, w=900, track=-0.05):
    """RGBA float image of one word/line, colour given as BGR"""
    f = inter(sz, w); d = ImageDraw.Draw(Image.new("L", (1, 1)))
    wd = sum(d.textlength(c, font=f) + track*sz for c in txt) - track*sz
    im = Image.new("RGBA", (int(wd) + 24, int(sz*1.32)), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); x = 12
    for c in txt: dr.text((x, int(sz*0.05)), c, font=f, fill=(col[2], col[1], col[0], 255)); x += d.textlength(c, font=f) + track*sz
    return np.array(im).astype(np.float32)
LOGO = cv2.imread(os.path.join(S, "v3/gfx/bounti_logo.png"), cv2.IMREAD_UNCHANGED)
def logo(w, col):
    im = cv2.resize(LOGO, (w, int(LOGO.shape[0]*w/LOGO.shape[1])), interpolation=cv2.INTER_AREA).astype(np.float32)[..., [2, 1, 0, 3]].copy()
    im[..., :3] = np.array(col[::-1], np.float32); return im
def icon(name, px, col):
    import resvg_py
    hexc = "#%02x%02x%02x" % (col[2], col[1], col[0])
    svg = open(os.path.join(S, "lib/icons/package/icons", name + ".svg")).read().replace('stroke="currentColor"', f'stroke="{hexc}"').replace('width="24"', f'width="{px}"').replace('height="24"', f'height="{px}"').replace('stroke-width="2"', 'stroke-width="2.1"')
    return np.array(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert("RGBA")).astype(np.float32)
def comp(f, rgba, cx, cy, sc=1.0, al=1.0, rot=0.0):
    """composite RGB(A)-ordered overlay onto BGR frame (fx.composite convention)"""
    if al <= 0.003 or sc <= 0.01: return
    fx.composite(f, rgba, cx, cy, sc, min(al, 1.0), rot)
# ---------------- live recordings ----------------
LIVE = os.path.join(S, "ugc/live")
class Clip:
    def __init__(s, n): s.n = n; s.meta = json.load(open(os.path.join(LIVE, n + ".json"))); s.cap = None; s.pos = -1; s.cur = None; s.fps = 24
    def at(s, sec):
        k = int(sec*s.fps)
        if s.cap is None or k < s.pos: s.cap = cv2.VideoCapture(os.path.join(LIVE, s.n + ".mp4")); s.pos = -1
        while s.pos < k:
            ok, fr = s.cap.read()
            if not ok: break
            s.pos += 1; s.cur = fr
        return s.cur
_clips = {}
def clip(n):
    if n not in _clips: _clips[n] = Clip(n)
    return _clips[n]
# ---------------- timeline ----------------
VO = json.load(open(os.path.join(L, "wav", NAME, "vo.json")))
MIN = dict(words=1.7, icons=2.2, phone=3.3, logo=1.3)
beats = []; t = 0.35
for i, (b, v) in enumerate(zip(CFG["beats"], VO)):
    k = b["scene"]["kind"]; last = i == len(VO) - 1
    d = max(v["dur"] + 0.55, MIN[k]) + (1.4 if last else 0.0)
    beats.append(dict(b, t0=t, t1=t + d, vo0=t + 0.12, vod=v["dur"], vofile=v["file"])); t += d
DUR = t + 0.1; N = int(DUR*FPS); TR = 0.34
for i, b in enumerate(beats):
    sc = b["scene"]
    if sc["kind"] == "phone":
        Lr = sum(e - s for _, s, e in sc["rec"]); b["spd"] = clamp(Lr/(b["t1"] - b["t0"] - 0.2), 0.8, 1.6)
def word_times(b, words):
    """approximate spoken time of each word from character share of the line"""
    vo = b["vo"].replace("\n", " "); tot = len(vo); out = []; pos = 0; low = vo.lower()
    for w in words:
        j = low.find(w.lower().strip(".,?*"), pos); j = pos if j < 0 else j; pos = j + 1
        out.append(b["vo0"] + b["vod"]*0.92*j/max(tot, 1))
    return out
# ---------------- scenes ----------------
def bg_of(sc): return INK if sc.get("bg") == "ink" or (sc["kind"] == "icons" and sc.get("bg") == "ink") else PAPER
def fg_of(sc): return (241, 240, 236) if sc.get("bg") == "ink" else (13, 13, 13)
_cache = {}
def words_layout(b, sz, maxw, key=None):
    key = key or (id(b), sz)
    if key in _cache: return _cache[key]
    sc = b["scene"]; col = fg_of(sc); lines = []; allw = []
    for ln in sc["text"].split("\n"):
        row = []
        for w in ln.split(" "):
            hi = w.startswith("*"); clean = w.replace("*", "")
            img = text_img(clean, sz, GOLD if hi else col); row.append(dict(img=img, hi=hi, w=clean)); allw.append(clean)
        lines.append(row)
    gap = sz*0.24
    widest = max(sum(r["img"].shape[1] for r in row) + gap*(len(row) - 1) for row in lines)
    if maxw and widest > maxw:
        _cache.pop(key, None); return words_layout(b, int(sz*maxw/widest*0.98), maxw, key)
    lh = sz*1.02; y0 = -(len(lines) - 1)*lh/2; items = []
    for li, row in enumerate(lines):
        W = sum(r["img"].shape[1] for r in row) + gap*(len(row) - 1); x = -W/2
        for r in row: items.append(dict(r, dx=x + r["img"].shape[1]/2, dy=y0 + li*lh)); x += r["img"].shape[1] + gap
    for it, tw in zip(items, word_times(b, allw)): it["t"] = tw
    _cache[key] = items; return items
def draw_words(f, b, t, cx, cy, sz, maxw=None):
    items = words_layout(b, sz, maxw)
    for it in items:
        u = t - (it["t"] - 0.08); k = spring(u, 0.38)
        if k <= 0: continue
        comp(f, it["img"], cx + it["dx"], cy + it["dy"] + 46*(1 - min(k, 1)), 0.88 + 0.12*k, clamp(u/0.12))
        if it["hi"]:                                         # hand-drawn gold underline under the highlight word
            p = eout((u - 0.25)/0.35); w = it["img"].shape[1]*0.92
            if p > 0:
                x0 = cx + it["dx"] - w/2; y = cy + it["dy"] + sz*0.62
                pts = [(x0 + w*p*s, y + 6*math.sin(s*math.pi*1.4) - 4*s) for s in np.linspace(0, 1, 24)]
                cv2.polylines(f, [np.int32(pts)], False, GOLD, max(6, sz//14), cv2.LINE_AA)
    if b["scene"].get("strike"):
        last = [it for it in items if it["dy"] == max(x["dy"] for x in items)]; tt = max(x["t"] for x in items) + 0.45
        p = eout((t - tt)/0.3)
        if p > 0:
            x0 = cx + min(x["dx"] - x["img"].shape[1]/2 for x in last); x1 = cx + max(x["dx"] + x["img"].shape[1]/2 for x in last); y = cy + last[0]["dy"] + sz*0.08
            cv2.line(f, (int(x0), int(y)), (int(x0 + (x1 - x0)*p), int(y - 6)), GOLD, max(8, sz//11), cv2.LINE_AA)
def scene_words(f, b, t):
    draw_words(f, b, t, OW/2, OH/2, 150 if VERT else 150, OW - 140)
def scene_icons(f, b, t):
    sc = b["scene"]; items = sc["items"]; n = len(items); ink = sc.get("bg") == "ink"
    tile_bg = (241, 240, 236) if ink else (13, 13, 13); icol = (13, 13, 13) if ink else (241, 240, 236); lcol = (241, 240, 236) if ink else (13, 13, 13)
    cols = (n if n <= 4 else 3) if not VERT else (1 if n == 3 else 2); rows = math.ceil(n/cols)
    if VERT and n == 3: cols, rows = 1, 3
    cw = (OW - 160)/cols; ch = min((OH - 300)/rows, 420 if VERT else 400); size = int(min(cw, ch)*0.68)
    ts = word_times(b, [lab.split(" ")[0] for _, lab in items])
    for i, (ic, lab) in enumerate(items):
        r, c = divmod(i, cols); cx = 80 + cw*(c + 0.5); cy = OH/2 + (r - (rows - 1)/2)*ch - 30
        u = t - ts[i] + 0.1; k = spring(u, 0.35)
        if k <= 0: continue
        key = ("icon", ic, size, ink)
        if key not in _cache:
            tile = np.zeros((size, size, 4), np.float32); cv2.circle(tile, (size//2, size//2), size//2 - 2, tuple(tile_bg[::-1]) + (255,), -1, cv2.LINE_AA)
            g = icon(ic, int(size*0.46), icol); fx.composite(tile[..., :3], g, size/2, size/2); _cache[key] = (tile, text_img(lab, int(size*0.24), lcol, 800, -0.03))
        tile, lab_img = _cache[key]
        comp(f, tile, cx, cy, k, clamp(u/0.1)); comp(f, lab_img, cx, cy + size*0.5 + lab_img.shape[0]*0.55, 1.0, clamp((u - 0.12)/0.2))
SW, SH = (640, 1386) if VERT else (430, 931)
def phone_img(fr, zoom=None, zk=0.0):
    scr = cv2.resize(fr, (SW, SH), interpolation=cv2.INTER_AREA).astype(np.float32)
    if zoom:                                                  # camera push-in (or a static crop) on part of the screen
        fy, zs = zoom[0], zoom[1]; fxa = zoom[2] if len(zoom) > 2 else 0.5; static = len(zoom) > 3
        z = zs if static else 1 + (zs - 1)*ease(zk); cy = SH*fy; cx = SW*fxa
        M = np.float32([[z, 0, cx - z*cx], [0, z, cy - z*cy]]); scr = cv2.warpAffine(scr, M, (SW, SH), borderMode=cv2.BORDER_REPLICATE)
    bz = int(SW*0.032); r = int(SW*0.13); W2, H2 = SW + 2*bz, SH + 2*bz; pad = 60
    out = np.zeros((H2 + 2*pad, W2 + 2*pad, 4), np.float32)
    def rr(img, x, y, w, h, rad, val):
        cv2.rectangle(img, (x + rad, y), (x + w - rad, y + h), val, -1); cv2.rectangle(img, (x, y + rad), (x + w, y + h - rad), val, -1)
        for qx, qy in ((x + rad, y + rad), (x + w - rad, y + rad), (x + rad, y + h - rad), (x + w - rad, y + h - rad)): cv2.circle(img, (qx, qy), rad, val, -1, cv2.LINE_AA)
    m = np.zeros(out.shape[:2], np.float32); rr(m, pad, pad, W2, H2, r + bz, 1.0)
    sh = cv2.GaussianBlur(m, (0, 0), 26)*0.32; out[..., 3] = np.roll(sh, 26, 0)*255
    out[..., :3] = 13*m[..., None]; out[..., 3] = np.maximum(out[..., 3], m*255)
    sm = np.zeros((SH, SW), np.float32); rr(sm, 0, 0, SW - 1, SH - 1, r, 1.0)
    reg = out[pad + bz:pad + bz + SH, pad + bz:pad + bz + SW]; reg[..., :3] = reg[..., :3]*(1 - sm[..., None]) + scr[..., ::-1]*sm[..., None]
    return out
def rec_time(b, tl):
    rt = max(tl, 0)*b["spd"]
    for n, s, e in b["scene"]["rec"]:
        if rt < e - s: return n, s + rt
        rt -= e - s
    n, s, e = b["scene"]["rec"][-1]; return n, e - 0.02
def scene_phone(f, b, t, i):
    sc = b["scene"]; prevp = i > 0 and beats[i - 1]["scene"]["kind"] == "phone"; tl = t - b["t0"]
    # soft gold disc behind the phone
    cx, cy = (OW/2, OH*0.6) if VERT else (OW*0.68, OH/2)
    k = 1.0 if prevp else spring(tl, 0.5)
    rad = int((560 if VERT else 470)*(0.6 + 0.4*k)); ov = f.copy(); cv2.circle(ov, (int(cx), int(cy)), rad, GOLD, -1, cv2.LINE_AA); f[:] = f*0.82 + ov*0.18
    n, rt = rec_time(b, tl); fr = clip(n).at(rt)
    ph = phone_img(fr, sc.get("zoom"), (tl - 0.6)/max(b["t1"] - b["t0"] - 1.2, 0.5))
    rot = 0 if prevp else -7*(1 - k); y = cy + (0 if prevp else 420*(1 - min(k, 1)))
    comp(f, ph, cx, y, 1.0, 1.0, rot)
    tx, ty = (OW/2, OH*0.155) if VERT else (OW*0.28, OH/2)
    draw_words(f, b, t, tx, ty, 118 if VERT else 112, OW - 120 if VERT else OW*0.5 - 120)
def scene_logo(f, b, t):
    sc = b["scene"]; tl = t - b["t0"]; last = b is beats[-1]
    lw = 640 if VERT else 700; cy = OH/2 - (90 if sc.get("url") else 0)
    k = eout(tl/0.55); lg = logo(lw, (13, 13, 13))
    if k < 1:
        bl = int(24*(1 - k))*2 + 1; lg = lg.copy(); lg[..., 3] = cv2.GaussianBlur(lg[..., 3], (bl, bl), 0)
    comp(f, lg, OW/2, cy, 1.22 - 0.22*k, k)
    p = eout((tl - 0.35)/0.45)
    if p > 0:
        w = lw*0.9; x0 = OW/2 - w/2; y = cy + lg.shape[0]*0.62
        pts = [(x0 + w*p*s, y + 10*math.sin(s*math.pi) - 6*s) for s in np.linspace(0, 1, 30)]; cv2.polylines(f, [np.int32(pts)], False, GOLD, 9, cv2.LINE_AA)
    if sc.get("sub"):
        key = ("sub", sc["sub"])
        if key not in _cache: _cache[key] = text_img(sc["sub"], 62 if VERT else 58, GREY, 800, -0.03)
        u = tl - 0.6; comp(f, _cache[key], OW/2, cy + lg.shape[0]*0.62 + 90 + 20*(1 - eout(u/0.35)), 1.0, clamp(u/0.3))
    if sc.get("url"):
        key = ("url", sc["url"])
        if key not in _cache:
            tx = text_img(sc["url"], 54, (241, 240, 236), 800, -0.02); h, w = tx.shape[:2]; pill = np.zeros((h + 34, w + 70, 4), np.float32); rr_ = pill.shape[0]//2
            cv2.rectangle(pill, (rr_, 0), (pill.shape[1] - rr_, pill.shape[0]), (13, 13, 13, 255), -1); cv2.circle(pill, (rr_, rr_), rr_, (13, 13, 13, 255), -1, cv2.LINE_AA); cv2.circle(pill, (pill.shape[1] - rr_, rr_), rr_, (13, 13, 13, 255), -1, cv2.LINE_AA)
            fx.composite(pill[..., :3], tx, pill.shape[1]/2, pill.shape[0]/2 + 2); _cache[key] = pill
        u = tl - 0.95; kk = spring(u, 0.35); comp(f, _cache[key], OW/2, cy + lg.shape[0]*0.62 + 230, 0.85 + 0.15*kk, clamp(u/0.12))
def render_scene(i, t):
    b = beats[i]; sc = b["scene"]; f = np.empty((OH, OW, 3), np.float32); f[:] = bg_of(sc) if sc["kind"] in ("words", "icons") else PAPER
    {"words": lambda: scene_words(f, b, t), "icons": lambda: scene_icons(f, b, t), "logo": lambda: scene_logo(f, b, t), "phone": lambda: scene_phone(f, b, t, i)}[sc["kind"]]()
    return f
def frame_at(t):
    i = next((k for k, b in enumerate(beats) if b["t0"] <= t < b["t1"]), len(beats) - 1 if t >= beats[-1]["t0"] else 0)
    f = render_scene(i, t)
    if i + 1 < len(beats) and t > beats[i]["t1"] - TR:
        same_phone = beats[i]["scene"]["kind"] == "phone" and beats[i + 1]["scene"]["kind"] == "phone"
        g = render_scene(i + 1, t); k = ease((t - (beats[i]["t1"] - TR))/TR)
        if same_phone: return f*(1 - k) + g*k
        off = int(k*(OH if VERT else OW)); out = np.empty_like(f)
        if VERT: out[:OH - off] = f[off:]; out[OH - off:] = g[:off]
        else: out[:, :OW - off] = f[:, off:]; out[:, OW - off:] = g[:, :off]
        if 0.15 < k < 0.85: out = cv2.blur(out, (1, 25) if VERT else (25, 1))
        return out
    if t < 0.35: f = f   # opens on paper, never black
    return f
prev = os.environ.get("PREVIEW")
if prev:
    ts = [float(x) for x in prev.split(",")]; sc = 0.2
    cv2.imwrite(os.path.join(L, f"pv_{NAME}_{FMT}.png"), np.hstack([cv2.resize(np.clip(frame_at(t), 0, 255).astype(np.uint8), (int(OW*sc), int(OH*sc))) for t in ts]))
    print("preview", NAME, FMT, "dur %.1f" % DUR, [(b["scene"]["kind"], round(b["t0"], 1), round(b.get("spd", 0), 2)) for b in beats]); sys.exit(0)
# ---------------- audio ----------------
NS = int((DUR + 0.5)*R); vo = np.zeros(NS, np.float32); speech = []
for b in beats:
    x, sr = sf.read(b["vofile"], dtype="float32")
    if sr != R: x = np.interp(np.arange(int(len(x)*R/sr))*sr/R, np.arange(len(x)), x).astype(np.float32)
    s = int(b["vo0"]*R); vo[s:s + len(x)] += x[:NS - s]; speech.append((b["vo0"], b["vo0"] + len(x)/R))
mp = os.path.join(S, "lib/ccmusic/freepd.com", CFG["music"] + ".mp3")
mus = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", mp, "-t", f"{DUR + 0.5:.2f}", "-f", "f32le", "-ac", "2", "-ar", str(R), "-"], capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
mus = np.pad(mus, ((0, max(0, NS - len(mus))), (0, 0)))[:NS]; tt = np.arange(NS)/R
mus *= (10**(-17/20)*np.clip(tt/0.4, 0, 1)*np.clip((DUR + 0.3 - tt)/1.2, 0, 1))[:, None]
sfx = np.zeros((NS, 2), np.float32)
for i, b in enumerate(beats[:-1]):
    nb = beats[i + 1]
    if not (b["scene"]["kind"] == "phone" and nb["scene"]["kind"] == "phone"): fx.place_sfx(sfx, "whoosh-fast-soft", b["t1"] - TR*0.5, -13, speech, R)
for b in beats:
    sc = b["scene"]
    if sc["kind"] == "icons":
        for tw in word_times(b, [lab.split(" ")[0] for _, lab in sc["items"]]): fx.place_sfx(sfx, "pop-small-in", tw - 0.08, -16, speech, R)
    if sc["kind"] == "phone":
        off = 0.0
        for n, s, e in sc["rec"]:
            for ev in clip(n).meta["events"]:
                if ev["kind"] == "tap" and s <= ev["t"] < e:
                    tv = b["t0"] + (off + ev["t"] - s)/b["spd"]
                    if tv < b["t1"]: fx.place_sfx(sfx, "click-tap-soft", tv, -13, speech, R)
            if n == "find_claim" and s <= 14.0 < e:
                tv = b["t0"] + (off + 14.0 - s)/b["spd"]
                if tv < b["t1"]: fx.place_sfx(sfx, "money-coin-drop", tv, -15, speech, R)
            off += e - s
    if sc["kind"] == "logo" and sc.get("url"): fx.place_sfx(sfx, "sting-minimal-short", b["t0"] + 0.05, -9, speech, R)
def wr(path, x, ch):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", str(ch), "-ar", str(R), "-i", "-", "-c:a", "pcm_f32le", path], stdin=subprocess.PIPE); p.stdin.write(x.astype(np.float32).tobytes()); p.stdin.close(); p.wait()
tmp = os.path.join(L, "tmp", f"{NAME}_{FMT}"); os.makedirs(tmp, exist_ok=True)
wr(f"{tmp}/v.wav", vo, 1); wr(f"{tmp}/m.wav", mus, 2); wr(f"{tmp}/s.wav", sfx, 2)
raw = f"{tmp}/raw.mp4"
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", raw], stdin=subprocess.PIPE)
for n in range(N):
    ff.stdin.write(np.clip(frame_at(n/FPS) + 0.5, 0, 255).astype(np.uint8).tobytes())
    if n % 300 == 0: print(NAME, FMT, n, "/", N, flush=True)
ff.stdin.close(); ff.wait()
out = os.path.join(S, "final/launch"); os.makedirs(out, exist_ok=True); OUT = os.path.join(out, f"Bounti-Launch-{NAME}-{'9x16' if VERT else '16x9'}.mp4")
FG = ("[1]acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120:makeup=2,asplit[v][k];[2][k]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=380[md];"
      "[v][md][3]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", f"{tmp}/v.wav", "-i", f"{tmp}/m.wav", "-i", f"{tmp}/s.wav", "-filter_complex", FG, "-map", "0:v", "-map", "[a]",
                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("DONE", OUT, "%.1fs" % DUR)
