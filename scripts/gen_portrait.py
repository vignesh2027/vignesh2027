#!/usr/bin/env python3
"""Render the portrait terminal panel from a source photo.

Run locally (the source photo is deliberately NOT committed):

    python3 scripts/gen_portrait.py "/path/to/photo.jpg"

The photo is duotoned into the dark-blue palette and embedded in the SVG as a
base64 data URI, so the panel has no external dependency at all. A dot-matrix
approximation was tried first and rejected: it was neither accurate nor
professional. A real photograph is both.
"""

import base64
import io
import sys

from PIL import Image, ImageOps, ImageEnhance

BG, PANEL, BORDER = "#05070c", "#0a0f1a", "#13395e"
BLUE, BLUE_D, DIM, FAINT = "#58a6ff", "#1f6feb", "#7d8ea3", "#41536b"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

CYCLE = 9.0          # every panel shares this loop length
IW, IH = 452, 566    # portrait pixel box

# duotone ramp: shadow -> midtone -> highlight
STOPS = [(0, (5, 7, 12)), (38, (13, 41, 94)), (68, (31, 111, 235)), (100, (200, 228, 255))]


def ramp():
    lut = []
    for i in range(256):
        pct = i / 255 * 100
        for j in range(len(STOPS) - 1):
            p0, c0 = STOPS[j]
            p1, c1 = STOPS[j + 1]
            if p0 <= pct <= p1:
                f = (pct - p0) / (p1 - p0) if p1 > p0 else 0
                lut.append(tuple(round(c0[k] + (c1[k] - c0[k]) * f) for k in range(3)))
                break
        else:
            lut.append(STOPS[-1][1])
    return lut


def duotone(path):
    src = Image.open(path).convert("L")
    w, h = src.size
    im = src.crop((int(w * 0.17), int(h * 0.03), int(w * 0.86), int(h * 0.66)))
    im = ImageOps.invert(im)                 # white studio backdrop -> dark
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = im.resize((IW, IH), Image.LANCZOS)

    lut = ramp()
    out = Image.new("RGB", im.size)
    out.putdata([lut[p] for p in im.getdata()])

    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def build(path):
    b64 = duotone(path)
    ox, oy = 24, 52
    w, h = IW + 48, IH + 118
    done = 4.2 / CYCLE                       # scan completes 4.2s into the loop

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
         f'height="{h}" role="img" aria-label="Vigneshwar L">'
         f'<defs>'
         f'<clipPath id="pclip"><rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" rx="6"/></clipPath>'
         f'<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
         f'<rect width="4" height="2" fill="#000" opacity=".22"/></pattern>'
         f'<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{BLUE}" stop-opacity="0"/>'
         f'<stop offset="100%" stop-color="#cfe8ff" stop-opacity=".75"/></linearGradient>'
         f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">'
         f'<stop offset="0%" stop-color="{BLUE_D}" stop-opacity=".55"/>'
         f'<stop offset="100%" stop-color="#0b2545" stop-opacity=".15"/></linearGradient>'
         f'</defs>'
         f'<rect width="{w}" height="{h}" fill="{BG}" rx="12"/>'
         f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>'
         f'<path d="M0.5 12.5a12 12 0 0 1 12-12h{w-25}a12 12 0 0 1 12 12V38H0.5z" fill="#0d1526" stroke="{BORDER}"/>'
         f'<circle cx="22" cy="20" r="5" fill="#1b5299"/>'
         f'<circle cx="41" cy="20" r="5" fill="#205295"/>'
         f'<circle cx="60" cy="20" r="5" fill="#2c74b3"/>'
         f'<text x="{w/2}" y="25" font-family="{MONO}" font-size="13" fill="{DIM}" '
         f'text-anchor="middle">vigneshwar.jpg</text>']

    p.append(f'<g clip-path="url(#pclip)">'
             f'<image x="{ox}" y="{oy}" width="{IW}" height="{IH}" '
             f'preserveAspectRatio="xMidYMid slice" '
             f'xlink:href="data:image/png;base64,{b64}" '
             f'xmlns:xlink="http://www.w3.org/1999/xlink"/>'
             f'<rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" fill="url(#scan)"/>'
             f'<rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" fill="url(#edge)"/>')

    # looping scan bar -- base opacity 0 so it never sticks without SMIL
    p.append(f'<rect x="{ox}" y="{oy}" width="{IW}" height="18" fill="url(#glow)" opacity="0">'
             f'<animate attributeName="y" values="{oy};{oy+IH-18};{oy+IH-18}" '
             f'keyTimes="0;{done:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;.8;.8;0;0" '
             f'keyTimes="0;0.03;{done-0.02:.4f};{done:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'</rect></g>')

    p.append(f'<rect x="{ox}" y="{oy}" width="{IW}" height="{IH}" rx="6" fill="none" stroke="{BORDER}"/>')

    # status bar
    by = oy + IH + 26
    p.append(f'<text x="{ox}" y="{by}" font-family="{MONO}" font-size="12.5" fill="{DIM}">'
             f'<tspan fill="{BLUE_D}">$</tspan> whoami</text>')
    p.append(f'<text x="{ox}" y="{by+24}" font-family="{MONO}" font-size="12.5" fill="{BLUE}">'
             f'vigneshwar l <tspan fill="{FAINT}">&#183; tamil nadu, india</tspan></text>')
    p.append(f'<rect x="{w-118}" y="{by-11}" width="94" height="6" rx="3" fill="#0d1c30"/>')
    p.append(f'<rect x="{w-118}" y="{by-11}" width="94" height="6" rx="3" fill="{BLUE_D}">'
             f'<animate attributeName="width" values="0;94;94" keyTimes="0;{done:.4f};1" '
             f'dur="{CYCLE}s" repeatCount="indefinite"/></rect>')
    p.append('</svg>')
    return "".join(p)


if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else "/Users/vignesh/Downloads/my profile .jpeg"
    svg = build(photo)
    with open("assets/panel-portrait.svg", "w") as fh:
        fh.write(svg)
    print(f"wrote assets/panel-portrait.svg ({len(svg)//1024} KB)")
