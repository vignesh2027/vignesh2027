#!/usr/bin/env python3
"""Render dark-blue terminal panels for the profile README from live GitHub data.

Everything the profile shows is generated here and committed to the repo, so the
README never depends on a third-party render service. The public
github-readme-stats / trophy / activity-graph deployments return 402/503 for
EVERY user whenever they run out of quota, which silently breaks a profile.

Two rules hold across every panel:

1. Animations LOOP (repeatCount="indefinite") on a shared CYCLE. An earlier
   version used fill="freeze" and played once, so the reveal had always finished
   before you scrolled to it -- it looked like nothing was animating at all.

2. Each element's BASE attribute is its FINAL, visible state, and the stagger
   lives in keyTimes rather than begin=. A renderer that ignores SMIL then shows
   the finished panel instead of an empty box.
"""

import json
import os
import subprocess
import sys

USER = "vignesh2027"
CYCLE = 9.0

BG     = "#05070c"
PANEL  = "#0a0f1a"
BORDER = "#13395e"
BLUE   = "#58a6ff"
BLUE_D = "#1f6feb"
DIM    = "#7d8ea3"
FAINT  = "#41536b"
TEXT   = "#e6edf3"
MONO   = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def gh(args):
    out = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if out.returncode != 0:
        print("gh failed:", out.stderr[:400], file=sys.stderr)
        sys.exit(1)
    return json.loads(out.stdout)


def anim(attr, final, t, dur=0.45, start="0"):
    k1 = min(max(t, 0) / CYCLE, 0.995)
    k2 = min((max(t, 0) + dur) / CYCLE, 0.997)
    return (f'<animate attributeName="{attr}" values="{start};{start};{final};{final}" '
            f'keyTimes="0;{k1:.4f};{k2:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>')


def fade(t, dur=0.45):
    return anim("opacity", "1", t, dur)


def defs(uid):
    """Shared gradients: soft inner glow + top highlight."""
    return (f'<defs>'
            f'<radialGradient id="g{uid}" cx="50%" cy="0%" r="90%">'
            f'<stop offset="0%" stop-color="{BLUE_D}" stop-opacity=".14"/>'
            f'<stop offset="100%" stop-color="{BLUE_D}" stop-opacity="0"/>'
            f'</radialGradient>'
            f'<linearGradient id="r{uid}" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{BLUE_D}"/>'
            f'<stop offset="100%" stop-color="#0b2545"/>'
            f'</linearGradient></defs>')


def shell(uid, w, h, title, label):
    """Terminal window: frame, title bar, three dots, inner glow, status rule."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{esc(label)}">'
            + defs(uid) +
            f'<rect width="{w}" height="{h}" fill="{BG}" rx="12"/>'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="11" fill="url(#g{uid})"/>'
            f'<path d="M0.5 12.5a12 12 0 0 1 12-12h{w-25}a12 12 0 0 1 12 12V40H0.5z" '
            f'fill="#0d1526" stroke="{BORDER}"/>'
            f'<circle cx="24" cy="20.5" r="5" fill="#1b5299"/>'
            f'<circle cx="43" cy="20.5" r="5" fill="#205295"/>'
            f'<circle cx="62" cy="20.5" r="5" fill="#2c74b3"/>'
            f'<text x="{w/2}" y="25.5" font-family="{MONO}" font-size="13" fill="{DIM}" '
            f'text-anchor="middle">{esc(title)}</text>'
            f'<rect x="0" y="{h-30}" width="{w}" height="29" fill="#080d16"/>'
            f'<rect x="0" y="{h-30}" width="{w}" height="1" fill="{BORDER}"/>')


def status(w, h, left, right):
    return (f'<text x="26" y="{h-11}" font-family="{MONO}" font-size="11.5" fill="{FAINT}">{esc(left)}</text>'
            f'<text x="{w-26}" y="{h-11}" font-family="{MONO}" font-size="11.5" fill="{FAINT}" '
            f'text-anchor="end">{esc(right)}</text>')


def typed(uid, x, y, text, t, size=15, cps=26):
    dur = max(0.5, len(text) / cps)
    w = (len(text) + 2) * size * 0.605 + 14   # +2 for the '$ ' prefix
    return (f'<defs><clipPath id="{uid}"><rect x="{x}" y="{y-size}" height="{size+8}" width="{w}">'
            + anim("width", f"{w:.1f}", t, dur) + '</rect></clipPath></defs>'
            f'<g clip-path="url(#{uid})"><text x="{x}" y="{y}" font-family="{MONO}" '
            f'font-size="{size}" fill="{BLUE}"><tspan fill="{BLUE_D}">$</tspan> {esc(text)}</text></g>'), t + dur


def caret(x, y, t, size=15):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{BLUE_D}" '
            f'opacity="1">$ <tspan fill="{DIM}">_'
            f'<animate attributeName="opacity" values="1;0;1" dur="1.15s" repeatCount="indefinite"/>'
            f'</tspan>{fade(t)}</text>')


def fetch():
    q = """
    { user(login: "%s") {
        followers { totalCount }
        contributionsCollection { contributionCalendar { totalContributions } }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes { stargazerCount
                  languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
                    edges { size node { name color } } } } }
    } }""" % USER
    u = gh(["api", "graphql", "-f", f"query={q}"])["data"]["user"]
    langs = {}
    for n in u["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            k = e["node"]["name"]
            langs.setdefault(k, {"size": 0, "color": e["node"]["color"] or BLUE})
            langs[k]["size"] += e["size"]
    return {
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "contribs": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "langs": sorted(langs.items(), key=lambda kv: -kv[1]["size"])[:6],
    }


def panel_identity():
    w, h = 706, 684
    rows = [
        ("NAME",   "Vigneshwar L", TEXT),
        ("ROLE",   "Backend  ·  Systems  ·  AI / ML Engineer", TEXT),
        ("STACK",  "Go   ·   Rust   ·   Python", BLUE),
        ("OPEN",   "OpenTelemetry · CNCF · Helm", DIM),
        ("",       "oxc · ripgrep", DIM),
        ("WORK",   "AI trainer & model evaluator", DIM),
        ("",       "Shipd (Datacurve)  ·  Handshake AI", DIM),
        ("BUILD",  "storage engines, distributed systems,", DIM),
        ("",       "and the tests that keep them honest", DIM),
        ("BASE",   "Tamil Nadu, India", DIM),
        ("NOW",    "reading other people's code, mostly", DIM),
    ]
    p = [shell("id", w, h, "vigneshwar@github ~ profile", "Vigneshwar L")]
    cmd, t = typed("cid", 30, 82, "cat /etc/profile", 0.3, size=15)
    p.append(cmd)
    y, t = 132, t + 0.35
    for k, v, col in rows:
        p.append(f'<g opacity="1">{fade(t)}')
        if k:
            p.append(f'<text x="30" y="{y}" font-family="{MONO}" font-size="14" '
                     f'fill="{BLUE_D}" font-weight="600">{esc(k)}</text>')
        p.append(f'<text x="126" y="{y}" font-family="{MONO}" font-size="14.5" '
                 f'fill="{col}">{esc(v)}</text></g>')
        y += 36 if k else 28
        t += 0.3
    p.append(f'<g opacity="1">{fade(t)}'
             f'<rect x="30" y="{y+6}" width="{w-60}" height="1" fill="{BORDER}"/>'
             f'<text x="30" y="{y+38}" font-family="{MONO}" font-size="14" fill="{BLUE}">'
             f'&#9679; available for hire</text>'
             f'<text x="30" y="{y+64}" font-family="{MONO}" font-size="12.5" fill="{FAINT}">'
             f'B.Tech CSE &#183; Cambridge Linguaskill C1</text></g>')
    p.append(caret(30, y + 100, t + 0.3))
    p.append(status(w, h, "profile.sh", "utf-8   ln 1:1"))
    p.append("</svg>")
    return "".join(p)


def panel_story():
    w, h = 1200, 486
    rows = [
        ("2023", "started B.Tech CSE. wrote the first code that actually ran.", TEXT),
        ("2024", "went low-level. C++, then Rust. learned how machines really work.", DIM),
        ("2025", "wrote FluxDB, a time-series database from scratch in Rust,", DIM),
        ("",     "to find out where the cost actually lives inside a storage engine.", DIM),
        ("2026", "started contributing to open source communities:", TEXT),
        ("",     "OpenTelemetry  ·  CNCF  ·  Helm  ·  oxc  ·  ripgrep", BLUE),
        ("2026", "joined Shipd (Datacurve) and Handshake AI,", DIM),
        ("",     "training and evaluating frontier models.", DIM),
        ("now",  "building systems, and reading a lot of other people's code.", TEXT),
    ]
    p = [shell("st", w, h, "vigneshwar@github ~ story", "how it started")]
    cmd, t = typed("cst", 30, 82, "git log --reverse --oneline --author=vigneshwar", 0.3, size=15)
    p.append(cmd)
    y, t = 128, t + 0.4
    for year, txt, col in rows:
        p.append(f'<g opacity="1">{fade(t)}')
        if year:
            p.append(f'<text x="30" y="{y}" font-family="{MONO}" font-size="14.5" '
                     f'fill="{BLUE_D}" font-weight="600">{esc(year)}</text>'
                     f'<text x="92" y="{y}" font-family="{MONO}" font-size="14.5" fill="{FAINT}">|</text>')
        p.append(f'<text x="120" y="{y}" font-family="{MONO}" font-size="14.5" '
                 f'fill="{col}">{esc(txt)}</text></g>')
        y += 34 if year else 27
        t += 0.32
    p.append(f'<g opacity="1">{fade(t)}'
             f'<text x="30" y="{y+22}" font-family="{MONO}" font-size="12" fill="{FAINT}">'
             f'~$2k earned to date authoring and grading frontier-model training data</text></g>')
    p.append(status(w, h, "story.log", "9 entries"))
    p.append("</svg>")
    return "".join(p)


def panel_stats(d):
    w, h = 592, 360
    rows = [
        ("contributions", f"{d['contribs']:,}", "last 365 days"),
        ("repositories",  f"{d['repos']}", "sources"),
        ("stars",         f"{d['stars']}", ""),
        ("followers",     f"{d['followers']}", ""),
    ]
    p = [shell("sx", w, h, "vignesh2027 ~ stats", "stats")]
    cmd, t = typed("csx", 28, 80, "gh api users/vignesh2027", 0.3, size=14)
    p.append(cmd)
    y, t = 128, t + 0.35
    for k, v, note in rows:
        dots = "." * max(2, 22 - len(k))
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="28" y="{y}" font-family="{MONO}" font-size="14" fill="{DIM}">'
                 f'{esc(k)} <tspan fill="#16324f">{dots}</tspan> '
                 f'<tspan fill="{TEXT}" font-weight="700" font-size="15">{esc(v)}</tspan>'
                 + (f'  <tspan fill="{FAINT}" font-size="11">{esc(note)}</tspan>' if note else "")
                 + '</text></g>')
        y += 34
        t += 0.3
    p.append(caret(28, y + 12, t + 0.2, size=14))
    p.append(status(w, h, "live", "auto-refreshed 6h"))
    p.append("</svg>")
    return "".join(p)


def panel_langs(d):
    w, h = 592, 360
    total = sum(v["size"] for _, v in d["langs"]) or 1
    p = [shell("lx", w, h, "vignesh2027 ~ languages", "languages")]
    cmd, t = typed("clx", 28, 80, "tokei --sort code", 0.3, size=14)
    p.append(cmd)
    y, t = 112, t + 0.35
    for name, v in d["langs"]:
        pct = v["size"] / total * 100
        bw = max(5, round(pct / 100 * 320))
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="28" y="{y+11}" font-family="{MONO}" font-size="13" fill="{TEXT}">{esc(name)}</text>'
                 f'<rect x="160" y="{y+1}" width="320" height="12" rx="6" fill="#0d1c30"/>'
                 f'<rect x="160" y="{y+1}" width="{bw}" height="12" rx="6" fill="{v["color"]}">'
                 + anim("width", str(bw), t + 0.1, 0.85) + '</rect>'
                 f'<text x="{w-28}" y="{y+11}" font-family="{MONO}" font-size="12.5" fill="{DIM}" '
                 f'text-anchor="end">{pct:.1f}%</text></g>')
        y += 33
        t += 0.32
    p.append(status(w, h, "by bytes across public sources", ""))
    p.append("</svg>")
    return "".join(p)


PROJECTS = [
    ("FluxDB", "Rust", "#dea584",
     "Time-series database, from scratch.",
     "Columnar compression, fast range queries."),
    ("rustkvd", "Rust", "#dea584",
     "Distributed key-value store.",
     "Raft consensus, LSM engine, MVCC, gRPC."),
    ("TemporalMesh", "PyTorch", "#ee4c2c",
     "An original transformer architecture.",
     "Mesh attention, adaptive depth routing."),
    ("LLM Eval", "Python", "#3572A5",
     "Evaluation and benchmarking harness.",
     "Rubric grading, reproducible scoring."),
    ("VORTEXRAG", "Python", "#3572A5",
     "Seven-layer retrieval framework.",
     "Built against drift and context poisoning."),
    ("PHANTASM", "Python", "#3572A5",
     "Hallucination-inversion research.",
     "Uncertainty calibration over generated text."),
]


def panel_projects():
    w = 1200
    cols, cw, gap = 3, 372, 22
    rows_n = (len(PROJECTS) + cols - 1) // cols
    ch, top = 132, 108
    # Panel must clear the last card AND the 30px status bar, or the bottom row
    # renders straight through it.
    h = top + rows_n * ch + (rows_n - 1) * gap + 46
    # Monospace advance is ~0.6em; anything wider than the card bleeds past its
    # border, which is how the first cut of this panel broke.
    for nm, _lang, _c, l1, l2 in PROJECTS:
        for txt, size in ((l1, 12.5), (l2, 12.0)):
            if len(txt) * size * 0.6 > cw - 40:
                raise SystemExit(
                    f"project copy too wide for {cw}px card: {nm!r}: {txt!r} "
                    f"({len(txt)} chars, max {int((cw - 40) / (size * 0.6))})")

    p = [shell("pj", w, h, "vigneshwar@github ~ projects", "projects")]
    cmd, t = typed("cpj", 30, 80, "ls -1 ~/projects", 0.3, size=15)
    p.append(cmd)
    t += 0.35
    for i, (name, lang, col, line1, line2) in enumerate(PROJECTS):
        cx = 30 + (i % cols) * (cw + gap)
        cy = top + (i // cols) * (ch + gap)
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="10" '
                 f'fill="#0b1220" stroke="{BORDER}"/>'
                 f'<rect x="{cx}" y="{cy}" width="{cw}" height="3" rx="1.5" fill="url(#rpj)"/>'
                 f'<text x="{cx+20}" y="{cy+36}" font-family="{MONO}" font-size="16" '
                 f'fill="{TEXT}" font-weight="700">{esc(name)}</text>'
                 f'<circle cx="{cx+cw-64}" cy="{cy+31}" r="4.5" fill="{col}"/>'
                 f'<text x="{cx+cw-52}" y="{cy+36}" font-family="{MONO}" font-size="12" '
                 f'fill="{DIM}">{esc(lang)}</text>'
                 f'<text x="{cx+20}" y="{cy+66}" font-family="{MONO}" font-size="12.5" '
                 f'fill="{BLUE}">{esc(line1)}</text>'
                 f'<text x="{cx+20}" y="{cy+90}" font-family="{MONO}" font-size="12" '
                 f'fill="{DIM}">{esc(line2)}</text></g>')
        t += 0.26
    p.append(status(w, h, f"{len(PROJECTS)} of 68 repositories", "github.com/vignesh2027"))
    p.append("</svg>")
    return "".join(p)


def panel_signoff():
    """Closing block. The scaling rings are the last thing on the page."""
    w, h = 1200, 300
    p = [shell("so", w, h, "vigneshwar@github ~ ", "thanks for scrolling")]
    cmd, t = typed("cso", 30, 82, "echo $CONTACT", 0.3, size=15)
    p.append(cmd)
    t += 0.4
    p.append(f'<g opacity="1">{fade(t)}'
             f'<text x="30" y="132" font-family="{MONO}" font-size="19" fill="{TEXT}" '
             f'font-weight="700">Open to backend, systems and cloud-native roles.</text>'
             f'<text x="30" y="166" font-family="{MONO}" font-size="14" fill="{DIM}">'
             f'linkedin.com/in/vigneshwar-l-td729994</text>'
             f'<text x="30" y="192" font-family="{MONO}" font-size="14" fill="{DIM}">'
             f'lkvarnesh@gmail.com</text></g>')

    # scaling rings -- pure decoration, they pulse outward on the shared cycle
    cx, cy = w - 150, 150
    for i in range(4):
        d = i * (CYCLE / 4)
        p.append(f'<circle cx="{cx}" cy="{cy}" r="26" fill="none" stroke="{BLUE_D}" '
                 f'stroke-width="1.4" opacity="0">'
                 f'<animate attributeName="r" values="26;92" dur="{CYCLE}s" '
                 f'begin="{d:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.55;0" dur="{CYCLE}s" '
                 f'begin="{d:.2f}s" repeatCount="indefinite"/></circle>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="none" stroke="{BLUE}" stroke-width="1.6"/>'
             f'<circle cx="{cx}" cy="{cy}" r="6" fill="{BLUE}">'
             f'<animate attributeName="opacity" values="1;.35;1" dur="2.6s" repeatCount="indefinite"/>'
             f'</circle>')
    p.append(status(w, h, "thanks for scrolling", "vignesh2027"))
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    d = fetch()
    os.makedirs("assets", exist_ok=True)
    for name, svg in (("panel-identity.svg", panel_identity()),
                      ("panel-story.svg",    panel_story()),
                      ("panel-stats.svg",    panel_stats(d)),
                      ("panel-langs.svg",    panel_langs(d)),
                      ("panel-projects.svg", panel_projects()),
                      ("panel-signoff.svg",  panel_signoff())):
        with open(f"assets/{name}", "w") as fh:
            fh.write(svg)
        print(f"wrote assets/{name} ({len(svg)} bytes)")
    print(json.dumps({k: v for k, v in d.items() if k != "langs"}))
