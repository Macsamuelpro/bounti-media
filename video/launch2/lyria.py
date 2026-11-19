"""Generate a music bed with google/lyria-3 via OpenRouter (streamed audio). usage: lyria.py out model "prompt" """
import sys, json, base64, urllib.request
out, model, prompt = sys.argv[1:4]
body = {"model": model, "modalities": ["text", "audio"], "audio": {"format": "wav"}, "stream": True, "messages": [{"role": "user", "content": prompt}]}
req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(), headers={"Authorization": "Bearer sk-or-dummy", "Content-Type": "application/json"})
buf = bytearray(); txt = []; usage = None
try:
    with urllib.request.urlopen(req, timeout=900) as r:
        for line in r:
            line = line.decode().strip()
            if not line.startswith("data:") or line == "data: [DONE]": continue
            try: d = json.loads(line[5:])
            except Exception: continue
            usage = d.get("usage") or usage
            for ch in d.get("choices", []):
                dl = ch.get("delta") or {}; a = dl.get("audio") or {}
                if a.get("data"): buf += base64.b64decode(a["data"])
                if dl.get("content"): txt.append(dl["content"])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read()[:800].decode()); sys.exit(1)
open(out, "wb").write(bytes(buf)); print(out, len(buf), "bytes", "".join(txt)[:200], usage)
