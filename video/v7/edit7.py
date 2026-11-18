"""Shared edit map for the Bounti crowd video: pieces, pacing, joins, clean dialogue audio, word timings."""
import json, subprocess, os, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); FPS = 24; R = 48000
P = json.load(open(os.path.join(HERE, "pieces.json")))
FIX = {"bounty": "Bounti", "Bounty": "Bounti", "partners.earnbouncy.com": "partners.earnbounti.com", "the police": "the place",
       "We've got crowd": "We've got crowd", "your creator": "you're a creator", "poof": "Poof."}
DROP = {("b01", 1.15), ("b01", 6.84)}                    # AI whoosh effects, not speech
# extra pause BEFORE pieces that start a new idea (seconds of breathing room)
NEW_IDEA = ("You've got", "You've launched", "Or maybe", "Now", "Think about", "Imagine", "and if you've got", "What if",
            "Sometimes", "Okay", "It's called", "and the beautiful", "If you're in", "Let's", "Please", "Opening day", "Wait")
def fix(t):
    for a, b in FIX.items(): t = t.replace(a, b)
    return t.strip()
pieces = []
for c in sorted(P):
    for a, b, t in P[c]["pieces"]:
        if (c, a) in DROP or not t or t.startswith("("): continue
        pieces.append(dict(c=c, a=a, b=b, txt=fix(t)))
PRE, POST = 0.05, 0.08
t = 0.0; segs = []; carry = 0.0
for i, p in enumerate(pieces):
    nxt = pieces[i + 1] if i + 1 < len(pieces) else None
    end = p["txt"].rstrip()[-1:] in ".?!"
    gap = 0.12
    if end: gap = 0.30
    if nxt and any(nxt["txt"].lower().startswith(k.lower()) for k in NEW_IDEA): gap = max(gap, 0.55)
    if nxt and nxt["txt"].startswith("Wait"): gap = 0.40
    if p["txt"].startswith("Poof"): gap = 0.35
    if nxt is None: gap = 0.6
    s0 = p["a"] - PRE - carry; s1 = p["b"] + POST
    if s0 < 0: lost = -s0; s0 = 0.0
    else: lost = 0.0
    if lost and segs: segs[-1]["hold"] = round(segs[-1]["hold"] + 0, 3)
    carry = 0.0
    hold = 0.0
    avail = (nxt["a"] - PRE - s1) if (nxt and nxt["c"] == p["c"]) else 9.9
    clip_end = P[p["c"]].get("dur", 8.04) - 0.05
    extra = min(gap, avail if avail > 0 else 0, clip_end - s1)          # natural room/picture after the line
    s1 += max(extra, 0); hold = max(gap - max(extra, 0), 0)            # shortfall: take it from the next take's lead-in
    if hold > 0 and nxt and nxt["c"] != p["c"] and nxt["a"] - PRE - hold >= 0: carry = hold; hold = 0.0
    segs.append(dict(c=p["c"], s0=round(s0, 3), s1=round(s1, 3), t0=round(t, 3), a=p["a"], b=p["b"], hold=round(hold, 3), txt=p["txt"]))
    t += (s1 - s0) + hold
DUR = t
# word timings (character-weighted inside each spoken piece)
words = []
for g in segs:
    ws = g["txt"].split(); wl = np.array([len(w) + 1.5 for w in ws]); e = np.concatenate([[0], np.cumsum(wl)])/wl.sum()*(g["b"] - g["a"])
    for w, a, b in zip(ws, e[:-1], e[1:]):
        words.append(dict(w=w, t0=round(g["t0"] + (g["a"] - g["s0"]) + a, 3), t1=round(g["t0"] + (g["a"] - g["s0"]) + b, 3)))
json.dump(dict(fps=FPS, duration=DUR, segs=segs, words=words), open(os.path.join(HERE, "edit7.json"), "w"), indent=1)
print("pieces", len(segs), "duration %.2f" % DUR)

# ---------------- clean dialogue ----------------
if __name__ == "__main__" and os.environ.get("AUDIO", "1") == "1":
    BD = os.path.join(os.path.dirname(HERE), "lib/rnn/rnnoise-models/beguiling-drafter-2018-08-30/bd.rnnn")
    CLEAN = ("highpass=f=80,bandreject=f=100:width_type=q:w=8,bandreject=f=200:width_type=q:w=8,bandreject=f=300:width_type=q:w=8,"
             f"arnndn=m={BD}:mix=0.95,equalizer=f=220:t=q:w=1:g=-1.2,equalizer=f=3200:t=q:w=1.3:g=1.5")
    os.makedirs(os.path.join(HERE, "clean"), exist_ok=True)
    for c in sorted({g["c"] for g in segs}):
        out = os.path.join(HERE, f"clean/{c}.wav")
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, f"src/{c}.mp4"), "-vn", "-af", CLEAN, "-ac", "1", "-ar", str(R), out])
    def read(c, a, b):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(a,0):.4f}", "-t", f"{b-max(a,0):.4f}", "-i", os.path.join(HERE, f"clean/{c}.wav"),
                              "-f", "f32le", "-ac", "1", "-ar", str(R), "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.float32).copy()
    gains = {}
    for c in sorted({g["c"] for g in segs}):
        x = np.concatenate([read(c, g["a"], g["b"]) for g in segs if g["c"] == c])
        p = subprocess.Popen(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "1", "-ar", str(R), "-i", "-", "-af", "ebur128", "-f", "null", "-"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = p.communicate(x.tobytes()); gains[c] = 10**((-19 - float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", err.decode())[-1]))/20)
    N = int((DUR + 1)*R); v = np.zeros(N, np.float32)
    for g in segs:
        x = read(g["c"], g["s0"], g["s1"])*gains[g["c"]]; n = len(x); f = np.ones(n, np.float32); k = min(int(0.012*R), n//2)
        if k: f[:k] = np.linspace(0, 1, k); f[-k:] = np.linspace(1, 0, k)
        s = int(round(g["t0"]*R)); v[s:s + n] += (x*f)[:max(0, min(n, N - s))]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "1", "-ar", str(R), "-i", "-", "-c:a", "pcm_f32le", os.path.join(HERE, "voice.wav")], stdin=subprocess.PIPE)
    p.stdin.write(v.tobytes()); p.stdin.close(); p.wait()
    print("gains dB", {c: round(20*np.log10(x), 1) for c, x in gains.items()})
