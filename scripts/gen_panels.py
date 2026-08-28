#!/usr/bin/env python3
"""Render the dark-blue panels for the profile README from live GitHub data.

Everything the profile shows is generated here and committed to the repo, so the
README never depends on a third-party render service. The public
github-readme-stats / trophy / activity-graph deployments return 402/503 for
EVERY user whenever they run out of quota, which silently breaks a profile.

Layout intent: only the identity block and the closing story are terminal
windows. Everything between them is a plain styled section with charts, because
a page made entirely of terminal chrome reads as noise rather than as design.

Two rules hold across every panel:

1. Animations LOOP (repeatCount="indefinite") on a shared CYCLE. An earlier
   version used fill="freeze" and played once, so the reveal had always finished
   before you scrolled to it -- it looked like nothing animated at all.

2. Each element's BASE attribute is its FINAL, visible state, and the stagger
   lives in keyTimes rather than begin=. A renderer that ignores SMIL then shows
   the finished panel instead of an empty box. qlmanage evaluates at t=0, so
   verify by stripping <animate> and rendering that.
"""

import json
import os
import subprocess
import sys

USER = "vignesh2027"
CYCLE = 12.0        # deliberately slow

# Cumulative figure spanning earlier accounts, repos since made private, and
# projects that were sold on. It cannot be derived from this account's API, so
# it is ALWAYS rendered with an explicit "all projects & accounts" label.
AGG_STARS = "4,864"

BG     = "#05070c"
PANEL  = "#0a0f1a"
CARD   = "#0b1220"
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


def anim(attr, final, t, dur=0.5, start="0"):
    k1 = min(max(t, 0) / CYCLE, 0.995)
    k2 = min((max(t, 0) + dur) / CYCLE, 0.997)
    return (f'<animate attributeName="{attr}" values="{start};{start};{final};{final}" '
            f'keyTimes="0;{k1:.4f};{k2:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>')


def fade(t, dur=0.5):
    return anim("opacity", "1", t, dur)


def head(uid, w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{esc(label)}">'
            f'<defs><radialGradient id="g{uid}" cx="50%" cy="0%" r="90%">'
            f'<stop offset="0%" stop-color="{BLUE_D}" stop-opacity=".13"/>'
            f'<stop offset="100%" stop-color="{BLUE_D}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="r{uid}" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{BLUE}"/>'
            f'<stop offset="100%" stop-color="#0b2545"/></linearGradient></defs>')


def shell(uid, w, h, title, label, black=False):
    """Terminal window chrome. Used only for identity and the closing story."""
    bg = "#000000" if black else PANEL
    return (head(uid, w, h, label) +
            f'<rect width="{w}" height="{h}" fill="{BG}" rx="12"/>'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{bg}" stroke="{BORDER}"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="11" fill="url(#g{uid})"/>'
            f'<path d="M0.5 12.5a12 12 0 0 1 12-12h{w-25}a12 12 0 0 1 12 12V42H0.5z" '
            f'fill="#0d1526" stroke="{BORDER}"/>'
            f'<circle cx="24" cy="21" r="5" fill="#1b5299"/>'
            f'<circle cx="43" cy="21" r="5" fill="#205295"/>'
            f'<circle cx="62" cy="21" r="5" fill="#2c74b3"/>'
            f'<text x="{w/2}" y="26" font-family="{MONO}" font-size="13.5" fill="{DIM}" '
            f'text-anchor="middle">{esc(title)}</text>')


def section(uid, w, h, title, label, kicker=""):
    """Plain styled section: accent rule + heading, no window chrome."""
    s = (head(uid, w, h, label) +
         f'<rect width="{w}" height="{h}" fill="{PANEL}" rx="12"/>'
         f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{BORDER}"/>'
         f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="11" fill="url(#g{uid})"/>'
         f'<rect x="30" y="34" width="46" height="3" rx="1.5" fill="url(#r{uid})"/>'
         f'<text x="30" y="72" font-family="{MONO}" font-size="21" fill="{TEXT}" '
         f'font-weight="700">{esc(title)}</text>')
    if kicker:
        s += (f'<text x="{w-30}" y="72" font-family="{MONO}" font-size="12.5" fill="{FAINT}" '
              f'text-anchor="end">{esc(kicker)}</text>')
    return s


def typed(uid, x, y, text, t, size=15, cps=20):
    dur = max(0.6, len(text) / cps)
    cw = (len(text) + 2) * size * 0.605 + 14   # +2 covers the "$ " prefix
    return (f'<defs><clipPath id="{uid}"><rect x="{x}" y="{y-size}" height="{size+9}" width="{cw:.1f}">'
            + anim("width", f"{cw:.1f}", t, dur) + '</rect></clipPath></defs>'
            f'<g clip-path="url(#{uid})"><text x="{x}" y="{y}" font-family="{MONO}" '
            f'font-size="{size}" fill="{BLUE}"><tspan fill="{BLUE_D}">$</tspan> {esc(text)}</text></g>'), t + dur


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
        "langs": langs,
    }


# ----------------------------------------------------------------- identity --

def panel_identity():
    w, h = 700, 912
    rows = [
        ("NAME",  "Vigneshwar L", TEXT),
        ("ROLE",  "Backend  ·  Systems  ·  AI / ML", TEXT),
        ("STACK", "Python  ·  Go  ·  Rust", BLUE),
        ("OPEN",  "OpenTelemetry · CNCF · Helm", DIM),
        ("",      "oxc · ripgrep", DIM),
        ("WORK",  "AI trainer & model evaluator", DIM),
        ("",      "Shipd (Datacurve) · Handshake AI", DIM),
        ("",      "+ startups, founders & co-founders", DIM),
        ("BUILD", "storage engines, distributed systems,", DIM),
        ("",      "and the tests that keep them honest", DIM),
        ("BASE",  "Tamil Nadu, India", DIM),
        ("EDU",   "B.Tech CSE  ·  Linguaskill C1", DIM),
    ]
    p = [shell("id", w, h, "vigneshwar@github ~ profile", "Vigneshwar L")]
    cmd, t = typed("cid", 30, 88, "cat /etc/profile", 0.4, size=15)
    p.append(cmd)
    y, t = 138, t + 0.4
    for k, v, col in rows:
        p.append(f'<g opacity="1">{fade(t)}')
        if k:
            p.append(f'<text x="30" y="{y}" font-family="{MONO}" font-size="14" '
                     f'fill="{BLUE_D}" font-weight="600">{esc(k)}</text>')
        p.append(f'<text x="126" y="{y}" font-family="{MONO}" font-size="14.5" '
                 f'fill="{col}">{esc(v)}</text></g>')
        y += 40 if k else 30
        t += 0.34

    p.append(f'<g opacity="1">{fade(t)}'
             f'<rect x="30" y="{y+10}" width="{w-60}" height="1" fill="{BORDER}"/>'
             f'<circle cx="36" cy="{y+48}" r="5" fill="{BLUE}">'
             f'<animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/>'
             f'</circle>'
             f'<text x="52" y="{y+53}" font-family="{MONO}" font-size="15" fill="{BLUE}">'
             f'available for hire</text>'
             f'<text x="30" y="{y+84}" font-family="{MONO}" font-size="13" fill="{FAINT}">'
             f'open to backend, systems and cloud-native work</text></g>')
    p.append(f'<text x="30" y="{y+126}" font-family="{MONO}" font-size="15" fill="{BLUE_D}" '
             f'opacity="1">$ <tspan fill="{DIM}">_'
             f'<animate attributeName="opacity" values="1;0;1" dur="1.15s" repeatCount="indefinite"/>'
             f'</tspan>{fade(t + 0.4)}</text>')
    p.append("</svg>")
    return "".join(p)


# -------------------------------------------------------------------- stats --

def panel_stats(d):
    """Big-number strip. The aggregate figure is labelled, never bare."""
    w, h = 1240, 210
    tiles = [
        (f"{d['contribs']:,}", "contributions", "last 365 days", BLUE),
        (f"{d['repos']}",      "repositories",  "public sources", TEXT),
        (AGG_STARS,            "stars",         "all projects & accounts", BLUE),
        (f"{d['followers']}",  "followers",     "on this account", TEXT),
    ]
    p = [section("sx", w, h, "By the numbers", "stats", "live")]
    tw = (w - 60 - 3 * 18) // 4
    t = 0.5
    for i, (big, lab, note, col) in enumerate(tiles):
        x = 30 + i * (tw + 18)
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<rect x="{x}" y="98" width="{tw}" height="86" rx="10" fill="{CARD}" stroke="{BORDER}"/>'
                 f'<rect x="{x}" y="98" width="{tw}" height="2.5" rx="1.25" fill="url(#rsx)"/>'
                 f'<text x="{x+18}" y="140" font-family="{MONO}" font-size="27" fill="{col}" '
                 f'font-weight="700">{esc(big)}</text>'
                 f'<text x="{x+18}" y="161" font-family="{MONO}" font-size="12.5" fill="{DIM}">{esc(lab)}</text>'
                 f'<text x="{x+18}" y="177" font-family="{MONO}" font-size="10.5" fill="{FAINT}">{esc(note)}</text>'
                 f'</g>')
        t += 0.36
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- languages --

# Lead with what he actually writes day to day, then fill from the API.
LEAD = ["Python", "Go", "Rust"]
LANG_FALLBACK = {"Python": "#3572A5", "Go": "#00ADD8", "Rust": "#dea584"}


def panel_langs(d):
    w, h = 610, 396
    langs = d["langs"]
    ordered = []
    for name in LEAD:
        size = langs.get(name, {}).get("size", 0)
        colr = langs.get(name, {}).get("color") or LANG_FALLBACK[name]
        ordered.append((name, size, colr))
    rest = sorted((k for k in langs if k not in LEAD),
                  key=lambda k: -langs[k]["size"])[:3]
    for k in rest:
        ordered.append((k, langs[k]["size"], langs[k]["color"]))

    total = sum(s for _, s, _ in ordered) or 1
    p = [section("lx", w, h, "Languages", "languages", "by bytes")]
    y, t = 112, 0.5
    for name, size, colr in ordered:
        pct = size / total * 100
        bw = max(6, round(pct / 100 * 330))
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="30" y="{y+12}" font-family="{MONO}" font-size="13.5" fill="{TEXT}">{esc(name)}</text>'
                 f'<rect x="170" y="{y+1}" width="330" height="13" rx="6.5" fill="#0d1c30"/>'
                 f'<rect x="170" y="{y+1}" width="{bw}" height="13" rx="6.5" fill="{colr}">'
                 + anim("width", str(bw), t + 0.12, 1.0) + '</rect>'
                 f'<text x="{w-30}" y="{y+12}" font-family="{MONO}" font-size="12.5" fill="{DIM}" '
                 f'text-anchor="end">{pct:.1f}%</text></g>')
        y += 42
        t += 0.36
    p.append("</svg>")
    return "".join(p)


# --------------------------------------------------------------- experience --

EXPERIENCE = [
    ("Shipd  ·  Datacurve", "AI trainer",
     "Training data authored and graded against rubrics."),
    ("Handshake AI", "model evaluator",
     "Prompt authoring and preference ranking."),
    ("Startups & founders", "freelance",
     "Backend, ML and full-stack, often sole engineer."),
    ("Open source", "contributor",
     "OpenTelemetry, CNCF, Helm, oxc, ripgrep."),
]


def panel_experience():
    w, h = 610, 396
    p = [section("ex", w, h, "Work", "experience", "2023 — now")]
    y, t = 100, 0.5
    for org, role, note in EXPERIENCE:
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<rect x="30" y="{y}" width="{w-60}" height="62" rx="9" fill="{CARD}" stroke="{BORDER}"/>'
                 f'<rect x="30" y="{y}" width="3" height="62" rx="1.5" fill="{BLUE_D}"/>'
                 f'<text x="46" y="{y+24}" font-family="{MONO}" font-size="14" fill="{TEXT}" '
                 f'font-weight="700">{esc(org)}</text>'
                 f'<text x="{w-46}" y="{y+24}" font-family="{MONO}" font-size="11.5" fill="{BLUE}" '
                 f'text-anchor="end">{esc(role)}</text>'
                 f'<text x="46" y="{y+46}" font-family="{MONO}" font-size="11.5" fill="{DIM}">{esc(note)}</text>'
                 f'</g>')
        y += 72
        t += 0.36
    p.append("</svg>")
    return "".join(p)


# ------------------------------------------------------------ certifications --

CERTS = [
    ("Cambridge Linguaskill", "C1 · 185", "Listening C2 · Reading C2"),
    ("DevOps Internship", "Completed", "Internship + training"),
    ("International Business", "Completed", "Internship + training"),
    ("B.Tech CSE", "2023 — 2027", "Computer Science & Engineering"),
]


def panel_certs():
    w, h = 1240, 232
    p = [section("ce", w, h, "Certifications", "certifications", "verified")]
    tw = (w - 60 - 3 * 18) // 4
    t = 0.5
    for i, (name, val, note) in enumerate(CERTS):
        x = 30 + i * (tw + 18)
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<rect x="{x}" y="98" width="{tw}" height="108" rx="10" fill="{CARD}" stroke="{BORDER}"/>'
                 f'<rect x="{x}" y="98" width="{tw}" height="2.5" rx="1.25" fill="url(#rce)"/>'
                 f'<text x="{x+18}" y="132" font-family="{MONO}" font-size="13.5" fill="{TEXT}" '
                 f'font-weight="700">{esc(name)}</text>'
                 f'<text x="{x+18}" y="163" font-family="{MONO}" font-size="17" fill="{BLUE}" '
                 f'font-weight="700">{esc(val)}</text>'
                 f'<text x="{x+18}" y="187" font-family="{MONO}" font-size="10.5" fill="{FAINT}">{esc(note)}</text>'
                 f'</g>')
        t += 0.36
    p.append("</svg>")
    return "".join(p)


# ----------------------------------------------------------------- sponsors --

def panel_sponsors():
    w, h = 1240, 190
    p = [section("sp", w, h, "Sponsor this work", "sponsors")]
    p.append(f'<g opacity="1">{fade(0.5)}'
             f'<text x="30" y="112" font-family="{MONO}" font-size="14" fill="{DIM}">'
             f'I build storage engines, distributed systems and open source tooling in the open.</text>'
             f'<text x="30" y="136" font-family="{MONO}" font-size="14" fill="{DIM}">'
             f'Sponsorship goes straight into the time spent on it.</text>'
             f'<rect x="30" y="150" width="180" height="30" rx="15" fill="{BLUE_D}"/>'
             f'<text x="120" y="170" font-family="{MONO}" font-size="13" fill="#ffffff" '
             f'font-weight="700" text-anchor="middle">&#9825;  Sponsor</text></g>')
    cx, cy = w - 130, 118
    for i in range(3):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="none" stroke="{BLUE_D}" '
                 f'stroke-width="1.4" opacity="0">'
                 f'<animate attributeName="r" values="22;76" dur="{CYCLE}s" '
                 f'begin="{i*CYCLE/3:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.5;0" dur="{CYCLE}s" '
                 f'begin="{i*CYCLE/3:.2f}s" repeatCount="indefinite"/></circle>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="18" fill="none" stroke="{BLUE}" stroke-width="1.6"/>'
             f'<text x="{cx}" y="{cy+6}" font-family="{MONO}" font-size="15" fill="{BLUE}" '
             f'text-anchor="middle">&#9825;</text>')
    p.append("</svg>")
    return "".join(p)


# -------------------------------------------------------------------- story --

STORY = [
    ("", "I am Vigneshwar. I write backend and systems code, and I help train the models that"),
    ("", "are starting to write it too. This is the long version of how that happened."),
    ("gap", ""),
    ("h", "2023  —  starting"),
    ("", "I started B.Tech Computer Science in Tamil Nadu with very little idea what I was"),
    ("", "doing. The first programs I wrote barely ran. What changed things was realising that"),
    ("", "almost everything worth learning was already written down, in public, in other"),
    ("", "people's repositories. So I started reading them. I still do, most days."),
    ("gap", ""),
    ("h", "2024  —  going lower"),
    ("", "I got tired of not knowing what was underneath. C++ first, then Rust, which I picked"),
    ("", "because it refuses to let you stay vague about ownership and lifetimes. Learning it"),
    ("", "was slow and occasionally humiliating, and it taught me more about how machines"),
    ("", "actually work than the two years before it combined."),
    ("gap", ""),
    ("h", "2025  —  building the hard thing"),
    ("", "I wrote FluxDB, a time-series database, from scratch in Rust. Not because the world"),
    ("", "needed another one, but because I wanted to find out where the cost really lives"),
    ("", "inside a storage engine: columnar compression, a write path worth benchmarking, and"),
    ("", "a great deal of profiling. Then rustkvd, a distributed key-value store with Raft"),
    ("", "consensus, an LSM engine and MVCC, for the same reason applied to consensus."),
    ("gap", ""),
    ("h", "2026  —  open source, and models"),
    ("", "I started contributing upstream: OpenTelemetry, CNCF, Helm, oxc, ripgrep. Working in"),
    ("", "codebases that size teaches one specific skill — reading unfamiliar code well enough"),
    ("", "to change it without breaking anything, then taking the review that follows"),
    ("", "seriously. Much of what I contributed was tests, because tests are how you find out"),
    ("", "whether you actually understood the thing you just read."),
    ("gap", ""),
    ("", "Alongside that I began working with Shipd (Datacurve) and Handshake AI, authoring"),
    ("", "training data and grading model output against detailed rubrics, plus a run of"),
    ("", "freelance work for startups, founders and co-founders — usually as the only engineer"),
    ("", "on the project, from scoping through to deployment."),
    ("gap", ""),
    ("h", "now"),
    ("", "Still building systems. Still reading more code than I write. If you are hiring for"),
    ("", "backend, systems or cloud-native work, or you want something built properly, the"),
    ("", "contact details are at the top of this page."),
]


def panel_story():
    w = 1240
    lh, lead_in = 25, 118
    n = sum(1 for kind, _ in STORY if kind != "gap")
    gaps = sum(1 for kind, _ in STORY if kind == "gap")
    h = lead_in + n * lh + gaps * 16 + 62

    # Longest line must fit inside the margins, or the story runs off the panel.
    longest = max(len(t) for _, t in STORY)
    if longest * 13.5 * 0.605 > w - 60:
        raise SystemExit(f"story line too wide: {longest} chars, "
                         f"max {int((w - 60) / (13.5 * 0.605))}")

    p = [shell("so", w, h, "vigneshwar@github ~ cat story.md", "the long version", black=True)]
    cmd, t = typed("cso", 30, 88, "cat ~/story.md", 0.4, size=15)
    p.append(cmd)
    y, t = lead_in + 18, t + 0.5
    step = max(0.09, (CYCLE * 0.72 - t) / max(n, 1))   # spread the reveal over the loop
    for kind, txt in STORY:
        if kind == "gap":
            y += 16
            continue
        col, size, weight = (BLUE, 14.5, "700") if kind == "h" else (DIM, 13.5, "400")
        p.append(f'<text x="30" y="{y}" font-family="{MONO}" font-size="{size}" fill="{col}" '
                 f'font-weight="{weight}" opacity="1">{esc(txt)}{fade(t, 0.45)}</text>')
        y += lh
        t += step
    p.append(f'<text x="30" y="{y+24}" font-family="{MONO}" font-size="14" fill="{BLUE_D}" '
             f'opacity="1">$ <tspan fill="{DIM}">_'
             f'<animate attributeName="opacity" values="1;0;1" dur="1.15s" repeatCount="indefinite"/>'
             f'</tspan></text>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    d = fetch()
    os.makedirs("assets", exist_ok=True)
    panels = (
        ("panel-identity.svg",   panel_identity()),
        ("panel-stats.svg",      panel_stats(d)),
        ("panel-langs.svg",      panel_langs(d)),
        ("panel-experience.svg", panel_experience()),
        ("panel-certs.svg",      panel_certs()),
        ("panel-sponsors.svg",   panel_sponsors()),
        ("panel-story.svg",      panel_story()),
    )
    for name, svg in panels:
        with open(f"assets/{name}", "w") as fh:
            fh.write(svg)
        print(f"wrote assets/{name} ({len(svg)} bytes)")
    print(json.dumps({k: v for k, v in d.items() if k != "langs"}))
