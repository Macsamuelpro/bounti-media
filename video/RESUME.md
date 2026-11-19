# RESUME (paused by Mac at 04:10 WAT, 2026-11-19; resume 06:01 WAT)

Scratchpad S = /tmp/claude-0/-home-user-Bounti/62af7c5f-52be-5258-8396-28d81e625d88/scratchpad
Live recorder L = /tmp/claude-0/-home-user/62af7c5f-52be-5258-8396-28d81e625d88/scratchpad/live
If S is gone: copy this repo's video/ folders back (launch2 -> S/launch2, ugc -> S/ugc + S/ugc_render.py + S/ugc_projects.py,
editkit/cards.py -> S/editkit, fx.py -> S/fx.py, ugc/live/*.js+live.py -> L) and re-record live clips:
serve Bounti/docs/design/export (`python3 -m http.server 8765 --bind 127.0.0.1`), then in L: `node rec.js <name>` + `python3 live.py <name>`
for browse_feed find_claim missions_detail trend_rules my_hunts dashboard house signup partner_create pub_setup pub_wall,
and `node drec.js d_landing|d_feed|d_missions`; copy rec/<name>.mp4 (yuv420p) + json {end,events,crop} into S/ugc/live.

## Delivered so far
- Bounti-Crowd-Shorts.zip (6 shorts, 1:00 to 1:05), Bounti-UGC-11-Videos.zip (v1, Mac wants a full redo, see below),
  Bounti-Launch-Videos.zip (v1, Mac rejected: generic voice/visuals).

## STEP 1: launch films v2 (resumed 06:01 WAT; H1, P1, U1, H2, P2 done; U2 V/H rendering)
- Done (in S/final/launch2): H1-No-Catch 9x16+16x9, P1-Real-People 9x16+16x9, U1-The-Wall 9x16+16x9.
- Remaining: H2-Your-Phone V/H, P2-Pay-For-Results V/H, U2-Easy-Setup V/H. Exact command (run in background, timeout 2h):
  cd S/launch2 && for j in H2-Your-Phone:V P2-Pay-For-Results:V U2-Easy-Setup:V H2-Your-Phone:H P2-Pay-For-Results:H U2-Easy-Setup:H; do ../venv/bin/python film.py ${j%:*} ${j#*:}; done
  (two at a time is fine on 4 cores). VO is in launch2/vo (ElevenLabs v3 via OpenRouter, voices alice/lily/george/daniel),
  music in launch2/music (Lyria 3 Pro, hunter/partner/publisher), shots in shots.py. Output already loudness-normalised (-14 LUFS two-pass).
- QA each (frames at shot changes, no black, loudness), zip as Bounti-Launch-Films-v2.zip. Do NOT send yet: Mac wants all zips together at the end.

## STEP 2: redo all 11 UGC videos (Mac 2026-11-19 ~04:00)
Rules: every video a different editing style, pattern and feel; different music for each (already composed: S/ugc/music/UGCn.mp3, Lyria);
text hooks never over faces (use face boxes from models/yunet.onnx, put hooks/captions in face-free zones); better text or visual hooks;
only TWO green screens, in two different formats, presenter shown torso-only; use Mac's L8 podcast-card style for one; keep live prototype
recordings (S/ugc/live) for app moments, matched to the line, few inserts. Plan (build S/ugc_render2.py from ugc_render.py, one style function each):
| UGC1 | punch-in jump-cut zooms per sentence, bold keyword captions low, hook box at chest | app = full-screen cutaways |
| UGC2 | L8 podcast cards (editkit/cards.py: shrink_to_tile, letter_reveal, fog_dissolve, two_size_caption), cream #FCF6E6 | app on a card |
| UGC3 | stacked split screen: presenter top half, live app bottom half, minimal lowercase captions at the seam | |
| UGC4 | screen-share/Loom: app full screen, presenter in a round face bubble bottom corner, sticky-note hook (Kalam) | |
| UGC5 | GREEN SCREEN A: live app full-bleed backdrop, presenter torso cut out low-right, step badges 1-2-3 | |
| UGC6 | cinematic: letterbox bars, serif captions inside the bars, warm grade, grain, slow push-ins, typewriter hook in top bar | app = polaroid card opposite the face |
| UGC7 | before/after: desaturated problem part + full-screen kinetic word cards, colour returns at "That's where Bounti" | app = angled 3D phone (reuse launch2/film.py device code) |
| UGC10 | duet side by side: presenter panel left, live app panel right, blurred bg | |
| UGC11 | vlog: DAY 1 HUD, checklist that ticks as lines are spoken, whip transitions | app = phone peeking up from the bottom edge |
| UGC12 | GREEN SCREEN B: floating angled device backdrop (3D), presenter torso centred low, zooms into the backdrop | |
| UGC13 | casual handheld shake, message-bubble hooks beside the face, link-card bubble that expands into the app | |
Then render each, QA (faces never covered, loudness two-pass -14), zip Bounti-UGC-v2.zip.
BUILT: S/ugc_render2.py (exec's ugc_v2_frames.py; styles in ugc_styles2.py; dev3d.py for 3D phones). Previews checked for all 11.
Render queue: S/ugc_chain2.sh (waits for film.py, renders final/ugc2, two-pass loudness into final/ugc2_lv). Log: S/ugc/chain_v2.log

## STEP 3: send ALL zip files together, in a row (Mac's request): launch films v2 zip, UGC v2 zip.
Also back up every edit to this repo (no file over 50 MB) and keep skills/bounti-video-editor updated.
OpenRouter credit left about $2.6 (speech: elevenlabs/eleven-v3 via /api/v1/audio/speech; music: google/lyria-3-pro-preview, stream true).
