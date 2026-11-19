"""Podcast-card style (learned from Mac's L8 reference): talking head intercut with warm cream cards.
- shrink_to_tile: the speaker frame scales into a rounded card with a soft shadow on cream
- letter_reveal: a keyword types in letter by letter with a small bounce (big word + small sub word)
- fog_dissolve: soft blurred dissolve between card states (no hard wipe)
- orbit_pop: small round avatars/icons pop in around the tile
- two_size_caption: small lead word + big key word for the back-on-camera moments
All functions draw onto float32 BGR frames."""
import math
import numpy as np, cv2
CREAM = np.array((230, 246, 252), np.float32)          # BGR of #FCF6E6
def _ease(t): t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def _spring(u, d=0.35):
    if u <= 0: return 0.0
    u = min(u/d, 1.0); return 1 - math.exp(-6*u)*math.cos(u*math.pi*2.2) if u < 1 else 1.0
def rounded_mask(h, w, r):
    m = np.zeros((h, w), np.float32)
    cv2.rectangle(m, (r, 0), (w - r, h), 1.0, -1); cv2.rectangle(m, (0, r), (w, h - r), 1.0, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 1.0, -1, cv2.LINE_AA)
    return m
def shrink_to_tile(frame, k, tile=(0.5, 0.36, 0.42), bg=CREAM, radius=42):
    """k 0 = full frame, 1 = tile. tile = (centre x frac, centre y frac, width frac). Returns a new frame."""
    H, W = frame.shape[:2]; e = _ease(k)
    tw = W*(1 - (1 - tile[2])*e); th = tw*H/W; cx = W*(0.5 + (tile[0] - 0.5)*e); cy = H*(0.5 + (tile[1] - 0.5)*e)
    out = np.empty_like(frame); out[:] = bg if e > 0 else frame
    if e <= 0: return frame.copy()
    small = cv2.resize(frame, (max(int(tw), 2), max(int(th), 2)), interpolation=cv2.INTER_AREA)
    r = int(radius*e) + 1; m = rounded_mask(small.shape[0], small.shape[1], r)
    x0, y0 = int(cx - small.shape[1]/2), int(cy - small.shape[0]/2)
    sh = np.zeros((H, W), np.float32); cv2.rectangle(sh, (x0 + 10, y0 + 24), (x0 + small.shape[1] - 10, y0 + small.shape[0] + 24), 1.0, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 30)*0.28*e; out *= (1 - sh[..., None])
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + small.shape[1], W), min(y0 + small.shape[0], H)
    sm = small[ya - y0:yb - y0, xa - x0:xb - x0]; mm = m[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb]*(1 - mm) + sm*mm
    if e < 1: out = frame*(1 - e) + out*e if e < 0.15 else out
    return out
def letter_reveal(frame, word, font_draw, t, cx, cy, per=0.055, col=(204, 196, 186)):
    """font_draw(text, colour) -> RGBA (RGB order) image of the text. Letters rise in one by one."""
    import fx
    imgs = [font_draw(c, col) for c in word]; widths = [im.shape[1]*0.86 for im in imgs]; x = cx - sum(widths)/2
    for i, (im, w) in enumerate(zip(imgs, widths)):
        k = _spring(t - i*per, 0.3)
        if k > 0: fx.composite(frame, im, x + w/2, cy + 40*(1 - min(k, 1)), 0.7 + 0.3*k, min(1, k*1.6))
        x += w
def fog_dissolve(a, b, k):
    """soft dissolve through blur: a blurs out while b sharpens in"""
    e = _ease(k); s = 1 + 28*math.sin(e*math.pi)
    ab = cv2.GaussianBlur(a, (0, 0), s); bb = cv2.GaussianBlur(b, (0, 0), s)
    return ab*(1 - e) + bb*e
def orbit_pop(frame, imgs, t, cx, cy, rx, ry, t0=0.0, gap=0.18):
    """pop small round images around a centre on an ellipse, one after another, with a gentle drift"""
    import fx
    n = len(imgs)
    for i, im in enumerate(imgs):
        a = -math.pi/2 + i*2*math.pi/n + 0.15*math.sin(t*0.8 + i); k = _spring(t - t0 - i*gap, 0.32)
        if k > 0: fx.composite(frame, im, cx + rx*math.cos(a), cy + ry*math.sin(a), k, min(1, k*1.5))
def two_size_caption(frame, lead_img, key_img, cx, cy, t, t0):
    """small lead word above, big key word below (key word bounces in after the lead)"""
    import fx
    k1 = _spring(t - t0, 0.3); k2 = _spring(t - t0 - 0.12, 0.35)
    if k1 > 0: fx.composite(frame, lead_img, cx - key_img.shape[1]*0.18, cy - key_img.shape[0]*0.62, k1, min(1, k1*1.5))
    if k2 > 0: fx.composite(frame, key_img, cx, cy, 0.8 + 0.2*k2, min(1, k2*1.5))
