#!/usr/bin/env python3
"""Render the portrait panel from a source photo.

Run locally (the source photo is deliberately NOT committed):

    python3 scripts/gen_portrait.py "/path/to/photo.jpg"

The photo stays a real photograph -- only the white studio backdrop is knocked
out and replaced with the panel's navy, then a light blue grade and fine
scanlines are laid over the top. Two earlier attempts (dot-matrix, then heavy
duotone) were rejected for not looking like him; detail beats stylisation here.

Output assets/panel-portrait.svg embeds the result as a base64 data URI, so the
panel has no external dependency at all.
"""

import base64
import io
import sys

from PIL import Image, ImageEnhance, ImageFilter

BG, PANEL, BORDER = "#05070c", "#0a0f1a", "#13395e"
BLUE, BLUE_D, DIM, FAINT = "#58a6ff", "#1f6feb", "#7d8ea3", "#41536b"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

CYCLE = 12.0          # slow: the scan takes its time
IW, IH = 620, 780     # portrait pixel box (2x the old one, so it stays sharp)

BACKDROP = (10, 20, 38)     # navy that replaces the white studio wall
TINT     = (46, 116, 210)   # light blue grade
TINT_MIX = 0.30


def cutout(path):
    """Replace the near-white studio backdrop with the panel navy."""
    src = Image.open(path).convert("RGB")
    w, h = src.size
    im = src.crop((int(w * 0.15), int(h * 0.02), int(w * 0.88), int(h * 0.70)))
    im = im.resize((IW, IH), Image.LANCZOS)

    # Alpha ramp on luminance: >=246 is certainly wall, <=224 certainly subject.
    lum = im.convert("L")
    mask = lum.point(lambda v: 0 if v >= 246 else (255 if v <= 224 else int((246 - v) / 22 * 255)))
    mask = mask.filter(ImageFilter.GaussianBlur(1.1))       # feather the hair edge

    out = Image.new("RGB", im.size, BACKDROP)
    out.paste(im, (0, 0), mask)

    out = ImageEnhance.Color(out).enhance(0.55)             # mute, don't kill, the colour
    out = ImageEnhance.Contrast(out).enhance(1.10)
    out = ImageEnhance.Brightness(out).enhance(1.04)

    px = out.load()
    for y in range(IH):
        for x in range(IW):
            r, g, b = px[x, y]
            px[x, y] = (round(r + (TINT[0] - r) * TINT_MIX),
                        round(g + (TINT[1] - g) * TINT_MIX),
                        round(b + (TINT[2] - b) * TINT_MIX))

    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=88, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def build(path):
    b64 = cutout(path)
    ox, oy = 26, 56
    w, h = IW + 52, IH + 132
    done = 6.0 / CYCLE

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" '
         f'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" '
         f'height="{h}" role="img" aria-label="Vigneshwar L">'
         f'<defs>'
         f'<clipPath id="pc"><rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" rx="8"/></clipPath>'
         f'<pattern id="sl" width="3" height="3" patternUnits="userSpaceOnUse">'
         f'<rect width="3" height="1" fill="#000" opacity=".16"/></pattern>'
         f'<linearGradient id="gl" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{BLUE}" stop-opacity="0"/>'
         f'<stop offset="100%" stop-color="#cfe8ff" stop-opacity=".55"/></linearGradient>'
         f'<linearGradient id="vg" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="70%" stop-color="#05070c" stop-opacity="0"/>'
         f'<stop offset="100%" stop-color="#05070c" stop-opacity=".55"/></linearGradient>'
         f'</defs>'
         f'<rect width="{w}" height="{h}" fill="{BG}" rx="12"/>'
         f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>'
         f'<path d="M0.5 12.5a12 12 0 0 1 12-12h{w-25}a12 12 0 0 1 12 12V42H0.5z" '
         f'fill="#0d1526" stroke="{BORDER}"/>'
         f'<circle cx="24" cy="21" r="5" fill="#1b5299"/>'
         f'<circle cx="43" cy="21" r="5" fill="#205295"/>'
         f'<circle cx="62" cy="21" r="5" fill="#2c74b3"/>'
         f'<text x="{w/2}" y="26" font-family="{MONO}" font-size="13.5" fill="{DIM}" '
         f'text-anchor="middle">vigneshwar.jpg</text>']

    p.append(f'<g clip-path="url(#pc)">'
             f'<image x="{ox}" y="{oy}" width="{IW}" height="{IH}" '
             f'preserveAspectRatio="xMidYMid slice" xlink:href="data:image/jpeg;base64,{b64}"/>'
             f'<rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" fill="url(#sl)"/>'
             f'<rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" fill="url(#vg)"/>'
             f'<rect x="{ox}" y="{oy}" width="{IW}" height="22" fill="url(#gl)" opacity="0">'
             f'<animate attributeName="y" values="{oy};{oy+IH-22};{oy+IH-22}" '
             f'keyTimes="0;{done:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;.6;.6;0;0" '
             f'keyTimes="0;0.03;{done-0.02:.4f};{done:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'</rect></g>'
             f'<rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" rx="8" fill="none" stroke="{BORDER}"/>')

    by = oy + IH + 32
    p.append(f'<text x="{ox}" y="{by}" font-family="{MONO}" font-size="13.5" fill="{DIM}">'
             f'<tspan fill="{BLUE_D}">$</tspan> whoami</text>'
             f'<text x="{ox}" y="{by+28}" font-family="{MONO}" font-size="13.5" fill="{BLUE}">'
             f'vigneshwar l <tspan fill="{FAINT}">&#183; tamil nadu, india</tspan></text>'
             f'<rect x="{w-150}" y="{by-11}" width="124" height="6" rx="3" fill="#0d1c30"/>'
             f'<rect x="{w-150}" y="{by-11}" width="124" height="6" rx="3" fill="{BLUE_D}">'
             f'<animate attributeName="width" values="0;124;124" keyTimes="0;{done:.4f};1" '
             f'dur="{CYCLE}s" repeatCount="indefinite"/></rect>')
    p.append('</svg>')
    return "".join(p)


if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else "/Users/vignesh/Downloads/my profile .jpeg"
    svg = build(photo)
    with open("assets/panel-portrait.svg", "w") as fh:
        fh.write(svg)
    print(f"wrote assets/panel-portrait.svg ({len(svg)//1024} KB)")
