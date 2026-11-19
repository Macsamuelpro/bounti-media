#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f chain_shorts.sh >/dev/null; do sleep 20; done
for u in UGC1 UGC2 UGC3 UGC4 UGC5 UGC6 UGC7 UGC10 UGC11 UGC12 UGC13; do
  venv/bin/python ugc_render.py $u > ugc/$u/render.log 2>&1 && echo "done $u" || echo "FAIL $u"
done
echo ALLDONE
