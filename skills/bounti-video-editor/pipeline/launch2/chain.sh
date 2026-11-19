#!/bin/bash
cd "$(dirname "$0")"
run() { for j in "$@"; do v=${j%:*}; f=${j#*:}; ../venv/bin/python film.py $v $f > tmp/log_${v}_$f.txt 2>&1 && echo "done $v $f" || echo "FAIL $v $f"; done; }
run H1-No-Catch:V P1-Real-People:V U1-The-Wall:V H2-Your-Phone:V P2-Pay-For-Results:V U2-Easy-Setup:V &
run H1-No-Catch:H P1-Real-People:H U1-The-Wall:H H2-Your-Phone:H P2-Pay-For-Results:H U2-Easy-Setup:H &
wait; echo ALLDONE
