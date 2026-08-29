#!/usr/bin/env python3
"""Render the dark-blue panels for the profile README from live GitHub data.

Everything the profile shows is generated here and committed to the repo, so the
README never depends on a third-party render service. The public
github-readme-stats / trophy / activity-graph deployments return 402/503 for
EVERY user whenever they run out of quota, which silently breaks a profile.

Layout intent: only the identity block and the closing story are terminal
windows. Everything between them is a plain styled section with charts, because
a page made entirely of terminal chrome reads as noise rather than as design.

Timing: these panels reveal ONCE, slowly, and stop (fill="freeze", no
repeatCount). Only the particle panel loops. Each element's base attribute is
its final visible state, so a renderer that ignores SMIL shows the finished
panel rather than an empty box -- qlmanage evaluates at t=0, so verify by
stripping <animate> and rendering that instead.
"""

import json
import os
import subprocess
import sys

USER = "vignesh2027"

# Cumulative star figure spanning earlier accounts, repos since made private and
# projects that were sold on. It cannot be derived from this account's API, so it
# is ALWAYS rendered with an explicit "all projects & accounts" label.
AGG_STARS = "4,658"
REVEAL = 26.0       # whole-panel reveal length; deliberately slow

# Monochrome base with a single warm accent. Dark blue read as "another dev
# profile"; black and white with one accent colour is the more restrained,
# more professional look, and the accent carries the emphasis on its own.
# Premium dark blue: a near-black blue ground with a clean bright accent.
# Reads more expensive than either the flat navy or the pure monochrome that
# came before it.
BG     = "#04050a"
PANEL  = "#06080f"
CARD   = "#0b1020"
BORDER = "#1b2740"
TEXT   = "#e8eefc"
DIM    = "#8ea2c4"
FAINT  = "#4a5b7a"
ACCENT = "#4d8dff"
ACC_D  = "#7aa7ff"
# aliases so existing call sites keep working
BLUE   = TEXT
BLUE_D = ACCENT
CYAN   = ACCENT
VIOLET = "#9db6ff"
LIT    = "#cfe0ff"
MONO   = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

HEAT = ["#0e1526", "#1b2b4a", "#2f4a7d", "#4d8dff", "#9dc0ff"]

# Windows in the skyline towers: lit ones cycle through the accent range so the
# panel has colour without leaving the dark-blue scheme.
WINDOW = ["#4d8dff", "#6ea1ff", "#8fb6ff", "#b3ceff", "#dcebff"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def gh(args):
    out = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if out.returncode != 0:
        print("gh failed:", out.stderr[:400], file=sys.stderr)
        sys.exit(1)
    return json.loads(out.stdout)


def anim(attr, final, t, dur=0.5, start="0", span=REVEAL):
    """One-shot reveal on a shared timeline; stagger lives in keyTimes."""
    k1 = min(max(t, 0) / span, 0.995)
    k2 = min((max(t, 0) + dur) / span, 0.997)
    return (f'<animate attributeName="{attr}" values="{start};{start};{final};{final}" '
            f'keyTimes="0;{k1:.4f};{k2:.4f};1" dur="{span}s" fill="freeze"/>')


def fade(t, dur=0.5, span=REVEAL):
    return anim("opacity", "1", t, dur, span=span)


def particles(uid, w, h, n=150):
    """Disabled. The drifting dot field read as noise rather than depth, so the
    background is now a flat near-black with only the soft top glow for depth.
    Kept as a no-op so every call site stays valid.
    """
    return ""


def _particles_unused(uid, w, h, n=150):
    """Former particle field.

    Positions come from a small deterministic LCG rather than random(), so a
    rebuild produces byte-identical output and the committed SVG only changes
    when the data does.
    """
    seed = sum(ord(c) for c in uid) * 7919 + 12345
    out = [f'<g clip-path="url(#c{uid})">']
    for i in range(n):
        seed = (1103515245 * seed + 12345) % (1 << 31)
        x = seed % w
        seed = (1103515245 * seed + 12345) % (1 << 31)
        y = seed % h
        seed = (1103515245 * seed + 12345) % (1 << 31)
        r = 0.6 + (seed % 100) / 100 * 1.5
        seed = (1103515245 * seed + 12345) % (1 << 31)
        op = 0.05 + (seed % 100) / 100 * 0.22
        seed = (1103515245 * seed + 12345) % (1 << 31)
        dur = 9 + (seed % 100) / 100 * 14
        col = "#9db6ff"
        out.append(f'<circle cx="{x}" cy="{y}" r="{r:.2f}" fill="{col}" opacity="{op:.3f}">'
                   f'<animate attributeName="opacity" values="{op:.3f};{op*2.4:.3f};{op:.3f}" '
                   f'dur="{dur:.1f}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="cy" values="{y};{max(0, y-14)};{y}" '
                   f'dur="{dur*1.7:.1f}s" repeatCount="indefinite"/></circle>')
    out.append('</g>')
    return "".join(out)


def head(uid, w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{esc(label)}">'
            f'<defs><radialGradient id="g{uid}" cx="50%" cy="0%" r="90%">'
            f'<stop offset="0%" stop-color="#4d8dff" stop-opacity=".07"/>'
            f'<stop offset="100%" stop-color="#4d8dff" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="r{uid}" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{ACCENT}"/>'
            f'<stop offset="100%" stop-color="#0e1526"/></linearGradient>'
            f'<clipPath id="c{uid}"><rect width="{w}" height="{h}"/></clipPath>'
            f'</defs>')


def shell(uid, w, h, title, label, black=False):
    bg = "#000000" if black else PANEL
    return (head(uid, w, h, label) +
            f'<rect width="{w}" height="{h}" fill="{bg}"/>'
            f'<rect width="{w}" height="{h}" fill="url(#g{uid})"/>'
            + particles(uid, w, h) +
            f'<path d="M0.5 12.5a12 12 0 0 1 12-12h{w-25}a12 12 0 0 1 12 12V42H0.5z" '
            f'fill="#0a0f1c" stroke="{BORDER}"/>'
            f'<circle cx="24" cy="21" r="5" fill="#25334f"/>'
            f'<circle cx="43" cy="21" r="5" fill="#35486d"/>'
            f'<circle cx="62" cy="21" r="5" fill="{ACCENT}" opacity=".8"/>'
            f'<text x="{w/2}" y="26" font-family="{MONO}" font-size="13.5" fill="{DIM}" '
            f'text-anchor="middle">{esc(title)}</text>')


def section(uid, w, h, title, label, kicker=""):
    s = (head(uid, w, h, label) +
         # Full-bleed and unstroked: rounded, bordered sections read as a stack
         # of boxes; butting them together makes the README one continuous page.
         f'<rect width="{w}" height="{h}" fill="{PANEL}"/>'
         f'<rect width="{w}" height="{h}" fill="url(#g{uid})"/>'
         + particles(uid, w, h) +
         f'<rect x="30" y="34" width="46" height="3" rx="1.5" fill="url(#r{uid})"/>'
         f'<text x="30" y="72" font-family="{MONO}" font-size="21" fill="{TEXT}" '
         f'font-weight="700">{esc(title)}</text>')
    if kicker:
        s += (f'<text x="{w-30}" y="72" font-family="{MONO}" font-size="12.5" fill="{FAINT}" '
              f'text-anchor="end">{esc(kicker)}</text>')
    return s


def typed(uid, x, y, text, t, size=15, cps=13, span=REVEAL):
    dur = max(0.8, len(text) / cps)
    cw = (len(text) + 2) * size * 0.605 + 14   # +2 covers the "$ " prefix
    return (f'<defs><clipPath id="{uid}"><rect x="{x}" y="{y-size}" height="{size+9}" width="{cw:.1f}">'
            + anim("width", f"{cw:.1f}", t, dur, span=span) + '</rect></clipPath></defs>'
            f'<g clip-path="url(#{uid})"><text x="{x}" y="{y}" font-family="{MONO}" '
            f'font-size="{size}" fill="{BLUE}"><tspan fill="{BLUE_D}">$</tspan> {esc(text)}</text></g>'), t + dur


def fetch():
    q = """
    { user(login: "%s") {
        followers { totalCount }
        contributionsCollection { contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount weekday } } } }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
            totalCount nodes { stargazerCount } }
    } }""" % USER
    u = gh(["api", "graphql", "-f", f"query={q}"])["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "contribs": cal["totalContributions"],
        "weeks": cal["weeks"],
    }


# ------------------------------------------------------------------- header --

# The page is pure black and white; the editor pane is the single place colour
# appears, and it is there because syntax highlighting is what code actually
# looks like. It reads as a working engineer rather than a stock graphic.
SYN = {
    "kw":   "#c586c0",   # keyword
    "ty":   "#4ec9b0",   # type
    "fn":   "#dcdcaa",   # function
    "str":  "#ce9178",   # string
    "num":  "#b5cea8",   # number
    "com":  "#6a9955",   # comment
    "op":   "#d4d4d4",   # punctuation / plain
    "var":  "#9cdcfe",   # binding
}

CODE = [
    [("impl", "kw"), (" ", "op"), ("Engine", "ty"), (" {", "op")],
    [("    fn ", "kw"), ("flush", "fn"), ("(&", "op"), ("mut ", "kw"), ("self", "var"),
     (") -> ", "op"), ("Result", "ty"), ("<()> {", "op")],
    [("        // fsync before the memtable rotates", "com")],
    [("        self", "var"), (".wal.", "op"), ("sync", "fn"), ("()?;", "op")],
    [("", "op")],
    [("        let ", "kw"), ("seg", "var"), (" = ", "op"), ("self", "var"),
     (".memtable.", "op"), ("freeze", "fn"), ("();", "op")],
    [("        self", "var"), (".levels[", "op"), ("0", "num"), ("].", "op"),
     ("push", "fn"), ("(", "op"), ("seg", "var"), (");", "op")],
    [("        self", "var"), (".metrics.", "op"), ("record", "fn"), ("(", "op"),
     ('"flush"', "str"), (");", "op")],
    [("", "op")],
    [("        Ok", "ty"), ("(())", "op")],
    [("    }", "op")],
    [("}", "op")],
]



def headset(cx, cy, r, col="#33507f", mic_left=True):
    """Over-ear headset: band, cups, boom mic with a live indicator."""
    mx = cx - r - 5 if mic_left else cx + r + 5
    tip = mx + (9 if mic_left else -9)
    return (f'<path d="M{cx-r-2} {cy} a{r+2} {r+2} 0 0 1 {2*(r+2)} 0" fill="none" '
            f'stroke="{col}" stroke-width="4" stroke-linecap="round"/>'
            f'<rect x="{cx-r-6}" y="{cy-3}" width="9" height="15" rx="4.5" fill="{col}"/>'
            f'<rect x="{cx+r-3}" y="{cy-3}" width="9" height="15" rx="4.5" fill="{col}"/>'
            f'<path d="M{mx} {cy+10} q {6 if mic_left else -6} 9 {tip-mx} 12" fill="none" '
            f'stroke="{col}" stroke-width="2.6" stroke-linecap="round"/>'
            f'<circle cx="{tip}" cy="{cy+22}" r="2.6" fill="{ACCENT}">'
            f'<animate attributeName="opacity" values="1;.3;1" dur="3.4s" repeatCount="indefinite"/>'
            f'</circle>')


def desk_monitor(x, y, w=132, h=88):
    """A small monitor on the desk, screen scrolling its own output."""
    g = [f'<g transform="translate({x},{y})">']
    g.append(f'<rect width="{w}" height="{h}" rx="6" fill="#0a1020" stroke="#2b3d5e"/>'
             f'<rect x="5" y="5" width="{w-10}" height="{h-14}" rx="3" fill="#050a16"/>')
    g.append(f'<clipPath id="mscr"><rect x="5" y="5" width="{w-10}" height="{h-14}"/></clipPath>')
    rows = ["$ cargo test", "  wal .... ok", "  lsm .... ok", "  raft ... ok",
            "3 passed", "$ ./deploy", "  building", "  shipped"]
    g.append('<g clip-path="url(#mscr)"><g>'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0; 0 -96; 0 0" dur="34s" repeatCount="indefinite"/>')
    for i, r in enumerate(rows):
        col = "#6ee7a8" if "ok" in r or "passed" in r else DIM
        g.append(f'<text x="11" y="{18 + i*12}" font-family="{MONO}" font-size="7.5" '
                 f'fill="{col}">{esc(r)}</text>')
    g.append('</g></g>')
    g.append(f'<rect x="{w/2-14}" y="{h-9}" width="28" height="5" fill="#2b3d5e"/>'
             f'<rect x="{w/2-24}" y="{h-5}" width="48" height="4" rx="2" fill="#22314f"/>')
    g.append('</g>')
    return "".join(g)


def pc_case(x, y):
    """Tower under the desk, drive light blinking."""
    return (f'<g transform="translate({x},{y})">'
            f'<rect width="34" height="62" rx="4" fill="#0d1424" stroke="#2b3d5e"/>'
            f'<rect x="7" y="8" width="20" height="3" rx="1.5" fill="#22314f"/>'
            f'<rect x="7" y="15" width="20" height="3" rx="1.5" fill="#22314f"/>'
            f'<circle cx="11" cy="28" r="2.6" fill="{ACCENT}">'
            f'<animate attributeName="opacity" values="1;.15;1" dur="1.6s" repeatCount="indefinite"/>'
            f'</circle>'
            f'<circle cx="21" cy="28" r="2.2" fill="#6ee7a8">'
            f'<animate attributeName="opacity" values=".2;1;.2" dur="4.2s" repeatCount="indefinite"/>'
            f'</circle>'
            f'<rect x="7" y="40" width="20" height="14" rx="2" fill="#050a16"/></g>')


def bug_hunt(x, y, w=430):
    """A snake hunting three bugs in sequence, getting faster each time.

    Right to the first bug, turn and back left for the second, then a fast dash
    right for the third. Each bug vanishes as the snake reaches it. The body is
    one stroked path whose `d` is animated between two wave phases, so it reads
    as a snake rather than the string of loose dots this was before.
    """
    # x positions of the three bugs, and the timeline that hunts them
    b1, b2, b3 = 232, 96, 330
    legs = [12.0, 8.0, 4.5, 3.5]                 # slower -> faster, then a pause
    total = sum(legs)
    k = []
    acc = 0.0
    for L in legs:
        acc += L
        k.append(acc / total)

    g = [f'<g transform="translate({x},{y})">']
    g.append(f'<rect x="0" y="40" width="{w}" height="1" fill="#16203a"/>')
    g.append(f'<text x="0" y="14" font-family="{MONO}" font-size="11" fill="{FAINT}">'
             f'$ debugging &#8212; three bugs, one snake, increasing speed</text>')

    # --- the three bugs ---
    for i, (bx, gone) in enumerate([(b1, k[0]), (b2, k[1]), (b3, k[2])]):
        g.append(f'<g transform="translate({bx},0)" opacity="1">'
                 f'<animate attributeName="opacity" values="1;1;0;0;1" '
                 f'keyTimes="0;{gone:.4f};{min(gone+0.012,0.999):.4f};0.9999;1" '
                 f'dur="{total}s" calcMode="discrete" repeatCount="indefinite"/>'
                 f'<g stroke="#c94848" stroke-width="1.2" stroke-linecap="round" fill="none">'
                 f'<path d="M-4 29 l-4.5 -4"/><path d="M-4 32.5 l-5 1"/><path d="M-4 36 l-4.5 4"/>'
                 f'<path d="M4 29 l4.5 -4"/><path d="M4 32.5 l5 1"/><path d="M4 36 l4.5 4"/></g>'
                 f'<ellipse cx="0" cy="33" rx="5" ry="4" fill="#e05a5a"/>'
                 f'<ellipse cx="0" cy="31.5" rx="5" ry="1.5" fill="#c94848"/>'
                 f'<circle cx="0" cy="27.5" r="2.5" fill="#c94848"/>'
                 f'<path d="M-1.5 25.5 l-2 -3 M1.5 25.5 l2 -3" stroke="#c94848" stroke-width="1.1" '
                 f'stroke-linecap="round" fill="none"/>'
                 f'<circle cx="-1" cy="27" r="0.7" fill="#f2d0d0"/>'
                 f'<circle cx="1" cy="27" r="0.7" fill="#f2d0d0"/></g>')

    # --- the snake ---
    g.append(f'<g transform="translate(80,0)">'
             f'<animateTransform attributeName="transform" type="translate" '
             f'values="80 0; {b1} 0; {b2} 0; {b3} 0; 80 0" '
             f'keyTimes="0;{k[0]:.4f};{k[1]:.4f};{k[2]:.4f};1" '
             f'dur="{total}s" repeatCount="indefinite"/>')
    # inner group flips to face the direction of travel
    g.append(f'<g><animateTransform attributeName="transform" type="scale" '
             f'values="1 1; -1 1; 1 1; 1 1; 1 1" '
             f'keyTimes="0;{k[0]:.4f};{k[1]:.4f};{k[2]:.4f};1" '
             f'dur="{total}s" calcMode="discrete" repeatCount="indefinite"/>')
    body_a = "M0 32 q -13 -7 -26 0 t -24 0"
    body_b = "M0 32 q -13 7 -26 0 t -24 0"
    g.append(f'<path d="{body_a}" fill="none" stroke="{ACCENT}" stroke-width="9" '
             f'stroke-linecap="round" opacity=".95">'
             f'<animate attributeName="d" values="{body_a};{body_b};{body_a}" dur="2.4s" '
             f'repeatCount="indefinite"/></path>')
    g.append(f'<path d="{body_a}" fill="none" stroke="{ACC_D}" stroke-width="3.2" '
             f'stroke-linecap="round" opacity=".5">'
             f'<animate attributeName="d" values="{body_a};{body_b};{body_a}" dur="2.4s" '
             f'repeatCount="indefinite"/></path>')
    g.append(f'<ellipse cx="5" cy="32" rx="8" ry="6.5" fill="{ACC_D}"/>'
             f'<circle cx="7.5" cy="30" r="1.5" fill="#04050a"/>'
             f'<path d="M13 32 l6 -2.5 m-6 2.5 l6 2.5" stroke="#e05a5a" stroke-width="1.2" '
             f'fill="none" stroke-linecap="round">'
             f'<animate attributeName="opacity" values="1;0;1;1" dur="1.1s" '
             f'repeatCount="indefinite"/></path>')
    g.append('</g></g></g>')
    return "".join(g)


def workstation(x, y, label_rows, flip=False):
    """A monitor on the desk with its own scrolling output."""
    w, h = 116, 78
    uid = f"scr{x}"
    g = [f'<g transform="translate({x},{y})">']
    g.append(f'<rect width="{w}" height="{h}" rx="5" fill="#0a1020" stroke="#2b3d5e"/>'
             f'<rect x="4" y="4" width="{w-8}" height="{h-13}" rx="3" fill="#050a16"/>'
             f'<clipPath id="{uid}"><rect x="4" y="4" width="{w-8}" height="{h-13}"/></clipPath>')
    g.append(f'<g clip-path="url(#{uid})"><g>'
             f'<animateTransform attributeName="transform" type="translate" '
             f'values="0 0; 0 -{11*len(label_rows)//2}; 0 0" dur="30s" repeatCount="indefinite"/>')
    for i, r in enumerate(label_rows):
        col = "#6ee7a8" if ("ok" in r or "pass" in r) else DIM
        g.append(f'<text x="9" y="{15 + i*11}" font-family="{MONO}" font-size="7" '
                 f'fill="{col}">{esc(r)}</text>')
    g.append('</g></g>')
    g.append(f'<rect x="{w/2-12}" y="{h-8}" width="24" height="4" fill="#2b3d5e"/>'
             f'<rect x="{w/2-21}" y="{h-5}" width="42" height="4" rx="2" fill="#22314f"/>')
    g.append('</g>')
    return "".join(g)



def laptop(x, y, rows):
    """A laptop: tilted lid with scrolling output, and a wedge base."""
    w, h = 118, 72
    uid = f"lap{x}"
    g = [f'<g transform="translate({x},{y})">']
    g.append(f'<rect width="{w}" height="{h}" rx="5" fill="#0a1020" stroke="#2b3d5e"/>'
             f'<rect x="4" y="4" width="{w-8}" height="{h-8}" rx="3" fill="#050a16"/>'
             f'<clipPath id="{uid}"><rect x="4" y="4" width="{w-8}" height="{h-8}"/></clipPath>')
    g.append(f'<g clip-path="url(#{uid})"><g>'
             f'<animateTransform attributeName="transform" type="translate" '
             f'values="0 0; 0 -{11*len(rows)//2}; 0 0" dur="38s" repeatCount="indefinite"/>')
    for i, r in enumerate(rows):
        col = "#6ee7a8" if ("ok" in r or "pass" in r or "merged" in r) else DIM
        g.append(f'<text x="9" y="{15 + i*11}" font-family="{MONO}" font-size="7" '
                 f'fill="{col}">{esc(r)}</text>')
    g.append('</g></g>')
    # base wedge, wider than the lid
    g.append(f'<path d="M-13 {h+1} h{w+26} l-9 9 h{-(w+8)} z" fill="#22314f"/>'
             f'<rect x="{w/2-16}" y="{h+3}" width="32" height="2.5" rx="1.25" fill="#0f1830"/>')
    g.append('</g>')
    return "".join(g)


def mug(x, y):
    """Coffee, steaming."""
    return (f'<g transform="translate({x},{y})">'
            f'<path d="M0 0 h16 v13 a8 8 0 0 1 -16 0 z" fill="#e8eefc"/>'
            f'<path d="M16 3 h4 a4 4 0 0 1 0 8 h-4" fill="none" stroke="#e8eefc" stroke-width="2.2"/>'
            f'<rect x="2" y="2" width="12" height="2.5" rx="1.25" fill="#6b4a2f"/>'
            f'<g stroke="#8ea2c4" stroke-width="1.4" stroke-linecap="round" fill="none" opacity=".55">'
            f'<path d="M5 -5 q3 -4 0 -8"><animate attributeName="opacity" '
            f'values=".15;.6;.15" dur="4.2s" repeatCount="indefinite"/></path>'
            f'<path d="M11 -5 q3 -5 0 -9"><animate attributeName="opacity" '
            f'values=".6;.15;.6" dur="4.2s" repeatCount="indefinite"/></path></g></g>')


def scene(x, y, t):
    """Tux and a rubber duck pair-programming, each at their own screen.

    Both type: Tux's flippers and the duck's wings tap their keyboards, the
    duck's lower beak hinges as it talks, and each screen scrolls its own
    output. The status line is a clipped scroller rather than stacked <text>
    elements, which previously printed all three messages on top of each other.
    """
    g = [f'<g transform="translate({x},{y})" opacity="1">{fade(t)}']

    g.append(pc_case(0, 138))
    g.append(f'<rect x="0" y="132" width="520" height="7" rx="3.5" fill="#16203a"/>'
             f'<rect x="487" y="139" width="7" height="50" fill="#0f1830"/>')

    g.append(workstation(112, 52, ["$ cargo test", " wal ... ok", " lsm ... ok",
                                   " raft .. ok", "3 passed", "$ ./deploy", " shipped"]))
    g.append(laptop(300, 56, ["$ git diff", " +12 -4", "$ review", " nit: naming",
                              " looks ok", "$ approve", " merged"]))
    g.append(mug(258, 112))

    # --- Tux, typing ---
    g.append('<g transform="translate(18,44)">'
             '<path d="M-4 84 h68 v10 a10 10 0 0 1 -10 10 h-48 a10 10 0 0 1 -10 -10 z" fill="#16203a"/>'
             '<ellipse cx="29" cy="62" rx="28" ry="26" fill="#12151c"/>'
             '<ellipse cx="29" cy="66" rx="18.5" ry="19.5" fill="#e8eefc"/>'
             '<ellipse cx="29" cy="24" rx="20.5" ry="19.5" fill="#12151c"/>'
             '<ellipse cx="21.5" cy="23" rx="6" ry="7.5" fill="#e8eefc"/>'
             '<ellipse cx="36.5" cy="23" rx="6" ry="7.5" fill="#e8eefc"/>'
             '<circle cx="23" cy="24" r="3" fill="#0a0c11"/>'
             '<circle cx="35" cy="24" r="3" fill="#0a0c11"/>'
             '<ellipse cx="29" cy="34" rx="7" ry="4.8" fill="#f5a623"/>'
             + headset(29, 12, 20, mic_left=False) +
             '<rect x="0" y="82" width="58" height="8" rx="3" fill="#22314f"/>'
             '<rect x="4" y="84" width="50" height="2" rx="1" fill="#0f1830"/>'
             '<ellipse cx="11" cy="78" rx="8" ry="5" fill="#12151c">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0; 0 4; 0 0" dur="0.9s" repeatCount="indefinite"/></ellipse>'
             '<ellipse cx="47" cy="78" rx="8" ry="5" fill="#12151c">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0; 0 4; 0 0" dur="0.9s" begin="0.45s" repeatCount="indefinite"/></ellipse>'
             '</g>')

    # --- duck, typing and talking ---
    g.append('<g transform="translate(400,52)">'
             '<path d="M-4 76 h68 v10 a10 10 0 0 1 -10 10 h-48 a10 10 0 0 1 -10 -10 z" fill="#16203a"/>'
             '<ellipse cx="29" cy="56" rx="28" ry="21" fill="#f7c948"/>'
             '<path d="M7 56 q12 -16 31 -9 -9 14 -31 9z" fill="#e0a915"/>'
             '<g><animateTransform attributeName="transform" type="rotate" '
             'values="0 38 28; -6 38 28; 0 38 28; 0 38 28" dur="5.2s" repeatCount="indefinite"/>'
             '<circle cx="38" cy="26" r="16" fill="#f7c948"/>'
             '<path d="M52 22h9q5 0 5 4t-5 4h-9z" fill="#f0932b"/>'
             '<path d="M52 30h9q4 0 4 3t-4 3h-9z" fill="#d97e1f">'
             '<animateTransform attributeName="transform" type="rotate" '
             'values="0 52 30; 12 52 30; 0 52 30; 0 52 30; 4 52 30; 0 52 30" '
             'dur="2.1s" repeatCount="indefinite"/></path>'
             '<circle cx="43" cy="21" r="2.8" fill="#12151c"/>'
             '<circle cx="44.1" cy="19.9" r="1" fill="#ffffff"/>'
             # glasses
             '<g fill="none" stroke="#1b2029" stroke-width="2.2">'
             '<circle cx="43" cy="21" r="7.5"/><circle cx="28" cy="23" r="7"/>'
             '<path d="M35.6 21.4 q3.5 -2 7 -0.6"/><path d="M21 22 l-6 -2"/></g>'
             '<circle cx="43" cy="21" r="7.5" fill="#cfe0ff" opacity=".12"/>'
             '<circle cx="28" cy="23" r="7" fill="#cfe0ff" opacity=".12"/>'
             + headset(38, 15, 16, mic_left=True) + '</g>'
             # keyboard, and both wings tapping it
             '<rect x="0" y="74" width="58" height="8" rx="3" fill="#22314f"/>'
             '<rect x="4" y="76" width="50" height="2" rx="1" fill="#0f1830"/>'
             '<ellipse cx="11" cy="70" rx="8.5" ry="5.5" fill="#e0a915">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0; 0 4; 0 0" dur="0.78s" repeatCount="indefinite"/></ellipse>'
             '<ellipse cx="47" cy="70" rx="8.5" ry="5.5" fill="#e0a915">'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0; 0 4; 0 0" dur="0.78s" begin="0.39s" repeatCount="indefinite"/></ellipse>'
             '</g>')

    # --- status: clipped scroller, so exactly one line is ever visible ---
    msgs = [("running tests ...", DIM), ("3 passed, 0 failed", "#6ee7a8"),
            ("reviewing the diff ...", DIM), ("LGTM - ship it", ACC_D)]
    g.append('<clipPath id="stat"><rect x="130" y="158" width="300" height="20"/></clipPath>')
    g.append('<g clip-path="url(#stat)"><g>'
             '<animateTransform attributeName="transform" type="translate" '
             'values="0 0; 0 -22; 0 -44; 0 -66; 0 0" keyTimes="0;0.25;0.5;0.75;1" '
             'dur="26s" repeatCount="indefinite"/>')
    for i, (m, col) in enumerate(msgs):
        g.append(f'<text x="280" y="{173 + i*22}" font-family="{MONO}" font-size="12.5" '
                 f'fill="{col}" text-anchor="middle">{esc(m)}</text>')
    g.append('</g></g>')
    g.append('</g>')
    return "".join(g)


# The code pane tells the story of code itself, not a personal timeline:
# hello world, then input and failure, then concurrency, then the guards you
# only write once something is in production.
SCENES = [
    ("hello.rs", [
        [("fn ", "kw"), ("main", "fn"), ("() {", "op")],
        [('    println!', "fn"), ("(", "op"), ('"hello, world"', "str"), (");", "op")],
        [("}", "op")],
    ]),
    ("input.rs", [
        [("fn ", "kw"), ("parse", "fn"), ("(", "op"), ("s", "var"), (": &", "op"),
         ("str", "ty"), (") -> ", "op"), ("Result", "ty"), ("<", "op"), ("u64", "ty"), ("> {", "op")],
        [("    // the first thing the world teaches you", "com")],
        [("    s.", "op"), ("trim", "fn"), ("().", "op"), ("parse", "fn"),
         ("().", "op"), ("map_err", "fn"), ("(Error::", "op"), ("Parse", "ty"), (")", "op")],
        [("}", "op")],
    ]),
    ("worker.rs", [
        [("async fn ", "kw"), ("run", "fn"), ("(", "op"), ("jobs", "var"), (": ", "op"),
         ("Receiver", "ty"), ("<", "op"), ("Job", "ty"), (">) {", "op")],
        [("    while let ", "kw"), ("Some", "ty"), ("(job) = jobs.", "op"),
         ("recv", "fn"), ("().", "op"), ("await", "kw"), (" {", "op")],
        [("        tokio::", "op"), ("spawn", "fn"), ("(", "op"), ("handle", "fn"), ("(job));", "op")],
        [("    }", "op")],
        [("}", "op")],
    ]),
    ("guard.rs", [
        [("// production is where the edge cases live", "com")],
        [("fn ", "kw"), ("admit", "fn"), ("(&", "op"), ("self", "var"), (", ", "op"),
         ("req", "var"), (": ", "op"), ("Request", "ty"), (") -> ", "op"), ("Result", "ty"), ("<()> {", "op")],
        [("    if ", "kw"), ("self", "var"), (".inflight >= ", "op"), ("self", "var"), (".limit {", "op")],
        [("        return ", "kw"), ("Err", "ty"), ("(", "op"), ("Shed", "ty"), ("::Overloaded);", "op")],
        [("    }", "op")],
        [("    self", "var"), (".budget.", "fn"), ("charge", "fn"), ("(req.cost)?;", "op")],
        [("    Ok", "ty"), ("(())", "op")],
        [("}", "op")],
    ]),
]

SYN = {
    "kw":  "#c586c0", "ty":  "#4ec9b0", "fn":  "#dcdcaa", "str": "#ce9178",
    "num": "#b5cea8", "com": "#6a9955", "op":  "#d4d4d4", "var": "#9cdcfe",
}

SCENE_SECS = 16.0                     # each program gets its own slow turn
CYCLE_SECS = SCENE_SECS * len(SCENES)


def panel_header(d):
    """Name and title left; a code pane and the pair-programming desk right."""
    w, h = 1240, 596
    lx = 40
    ex, ey, ew, eh = 636, 56, 566, 268
    fs, lh = 13, 21
    ch = fs * 0.605

    p = [head("hd", w, h, "Vigneshwar L")]
    p.append(f'<rect width="{w}" height="{h}" fill="{PANEL}"/>'
             f'<rect width="{w}" height="{h}" fill="url(#ghd)"/>')

    # ---- left: identity ----
    p.append(f'<g opacity="1">{fade(0.6)}'
             f'<rect x="{lx}" y="72" width="52" height="3" rx="1.5" fill="url(#rhd)"/>'
             f'<text x="{lx}" y="132" font-family="{MONO}" font-size="38" fill="{TEXT}" '
             f'font-weight="700">Vigneshwar L</text></g>')
    lines = [
        ("Backend  ·  Systems  ·  AI / ML", TEXT, 15.5, 1.8),
        ("Python  ·  Go  ·  Rust", DIM, 14.5, 3.0),
        ("OpenTelemetry · CNCF · Helm · oxc · ripgrep", DIM, 13.5, 4.2),
        ("clients, startups & founders · Shipd · Handshake AI", DIM, 13.5, 5.4),
        ("models, RL environments, agents, RAG and storage engines", DIM, 13.5, 6.6),
        ("Tamil Nadu, India", FAINT, 13, 7.8),
    ]
    y = 170
    for txt, col, size, t in lines:
        p.append(f'<text x="{lx}" y="{y}" font-family="{MONO}" font-size="{size}" '
                 f'fill="{col}" opacity="1">{esc(txt)}{fade(t, 1.0)}</text>')
        y += 30
    p.append(f'<g opacity="1">{fade(9.2, 1.0)}'
             f'<rect x="{lx}" y="{y+6}" width="540" height="1" fill="{BORDER}"/>'
             f'<circle cx="{lx+6}" cy="{y+44}" r="5.5" fill="{ACCENT}">'
             f'<animate attributeName="opacity" values="1;.25;1" dur="3.6s" repeatCount="indefinite"/>'
             f'</circle>'
             f'<text x="{lx+22}" y="{y+49}" font-family="{MONO}" font-size="15" fill="{TEXT}" '
             f'font-weight="700">looking for open source contributions</text>'
             f'<text x="{lx}" y="{y+78}" font-family="{MONO}" font-size="12.5" fill="{FAINT}">'
             f'open to new projects, mentorships and international contract work</text></g>')

    # ---- left, lower: the snake hunting a bug ----
    p.append(f'<g opacity="1">{fade(11.0, 1.2)}' + bug_hunt(lx, 470) + '</g>')

    # ---- right: code pane, cycling through the scenes ----
    p.append(f'<rect x="{ex}" y="{ey}" width="{ew}" height="{eh}" rx="10" fill="#080c18" '
             f'stroke="{BORDER}"/>'
             f'<path d="M{ex}.5 {ey+10}a10 10 0 0 1 10-10h{ew-21}a10 10 0 0 1 10 10v22H{ex}.5z" '
             f'fill="#0f1526" stroke="{BORDER}"/>'
             f'<circle cx="{ex+18}" cy="{ey+17}" r="4" fill="#25334f"/>'
             f'<circle cx="{ex+33}" cy="{ey+17}" r="4" fill="#35486d"/>'
             f'<circle cx="{ex+48}" cy="{ey+17}" r="4" fill="{ACCENT}" opacity=".8"/>'
             f'<rect x="{ex+1}" y="{ey+33}" width="34" height="{eh-34}" fill="#0a0f1e"/>')

    for si, (fname, code) in enumerate(SCENES):
        k0 = si * SCENE_SECS / CYCLE_SECS
        k1 = (si * SCENE_SECS + 0.4) / CYCLE_SECS
        k2 = ((si + 1) * SCENE_SECS - 0.8) / CYCLE_SECS
        k3 = ((si + 1) * SCENE_SECS - 0.4) / CYCLE_SECS
        last = si == len(SCENES) - 1
        # base opacity: the final scene stays visible if SMIL never runs
        p.append(f'<g opacity="{1 if last else 0}">'
                 f'<animate attributeName="opacity" values="0;1;1;0;0" '
                 f'keyTimes="0;{k1:.4f};{k2:.4f};{k3:.4f};1" dur="{CYCLE_SECS}s" '
                 f'repeatCount="indefinite"/>')
        p.append(f'<text x="{ex+ew/2}" y="{ey+21}" font-family="{MONO}" font-size="12" '
                 f'fill="{FAINT}" text-anchor="middle">{esc(fname)}</text>')
        cy = ey + 62
        tt = si * SCENE_SECS + 0.8
        for li, spans in enumerate(code):
            plain = "".join(tx for tx, _ in spans)
            p.append(f'<text x="{ex+22}" y="{cy}" font-family="{MONO}" font-size="11.5" '
                     f'fill="#2b3d5e" text-anchor="end">{li+1}</text>')
            if plain.strip():
                cw = len(plain) * ch + 10
                uid = f"s{si}l{li}"
                a0 = tt / CYCLE_SECS
                a1 = (tt + max(0.9, len(plain) / 14)) / CYCLE_SECS
                p.append(f'<clipPath id="{uid}"><rect x="{ex+44}" y="{cy-fs}" height="{fs+7}" '
                         f'width="{cw:.1f}">'
                         f'<animate attributeName="width" values="0;0;{cw:.1f};{cw:.1f}" '
                         f'keyTimes="0;{a0:.4f};{a1:.4f};1" dur="{CYCLE_SECS}s" '
                         f'repeatCount="indefinite"/></rect></clipPath>')
                p.append(f'<g clip-path="url(#{uid})"><text x="{ex+44}" y="{cy}" '
                         f'font-family="{MONO}" font-size="{fs}" xml:space="preserve">')
                for tx, kind in spans:
                    p.append(f'<tspan fill="{SYN[kind]}">{esc(tx)}</tspan>')
                p.append('</text></g>')
                tt += max(0.9, len(plain) / 14) + 0.25
            cy += lh
        p.append('</g>')

    # ---- right, lower: the desk ----
    p.append(scene(ex + 40, ey + 300, 12.0))
    p.append("</svg>")
    return "".join(p)



EXPERIENCE = [
    ("Clients & startups", "since 2023",
     "Early-stage builds, usually as the only engineer."),
    ("Shipd  ·  Datacurve", "AI trainer",
     "Training data authored and graded against rubrics."),
    ("Handshake AI", "model evaluator",
     "Prompt authoring and preference ranking."),
    ("Open source", "contributor",
     "OpenTelemetry, CNCF, Helm, oxc, ripgrep."),
]


def panel_experience():
    w, h = 610, 420
    p = [section("ex", w, h, "Work", "experience", "2023 — now")]
    y, t = 104, 1.0
    for org, role, note in EXPERIENCE:
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<rect x="30" y="{y}" width="{w-60}" height="66" fill="{CARD}"/>'
                 f'<rect x="30" y="{y}" width="3" height="66" rx="1.5" fill="{BLUE_D}"/>'
                 f'<text x="46" y="{y+26}" font-family="{MONO}" font-size="14" fill="{TEXT}" '
                 f'font-weight="700">{esc(org)}</text>'
                 f'<text x="{w-46}" y="{y+26}" font-family="{MONO}" font-size="11.5" fill="{BLUE}" '
                 f'text-anchor="end">{esc(role)}</text>'
                 f'<text x="46" y="{y+49}" font-family="{MONO}" font-size="11.5" fill="{DIM}">{esc(note)}</text>'
                 f'</g>')
        y += 76
        t += 1.5
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- languages --

# Monochrome ramp with the accent on the leader. GitHub's official language
# colours were the only hues left breaking the black-and-white scheme.
SKILLS = [
    ("Python",     72, ACCENT),
    ("Rust",       68, "#ffffff"),
    ("Go",         65, "#9aa0a6"),
    ("TypeScript", 42, "#3a4f78"),
]


def panel_langs():
    """Self-assessed proficiency, not repo byte share -- labelled as such."""
    w, h = 610, 420
    p = [section("lx", w, h, "Languages", "languages", "proficiency")]
    y, t = 118, 1.0
    for name, lvl, colr in SKILLS:
        bw = round(lvl / 100 * 320)
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="30" y="{y+12}" font-family="{MONO}" font-size="14" fill="{TEXT}">{esc(name)}</text>'
                 f'<rect x="170" y="{y+1}" width="320" height="14" rx="7" fill="#0e1526"/>'
                 f'<rect x="170" y="{y+1}" width="{bw}" height="14" rx="7" fill="{colr}">'
                 + anim("width", str(bw), t + 0.2, 1.6) + '</rect>'
                 f'<text x="{w-30}" y="{y+12}" font-family="{MONO}" font-size="13" fill="{DIM}" '
                 f'text-anchor="end">{lvl}</text></g>')
        y += 52
        t += 1.5
    p.append(f'<g opacity="1">{fade(t)}'
             f'<text x="30" y="{y+22}" font-family="{MONO}" font-size="11.5" fill="{FAINT}">'
             f'also C++, SQL, Bash &#183; PyTorch, LangChain, Docker, Kubernetes</text></g>')
    p.append("</svg>")
    return "".join(p)


# ------------------------------------------------------------------ skyline --

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def panel_skyline(d):
    """Stars and contributions in one panel: stat tiles above, skyline below.

    Two things this fixes from the first cut. The upper half was dead space, so
    the star and repo figures now live up there instead of in a separate panel.
    And every day of a month is drawn as a window -- unlit when there was no
    activity -- so a quiet month reads as a dark tower rather than an empty box.
    """
    w, h = 1240, 480
    ground = h - 78

    monthly, days = {}, {}
    for wk in d["weeks"]:
        for day in wk["contributionDays"]:
            k = day["date"][:7]
            monthly[k] = monthly.get(k, 0) + day["contributionCount"]
            days.setdefault(k, []).append(day["contributionCount"])
    keys = sorted(monthly)[-12:]
    top = max((monthly[k] for k in keys), default=1) or 1

    p = [section("ct", w, h, "Contributions & stars", "contributions and stars",
                 f"{d['contribs']:,} contributions in the last year")]

    # --- stat tiles fill what used to be empty sky ---
    # Only the star figure remains: the communities / projects / years tiles
    # were noise beside a chart that already says how much work happens.
    tiles = [
        (AGG_STARS, "stars", "all projects & accounts", TEXT),
    ]
    tw = 300
    for i, (big, lab, note, col) in enumerate(tiles):
        x = 30 + i * (tw + 18)
        p.append(f'<g opacity="1">{fade(0.6 + i * 0.5)}'
                                  f'<rect x="{x}" y="96" width="{tw}" height="2.5" rx="1.25" fill="url(#rct)"/>'
                 f'<text x="{x+18}" y="140" font-family="{MONO}" font-size="28" fill="{col}" '
                 f'font-weight="700">{esc(big)}</text>'
                 f'<text x="{x+18}" y="162" font-family="{MONO}" font-size="12.5" fill="{DIM}">{esc(lab)}</text>'
                 f'<text x="{x+18}" y="179" font-family="{MONO}" font-size="10.5" fill="{FAINT}">{esc(note)}</text>'
                 f'</g>')

    # --- skyline ---
    max_h = ground - 206

    def height_of(total):
        # sqrt, not linear: one 385-commit month against a 12-commit one flattens
        # every quiet month to an invisible stub on a linear scale.
        # High floor so a quiet month is still a lit building rather than a
        # stub leaving a hole in the skyline; the exact figure is printed
        # above every tower, so the compression misleads nobody.
        return max(128, round((total / top) ** 0.5 * max_h))

    # No sky rectangle: a filled band behind the towers drew a visible box edge,
    # which is exactly the look being removed everywhere else. Just the ground.
    p.append(f'<rect x="30" y="{ground}" width="{w-60}" height="2" rx="1" fill="{BORDER}"/>')

    slot = (w - 60) / 12
    tower_w = slot - 26

    for i, k in enumerate(keys):
        total = monthly[k]
        th = height_of(total)
        x = 30 + i * slot + 13
        ty = ground - th
        t = 3.0 + i * 0.7

        p.append(f'<g opacity="1">{fade(t)}')
        p.append(f'<rect x="{x:.0f}" y="{ty:.0f}" width="{tower_w:.0f}" height="{th}" rx="5" '
                 f'fill="{CARD}" stroke="{BORDER}">'
                 + anim("height", str(th), t, 1.2)
                 + anim("y", f"{ty:.0f}", t, 1.2, start=str(ground)) + '</rect>')
        p.append(f'<rect x="{x:.0f}" y="{ty:.0f}" width="{tower_w:.0f}" height="3" rx="1.5" '
                 f'fill="{CYAN if total else BORDER}">'
                 + anim("y", f"{ty:.0f}", t, 1.2, start=str(ground)) + '</rect>')

        # Windows light at random in EVERY tower, with the lit fraction scaled by
        # how busy the month was and floored so a quiet month still reads as an
        # occupied building rather than a dark slab. Deterministic LCG, so a
        # rebuild is byte-identical.
        cols = max(1, int((tower_w - 14) // 13))
        rows_fit = max(0, int((th - 22) // 15))
        lit_ratio = max(0.42, min(0.88, total / top))
        seed = (i + 1) * 7919 + 104729
        for n in range(cols * rows_fit):
            wx = x + 8 + (n % cols) * 13
            wy = ty + 14 + (n // cols) * 15
            seed = (1103515245 * seed + 12345) % (1 << 31)
            roll = (seed % 1000) / 1000
            seed = (1103515245 * seed + 12345) % (1 << 31)
            if roll < lit_ratio:
                shade = WINDOW[seed % len(WINDOW)]
                op = 0.55 + (seed % 45) / 100
            else:
                shade, op = "#1b2740", 0.85
            p.append(f'<rect x="{wx:.0f}" y="{wy:.0f}" width="7" height="8" rx="1.5" '
                     f'fill="{shade}" opacity="{op:.2f}">'
                     + anim("opacity", f"{op:.2f}", t + 0.5 + n * 0.01, 0.5) + '</rect>')

        p.append(f'<text x="{x + tower_w/2:.0f}" y="{ground+26}" font-family="{MONO}" '
                 f'font-size="12.5" fill="{DIM}" text-anchor="middle">{MONTHS[int(k[5:7])-1]}</text>')
        p.append(f'<text x="{x + tower_w/2:.0f}" y="{ty-11:.0f}" font-family="{MONO}" '
                 f'font-size="13" fill="{CYAN if total else FAINT}" text-anchor="middle" '
                 f'font-weight="700">{total}</text>')
        p.append('</g>')

    p.append(f'<text x="30" y="{h-20}" font-family="{MONO}" font-size="11.5" fill="{FAINT}" '
             # Windows are lit at random now, so the old "each window = a day"
             # caption would be untrue. Height is the only claim being made.
             f'opacity="1">{fade(11.5)}tower height = commits that month</text>')
    p.append("</svg>")
    return "".join(p)


# -------------------------------------------------------------------- story --

PAGES = [
    ("who", [
        "I am Vigneshwar. I build backend and systems software, and I help train",
        "the models that are starting to write it too.",
        "",
        "Most of my work has been for other people's companies at the point where",
        "nothing exists yet: clients, early-stage startups, founders and",
        "co-founders who need the first version to actually work.",
    ]),
    ("what I build", [
        "Models, reinforcement-learning environments, agents and RAG systems on",
        "one side. Storage engines, distributed systems and backend services on",
        "the other.",
        "",
        "The two halves inform each other more than people expect. Knowing where",
        "latency really comes from makes you a better engineer of AI systems, not",
        "just a better backend developer.",
    ]),
    ("2023  —  starting", [
        "I started B.Tech Computer Science in Tamil Nadu with very little idea",
        "what I was doing. The first programs I wrote barely ran.",
        "",
        "What changed things was realising that almost everything worth learning",
        "was already written down, in public, in other people's repositories.",
        "So I started reading them. I still do, most days.",
    ]),
    ("2024  —  going lower", [
        "I got tired of not knowing what was underneath. C++ first, then Rust,",
        "which I picked because it refuses to let you stay vague about ownership",
        "and lifetimes.",
        "",
        "Learning it was slow and occasionally humiliating, and it taught me more",
        "about how machines actually work than the two years before it combined.",
    ]),
    ("2025  —  building the hard thing", [
        "I wrote FluxDB, a time-series database, from scratch in Rust. Not",
        "because the world needed another one, but because I wanted to find out",
        "where the cost really lives inside a storage engine: columnar",
        "compression, a write path worth benchmarking, a great deal of profiling.",
        "",
        "Then rustkvd, a distributed key-value store with Raft consensus, an LSM",
        "engine and MVCC, for the same reason applied to consensus.",
    ]),
    ("2026  —  models and agents", [
        "I began working with Shipd (Datacurve) and Handshake AI, authoring",
        "training data and grading model output against detailed rubrics.",
        "",
        "Alongside that: agent systems, RL environments and retrieval pipelines",
        "for startups who needed them working, not demonstrated. Evaluation is",
        "the part most people skip, and it is the part that decides whether any",
        "of it survives contact with real inputs.",
    ]),
    ("open source", [
        "OpenTelemetry, CNCF, Helm, oxc, ripgrep.",
        "",
        "Working in codebases that size teaches one specific skill: reading",
        "unfamiliar code well enough to change it without breaking anything, then",
        "taking the review that follows seriously.",
        "",
        "Much of what I contributed was tests, because tests are how you find out",
        "whether you actually understood the thing you just read.",
    ]),
    ("now", [
        "Still building systems. Still reading more code than I write.",
        "",
        "If you are hiring for backend, systems or cloud-native work, or you have",
        "something at an early stage that needs building properly, the contact",
        "details are at the top of this page.",
    ]),
]

PAGE_HOLD = 7.0


def panel_story():
    """One page at a time, slowly, once through. Does not loop."""
    w, h = 1240, 430
    span = PAGE_HOLD * len(PAGES)
    p = [shell("so", w, h, "vigneshwar@github ~ cat story.md", "the long version", black=True)]
    cmd, _ = typed("cso", 30, 88, "cat ~/story.md", 0.5, size=15, span=span)
    p.append(cmd)

    widest = max(len(l) for _, ls in PAGES for l in ls)
    if widest * 13.5 * 0.605 > w - 60:
        raise SystemExit(f"story line too wide: {widest} chars, "
                         f"max {int((w - 60) / (13.5 * 0.605))}")

    for i, (heading, lines) in enumerate(PAGES):
        t0 = 1.6 + i * PAGE_HOLD
        # visible for its own slot only; the last page stays up at the end
        last = i == len(PAGES) - 1
        kt = [0.0, max(0.0001, (t0 - 0.5) / span), min(t0 / span, 0.99),
              min((t0 + PAGE_HOLD - 0.7) / span, 0.995),
              min((t0 + PAGE_HOLD - 0.2) / span, 0.998), 1.0]
        vv = ["0", "0", "1", "1", "1" if last else "0", "1" if last else "0"]
        kt = [round(min(max(v, 0.0), 1.0), 5) for v in kt]
        for j in range(1, len(kt)):
            kt[j] = max(kt[j], kt[j - 1] + 1e-5)
        kt[-1] = 1.0
        p.append(f'<g opacity="{1 if last else 0}">'
                 f'<animate attributeName="opacity" values="{";".join(vv)}" '
                 f'keyTimes="{";".join(f"{v:g}" for v in kt)}" dur="{span}s" fill="freeze"/>')
        p.append(f'<text x="30" y="132" font-family="{MONO}" font-size="15" fill="{BLUE}" '
                 f'font-weight="700">{esc(heading)}</text>')
        y = 172
        for ln in lines:
            if ln:
                p.append(f'<text x="30" y="{y}" font-family="{MONO}" font-size="13.5" '
                         f'fill="{DIM}">{esc(ln)}</text>')
            y += 26
        p.append(f'<text x="{w-30}" y="{h-18}" font-family="{MONO}" font-size="11.5" '
                 f'fill="{FAINT}" text-anchor="end">{i+1} / {len(PAGES)}</text>')
        p.append('</g>')

    p.append(f'<text x="30" y="{h-18}" font-family="{MONO}" font-size="13" fill="{BLUE_D}" '
             f'opacity="1">$ <tspan fill="{DIM}">_'
             f'<animate attributeName="opacity" values="1;0;1" dur="1.15s" repeatCount="indefinite"/>'
             f'</tspan></text>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    d = fetch()
    os.makedirs("assets", exist_ok=True)
    panels = (
        ("panel-header.svg",     panel_header(d)),
        ("panel-experience.svg", panel_experience()),
        ("panel-langs.svg",      panel_langs()),
        ("panel-skyline.svg",    panel_skyline(d)),
        ("panel-story.svg",      panel_story()),
    )
    for name, svg in panels:
        with open(f"assets/{name}", "w") as fh:
            fh.write(svg)
        print(f"wrote assets/{name} ({len(svg)} bytes)")
    print(json.dumps({k: v for k, v in d.items() if k != "weeks"}))
