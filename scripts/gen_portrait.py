#!/usr/bin/env python3
"""Render the dot-matrix portrait terminal panel from a source photo.

Run locally (the source photo is deliberately NOT committed):

    python3 scripts/gen_portrait.py "/path/to/photo.jpg"

Output assets/panel-portrait.svg is committed, so the profile has no runtime
dependency on the photo or on any image host.

Like gen_panels.py, every animation sits on a single timeline starting at 0s
with the stagger in keyTimes, and each element's BASE attribute is its final
visible state -- a renderer that ignores SMIL shows the finished portrait
rather than an empty frame.
"""

import sys
from PIL import Image, ImageOps, ImageEnhance

BG, PANEL, BORDER = "#05070c", "#0a0f1a", "#13395e"
BLUE, BLUE_D, DIM, FAINT = "#58a6ff", "#1f6feb", "#7d8ea3", "#41536b"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

RAMP = [None, "#0b2545", "#13395e", "#1b5299", "#1f6feb", "#58a6ff", "#a5d6ff"]
COLS, ROWS, CELL, GAP = 56, 64, 6, 1
TOTAL = 4.6                      # deliberately slow: the portrait "prints" in


def cells_from(path):
    src = Image.open(path).convert("L")
    w, h = src.size
    im = src.crop((int(w * 0.20), int(h * 0.045), int(w * 0.83), int(h * 0.62)))
    im = ImageOps.invert(im)
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Contrast(im).enhance(1.25)
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    px = im.load()
    out = []
    for y in range(ROWS):
        for x in range(COLS):
            lvl = min(len(RAMP) - 1, int((px[x, y] / 255) ** 1.1 * len(RAMP)))
            if lvl:
                out.append((x, y, lvl))
    return out


def build(path):
    cells = cells_from(path)
    step = CELL + GAP
    pw, ph = COLS * step, ROWS * step
    ox, oy = 24, 52
    w, h = pw + 48, ph + 108
    scan_end = 3.6 / TOTAL       # portrait finishes printing at ~3.6s

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
         f'height="{h}" role="img" aria-label="Vigneshwar L portrait">'
         f'<rect width="{w}" height="{h}" fill="{BG}" rx="10"/>'
         f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>'
         f'<path d="M0.5 10.5a10 10 0 0 1 10-10h{w-21}a10 10 0 0 1 10 10V34H0.5z" fill="#0d1526" stroke="{BORDER}"/>'
         f'<circle cx="20" cy="18" r="4.5" fill="#1b5299"/>'
         f'<circle cx="37" cy="18" r="4.5" fill="#205295"/>'
         f'<circle cx="54" cy="18" r="4.5" fill="#2c74b3"/>'
         f'<text x="{w/2}" y="22.5" font-family="{MONO}" font-size="12" fill="{DIM}" '
         f'text-anchor="middle">render portrait.ppm</text>']

    # scanline clip: base height = full, so no-SMIL renders the whole portrait
    p.append(f'<defs><clipPath id="scan"><rect x="{ox}" y="{oy}" width="{pw}" height="{ph}">'
             f'<animate attributeName="height" values="0;{ph};{ph}" '
             f'keyTimes="0;{scan_end:.4f};1" dur="{TOTAL}s" fill="freeze"/>'
             f'</rect></clipPath>'
             f'<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0%" stop-color="{BLUE}" stop-opacity="0"/>'
             f'<stop offset="100%" stop-color="#a5d6ff" stop-opacity=".9"/>'
             f'</linearGradient></defs>')

    p.append('<g clip-path="url(#scan)">')
    for lvl in range(1, len(RAMP)):
        pts = [c for c in cells if c[2] == lvl]
        if not pts:
            continue
        p.append(f'<g fill="{RAMP[lvl]}">')
        p += [f'<rect x="{ox+x*step}" y="{oy+y*step}" width="{CELL}" height="{CELL}" rx="1.4"/>'
              for x, y, _ in pts]
        p.append('</g>')
    p.append('</g>')

    # moving scan glow -- decorative, base opacity 0 so it never sticks
    p.append(f'<rect x="{ox}" y="{oy}" width="{pw}" height="14" fill="url(#glow)" opacity="0">'
             f'<animate attributeName="y" values="{oy};{oy+ph-14};{oy+ph-14}" '
             f'keyTimes="0;{scan_end:.4f};1" dur="{TOTAL}s" fill="freeze"/>'
             f'<animate attributeName="opacity" values="0;.85;.85;0;0" '
             f'keyTimes="0;0.04;{scan_end-0.02:.4f};{scan_end:.4f};1" dur="{TOTAL}s" fill="freeze"/></rect>')

    # PRINTING readout: counts up, base state is the finished 100%
    by = oy + ph + 22
    p.append(f'<text x="{ox}" y="{by}" font-family="{MONO}" font-size="11.5" fill="{DIM}">PRINTING</text>')
    p.append(f'<rect x="{ox+70}" y="{by-9}" width="{pw-118}" height="8" rx="4" fill="#0d1c30"/>')
    p.append(f'<rect x="{ox+70}" y="{by-9}" width="{pw-118}" height="8" rx="4" fill="{BLUE_D}">'
             f'<animate attributeName="width" values="0;{pw-118};{pw-118}" '
             f'keyTimes="0;{scan_end:.4f};1" dur="{TOTAL}s" fill="freeze"/></rect>')
    for i in range(1, 11):
        pct = i * 10
        a, b = (i - 1) / 10 * scan_end, i / 10 * scan_end
        last = i == 10
        p.append(f'<text x="{w-24}" y="{by}" font-family="{MONO}" font-size="11.5" '
                 f'fill="{BLUE}" text-anchor="end" opacity="{1 if last else 0}">{pct}%'
                 f'<animate attributeName="opacity" values="0;1;{1 if last else 0};{1 if last else 0}" '
                 f'keyTimes="0;{a:.4f};{b:.4f};1" dur="{TOTAL}s" fill="freeze"/></text>')

    p.append(f'<text x="{ox}" y="{by+22}" font-family="{MONO}" font-size="11.5" fill="{FAINT}">'
             f'<tspan fill="{BLUE_D}">$</tspan> whoami &#8594; '
             f'<tspan fill="{DIM}">vigneshwar l</tspan></text>')
    p.append('</svg>')
    return "".join(p)


if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else "/Users/vignesh/Downloads/my profile .jpeg"
    svg = build(photo)
    with open("assets/panel-portrait.svg", "w") as fh:
        fh.write(svg)
    print(f"wrote assets/panel-portrait.svg ({len(svg)} bytes)")
