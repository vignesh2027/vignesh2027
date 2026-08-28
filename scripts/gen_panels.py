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
REVEAL = 26.0       # whole-panel reveal length; deliberately slow

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

HEAT = ["#0d1c30", "#13395e", "#1b5299", "#1f6feb", "#58a6ff"]


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
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) { totalCount }
    } }""" % USER
    u = gh(["api", "graphql", "-f", f"query={q}"])["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    return {
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "contribs": cal["totalContributions"],
        "weeks": cal["weeks"],
    }


# ----------------------------------------------------------------- identity --

def panel_identity():
    w, h = 700, 852
    rows = [
        ("NAME",  "Vigneshwar L", TEXT),
        ("ROLE",  "Backend  ·  Systems  ·  AI / ML", TEXT),
        ("STACK", "Python  ·  Go  ·  Rust", BLUE),
        ("OPEN",  "OpenTelemetry · CNCF · Helm", DIM),
        ("",      "oxc · ripgrep", DIM),
        ("WORK",  "clients, startups & founders", DIM),
        ("",      "Shipd (Datacurve) · Handshake AI", DIM),
        ("BUILD", "models, RL environments, agents,", DIM),
        ("",      "RAG systems and storage engines", DIM),
        ("BASE",  "Tamil Nadu, India", DIM),
        ("EDU",   "B.Tech CSE  ·  Linguaskill C1", DIM),
    ]
    p = [shell("id", w, h, "vigneshwar@github ~ profile", "Vigneshwar L")]
    cmd, t = typed("cid", 30, 88, "cat /etc/profile", 0.6, size=15)
    p.append(cmd)
    y, t = 138, t + 0.8
    for k, v, col in rows:
        p.append(f'<g opacity="1">{fade(t)}')
        if k:
            p.append(f'<text x="30" y="{y}" font-family="{MONO}" font-size="14" '
                     f'fill="{BLUE_D}" font-weight="600">{esc(k)}</text>')
        p.append(f'<text x="126" y="{y}" font-family="{MONO}" font-size="14.5" '
                 f'fill="{col}">{esc(v)}</text></g>')
        y += 40 if k else 30
        t += 0.9
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
             f'</tspan>{fade(t + 0.8)}</text>')
    p.append("</svg>")
    return "".join(p)


# --------------------------------------------------------------- experience --

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
                 f'<rect x="30" y="{y}" width="{w-60}" height="66" rx="9" fill="{CARD}" stroke="{BORDER}"/>'
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

SKILLS = [
    ("Python",     72, "#3572A5"),
    ("Rust",       68, "#dea584"),
    ("Go",         65, "#00ADD8"),
    ("TypeScript", 42, "#3178c6"),
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
                 f'<rect x="170" y="{y+1}" width="320" height="14" rx="7" fill="#0d1c30"/>'
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


# -------------------------------------------------------------- contributions --

def panel_contrib(d):
    """Full-year heatmap plus monthly totals, drawn from the real calendar."""
    w, h = 1240, 430
    weeks = d["weeks"]
    cell, gap = 15, 4
    step = cell + gap
    ox, oy = 30, 132

    nz = sorted(day["contributionCount"] for wk in weeks
                for day in wk["contributionDays"] if day["contributionCount"] > 0)

    def level(c):
        if c == 0:
            return 0
        if not nz:
            return 1
        q = [nz[int(len(nz) * f)] for f in (0.25, 0.55, 0.85)]
        return 1 + sum(c >= t for t in q)

    p = [section("ct", w, h, "Contributions", "contributions",
                 f"{d['contribs']:,} in the last year")]

    grid_w = len(weeks) * step
    scale = min(1.0, (w - 60) / grid_w)

    p.append(f'<g transform="translate({ox},{oy}) scale({scale:.4f})">')
    months, seen = [], set()
    for wi, wk in enumerate(weeks):
        for day in wk["contributionDays"]:
            c = day["contributionCount"]
            lvl = level(c)
            x, y = wi * step, day["weekday"] * step
            t = 1.2 + (wi / max(len(weeks) - 1, 1)) * 9.0   # sweeps left to right
            p.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3.5" '
                     f'fill="{HEAT[lvl]}" opacity="1">{fade(t, 0.5)}</rect>')
        mo = day["date"][:7]
        if mo not in seen:
            seen.add(mo)
            if not months or wi * step - months[-1][0] > 70:
                months.append((wi * step, day["date"]))
    p.append('</g>')

    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for x, date in months:
        mi = int(date[5:7]) - 1
        p.append(f'<text x="{ox + x*scale:.0f}" y="{oy-12}" font-family="{MONO}" '
                 f'font-size="11" fill="{FAINT}" opacity="1">{labels[mi]}{fade(1.0)}</text>')

    # monthly totals
    totals = {}
    for wk in weeks:
        for day in wk["contributionDays"]:
            totals[day["date"][:7]] = totals.get(day["date"][:7], 0) + day["contributionCount"]
    keys = sorted(totals)[-12:]
    top = max((totals[k] for k in keys), default=1) or 1
    bx, by, bw_max = 30, 396, 74
    p.append(f'<text x="30" y="{by-128}" font-family="{MONO}" font-size="12.5" fill="{DIM}" '
             f'opacity="1">monthly{fade(10.5)}</text>')
    for i, k in enumerate(keys):
        bh = max(4, round(totals[k] / top * 96))
        x = bx + i * ((w - 60) / 12)
        t = 10.8 + i * 0.35
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<rect x="{x:.0f}" y="{by-bh}" width="{bw_max}" height="{bh}" rx="4" fill="{BLUE_D}"/>'
                 f'<text x="{x+bw_max/2:.0f}" y="{by+16}" font-family="{MONO}" font-size="10.5" '
                 f'fill="{FAINT}" text-anchor="middle">{labels[int(k[5:7])-1]}</text>'
                 f'<text x="{x+bw_max/2:.0f}" y="{by-bh-6}" font-family="{MONO}" font-size="10.5" '
                 f'fill="{DIM}" text-anchor="middle">{totals[k]}</text></g>')

    # legend
    lx = w - 210
    p.append(f'<text x="{lx-42}" y="{by-120}" font-family="{MONO}" font-size="11" '
             f'fill="{FAINT}" opacity="1">less{fade(10.5)}</text>')
    for i, c in enumerate(HEAT):
        p.append(f'<rect x="{lx + i*22}" y="{by-131}" width="15" height="15" rx="3.5" '
                 f'fill="{c}" opacity="1">{fade(10.5)}</rect>')
    p.append(f'<text x="{lx + 5*22 + 6}" y="{by-120}" font-family="{MONO}" font-size="11" '
             f'fill="{FAINT}" opacity="1">more{fade(10.5)}</text>')
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
        ("panel-identity.svg",   panel_identity()),
        ("panel-experience.svg", panel_experience()),
        ("panel-langs.svg",      panel_langs()),
        ("panel-contrib.svg",    panel_contrib(d)),
        ("panel-story.svg",      panel_story()),
    )
    for name, svg in panels:
        with open(f"assets/{name}", "w") as fh:
            fh.write(svg)
        print(f"wrote assets/{name} ({len(svg)} bytes)")
    print(json.dumps({k: v for k, v in d.items() if k != "weeks"}))
