---
name: bounti-video-editor
description: Edit short-form vertical videos for Bounti (and similar talking-head or skit ads) from AI-generated or filmed 8–10 s clips. Covers transcription, cleaning dialogue, removing background sound, natural pacing, invisible joins (morph cuts, angle cuts, cutaways), removing crew gear and burned-in text, natural colour grading matched to a reference, captions in many styles, Bounti logo moments, animated character scenes in Bounti style, real Bounti site screens, phone screen replacement, sound design, short cut-downs with hook/middle/CTA, and delivering several style versions. Use when Mac sends video clips to edit, asks for short versions, or asks for multiple edit styles.
---

# Bounti video editor

You are Mac's chief editor. Read PLAYBOOK.md in this folder before every edit: it holds every rule Mac has given, and those rules win over your defaults.

## Inputs Mac usually gives
- 8–10 s clips (AI video: Gemini Omni/Veo style), sometimes with a script, sometimes with a reference video or still for the look.
- Two batches are common; wait for "that's all" or count clips against the script before assembling.

## Workflow
1. **Inventory**: ffprobe every clip; contact sheet at 1–2 fps; `scdet` for internal angle cuts.
2. **Transcribe locally** (no paid API needed): pywhispercpp + `ggml-base.en.bin` (fetch from a GitHub repo that hosts it, e.g. via `gh api search/code filename:ggml-base.en.bin`). Segment speech by RMS envelope, transcribe each piece separately (word-accurate pieces with timings). Fix brand words (Bounty→Bounti, earnbouncy→earnbounti).
3. **Find problems**: repeats (compare MFCC fingerprints between pieces with subsequence DTW; < ~0.2 = same line said twice), unneeded laughs/smiles (look at frames between pieces), AI whoosh effects, crew gear (tripod/phone at frame edges), AI-burned subtitles.
4. **Clean audio**: highpass 80, notches at mains hum harmonics (100/200/300 Hz when present), RNNoise model `bd.rnnn` (github GregorR/rnnoise-models) via ffmpeg `arnndn`, EQ (-1.5 dB @220, +1.5 dB @3.2 kHz), match every clip to -19 LUFS.
5. **Pacing map** (`pipeline/edit7.py`, `pipeline/shorts.py`): pieces + gaps. ~0.12 s inside a sentence, ~0.30 s after a sentence, ~0.5 s before a new idea, ~0.25 s turn-taking in dialogue. Fill shortfalls from the next take's lead-in, never freeze on speech.
6. **Joins**: same take → morph cut (optical flow, 6 frames); different camera angle → hard cut; pauses inside a take → cutaway or L/J cut; scene changes → one transition that suits the tone (`scripts/transitions.py`, 44 families with paired SFX).
7. **Look**: natural, bright, real skin texture. Match Mac's reference still with `scripts/grade5.py`/`grade.match_reference` (tone distribution, white balance, skin). Keep curve slopes 0.45–1.45 to avoid compression blocking. Never open on black.
8. **Graphics**:
   - Bounti brand: Inter Black (tracking -0.055), paper #F1F0EC, ink #0D0D0D, grey #5E5E5E, Kalam handwritten accents, logo `web/bounti_logo.png` (transparent).
   - Every "Bounti" gets the bold logo (behind the subject via person mask, or in front).
   - Real site screens: capture earnbounti.com / partners / app with Playwright at 390x844 @3x; crop UI cards (`pipeline` web/cards.js approach).
   - Animated scenes: `pipeline/mg7.py` (Open Peeps characters, CC0) — characters and stories, not charts.
   - Props only where they help, inside the safe zone, never over the face.
9. **Captions**: `scripts/captions.py` (30 styles × 17 animations). Match the tone: bold/italic bar for energy, serif with gold italic for elegant, none for skits when Mac says so. Move them around into empty space (mask-aware), never over the face or shirt logos, box fallback in close-ups. Read every caption line: punctuation and conjunctions must make sense as sentences.
10. **Sound**: music bed 16–20 dB under voice with sidechain ducking; only a few SFX tied to visible events (real mouse click for sign-ups, no twinkly stings). Master -14 LUFS, -1.5 dBTP.
11. **QA before sending**: frames at every join, scene edge, caption and card moment; loudness numbers; read the full caption script. You cannot watch or listen: say so and give the numbers.
12. **Deliver**: SendUserFile; zip multiple files (`zip -0`); back up working files to github Macsamuelpro/bounti-media under `video/<project>/` (no file over 50 MB, no renders or raw footage).

## Short cut-downs (60–105 s)
Hook (strongest claim/question, first 3 s) → one coherent middle (one story or one use case) → Bounti reveal → CTA (partners.earnbounti.com, "Let's put a crowd behind your next big thing."). Build each cut as a list of whole lines in `shorts.py`, set display text per line (`TXT`) so sentences read correctly, then render with `EDIT=cuts/<name>.json` and mix with `VOICE=cuts/<name>_voice.wav`. Produce as many distinct, sensible cuts as the material allows, each in a style that fits its ambience.

## Styles that exist (render7.py)
- **A Cut-out**: subject on Bounti paper, big keyword behind the head, small highlighted captions in empty space, dissolves.
- **B Natural/Bold**: real footage, light clean grade, bold italic bar captions, keyword behind subject, zoom-blur transitions, site cards.
- **C Editorial**: real footage, serif captions on a soft band, vignette, whip transitions, fewer scenes.

## Practical limits
- 15 GB RAM: one render at a time (plus mask extraction).
- Person masks: u2net_human_seg.onnx (rembg release) every 3rd frame (`masks7.py`), ~1.5 min per clip.
- Network is limited: stock B-roll sites are blocked unless Mac allows them; use animated scenes and real Bounti pages instead.
- Long renders: run in background, chain them, keep a RESUME.md with exact next commands.
