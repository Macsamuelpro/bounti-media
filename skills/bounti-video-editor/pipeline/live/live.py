"""Turn a live prototype recording (rec/<name>/meta.json, real-time screencast frames) into
rec/<name>.mp4 at 24 fps: cropped to the design's phone frame, with touch rings at real taps.
Also writes rec/frame_mask.png (rounded phone outline alpha). usage: live.py name [name...]"""
import json, sys, subprocess, os, bisect
import numpy as np
from PIL import Image, ImageDraw
FPS = 24
def ring(img, x, y, age):
    # iOS-style touch indicator: soft filled dot while pressed, then an expanding fading ring
    d = ImageDraw.Draw(img, "RGBA")
    if age < 0.16:
        r = 30; d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 120), outline=(20, 20, 20, 90), width=3)
    if age < 0.5:
        k = age / 0.5; r = 30 + 34 * k; a = int(150 * (1 - k))
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, a), width=5)
def build(name):
    m = json.load(open(f"rec/{name}/meta.json")); F = m["frames"]; cx, cy, cw, ch = m["crop"]
    ts = [f[0] for f in F]; end = max(m.get("end", ts[-1]), ts[-1]) + 0.2
    taps = [e for e in m["events"] if e["kind"] == "tap"]; swipes = [e for e in m["events"] if e["kind"] == "swipe" and "ms" not in e]
    n = int(end * FPS); out = f"rec/{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cw}x{ch}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "11", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    cache = {}
    for k in range(n):
        t = k / FPS; i = max(bisect.bisect_right(ts, t) - 1, 0); fn = F[i][1]
        if fn not in cache: cache.clear(); cache[fn] = Image.open(fn).convert("RGB").crop((cx, cy, cx + cw, cy + ch))
        im = cache[fn].copy()
        for e in taps:
            age = t - e["t"]
            if 0 <= age < 0.5: ring(im, e["x"] - cx, e["y"] - cy, age)
        for e in swipes:
            age = t - e["t"] + 0.28  # finger lands just before the flick registers
            if 0 <= age < 0.45:
                k = min(age / 0.3, 1.0); k = 1 - (1 - k) ** 2; yy = e["y"] - cy - 340 * k; a = int(140 * (1 - max(age - 0.3, 0) / 0.15))
                ImageDraw.Draw(im, "RGBA").ellipse([e["x"] - cx - 30, yy - 30, e["x"] - cx + 30, yy + 30], fill=(255, 255, 255, a // 1), outline=(20, 20, 20, a // 2), width=3)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait(); print(name, f"{n} frames {n/FPS:.1f}s", (cw, ch))
    if not os.path.exists("rec/frame_mask.png"):
        # alpha of the phone silhouette: everything not equal to the page background
        im = np.asarray(Image.open(F[0][1]).convert("RGB").crop((cx, cy, cx + cw, cy + ch))).astype(int)
        bg = np.array([0xe7, 0xe5, 0xe0]); diff = np.abs(im - bg).sum(2)
        Image.fromarray(((diff > 18) * 255).astype(np.uint8)).save("rec/frame_mask_raw.png")
for nm in sys.argv[1:]: build(nm)
