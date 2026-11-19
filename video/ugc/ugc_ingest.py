import os, glob, subprocess, sys
U = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ugc")
for d in sorted(os.listdir(U)):
    P = os.path.join(U, d)
    if not os.path.isdir(P) or not d.startswith("UGC"): continue
    src = os.path.join(P, "src"); wav = os.path.join(P, "wav")
    for x in glob.glob(os.path.join(src, "*")) + glob.glob(os.path.join(wav, "*")): os.remove(x)
    os.makedirs(src, exist_ok=True); os.makedirs(wav, exist_ok=True)
    clips = [f for f in glob.glob(os.path.join(P, "**", "*.mp4"), recursive=True) if "/src/" not in f]
    clips.sort(key=lambda f: int(os.path.basename(f).rsplit("_", 1)[1].split(".")[0]))
    durs = []
    for i, f in enumerate(clips, 1):
        os.symlink(f, os.path.join(src, f"c{i}.mp4"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", os.path.join(wav, f"c{i}.wav")])
        durs.append(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip())
    print(d, len(clips), "clips", durs)
