#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "film.py" >/dev/null; do sleep 20; done
mkdir -p final/ugc2_lv
for u in UGC1 UGC2 UGC3 UGC4 UGC5 UGC6 UGC7 UGC10 UGC11 UGC12 UGC13; do
  venv/bin/python ugc_render2.py $u > ugc/$u/render2.log 2>&1 || { echo "FAIL $u"; continue; }
  f=$(ls final/ugc2/Bounti-$u-*.mp4 | head -1); o=final/ugc2_lv/$(basename "$f")
  J=$(ffmpeg -hide_banner -nostats -i "$f" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  read mi mtp mlra mth off <<< $(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
  ffmpeg -v error -y -i "$f" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$mi:measured_TP=$mtp:measured_LRA=$mlra:measured_thresh=$mth:offset=$off:linear=true,aresample=48000" -c:a aac -b:a 256k -movflags +faststart "$o"
  echo "done $u"
done
echo ALLDONE
