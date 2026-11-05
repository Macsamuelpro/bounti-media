"""Render a Bounti wanted poster.

Usage:
  python3 poster/render.py <villain-id> <bounty> <status> <out.jpg>
  status: wanted | captured | escaped
Reads villain names and crop focus from lore/villains.json. Run from the repo root.
"""
import json
import sys
from PIL import Image, ImageDraw, ImageFont

FRAME = (63, 214, 970, 838)  # inside of the portrait frame: left, top, right, bottom
NAME_BOX = (120, 1045, 913, 1185)
AMOUNT_X, AMOUNT_TOP, AMOUNT_BOTTOM, AMOUNT_RIGHT = 212, 1212, 1314, 955
INK = (72, 38, 25)
FONT = "poster/font-bold.ttf"


def fit_font(draw, text, max_w, max_h, start):
    size = start
    while size > 20:
        f = ImageFont.truetype(FONT, size)
        l, t, r, b = draw.textbbox((0, 0), text, font=f)
        if r - l <= max_w and b - t <= max_h:
            return f
        size -= 2
    return ImageFont.truetype(FONT, size)


def main(vid, bounty, status, out):
    villains = json.load(open("lore/villains.json"))
    v = villains[vid]
    poster = Image.open("poster/base.png").convert("RGB")

    # Portrait, cropped to the frame, keeping the face in view.
    fw, fh = FRAME[2] - FRAME[0], FRAME[3] - FRAME[1]
    p = Image.open(f"villains/{vid}.jpg").convert("RGB")
    zoom = v.get("zoom", 1.0)  # above 1 crops closer to the face
    scale = fw * zoom / p.width
    p = p.resize((round(fw * zoom), round(p.height * scale)), Image.LANCZOS)
    focus = v.get("focus", 0.12)  # share of the image above the crop's top edge
    top = min(max(0, round(p.height * focus)), p.height - fh)
    left = min(max(0, round(p.width * v.get("focus_x", 0.5) - fw / 2)), p.width - fw)
    p = p.crop((left, top, left + fw, top + fh))
    poster.paste(p, (FRAME[0], FRAME[1]))

    d = ImageDraw.Draw(poster)

    # Name, centred between WANTED and the bounty.
    name = v["poster_name"].upper()
    f = fit_font(d, name, NAME_BOX[2] - NAME_BOX[0], 92, 92)
    l, t, r, b = d.textbbox((0, 0), name, font=f)
    x = (NAME_BOX[0] + NAME_BOX[2] - (r - l)) / 2 - l
    y = (NAME_BOX[1] + NAME_BOX[3] - (b - t)) / 2 - t
    d.text((x, y), name, font=f, fill=INK)

    # Bounty, after the B mark.
    amount = f"{int(bounty):,}"
    f = fit_font(d, amount, AMOUNT_RIGHT - AMOUNT_X, AMOUNT_BOTTOM - AMOUNT_TOP, 110)
    l, t, r, b = d.textbbox((0, 0), amount, font=f)
    y = (AMOUNT_TOP + AMOUNT_BOTTOM - (b - t)) / 2 - t
    d.text((AMOUNT_X - l, y), amount, font=f, fill=INK)

    # Status stamp across the portrait.
    if status in ("captured", "escaped"):
        word = "CAPTURED" if status == "captured" else "ESCAPED"
        colour = (178, 24, 24, 215) if status == "captured" else (30, 30, 30, 200)
        stamp = Image.new("RGBA", (900, 260), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp)
        sf = ImageFont.truetype(FONT, 150)
        l, t, r, b = sd.textbbox((0, 0), word, font=sf)
        w, h = r - l + 80, b - t + 60
        sd.rounded_rectangle((10, 10, 10 + w, 10 + h), radius=18, outline=colour, width=14)
        sd.text((50 - l, 40 - t), word, font=sf, fill=colour)
        stamp = stamp.crop((0, 0, w + 20, h + 20)).rotate(14, expand=True, resample=Image.BICUBIC)
        cx = (FRAME[0] + FRAME[2] - stamp.width) // 2
        cy = (FRAME[1] + FRAME[3] - stamp.height) // 2
        poster.paste(stamp, (cx, cy), stamp)

    poster.save(out, quality=88)


if __name__ == "__main__":
    main(*sys.argv[1:5])
