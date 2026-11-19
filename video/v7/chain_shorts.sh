#!/bin/bash
cd "$(dirname "$0")"
M_A="../lib/ccmusic/freepd.com/City Sunshine.mp3"; M_B="../lib/ccmusic/freepd.com/Beat One.mp3"; M_C="../lib/ccmusic/freemusicarchive.org/HoliznaCC0 - Not It (Lofi).mp3.mp3"
for job in "$@"; do
  IFS=: read n v label <<< "$job"
  out=out/short_${n}_${v}.mp4
  EDIT=cuts/$n.json ../venv/bin/python render7.py $v $out > out/short_${n}_${v}.log 2>&1 || { echo "FAIL render $n $v"; continue; }
  case $v in A) M="$M_A"; DB=-21;; B) M="$M_B"; DB=-19;; C) M="$M_C"; DB=-19;; esac
  EDIT=cuts/$n.json VOICE=cuts/${n}_voice.wav ../venv/bin/python mix7.py $out "../final/shorts/Bounti-Short-${n}-${label}.mp4" "$M" $DB > out/mix_${n}_${v}.log 2>&1 || echo "FAIL mix $n $v"
  echo "done $n $v"
done
echo ALLDONE
