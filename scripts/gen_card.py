#!/usr/bin/env python3
"""Render the profile as white cards with one blue accent.

Each panel carries its own white background, so the page looks the same on
GitHub's light and dark themes: clean white cards, dark text, a single blue for
emphasis and the usual brand colours on the contact icons. Nothing animates.

Content comes from gen_panels.py so there is one source of truth.

Run:  GH_TOKEN=... python3 scripts/gen_card.py
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

BG = "#ffffff"
BORDER = "#e3e6ea"
INK = "#0f172a"
TEXT = "#334155"
MUTED = "#64748b"
TRACK = "#eef2f7"
ACCENT = "#2563eb"
GREEN = "#16a34a"


def esc(s):
    return gp.esc(s)


def card(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="16" '
            f'fill="{BG}" stroke="{BORDER}"/>')


def title(x, y, text, note=""):
    out = (f'<rect x="{x}" y="{y-26}" width="28" height="3" rx="1.5" fill="{ACCENT}"/>'
           f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="20" font-weight="700" '
           f'fill="{INK}">{esc(text)}</text>')
    return out


def text_width(s, size, mono=False):
    return len(s) * size * (0.605 if mono else 0.56)


def check_fits(s, size, room):
    if text_width(s, size) > room:
        raise SystemExit(f"text too wide for its box: {s!r}")


# ------------------------------------------------------------------ header --

def header():
    w, h = 1200, 320
    p = [card(w, h, "Vigneshwar L, backend, systems and AI/ML engineer")]
    x = 56
    p.append(f'<rect x="{x}" y="70" width="44" height="4" rx="2" fill="{ACCENT}"/>')
    p.append(f'<text x="{x-2}" y="148" font-family="{SERIF}" font-size="62" '
             f'fill="{INK}">Vigneshwar L</text>')
    p.append(f'<text x="{x}" y="192" font-family="{SANS}" font-size="21" '
             f'fill="{TEXT}">Backend, systems and AI/ML engineer</text>')
    cx = x
    for lang in ("Python", "Go", "Rust"):
        cw = round(text_width(lang, 13) + 28)
        p.append(f'<rect x="{cx}" y="216" width="{cw}" height="28" rx="14" fill="#eff4ff"/>'
                 f'<text x="{cx + cw/2:.0f}" y="235" font-family="{SANS}" font-size="13" '
                 f'font-weight="600" fill="{ACCENT}" text-anchor="middle">{lang}</text>')
        cx += cw + 10

    rows = [
        ("Based in", "Tamil Nadu, India"),
        ("Open source", "OpenTelemetry · CNCF · Helm · oxc · ripgrep"),
        ("Works with", "clients, startups and founders"),
        ("Builds", "models, agents, RAG and storage engines"),
    ]
    p.append(f'<rect x="640" y="64" width="1" height="{h-128}" fill="{BORDER}"/>')
    kx, vx, y = 676, 786, 100
    for k, v in rows:
        check_fits(v, 15, w - 48 - vx)
        p.append(f'<text x="{kx}" y="{y}" font-family="{SANS}" font-size="13" '
                 f'fill="{MUTED}">{esc(k)}</text>'
                 f'<text x="{vx}" y="{y}" font-family="{SANS}" font-size="15" '
                 f'fill="{INK}">{esc(v)}</text>')
        y += 38
    p.append(f'<circle cx="{kx+5}" cy="{y-5}" r="5" fill="{GREEN}"/>'
             f'<text x="{kx+20}" y="{y}" font-family="{SANS}" font-size="15" font-weight="600" '
             f'fill="{INK}">Open to projects, mentorships and contract work</text>')
    p.append("</svg>")
    return "".join(p)


# ----------------------------------------------------------------- buttons --

COFFEE = (24,
          '<path d="M2.5 4h15v9.5A5.5 5.5 0 0 1 12 19H8a5.5 5.5 0 0 1-5.5-5.5z" fill="{a}"/>'
          '<path d="M17.5 6.5h2.4a3.6 3.6 0 0 1 0 7.2h-2.4" fill="none" stroke="{a}" stroke-width="2"/>'
          '<rect x="0.5" y="20.5" width="19" height="2.2" rx="1.1" fill="{a}"/>')

BUTTONS = [
    # key, label, icon colour, fill, border
    ("linkedin", "LinkedIn", "#0a66c2", BG, "#d0d7de"),
    ("email", "Email", "#ea4335", BG, "#d0d7de"),
    ("repos", "Repositories", "#24292f", BG, "#d0d7de"),
    ("coffee", "Buy me a coffee", "#b45309", "#fff7e6", "#f5b342"),
]


def button(key, label, icol, fill, border):
    h, fs, box = 36, 13.5, 16.0
    grid, markup = COFFEE if key == "coffee" else gb.ICONS[key]
    tx = 40
    w = round(tx + text_width(label, fs) + 18)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{esc(label)}">'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="8" fill="{fill}" '
            f'stroke="{border}"/>'
            f'<g transform="translate(14,{(h-box)/2:.1f}) scale({box/grid:.4f})">'
            f'{markup.replace("{a}", icol)}</g>'
            f'<text x="{tx}" y="{h/2+4.8}" font-family="{SANS}" font-size="{fs}" '
            f'font-weight="600" fill="#1f2328">{esc(label)}</text></svg>')


# -------------------------------------------------------------------- work --

def work():
    w, h = 590, 400
    p = [card(w, h, "Work"), title(40, 66, "Work")]
    p.append(f'<text x="{w-40}" y="66" font-family="{SANS}" font-size="13" fill="{MUTED}" '
             f'text-anchor="end">2023 to now</text>')
    y = 104
    for org, role, note in gp.EXPERIENCE:
        org = org.replace("  ", " ")
        p.append(f'<circle cx="46" cy="{y+12}" r="4" fill="{ACCENT}"/>'
                 f'<text x="62" y="{y+17}" font-family="{SANS}" font-size="16" font-weight="700" '
                 f'fill="{INK}">{esc(org)}</text>'
                 f'<text x="{w-40}" y="{y+17}" font-family="{SANS}" font-size="13" '
                 f'fill="{ACCENT}" text-anchor="end">{esc(role)}</text>'
                 f'<text x="62" y="{y+42}" font-family="{SANS}" font-size="14" '
                 f'fill="{TEXT}">{esc(note)}</text>')
        if y < 104 + 3 * 70:
            p.append(f'<rect x="45.5" y="{y+22}" width="1" height="54" fill="{BORDER}"/>')
        y += 70
    p.append("</svg>")
    return "".join(p)


# --------------------------------------------------------------- languages --

def langs():
    w, h = 590, 400
    p = [card(w, h, "Languages, self-assessed proficiency out of 100"),
         title(40, 66, "Languages")]
    p.append(f'<text x="{w-40}" y="66" font-family="{SANS}" font-size="13" fill="{MUTED}" '
             f'text-anchor="end">self-assessed, out of 100</text>')
    y, bx, bw = 112, 160, 330
    for i, (name, lvl, _) in enumerate(gp.SKILLS):
        fill = round(lvl / 100 * bw)
        p.append(f'<text x="40" y="{y+12}" font-family="{SANS}" font-size="16" '
                 f'fill="{INK}">{esc(name)}</text>'
                 f'<rect x="{bx}" y="{y}" width="{bw}" height="14" rx="7" fill="{TRACK}"/>'
                 f'<rect x="{bx}" y="{y}" width="{fill}" height="14" rx="7" fill="{ACCENT}" '
                 f'opacity="{1 - i * 0.15:.2f}"/>'
                 f'<text x="{w-40}" y="{y+12}" font-family="{MONO}" font-size="14" '
                 f'fill="{TEXT}" text-anchor="end">{lvl}</text>')
        y += 52
    p.append(f'<text x="40" y="{y+30}" font-family="{SANS}" font-size="14" fill="{MUTED}">'
             f'Also C++, SQL and Bash. PyTorch, LangChain, Docker, Kubernetes.</text>')
    p.append("</svg>")
    return "".join(p)


# ----------------------------------------------------------------- skyline --

def skyline(d):
    w, h = 1200, 420
    ground = h - 64
    monthly = {}
    for wk in d["weeks"]:
        for day in wk["contributionDays"]:
            k = day["date"][:7]
            monthly[k] = monthly.get(k, 0) + day["contributionCount"]
    keys = sorted(monthly)[-12:]
    top = max((monthly[k] for k in keys), default=1) or 1

    p = [card(w, h, "Contributions per month over the last year"),
         title(40, 66, "Contributions")]
    p.append(f'<text x="{w-40}" y="58" font-family="{SANS}" font-size="15" font-weight="600" '
             f'fill="{INK}" text-anchor="end">{d["contribs"]:,} in the last year</text>'
             f'<text x="{w-40}" y="78" font-family="{SANS}" font-size="13" fill="{MUTED}" '
             f'text-anchor="end">{gp.AGG_STARS} stars across all projects and accounts</text>')

    left, right = 40, w - 40
    max_h = ground - 140
    slot = (right - left) / 12
    tw = slot - 28
    for i, k in enumerate(keys):
        total = monthly[k]
        th = max(10, round((total / top) ** 0.5 * max_h)) if total else 4
        x = left + i * slot + 14
        y = ground - th
        p.append(f'<rect x="{x:.0f}" y="{y}" width="{tw:.0f}" height="{th}" rx="5" '
                 f'fill="{ACCENT}" opacity="{0.35 + 0.65 * (total / top) ** 0.5:.2f}"/>'
                 f'<text x="{x + tw/2:.0f}" y="{y-10}" font-family="{MONO}" font-size="13" '
                 f'fill="{TEXT}" text-anchor="middle">{total}</text>'
                 f'<text x="{x + tw/2:.0f}" y="{ground+28}" font-family="{SANS}" font-size="13" '
                 f'fill="{MUTED}" text-anchor="middle">{gp.MONTHS[int(k[5:7])-1]}</text>')
    p.append(f'<rect x="{left}" y="{ground}" width="{right-left}" height="1" fill="{BORDER}"/>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    d = gp.fetch()
    os.makedirs("assets/card", exist_ok=True)
    files = {
        "header.svg": header(),
        "work.svg": work(),
        "langs.svg": langs(),
        "skyline.svg": skyline(d),
    }
    for key, label, icol, fill, border in BUTTONS:
        files[f"btn-{key}.svg"] = button(key, label, icol, fill, border)
    for name, svg in files.items():
        with open(f"assets/card/{name}", "w") as fh:
            fh.write(svg)
        print(f"wrote assets/card/{name}")
