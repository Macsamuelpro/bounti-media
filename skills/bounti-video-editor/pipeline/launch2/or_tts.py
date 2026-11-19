"""Directed voiceover through OpenRouter openai/gpt-audio (streamed pcm16 24 kHz).
usage: or_tts.py out.wav voice "direction" "script" """
import sys, json, base64, wave, urllib.request
out, voice, direction, script = sys.argv[1:5]
body = {"model": sys.argv[5] if len(sys.argv) > 5 else "openai/gpt-audio", "modalities": ["text", "audio"], "audio": {"voice": voice, "format": "pcm16"}, "stream": True,
        "messages": [{"role": "system", "content": "You are a professional voice actor recording a premium product launch ad. Perform the script exactly as written, word for word. Add nothing, skip nothing, no greeting, no comments. " + direction},
                     {"role": "user", "content": "Script:\n" + script}]}
req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(), headers={"Authorization": "Bearer sk-or-dummy", "Content-Type": "application/json"})
pcm = bytearray(); txt = []
with urllib.request.urlopen(req, timeout=300) as r:
    for line in r:
        line = line.decode().strip()
        if not line.startswith("data:") or line == "data: [DONE]": continue
        try: d = json.loads(line[5:])
        except Exception: continue
        for ch in d.get("choices", []):
            a = (ch.get("delta") or {}).get("audio") or {}
            if a.get("data"): pcm += base64.b64decode(a["data"])
            if a.get("transcript"): txt.append(a["transcript"])
with wave.open(out, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(bytes(pcm))
print(out, "%.2fs" % (len(pcm)/48000), "|", "".join(txt))
