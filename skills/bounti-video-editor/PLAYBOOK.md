# Bounti editing playbook

Rules learned from Mac's feedback across five edits and from 13 reference videos. Apply them to every edit.

## Mac's standing rules
- Never open on a black or dark screen. The first frame is picture.
- Look: natural, clean and bright, with real skin texture. It should not look cinematic, washed out or flat. Match the white-sweater reference (`v4/ref_look.json`): neutral whites, lifted exposure, warm natural skin.
- Cut every repeat, double take and redundant smile or laugh. Keep a laugh only where the script calls for it.
- Pacing is human: about 0.25 s between sentences and 0.1 s inside one. One speaker answers the other after about 0.25 s.
- No visible jump cuts. Inside one take, use a morph cut or a cutaway. Between takes, use a hard cut, or a transition when the cut looks off.
- Remove crew gear (tripod, phone) cleanly: reframe first, inpaint only when the gear is small and short-lived. Remove AI-burned subtitles.
- Every "Bounti" gets the bold logo, either behind him (person-masked) or in front.
- Say the site exactly as Mac gives it (partners.earnbounti.com, earnbounti.com).
- Props: few, high quality (Lucide icons on clean cards), never covering the person, inside the safe zone.
- Sound effects and music only where they earn their place. No twinkly or "feminine" stings. Use real UI sounds (mouse click on sign-ups).
- Zoom moves: clean and occasional, not on every cut.
- Captions by tone: elegant/professional uses a serif (Playfair, Instrument Serif, Cormorant) with a gold-italic key word. Energetic uses heavy italic with a black bar under the spoken word. No captions when Mac says so (skits).

## Hooks (first 3 seconds)
- Visual hooks: a quick push-in that settles, a crash zoom, an object thrown at the lens, a door or walk reveal, or a hand covering the lens and pulling away.
- Text hooks: text behind the subject (person mask), walking between text, text written on screen, text pulled out of the frame, the open-hand reveal, and the swipe-out.
- One hook only. Make it the strongest claim or question in the script.

## Transitions (`editkit/transitions.py`, 44 families)
- **Talking head, same take:** `morph_cut`. Different take, same framing: `punch_in`, or a cutaway.
- **Energy:** `whip_pan` with a whoosh, `zoom_in`, `zoom_blur` with a click, `flash` with a swish, and a hard cut on the beat.
- **Story or scene change:** `film_burn`, `light_leak` (subtle), `blur_dissolve`, `dip_black` or `blackout`.
- **Tech or brand:** `glitch`, `mask_glitch`, `rgb_split`, `pixelate`.
- **Continuity:** `match_cut` (same shape or motion), `body_wipe` (subject crosses the frame), and J and L cuts (audio leads or trails the picture).
- **Duration:** 6 to 10 frames for energetic cuts, 12 to 20 for soft ones. Pair each with the sound in `SOUND` and place it by `sync.at`.
- Use only what the cut needs. Mac's rule: you don't need 50 transitions, you need 5 that hit perfectly.

## Camera (`editkit/camera.py`)
- **Moves:** push_in, pull_out, crash_zoom, pan, tilt, truck, pedestal, ken_burns, drift, handheld, impact_shake, dutch_roll, whip, step_punch, arc, dolly_zoom (masked), follow_face, speed_ramp, freeze_frame.
- **Talking heads:** a slow push on key lines, a step punch on emphasis (at most every 3 to 4 lines), and handheld at intensity 0.3 for UGC realism.

## Captions (`editkit/captions.py`)
- 30 styles × 17 animations × highlight modes (colour, bar, marker, underline, italic, scale, karaoke).
- Show 2 to 4 words per chunk, timed to the words.
- Placement: just above centre or the lower third, clear of the face and the platform UI, and lifted above shirt logos.

## Colour and light (`editkit/grade.py`)
- Primaries: exposure, contrast, highlights, shadows, whites, blacks, temperature, tint, saturation, vibrance, clarity.
- Finishing: split tone, curves, matte, vignette, bloom, halation, grain, sharpen, denoise.
- 22 looks, `.cube` LUT support, and `match_reference()` to match a still.
- Order of work: fix exposure and white balance per clip, match the clips to each other, then the look, then finishing.
- Keep each clip's curve slope between 0.45 and 1.45 so compression blocks don't show.

## Audio
- Clean every clip the same way: highpass, light FFT denoise, small cut at 220 Hz, presence lift at 3.2 kHz.
- Match every clip to -19/-20 LUFS before the mix.
- Run continuous room tone under the cuts. Duck the music under speech with a sidechain.
- Master to -14 LUFS with a true peak of -1.5 dB.

## 2026-11-19 additions (Mac)
- UGC: editor notes are suggestions; use judgment per video. Do not put Bounti pages everywhere, only where a line describes something on screen.
- Pages must match the words exactly; no filler pages.
- Pages are live and functional (recorded interactions with the prototype), never static images. Green screen backdrops too.
- Short cut-downs must be at least 1:00 (and at most 1:45): extend with whole lines that continue the story, not filler.
- Learn Mac's L8 podcast-card style (Style D in SKILL.md).
- Back up every edit to github Macsamuelpro/bounti-media, always.
