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

## App screens in videos: live, matched, sparing (Mac, 2026-11-19)
- Use phone inserts only where a line describes something the viewer can see; most lines need none. One to three inserts per UGC video, never one per sentence. Editor notes are suggestions, not orders.
- The screen must show exactly what is being said (browse = swiping the feed, "check the requirements" = the rules sheet, "submit / approved" = verification then the pending reward, "dashboard" = profile balances).
- Never a static screenshot when the page can be driven: record the working prototype in `Bounti/docs/design/export` (`pipeline/live/`). Serve the folder over HTTP (`python3 -m http.server 8765`), drive it with Playwright through the app's own `go()` (found via the React fiber: `stateNode.logic`), draw it at scale 2 in a 944x1972 viewport, and record with the CDP screencast (real time). Every on-camera action is a real tap or scroll; taps get a touch ring and a soft tap sound. Set real design state only (e.g. `connected` accounts), never fake approvals.
- Feed cards snap on one wheel flick (`flick()`), not small wheel steps. Some buttons sit under decoration: `tapJs` clicks through.
- Green screen = a live recording played full bleed behind the presenter (`greenscreen`/`bg_switch` take live specs).
- Never show partner prices, cost per action, budgets or publisher revenue in any public video: stop the partner wizard before the budget step; crop or cut past publisher reward amounts.
- `fx.composite` takes RGB(A) overlays. Convert BGR frames (`[..., ::-1]`) before compositing or skin turns blue.
- OpenCV mis-decodes yuv444p: encode intermediate clips as yuv420p.

## Short cut-downs (60–105 s)
Hook (strongest claim/question, first 3 s) → one coherent middle (one story or one use case) → Bounti reveal → CTA (partners.earnbounti.com, "Let's put a crowd behind your next big thing."). Build each cut as a list of whole lines in `shorts.py`, set display text per line (`TXT`) so sentences read correctly, then render with `EDIT=cuts/<name>.json` and mix with `VOICE=cuts/<name>_voice.wav`. Produce as many distinct, sensible cuts as the material allows, each in a style that fits its ambience.

## Styles that exist (render7.py)
- **A Cut-out**: subject on Bounti paper, big keyword behind the head, small highlighted captions in empty space, dissolves.
- **B Natural/Bold**: real footage, light clean grade, bold italic bar captions, keyword behind subject, zoom-blur transitions, site cards.
- **C Editorial**: real footage, serif captions on a soft band, vignette, whip transitions, fewer scenes.

- **D Podcast cards (Mac's L8)**: talking head intercut with warm cream (#FCF6E6) cards. The speaker shrinks into a rounded tile with a soft shadow while a keyword types in letter by letter below; small round avatars pop around the tile; fog (blur) dissolves between card states; full cream B-roll cards (icon cluster, sliding post cards with a progress bar, word swap over a photo collage); back on camera, two-size captions (small lead word, big key word). Kit: `scripts/cards.py` (shrink_to_tile, letter_reveal, fog_dissolve, orbit_pop, two_size_caption).

## Launch videos (motion graphics, `pipeline/launch/`)
- `scripts.py` holds each video as beats: voiceover line plus one scene (words = kinetic type with *gold* highlight and hand-drawn underline, icons = lucide tiles popping on their spoken word, phone = live prototype recording in a bezel with a soft gold disc, logo = blur-in resolve with underline, sub line and URL pill).
- `vo.py` makes the voiceover locally with Kokoro (kokoro-onnx, model files from the thewh1teagle/kokoro-onnx GitHub release; voices af_heart, am_michael, am_fenrir, bm_george). OpenRouter is the alternative when it has credit.
- `launch.py <video> V|H` renders 1080x1920 or 1920x1080 at 30 fps: push transitions with motion blur, phone to phone crossfades, whoosh/pop/tap/coin SFX, CC0 music ducked under the voice, -14 LUFS.
- Copy comes from the design export. No invented numbers, prices or claims.


## Premium launch films v2 (Mac, 2026-11-19: "Apple/Samsung style, premium, not generic")
- Scripts: research first (product specs plus market research), hook in the first 3 seconds, benefit-led, every claim traced to the specs, global audience (not one country), clean grammar. Use emotion where it earns it: sarcasm on the hook, thought on the turn, calm on the trust line.
- Voice: OpenRouter has dedicated speech models (`/api/v1/audio/speech`): elevenlabs/eleven-v3 (inline tags like [sarcastic] [curious] [whispers] [sighs] [calm], about $0.08 per 1,000 characters, British premade voices george, daniel, alice, lily), plus openai/gpt-audio, gemini TTS, minimax, fish-audio and others. List them with `GET /api/v1/models?output_modalities=all`. `pipeline/launch2/gen_vo.py` makes two takes per line and keeps the take whose Whisper transcript matches.
- Music: google/lyria-3-pro-preview via OpenRouter chat completions with `stream: true` (about $0.08 per track, 60 to 70 s, mp3). Analyse beats and the drop with librosa; shift the track so the drop lands on the brand reveal; snap cuts to beats.
- Visuals (`pipeline/launch2/film.py` + `shots.py`): phones and a laptop as 3D perspective planes with keyframed yaw/pitch/roll, soft shadows, glass sheen, exploded screen layers, a laptop + phone duo for desktop and mobile, three-phone fans, masked line-reveal type with gold highlight words, whip/zoom transitions, two-pass loudness to -14 LUFS.
- Desktop designs: Landing Desktop, DeskFeed, DeskMissions (recorded with `pipeline/live/drec.js`). Partner and publisher screens exist only on mobile.

## UGC v2 style engines (`pipeline/ugc_render2.py` + `ugc_v2_frames.py` + `ugc_styles2.py`)
punch (jump-cut punch-ins, chest hook card, full-screen app cutaways), cards (Mac's L8), split (stacked), loom (screen-share + face bubble),
gs_side (green screen A: full-bleed app, torso right, step badges), cinema (letterbox, serif captions in bars, warm grain, polaroid app card),
contrast (B&W problem + word cards, colour on the turn, 3D phone), duet (side-by-side panels), vlog (DAY 1 HUD, ticking checklist, whips, phone peek),
gs_float (green screen B: paper backdrop, floating 3D phone, torso centred), chat (handheld, chat-bubble hook, link card that opens into the app).

## Practical limits
- 15 GB RAM: one render at a time (plus mask extraction).
- Person masks: u2net_human_seg.onnx (rembg release) every 3rd frame (`masks7.py`), ~1.5 min per clip.
- Network is limited: stock B-roll sites are blocked unless Mac allows them; use animated scenes and real Bounti pages instead.
- Long renders: run in background, chain them, keep a RESUME.md with exact next commands.
