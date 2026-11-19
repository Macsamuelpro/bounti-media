"""Minimal 3D device helpers (perspective phone plane with shadow), shared by UGC v2 styles."""
import math, numpy as np, cv2
OW, OH = 1080, 1920; FOC = 2.2*1080
def rot(yaw, pitch, roll):
    y, p, r = map(math.radians, (yaw, pitch, roll))
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]]); Rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]]); return Ry @ Rx @ Rz
def project(P, pose):
    Q = (P*pose.get("s", 1)) @ rot(pose.get("yaw", 0), pose.get("pitch", 0), pose.get("roll", 0)).T; z = Q[:, 2] + pose.get("z", 0) + FOC
    return np.stack([pose["x"] + Q[:, 0]*FOC/z, pose["y"] + Q[:, 1]*FOC/z], 1)
def rrect(h, w, r):
    m = np.zeros((h, w), np.float32); cv2.rectangle(m, (r, 0), (w - r, h), 1, -1); cv2.rectangle(m, (0, r), (w, h - r), 1, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 1, -1, cv2.LINE_AA)
    return m
def phone_tex(fr, PW=430):
    PH = int(PW*1864/860); bz = 14; r = 62; W, H = PW + 2*bz, PH + 2*bz; t = np.zeros((H, W, 4), np.float32); o = rrect(H, W, r + bz)
    t[..., :3] = 18; t[..., 3] = o*255; e = o - cv2.erode(o, np.ones((5, 5), np.uint8)); t[..., :3] += e[..., None]*70
    sm = rrect(PH, PW, r)[..., None]; reg = t[bz:bz + PH, bz:bz + PW, :3]; reg[:] = reg*(1 - sm) + cv2.resize(fr, (PW, PH), interpolation=cv2.INTER_AREA).astype(np.float32)*sm
    return t
def warp(canvas, tex, q, alpha=1.0):
    h, w = tex.shape[:2]; H, W = canvas.shape[:2]; x0, y0 = np.floor(q.min(0)).astype(int) - 2; x1, y1 = np.ceil(q.max(0)).astype(int) + 2
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if xa >= xb or ya >= yb: return
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(q - [xa, ya]))
    o = cv2.warpPerspective(tex, M, (xb - xa, yb - ya), borderValue=(0, 0, 0, 0)); a = o[..., 3:4]/255*alpha; reg = canvas[ya:yb, xa:xb]; reg[:] = reg*(1 - a) + o[..., :3]*a
def shadow(canvas, q, k=0.35, blur=38, dy=34):
    H, W = canvas.shape[:2]; q = q.copy(); q[:, 1] += dy; x0, y0 = np.floor(q.min(0)).astype(int) - 3*blur; x1, y1 = np.ceil(q.max(0)).astype(int) + 3*blur
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if xa >= xb or ya >= yb: return
    m = np.zeros((yb - ya, xb - xa), np.float32); cv2.fillConvexPoly(m, np.int32(q - [xa, ya]), 1.0, cv2.LINE_AA); m = cv2.GaussianBlur(m, (0, 0), blur)*k
    canvas[ya:yb, xa:xb] *= (1 - m[..., None])
def phone3d(canvas, fr, pose, alpha=1.0):
    tex = phone_tex(fr); h, w = tex.shape[:2]; P = np.array([[-w/2, -h/2, 0], [w/2, -h/2, 0], [w/2, h/2, 0], [-w/2, h/2, 0]], np.float32)
    q = project(P, pose); shadow(canvas, q); warp(canvas, tex, q, alpha); return q
