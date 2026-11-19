"""Build short cuts from the line list in edit7.json. usage: shorts.py <name>   -> cuts/<name>.json + cuts/<name>_voice.wav"""
import json, os, sys, subprocess, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); R = 48000
FULL = json.load(open(os.path.join(HERE, "edit7.json")))["segs"]
CTA = [65, 66, 67, 80, 81]
CUTS = {
 "1-budget":   [0, 1, 2, 3, 4, 5, 6, 7, 12, 13, 14, 63, 64, 65, 66, 67, 71, 72, 73, 74, 75, 80, 81],
 "2-opening":  [21, 22, 23, 24, 25, 26, 27, 28, 29, 33, 48, 49, 50, 51, 52, 53, 54, 63, 64, 65, 66, 67, 71, 72, 73, 80, 81],
 "3-viral":    [43, 44, 45, 46, 35, 36, 37, 38, 39, 40, 41, 42, 63, 64, 65, 66, 67, 68, 69, 70, 80, 81],
 "4-web-apps": [12, 13, 14, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 71, 72, 73, 80, 81],
 "5-partners": [0, 1, 2, 12, 13, 14, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81],
}
TXT = {3: "Every month,", 4: "money goes into ads.", 7: "where are the customers?", 22: "Beautiful interior,", 23: "products arranged, everything looking perfect.",
 25: "And it's just you,", 26: "two staff members", 27: "and your cousin who came to support you.", 36: "What if you could get thousands of people", 37: "helping you spread the word?",
 38: "People watching your content,", 39: "sharing your links,", 40: "engaging with your brand,", 48: "Imagine people already walking in,", 49: "checking out your products,",
 50: "taking pictures", 51: "and talking about the place.", 52: "Now someone passing by sees all that activity and thinks,", 56: "Imagine thousands of people sharing that link,",
 57: "sending it to their friends", 58: "and getting more people to check it out.", 59: "And if you've got a really good app or game,", 60: "you can get people through the door,",
 61: "playing, exploring", 62: "and discovering what makes it worth coming back to.", 66: "We've got crowd marketing,", 67: "trend marketing and compound affiliate marketing.",
 68: "Basically, you get the power of a crowd,", 69: "the momentum of trends", 70: "and the reach of an affiliate network working around your campaign.", 71: "And the beautiful part?",
 72: "You decide what actions matter to your business,", 73: "and you spend on getting those actions.", 74: "Not just sitting around celebrating impressions", 75: "while your sales department is having a crisis.",
 80: "Head over to partners.earnbounti.com.", 44: "Well, you need people to start watching, engaging and sharing."}
NEW_IDEA = ("You've got", "You've launched", "Now", "Think about", "Imagine", "and if you've got", "What if", "Sometimes", "Okay",
            "It's called", "and the beautiful", "If you're in", "Let's", "Please", "Opening day", "Wait", "head over")
def build(name):
    idx = CUTS[name]; pieces = [dict(FULL[i]) for i in idx]
    for i, p in zip(idx, pieces): p["txt"] = TXT.get(i, p["txt"])
    PRE, POST = 0.05, 0.08; t = 0.0; segs = []; carry = 0.0
    for i, p in enumerate(pieces):
        nxt = pieces[i + 1] if i + 1 < len(pieces) else None
        end = p["txt"].rstrip()[-1:] in ".?!"; gap = 0.30 if end else 0.12
        if nxt and any(nxt["txt"].lower().startswith(k.lower()) for k in NEW_IDEA): gap = max(gap, 0.50)
        if nxt and nxt["txt"].startswith("Wait"): gap = 0.40
        if p["txt"].startswith("Poof"): gap = 0.35
        if nxt is None: gap = 0.6
        s0 = max(p["a"] - PRE - carry, 0.0); carry = 0.0; s1 = p["b"] + POST
        contiguous = nxt is not None and nxt["c"] == p["c"] and nxt["a"] > p["b"]
        avail = (nxt["a"] - PRE - s1) if contiguous else 9.9
        clip_end = 8.0 if p["c"] not in ("b12", "b13", "b18", "b25") else 10.0
        extra = max(min(gap, avail if avail > 0 else 0, clip_end - 0.05 - s1), 0); s1 += extra; hold = max(gap - extra, 0)
        if hold > 0 and nxt and not contiguous and nxt["a"] - PRE - hold >= 0: carry = hold; hold = 0.0
        segs.append(dict(c=p["c"], s0=round(s0, 3), s1=round(s1, 3), t0=round(t, 3), a=p["a"], b=p["b"], hold=round(hold, 3), txt=p["txt"]))
        t += (s1 - s0) + hold
    ws = []
    for g in segs:
        w = g["txt"].split(); wl = np.array([len(x) + 1.5 for x in w]); e = np.concatenate([[0], np.cumsum(wl)])/wl.sum()*(g["b"] - g["a"])
        for x, a, b in zip(w, e[:-1], e[1:]): ws.append(dict(w=x, t0=round(g["t0"] + g["a"] - g["s0"] + a, 3), t1=round(g["t0"] + g["a"] - g["s0"] + b, 3)))
    os.makedirs(os.path.join(HERE, "cuts"), exist_ok=True)
    js = os.path.join(HERE, f"cuts/{name}.json"); json.dump(dict(fps=24, duration=t, segs=segs, words=ws), open(js, "w"), indent=1)
    # voice (reuse cleaned clips, same per-clip gains as the full edit)
    def read(c, a, b):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(a,0):.4f}", "-t", f"{b-max(a,0):.4f}", "-i", os.path.join(HERE, f"clean/{c}.wav"),
                              "-f", "f32le", "-ac", "1", "-ar", str(R), "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.float32).copy()
    gains = {}
    for c in sorted({g["c"] for g in FULL}):
        x = np.concatenate([read(c, g["a"], g["b"]) for g in FULL if g["c"] == c])
        p = subprocess.Popen(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "1", "-ar", str(R), "-i", "-", "-af", "ebur128", "-f", "null", "-"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = p.communicate(x.tobytes()); gains[c] = 10**((-19 - float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", err.decode())[-1]))/20)
    N = int((t + 1)*R); v = np.zeros(N, np.float32)
    for g in segs:
        x = read(g["c"], g["s0"], g["s1"])*gains[g["c"]]; n = len(x); f = np.ones(n, np.float32); k = min(int(0.012*R), n//2)
        if k: f[:k] = np.linspace(0, 1, k); f[-k:] = np.linspace(1, 0, k)
        s = int(round(g["t0"]*R)); v[s:s + n] += (x*f)[:max(0, min(n, N - s))]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "1", "-ar", str(R), "-i", "-", "-c:a", "pcm_f32le", os.path.join(HERE, f"cuts/{name}_voice.wav")], stdin=subprocess.PIPE)
    p.stdin.write(v.tobytes()); p.stdin.close(); p.wait()
    print(name, "%.1fs" % t); print("   " + " ".join(g["txt"] for g in segs))
for n in (sys.argv[1:] or CUTS): build(n)
