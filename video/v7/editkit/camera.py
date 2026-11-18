"""Virtual camera moves for locked-off or AI footage. move(frame, u, **p) where u in [0,1] across the move.
All moves are crop-based (no black borders) and can be stacked with combine()."""
import math
import numpy as np, cv2

def _s(t): t = min(max(t, 0.0), 1.0); return t*t*(3 - 2*t)
def _io(t): t = min(max(t, 0.0), 1.0); return 4*t**3 if t < 0.5 else 1 - (-2*t + 2)**3/2
def _out(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t)**3
EASE = {"smooth": _s, "inout": _io, "out": _out, "linear": lambda t: min(max(t, 0.0), 1.0)}

def M_zoom(z, cx, cy): return np.array([[z, 0, cx*(1 - z)], [0, z, cy*(1 - z)], [0, 0, 1]], np.float64)
def M_shift(dx, dy): return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], np.float64)
def M_rot(deg, cx, cy): R = cv2.getRotationMatrix2D((cx, cy), deg, 1.0); return np.vstack([R, [0, 0, 1]])
def render(frame, M, perspective=None):
    h, w = frame.shape[:2]
    if perspective is not None: return cv2.warpPerspective(frame, perspective @ M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return cv2.warpAffine(frame, M[:2], (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def _noise1d(t, seed, freq):
    rng = np.random.default_rng(seed); k = rng.random(64)*2 - 1; x = t*freq; i = int(math.floor(x)) % 63; f = x - math.floor(x)
    f = f*f*(3 - 2*f); return k[i]*(1 - f) + k[i + 1]*f

# each returns a 3x3 matrix for frame size (w,h) at progress u (or absolute time t for continuous moves)
def push_in(w, h, u, amount=0.12, cx=0.5, cy=0.4, ease="smooth"): return M_zoom(1 + amount*EASE[ease](u), w*cx, h*cy)
def pull_out(w, h, u, amount=0.12, cx=0.5, cy=0.4, ease="smooth"): return M_zoom(1 + amount*(1 - EASE[ease](u)), w*cx, h*cy)
def crash_zoom(w, h, u, amount=0.45, cx=0.5, cy=0.38): return M_zoom(1 + amount*_out(min(u/0.18, 1)), w*cx, h*cy)
def pan(w, h, u, direction=1, amount=0.10, zoom=1.12, ease="inout"):
    z = M_zoom(zoom, w/2, h/2); span = w*(zoom - 1)/2*amount/0.06 if amount else 0
    return M_shift(-direction*(EASE[ease](u) - 0.5)*min(span, w*(zoom - 1)/2*0.95), 0) @ z
def tilt(w, h, u, direction=1, zoom=1.12, ease="inout"):
    z = M_zoom(zoom, w/2, h/2); r = h*(zoom - 1)/2*0.95; return M_shift(0, -direction*(EASE[ease](u) - 0.5)*2*r) @ z
truck = pan; pedestal = tilt
def ken_burns(w, h, u, z0=1.0, z1=1.15, start=(0.5, 0.5), end=(0.45, 0.35)):
    k = _s(u); z = z0 + (z1 - z0)*k; cx = (start[0] + (end[0] - start[0])*k)*w; cy = (start[1] + (end[1] - start[1])*k)*h
    return M_zoom(z, cx, cy)
def drift(w, h, t, speed=0.6, amp=0.012, zoom=1.04, seed=3):
    dx = _noise1d(t, seed, speed)*w*amp; dy = _noise1d(t, seed + 1, speed)*h*amp; return M_shift(dx, dy) @ M_zoom(zoom, w/2, h/2)
def handheld(w, h, t, intensity=1.0, seed=7, zoom=1.06):
    """Organic handheld: low-frequency sway + small high-frequency jitter + slight roll."""
    s = intensity; dx = (_noise1d(t, seed, 0.7)*0.010 + _noise1d(t, seed + 2, 6)*0.0015)*w*s
    dy = (_noise1d(t, seed + 1, 0.6)*0.008 + _noise1d(t, seed + 3, 7)*0.0015)*h*s; r = _noise1d(t, seed + 4, 0.5)*0.6*s
    return M_rot(r, w/2, h/2) @ M_shift(dx, dy) @ M_zoom(zoom, w/2, h/2)
def impact_shake(w, h, t, t0, amp=0.02, decay=6.0, seed=9, zoom=1.06):
    if t < t0: return M_zoom(zoom, w/2, h/2)
    e = math.exp(-(t - t0)*decay); rng = np.random.default_rng(seed + int((t - t0)*60))
    return M_shift(rng.normal()*w*amp*e, rng.normal()*h*amp*e) @ M_zoom(zoom, w/2, h/2)
def dutch_roll(w, h, u, degrees=4, zoom=1.12): return M_rot(degrees*_s(u), w/2, h/2) @ M_zoom(zoom, w/2, h/2)
def whip(w, h, u, direction=1, zoom=1.0): return M_shift(-direction*w*_io(u), 0) @ M_zoom(zoom, w/2, h/2)
def step_punch(w, h, t, beats, amounts=(1.0, 1.12), cx=0.5, cy=0.38):
    """Punch-in on beats/emphasis: alternate framing at each beat time (cut-zoom, no easing)."""
    i = int(np.searchsorted(np.array(beats), t, side="right")); return M_zoom(amounts[i % len(amounts)], w*cx, h*cy)
def arc(w, h, u, degrees=6, zoom=1.15):
    """Simulated arc/orbit: horizontal perspective swing + counter-pan."""
    k = (_io(u) - 0.5)*2; a = math.radians(degrees*k); f = w*1.2
    P = np.array([[math.cos(a), 0, w/2*(1 - math.cos(a))], [0, 1, 0], [-math.sin(a)/f, 0, 1 + math.sin(a)*w/2/f]], np.float64)
    return P @ M_zoom(zoom, w/2, h/2)

def dolly_zoom(frame, mask, u, amount=0.18, cx=0.5, cy=0.42):
    """Vertigo: subject (mask) holds size while the background scales the opposite way."""
    h, w = frame.shape[:2]; k = _io(u)
    bg = render(frame, M_zoom(1 + amount*k, w*cx, h*cy)); m = mask[..., None] if mask.ndim == 2 else mask
    return bg*(1 - m) + frame*m
def follow_face(w, h, face_xy, zoom=1.25, smooth_state=None, alpha=0.15):
    """Auto-reframe that tracks a face with smoothing (call per frame with detector output)."""
    fx, fy = face_xy
    if smooth_state is not None:
        fx = smooth_state[0]*(1 - alpha) + fx*alpha; fy = smooth_state[1]*(1 - alpha) + fy*alpha
    return M_zoom(zoom, fx, fy - h*0.08), (fx, fy)
def combine(*Ms):
    out = np.eye(3)
    for M in Ms: out = M @ out
    return out

def speed_ramp_times(a, b, zones, fps=24, ramp=0.3):
    """Source times for a speed-ramped segment: zones (z0, z1, speed) with eased ramps (speed <1 = slow-mo)."""
    def v(s):
        out = 1.0
        for z0, z1, vm in zones:
            if z0 - ramp <= s <= z1 + ramp:
                k = min(_s((s - (z0 - ramp))/ramp), _s(((z1 + ramp) - s)/ramp)); out = out + (vm - 1)*k
        return max(out, 0.05)
    ts, s = [], a
    while s < b - 1e-6: ts.append(s); s += v(s)/fps
    return ts
def freeze_frame(t, at, hold): return at if at <= t < at + hold else (t - hold if t >= at + hold else t)

MOVES = ["push_in", "pull_out", "crash_zoom", "pan", "tilt", "truck", "pedestal", "ken_burns", "drift", "handheld", "impact_shake",
         "dutch_roll", "whip", "step_punch", "arc", "dolly_zoom", "follow_face", "speed_ramp", "freeze_frame"]
