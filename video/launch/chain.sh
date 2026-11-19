#!/bin/bash
cd "$(dirname "$0")"
for v in H1-Simple-Tasks H2-Bigger-Bounties P1-Real-People P2-Business-Growth U1-Add-The-Wall U2-Set-Up; do
  for f in V H; do ../venv/bin/python launch.py $v $f > tmp/log_${v}_$f.txt 2>&1 && echo "done $v $f" || echo "FAIL $v $f"; done
done
echo ALLDONE
