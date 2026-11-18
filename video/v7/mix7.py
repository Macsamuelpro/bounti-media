"""usage: mix7.py <raw.mp4> <out.mp4> <track> <music_db>"""
import sys, os, json, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import fx
RAWV, OUTV, TRACK, MDB = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
meta = json.load(open(RAWV + ".json")); E = json.load(open(os.path.join(HERE, "edit7.json"))); R = 48000
DUR = meta["duration"]; MAIN = meta["main"]; N = int(DUR*R) + R; tt = np.arange(N)/R
def rd(p, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", p, "-f", "f32le", "-ac", "2", "-ar", str(R), "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); return np.pad(x, ((0, max(0, N - len(x))), (0, 0)))[:N]
def wr(name, x):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(R), "-i", "-", "-c:a", "pcm_f32le", name], stdin=subprocess.PIPE)
    p.stdin.write(x.astype(np.float32).tobytes()); p.stdin.close(); p.wait()
voice = rd(os.path.join(HERE, "voice.wav"), 0, DUR + 1)
speech = [(g["t0"] + g["a"] - g["s0"], g["t0"] + g["b"] - g["s0"]) for g in E["segs"]]
mus = rd(TRACK, 0, DUR + 1)*10**(MDB/20); mus *= (np.clip(tt/1.5, 0, 1)*np.clip((DUR - tt)/2.0, 0, 1))[:, None]
sfx = np.zeros((N, 2), np.float32)
for name, a, b in meta["scenes"]:
    if a > 0.05: fx.place_sfx(sfx, "whoosh-fast-soft", a, -10, speech, R)
    if name in ("bounti",): fx.place_sfx(sfx, "boom-hit-soft", a + 0.05, -6, speech, R)
    if name in ("crowd", "empty_store", "spread", "pillars"): fx.place_sfx(sfx, "pop-small-in", a + 0.3, -9, speech, R)
fx.place_sfx(sfx, "pop-medium-in", 0.55, -8, speech, R)                       # "poof"
for name, t0 in meta.get("cards", []): fx.place_sfx(sfx, "pop-small-in", t0 + 0.02, -9, speech, R)
fx.place_sfx(sfx, "sting-minimal-short", MAIN + 0.2, -6, speech, R)
D = os.path.dirname(OUTV); wr(os.path.join(D, "_v.wav"), voice); wr(os.path.join(D, "_m.wav"), mus); wr(os.path.join(D, "_s.wav"), sfx)
FG = ("[0]acompressor=threshold=-22dB:ratio=2.5:attack=6:release=120:makeup=2,deesser=i=0.3,asplit[v][k];"
      "[1][k]sidechaincompress=threshold=0.03:ratio=4:attack=25:release=450:knee=6[md];[v][md][2]amix=inputs=3:normalize=0:duration=first,"
      "loudnorm=I=-14:TP=-1.5:LRA=11")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", RAWV, "-i", os.path.join(D, "_v.wav"), "-i", os.path.join(D, "_m.wav"), "-i", os.path.join(D, "_s.wav"),
                "-filter_complex", FG.replace("[0]", "[1]").replace("[1][k]", "[2][k]").replace("[v][md][2]", "[v][md][3]"), "-map", "0:v",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                "-shortest", "-movflags", "+faststart", OUTV], check=True)
print(subprocess.run(["ffmpeg", "-hide_banner", "-i", OUTV, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr.split("Summary:")[-1].strip().replace("\n", " ")[:220])
