#!/usr/bin/env python3
"""Particle panel: the face assembles, then morphs through the project icons.

Run locally (the source photo is deliberately NOT committed):

    python3 scripts/gen_particles.py "/path/to/photo.jpg"

Every particle is one <circle> whose cx/cy step through a shared list of
keyframes, so the whole cloud reshapes together: face -> 9 project glyphs ->
face, on a loop. This is the one thing on the page that loops; the terminals
deliberately play once and stop.

Particles are matched between keyframes by polar angle around the centroid.
Without that they cross straight through each other and the morph reads as
noise rather than as one shape becoming another.
"""

import math
import random
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

BG, PANEL, BORDER = "#05070c", "#0a0f1a", "#13395e"
BLUE, BLUE_D, DIM, FAINT = "#58a6ff", "#1f6feb", "#7d8ea3", "#41536b"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

N = 620                 # particle count
W, H = 620, 720         # particle canvas
HOLD, MORPH = 2.6, 1.5  # seconds held on a shape, and spent travelling
random.seed(7)          # stable output across runs, so re-renders don't churn


# ------------------------------------------------------------------ shapes --

def _ring(n, cx, cy, r, jitter=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n) + random.uniform(-jitter, jitter),
             cy + r * math.sin(2 * math.pi * i / n) + random.uniform(-jitter, jitter))
            for i in range(n)]


def _line(n, x0, y0, x1, y1):
    return [(x0 + (x1 - x0) * i / max(n - 1, 1),
             y0 + (y1 - y0) * i / max(n - 1, 1)) for i in range(n)]


def _arc(n, cx, cy, r, a0, a1):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / max(n - 1, 1)),
             cy + r * math.sin(a0 + (a1 - a0) * i / max(n - 1, 1))) for i in range(n)]


def shape_database():
    """FluxDB - stacked cylinder."""
    p = []
    for k in range(4):
        y = 210 + k * 100
        p += _ring(60, 310, y, 150)
        p += [(310 + 150 * math.cos(a), y + 42 * math.sin(a))
              for a in [2 * math.pi * i / 40 for i in range(40)]]
    p += _line(30, 160, 210, 160, 510) + _line(30, 460, 210, 460, 510)
    return p


def shape_nodes():
    """rustkvd - ring of nodes with a connected core."""
    p, hub = [], (310, 360)
    outer = _ring(6, 310, 360, 230)
    for (x, y) in outer:
        p += _ring(26, x, y, 34)
        p += _line(22, hub[0], hub[1], x, y)
    p += _ring(40, hub[0], hub[1], 46)
    return p


def shape_mesh():
    """TemporalMesh - lattice."""
    p = []
    for r in range(5):
        for c in range(5):
            p += _ring(10, 130 + c * 90, 180 + r * 90, 15)
    for r in range(5):
        p += _line(28, 130, 180 + r * 90, 490, 180 + r * 90)
    for c in range(5):
        p += _line(28, 130 + c * 90, 180, 130 + c * 90, 540)
    return p


def shape_bars():
    """LLM-Eval - bar chart."""
    p, hs = [], [150, 250, 190, 320, 260]
    for i, hh in enumerate(hs):
        x = 130 + i * 82
        p += _line(20, x, 560, x, 560 - hh)
        p += _line(20, x + 52, 560, x + 52, 560 - hh)
        p += _line(14, x, 560 - hh, x + 52, 560 - hh)
    p += _line(60, 100, 560, 540, 560)
    return p


def shape_vortex():
    """VORTEXRAG - spiral."""
    p = []
    for i in range(320):
        t = i / 320 * 6.2 * math.pi
        r = 18 + t * 12
        p.append((310 + r * math.cos(t), 360 + r * math.sin(t)))
    return p


def shape_wave():
    """PHANTASM - decaying waveform."""
    p = []
    for i in range(340):
        x = 90 + i * (440 / 340)
        t = i / 340 * 4 * math.pi
        p.append((x, 360 + math.sin(t) * 170 * math.exp(-i / 420)))
    p += _line(60, 90, 360, 530, 360)
    return p


def shape_hex():
    """SYNTHRON - hex network."""
    p = []
    for k, r in enumerate((110, 190, 260)):
        for i in range(6):
            a = 2 * math.pi * i / 6 + k * 0.26
            b = 2 * math.pi * (i + 1) / 6 + k * 0.26
            p += _line(18, 310 + r * math.cos(a), 360 + r * math.sin(a),
                       310 + r * math.cos(b), 360 + r * math.sin(b))
    p += _ring(30, 310, 360, 40)
    return p


def shape_gear():
    """CODEFORGE - gear."""
    p = []
    for i in range(12):
        a = 2 * math.pi * i / 12
        p += _line(14, 310 + 170 * math.cos(a), 360 + 170 * math.sin(a),
                   310 + 240 * math.cos(a), 360 + 240 * math.sin(a))
    p += _ring(120, 310, 360, 170) + _ring(50, 310, 360, 78)
    return p


def shape_layers():
    """Vashtra - a small feed-forward net."""
    p, cols = [], [(150, 4), (280, 6), (410, 5), (520, 3)]
    pts = []
    for x, k in cols:
        col = [(x, 360 + (i - (k - 1) / 2) * 78) for i in range(k)]
        pts.append(col)
        for (px, py) in col:
            p += _ring(14, px, py, 20)
    for a, b in zip(pts, pts[1:]):
        for (x0, y0) in a:
            for (x1, y1) in b:
                p += _line(6, x0, y0, x1, y1)
    return p


def shape_face(path, step=9):
    """Halftone grid sampled from the photo. Returns (x, y, weight) per particle.

    A regular grid, not random sampling: random points skip small features, so
    the eyes and nose never appeared. The white studio backdrop is masked out
    first, then weight follows BRIGHTNESS inside the subject -- lit skin gets
    dense large dots, dark hair stays sparse. Weighting by darkness instead
    renders the portrait as a negative, with the hair as a bright mass.
    """
    src = Image.open(path).convert("L")
    w, h = src.size
    im = src.crop((int(w * 0.235), int(h * 0.075), int(w * 0.795), int(h * 0.55)))
    im = im.resize((W, H), Image.LANCZOS)

    mask = im.point(lambda v: 0 if v >= 246 else (255 if v <= 224 else int((246 - v) / 22 * 255)))
    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    tone = ImageEnhance.Contrast(ImageOps.autocontrast(im, cutoff=5)).enhance(1.55)
    pt, pm = tone.load(), mask.load()

    pts = []
    for gy in range(0, H, step):
        for gx in range(0, W, step):
            t = m = cnt = 0
            for y in range(gy, min(gy + step, H)):
                for x in range(gx, min(gx + step, W)):
                    t += pt[x, y]
                    m += pm[x, y]
                    cnt += 1
            inside = (m / cnt) / 255
            bright = (t / cnt) / 255
            v = inside * (0.06 + bright * 1.06)
            if v > 0.26:
                pts.append((gx + step / 2.0, gy + step / 2.0, v))
    return pts


# --------------------------------------------------------------- resampling --

def resample(pts, n):
    """Force any point list to exactly n points."""
    if not pts:
        return [(W / 2, H / 2)] * n
    if len(pts) >= n:
        step = len(pts) / n
        return [pts[int(i * step)] for i in range(n)]
    out = list(pts)
    while len(out) < n:
        x, y = pts[len(out) % len(pts)]
        out.append((x + random.uniform(-3, 3), y + random.uniform(-3, 3)))
    return out


def by_angle(pts):
    """Order by polar angle so consecutive shapes morph without crossing over."""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return sorted(pts, key=lambda p: (math.atan2(p[1] - cy, p[0] - cx),
                                      (p[0] - cx) ** 2 + (p[1] - cy) ** 2))


def by_angle3(pts):
    """by_angle, but carrying each point's weight through the sort."""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return sorted(pts, key=lambda p: (math.atan2(p[1] - cy, p[0] - cx),
                                      (p[0] - cx) ** 2 + (p[1] - cy) ** 2))


def build(photo):
    """Two layers, because one dense animated cloud is both illegible and heavy.

    A face sharp enough to recognise needs ~2700 points, but animating that many
    through 10 shapes produced a 1.1 MB file that stuttered. So: a small MORPH
    cloud carries positions through every shape, and a dense DETAIL layer -- which
    only ever animates its opacity, not its position -- fades in over the face and
    back out before the shapes begin. Together they read as one cloud.
    """
    face_all = by_angle3(shape_face(photo, step=9))
    m = min(760, len(face_all))
    stride = len(face_all) / m
    keep = {int(i * stride) for i in range(m)}
    face_morph = [face_all[i] for i in sorted(keep)]
    detail = [p for i, p in enumerate(face_all) if i not in keep]
    n = len(face_morph)
    radii = [round(0.3 + (v ** 2.5) * 4.5, 2) for _, _, v in face_morph]

    frames = [
        ("FluxDB",       shape_database()),
        ("rustkvd",      shape_nodes()),
        ("TemporalMesh", shape_mesh()),
        ("LLM Eval",     shape_bars()),
        ("VORTEXRAG",    shape_vortex()),
        ("PHANTASM",     shape_wave()),
        ("SYNTHRON",     shape_hex()),
        ("CODEFORGE",    shape_gear()),
        ("Vashtra",      shape_layers()),
    ]
    labels = ["vigneshwar l"] + [nm for nm, _ in frames]
    clouds = [[(x, y) for x, y, _ in face_morph]]
    clouds += [by_angle(resample(pts, n)) for _, pts in frames]
    clouds.append(clouds[0])

    key_times, vals_idx, acc = [], [], 0.0
    total = (HOLD + MORPH) * (len(clouds) - 1)
    for i in range(len(clouds)):
        key_times.append(round(acc / total, 4)); vals_idx.append(i)
        acc += HOLD
        key_times.append(round(acc / total, 4)); vals_idx.append(i)
        if i < len(clouds) - 1:
            acc += MORPH
    key_times[-1] = 1.0
    kts = ";".join(f"{t:g}" for t in key_times)

    ow, oh = W + 52, H + 132
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ow} {oh}" width="{ow}" '
         f'height="{oh}" role="img" aria-label="Vigneshwar L">'
         f'<defs><radialGradient id="pg" cx="50%" cy="38%" r="70%">'
         f'<stop offset="0%" stop-color="{BLUE_D}" stop-opacity=".16"/>'
         f'<stop offset="100%" stop-color="{BLUE_D}" stop-opacity="0"/></radialGradient></defs>'
         f'<rect width="{ow}" height="{oh}" fill="{BG}" rx="12"/>'
         f'<rect x="0.5" y="0.5" width="{ow-1}" height="{oh-1}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>'
         f'<path d="M0.5 12.5a12 12 0 0 1 12-12h{ow-25}a12 12 0 0 1 12 12V42H0.5z" '
         f'fill="#0d1526" stroke="{BORDER}"/>'
         f'<circle cx="24" cy="21" r="5" fill="#1b5299"/>'
         f'<circle cx="43" cy="21" r="5" fill="#205295"/>'
         f'<circle cx="62" cy="21" r="5" fill="#2c74b3"/>'
         f'<text x="{ow/2}" y="26" font-family="{MONO}" font-size="13.5" fill="{DIM}" '
         f'text-anchor="middle">render particles</text>'
         f'<rect x="26" y="56" width="{W}" height="{H}" rx="8" fill="url(#pg)"/>']

    # detail layer: present only while the face is assembled
    dv = ["0"] * len(key_times)
    dv[0] = dv[1] = dv[-1] = dv[-2] = "1"
    p.append(f'<g fill="#a8ceff"><g opacity="1">'
             f'<animate attributeName="opacity" values="{";".join(dv)}" keyTimes="{kts}" '
             f'dur="{total:g}s" repeatCount="indefinite"/>')
    for (x, y, v) in detail:
        p.append(f'<circle cx="{x+26:.0f}" cy="{y+56:.0f}" r="{0.3+(v**2.5)*4.5:.2f}"/>')
    p.append('</g></g>')

    # morph layer: the cloud that travels through every shape
    p.append(f'<g fill="{BLUE}" opacity=".92">')
    for i in range(n):
        xs = ";".join(f"{clouds[j][i][0] + 26:.0f}" for j in vals_idx)
        ys = ";".join(f"{clouds[j][i][1] + 56:.0f}" for j in vals_idx)
        p.append(f'<circle r="{radii[i]}" cx="{clouds[0][i][0]+26:.0f}" cy="{clouds[0][i][1]+56:.0f}">'
                 f'<animate attributeName="cx" values="{xs}" keyTimes="{kts}" '
                 f'dur="{total:g}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="cy" values="{ys}" keyTimes="{kts}" '
                 f'dur="{total:g}s" repeatCount="indefinite"/></circle>')
    p.append('</g>')

    by = H + 92
    for i, name in enumerate(labels):
        on = ["0"] * len(key_times)
        on[2 * i] = on[2 * i + 1] = "1"
        p.append(f'<text x="26" y="{by}" font-family="{MONO}" font-size="13.5" '
                 f'fill="{BLUE}" opacity="{1 if i == 0 else 0}">{name}'
                 f'<animate attributeName="opacity" values="{";".join(on)}" keyTimes="{kts}" '
                 f'dur="{total:g}s" repeatCount="indefinite"/></text>')
    p.append(f'<text x="26" y="{by+28}" font-family="{MONO}" font-size="11.5" fill="{FAINT}">'
             f'particles reassemble into each project</text>')
    p.append(f'<rect x="{ow-150}" y="{by-11}" width="124" height="5" rx="2.5" fill="#0d1c30"/>'
             f'<rect x="{ow-150}" y="{by-11}" width="8" height="5" rx="2.5" fill="{BLUE_D}">'
             f'<animate attributeName="x" values="{ow-150};{ow-34}" dur="{total:g}s" '
             f'repeatCount="indefinite"/></rect>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else "/Users/vignesh/Downloads/my profile .jpeg"
    svg = build(photo)
    with open("assets/panel-particles.svg", "w") as fh:
        fh.write(svg)
    print(f"wrote assets/panel-particles.svg ({len(svg)//1024} KB, {N} particles)")
