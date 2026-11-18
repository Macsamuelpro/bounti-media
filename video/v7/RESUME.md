# Resume note: Bounti "crowd" video, 3 versions (paused 04:02 WAT, 18 Nov)

Working folder: /tmp/claude-0/-home-user-Bounti/62af7c5f-52be-5258-8396-28d81e625d88/scratchpad/v7
Python: ../venv/bin/python (run everything from the v7 folder)

## Finished
- Script and pacing: 26 clips in src/b01..b26.mp4, transcribed in pieces.json.
- Edit decisions in edit7.py, output in edit7.json: 82 pieces, 182.1 s.
  - Pauses: 0.30 s after a sentence, 0.55 s before a new idea (for example "You've got a new store?", "You've launched a website?"), 0.12 s inside a sentence.
  - The AI whooshes in b01 are dropped.
- Clean dialogue: voice.wav. The background hum and noise are removed (hum notches at 100/200/300 Hz plus the RNNoise "bd" model), and every clip is matched to -19 LUFS. Per-clip cleaned files are in clean/.
- Bounti assets:
  - web/: live earnbounti.com screenshots, including the partners and app pages, the section crops sec_*.png and the UI cards card_*.png.
  - Brand: Inter Black, paper #F1F0EC, ink #0D0D0D, plus Kalam.
- Animated scenes in mg7.py, with Open Peeps characters (CC0): poof, scroll_past, empty_store, rsvp, crowd, spread, busy_store, bounti, pillars, partners, end. All are tested.
- Renderer: render7.py, versions A (cut-out on paper), B (natural, bold captions) and C (editorial). Previews of all three are checked.
- Mixer: mix7.py, not yet run.

## Half done
- Person masks (masks7.py): b01 to b17 are done in masks/. b18 to b26 are still to do. The script skips clips already done, so just rerun it.
- C render was stopped at frame 2880/4443. out/C_raw.mp4 is incomplete and must be re-rendered from the start.

## Next steps (in order)
1. Finish the masks:
   `nohup ../venv/bin/python masks7.py > masks.log 2>&1 &`
   About 15 min, until masks/ has 26 files.
2. Render C (this needs no masks, so it can run alongside step 1):
   `nohup ../venv/bin/python render7.py C out/C_raw.mp4 > out/C.log 2>&1 &`
   About 35 min.
3. Once the masks are done, render A and B, one at a time:
   - `../venv/bin/python render7.py A out/A_raw.mp4 > out/A.log 2>&1`
   - `../venv/bin/python render7.py B out/B_raw.mp4 > out/B.log 2>&1`
4. Mix each version. The music beds are:
   - A: freepd "City Sunshine"
   - B: freepd "Beat One"
   - C: freemusicarchive "HoliznaCC0 - Not It (Lofi)"

   Run each mix:
   - `../venv/bin/python mix7.py out/C_raw.mp4 ../final/Bounti-Crowd-C-Editorial.mp4 "../lib/ccmusic/freemusicarchive.org/HoliznaCC0 - Not It (Lofi).mp3.mp3" -24`
   - `../venv/bin/python mix7.py out/A_raw.mp4 ../final/Bounti-Crowd-A-Cutout.mp4 "../lib/ccmusic/freepd.com/City Sunshine.mp3" -26`
   - `../venv/bin/python mix7.py out/B_raw.mp4 ../final/Bounti-Crowd-B-Natural.mp4 "../lib/ccmusic/freepd.com/Beat One.mp3" -24`

   Then check that the music sits about 18 to 20 dB under the voice. Adjust the last argument if not.
5. QA frames at the scene edges and card moments, then send all three to Mac with SendUserFile.

## Notes
- Do not run two renders at once (memory limit is 15 GB). A single render plus masks7 together is fine.
- If the B-roll hosts (Pexels or Mixkit) were approved, add them. Mac declined that network change, so all B-roll is the animated scenes plus the Bounti site.

## If the working folder is gone (container reset)
Everything that is costly to redo is backed up in the repo at github.com/Macsamuelpro/bounti-media, under video/v7/:
- scripts
- edit decisions
- cleaned audio
- web captures
- the editkit

To restore:
1. `git clone --depth 1 https://github.com/Macsamuelpro/bounti-media /home/user/bounti-media`
2. Recreate the scratchpad layout:
   - copy video/v7/* into scratchpad/v7/;
   - copy editkit/* into scratchpad/editkit/;
   - copy scripts/fx.py into scratchpad/;
   - copy scripts/segmask.py into scratchpad/v3/;
   - copy web/bounti_logo.png into scratchpad/v3/gfx/.
3. Re-fetch the cheap inputs:
   - the source clips from Mac's uploads (link them as src/bNN.mp4 in the order listed in pieces.json);
   - the venv (opencv, onnxruntime, pillow, scipy, resvg-py, pywhispercpp);
   - models/u2net_human_seg.onnx from the rembg GitHub release;
   - lib/ fonts (google/fonts sparse checkout), icons (npm lucide-static@0.460.0), open-peeps (github jenshor/open-peeps), the sfx-kit (github wyzowl/sfx-kit) and the CC0 music (github SoundSafari/CC0-1.0-Music sparse checkout).
4. Masks (masks/*.npz) are not backed up. Regenerate them with masks7.py, about 40 min.
