#!/usr/bin/env python3
"""Render the black and white profile panels, in a dark and a light variant.

The README picks the right file with <picture> and prefers-color-scheme, so the
page looks deliberate on both GitHub themes instead of being a dark slab on a
white page. Backgrounds are transparent and the type does the work: a serif
name, a plain sans for prose, monospace only for small labels and figures.

Nothing here animates. A still page reads as finished; the earlier reveal
animations mostly played before anyone scrolled to them anyway.

Data (contribution calendar, work, languages) comes from gen_panels.py so there
is one source of truth for the content.

Run:  GH_TOKEN=... python3 scripts/gen_mono.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import gen_panels as gp          # noqa: E402
import gen_buttons as gb         # noqa: E402

SERIF = "Georgia, 'Iowan Old Style', 'Times New Roman', serif"
SANS = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', "
        "Helvetica, Arial, sans-serif")
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

THEMES = {
    "dark": {"fg": "#f2f2f2", "dim": "#a3a3a3", "faint": "#6b6b6b",
             "line": "#2b2b2b", "card": "#161616"},
    "light": {"fg": "#111111", "dim": "#555555", "faint": "#8c8c8c",
              "line": "#dcdcdc", "card": "#f4f4f4"},
}


def esc(s):
    return gp.esc(s)


def svg_open(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img" aria-label="{esc(label)}">')


def text_width(s, size, mono=False):
    # rough advance widths, used only to keep copy inside its box
    return len(s) * size * (0.605 if mono else 0.56)


def check_fits(s, size, room, mono=False):
    if text_width(s, size, mono) > room:
        raise SystemExit(f"text too wide for its box: {s!r}")


# ------------------------------------------------------------------ header --

def header(t):
    w, h = 1200, 300
    p = [svg_open(w, h, "Vigneshwar L, backend, systems and AI/ML engineer")]
    p.append(f'<text x="0" y="96" font-family="{SERIF}" font-size="64" '
             f'fill="{t["fg"]}">Vigneshwar L</text>')
    p.append(f'<text x="2" y="142" font-family="{SANS}" font-size="21" '
             f'fill="{t["dim"]}">Backend, systems and AI/ML engineer</text>')
    p.append(f'<text x="2" y="178" font-family="{MONO}" font-size="14" '
             f'fill="{t["faint"]}" letter-spacing="1">PYTHON  ·  GO  ·  RUST</text>')

    rows = [
        ("based in", "Tamil Nadu, India"),
        ("open source", "OpenTelemetry · CNCF · Helm · oxc · ripgrep"),
        ("works with", "clients, startups and founders"),
        ("builds", "models, agents, RAG and storage engines"),
    ]
    kx, vx, y = 640, 760, 60
    for k, v in rows:
        check_fits(v, 15, w - vx)
        p.append(f'<text x="{kx}" y="{y}" font-family="{MONO}" font-size="12" '
                 f'fill="{t["faint"]}" letter-spacing="1">{esc(k.upper())}</text>')
        p.append(f'<text x="{vx}" y="{y}" font-family="{SANS}" font-size="15" '
                 f'fill="{t["fg"]}">{esc(v)}</text>')
        y += 36
    p.append(f'<circle cx="{kx+5}" cy="{y-5}" r="4.5" fill="{t["fg"]}"/>')
    p.append(f'<text x="{kx+20}" y="{y}" font-family="{SANS}" font-size="15" '
             f'fill="{t["fg"]}" font-weight="600">Open to projects, mentorships and contract work</text>')

    p.append(f'<rect x="0" y="{h-40}" width="{w}" height="1" fill="{t["line"]}"/>')
    p.append("</svg>")
    return "".join(p)


# ----------------------------------------------------------------- buttons --

BUTTONS = [
    ("linkedin", "LinkedIn"),
    ("email", "Email"),
    ("repos", "Repositories"),
    ("coffee", "Buy me a coffee"),
]

# monochrome cup: the generator's version is a gold gradient with steam
COFFEE = (24,
          '<path d="M2.5 4h15v9.5A5.5 5.5 0 0 1 12 19H8a5.5 5.5 0 0 1-5.5-5.5z" fill="{a}"/>'
          '<path d="M17.5 6.5h2.4a3.6 3.6 0 0 1 0 7.2h-2.4" fill="none" stroke="{a}" stroke-width="2"/>'
          '<rect x="0.5" y="20.5" width="19" height="2.2" rx="1.1" fill="{a}"/>')


def button(t, key, label):
    h, fs = 34, 13
    grid, markup = COFFEE if key == "coffee" else gb.ICONS[key]
    box = 15.0
    scale = box / grid
    tx = 36
    w = round(tx + text_width(label, fs) + 16)
    return (f'{svg_open(w, h, label)}'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="6" fill="none" '
            f'stroke="{t["line"] if key != "coffee" else t["fg"]}"/>'
            f'<g transform="translate(12,{(h-box)/2:.1f}) scale({scale:.4f})">'
            f'{markup.replace("{a}", t["fg"])}</g>'
            f'<text x="{tx}" y="{h/2+4.6}" font-family="{SANS}" font-size="{fs}" '
            f'fill="{t["fg"]}" font-weight="600">{esc(label)}</text></svg>')


# --------------------------------------------------------------- languages --

def langs(t):
    w, h = 1200, 250
    p = [svg_open(w, h, "Languages, self-assessed proficiency out of 100")]
    p.append(f'<text x="0" y="22" font-family="{MONO}" font-size="12" fill="{t["faint"]}" '
             f'letter-spacing="1">PROFICIENCY, SELF-ASSESSED OUT OF 100</text>')
    y, bx, bw = 64, 180, 880
    for i, (name, lvl, _) in enumerate(gp.SKILLS):
        fill = round(lvl / 100 * bw)
        p.append(f'<text x="0" y="{y+11}" font-family="{SANS}" font-size="16" '
                 f'fill="{t["fg"]}">{esc(name)}</text>')
        p.append(f'<rect x="{bx}" y="{y}" width="{bw}" height="12" fill="{t["card"]}"/>')
        p.append(f'<rect x="{bx}" y="{y}" width="{fill}" height="12" fill="{t["fg"]}" '
                 f'opacity="{1 - i * 0.18:.2f}"/>')
        p.append(f'<text x="{w}" y="{y+11}" font-family="{MONO}" font-size="14" '
                 f'fill="{t["dim"]}" text-anchor="end">{lvl}</text>')
        y += 40
    p.append(f'<text x="0" y="{y+18}" font-family="{SANS}" font-size="14" fill="{t["faint"]}">'
             f'Also C++, SQL and Bash. PyTorch, LangChain, Docker, Kubernetes.</text>')
    p.append("</svg>")
    return "".join(p)


# ----------------------------------------------------------------- skyline --

def skyline(t, d):
    w, h = 1200, 380
    ground = h - 50
    monthly = {}
    for wk in d["weeks"]:
        for day in wk["contributionDays"]:
            k = day["date"][:7]
            monthly[k] = monthly.get(k, 0) + day["contributionCount"]
    keys = sorted(monthly)[-12:]
    top = max((monthly[k] for k in keys), default=1) or 1

    p = [svg_open(w, h, "Contributions per month over the last year")]
    p.append(f'<text x="0" y="22" font-family="{MONO}" font-size="12" fill="{t["faint"]}" '
             f'letter-spacing="1">{d["contribs"]:,} CONTRIBUTIONS IN THE LAST YEAR</text>')
    p.append(f'<text x="{w}" y="22" font-family="{MONO}" font-size="12" fill="{t["faint"]}" '
             f'letter-spacing="1" text-anchor="end">{gp.AGG_STARS} STARS ACROSS ALL PROJECTS AND ACCOUNTS</text>')

    max_h = ground - 90
    slot = w / 12
    tw = slot - 30
    for i, k in enumerate(keys):
        total = monthly[k]
        th = max(18, round((total / top) ** 0.5 * max_h)) if total else 6
        x = i * slot + 15
        y = ground - th
        p.append(f'<rect x="{x:.0f}" y="{y}" width="{tw:.0f}" height="{th}" fill="{t["fg"]}" '
                 f'opacity="{0.25 + 0.75 * (total / top) ** 0.5:.2f}"/>')
        p.append(f'<text x="{x + tw/2:.0f}" y="{y-10}" font-family="{MONO}" font-size="13" '
                 f'fill="{t["dim"]}" text-anchor="middle">{total}</text>')
        p.append(f'<text x="{x + tw/2:.0f}" y="{ground+28}" font-family="{SANS}" font-size="13" '
                 f'fill="{t["faint"]}" text-anchor="middle">{gp.MONTHS[int(k[5:7])-1]}</text>')
    p.append(f'<rect x="0" y="{ground}" width="{w}" height="1" fill="{t["line"]}"/>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    d = gp.fetch()
    os.makedirs("assets/mono", exist_ok=True)
    for mode, t in THEMES.items():
        files = {
            f"header-{mode}.svg": header(t),
            f"langs-{mode}.svg": langs(t),
            f"skyline-{mode}.svg": skyline(t, d),
        }
        for key, label in BUTTONS:
            files[f"btn-{key}-{mode}.svg"] = button(t, key, label)
        for name, svg in files.items():
            with open(f"assets/mono/{name}", "w") as fh:
                fh.write(svg)
            print(f"wrote assets/mono/{name}")
