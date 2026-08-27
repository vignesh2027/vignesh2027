#!/usr/bin/env python3
"""Render dark-blue terminal-style SVG panels from live GitHub data.

Everything the profile shows is generated here and committed to the repo, so
the README never depends on a third-party render service. The public
github-readme-stats / trophy / activity-graph deployments return 402/503 for
every user whenever they run out of quota, which silently breaks a profile.

Panels animate once on load (staggered reveal, fill="freeze") so the terminal
appears to boot rather than snapping into place.
"""

import json
import os
import subprocess
import sys

USER = "vignesh2027"

# Cumulative figures spanning earlier accounts, repos since made private, and
# projects that were sold on. They cannot be derived from this account's API,
# so they are ALWAYS rendered with an explicit "all projects & accounts" label
# and shown alongside the live, self-verifying numbers for this account.
AGG_STARS = "2.4k"
AGG_CONTRIB = "2.5k"

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


# Every animation runs on ONE timeline that begins at 0s, with the stagger
# encoded in keyTimes rather than begin=. That keeps the element's base
# attribute at its FINAL (visible) value, so a renderer that ignores SMIL --
# some previews, thumbnailers and feed readers -- shows the finished panel
# instead of an empty box. Staggering via begin= would leave them blank.
TOTAL = 3.2


def anim(attr, final, t, dur=0.32, start="0"):
    k1 = min(t / TOTAL, 0.996)
    k2 = min((t + dur) / TOTAL, 0.998)
    return (f'<animate attributeName="{attr}" values="{start};{start};{final};{final}" '
            f'keyTimes="0;{k1:.4f};{k2:.4f};1" dur="{TOTAL}s" fill="freeze"/>')


def fade(delay, dur=0.32):
    """Reveal an element whose base opacity is 1 (visible without SMIL)."""
    return anim("opacity", "1", delay, dur)


def typed(uid, x, y, text, delay, cps=34):
    """A command line that types itself in, with a trailing cursor."""
    dur = max(0.35, len(text) / cps)
    # Generous: the clip must fully clear the glyphs (incl. the "$ " prefix) or
    # the command renders visibly truncated once the animation settles.
    w = (len(text) + 2) * 8.4 + 40
    return (
        f'<defs><clipPath id="{uid}"><rect x="{x}" y="{y-13}" height="20" width="{w}">'
        + anim("width", str(w), delay, dur) + '</rect></clipPath></defs>'
        f'<g clip-path="url(#{uid})"><text x="{x}" y="{y}" font-family="{MONO}" '
        f'font-size="13" fill="{BLUE}"><tspan fill="{BLUE_D}">$</tspan> {esc(text)}</text></g>')


def chrome(w, h, title):
    return (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" '
            f'fill="{PANEL}" stroke="{BORDER}"/>'
            f'<path d="M0.5 10.5a10 10 0 0 1 10-10h{w-21}a10 10 0 0 1 10 10V34H0.5z" '
            f'fill="#0d1526" stroke="{BORDER}"/>'
            f'<circle cx="20" cy="18" r="4.5" fill="#1b5299"/>'
            f'<circle cx="37" cy="18" r="4.5" fill="#205295"/>'
            f'<circle cx="54" cy="18" r="4.5" fill="#2c74b3"/>'
            f'<text x="{w/2}" y="22.5" font-family="{MONO}" font-size="12" '
            f'fill="{DIM}" text-anchor="middle">{esc(title)}</text>')


def head(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<rect width="{w}" height="{h}" fill="{BG}" rx="10"/>')


def cursor(x, y, delay):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="13" '
            f'fill="{BLUE_D}" opacity="1">$ <tspan fill="{DIM}">_'
            f'<animate attributeName="opacity" values="1;0;1" dur="1.1s" '
            f'begin="{delay:.2f}s" repeatCount="indefinite"/></tspan>{fade(delay)}</text>')


def fetch():
    q = """
    { user(login: "%s") {
        followers { totalCount }
        contributionsCollection { contributionCalendar { totalContributions } }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes { stargazerCount
                  languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
                    edges { size node { name color } } } }
        }
    } }""" % USER
    u = gh(["api", "graphql", "-f", f"query={q}"])["data"]["user"]
    merged = gh(["api", "search/issues?q=author:%s+type:pr+is:merged+-user:%s"
                 % (USER, USER)])["total_count"]
    # Weight each repository equally instead of by raw bytes. Byte-weighting
    # lets one vendored/bundled repo dominate the whole chart (a single
    # TypeScript template put TS at 87%), which misrepresents what the work
    # actually is. Per-repo shares answer "what does he write?" not "which
    # repo has the biggest node_modules".
    langs = {}
    for n in u["repositories"]["nodes"]:
        edges = n["languages"]["edges"]
        tot = sum(e["size"] for e in edges)
        if not tot:
            continue
        for e in edges:
            k = e["node"]["name"]
            langs.setdefault(k, {"size": 0.0, "color": e["node"]["color"] or BLUE})
            langs[k]["size"] += e["size"] / tot
    return {
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "contribs": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "merged": merged,
        "langs": sorted(langs.items(), key=lambda kv: -kv[1]["size"])[:6],
        # percentages must divide by the FULL total, not just the top 6
        "lang_total": sum(v["size"] for v in langs.values()),
    }


def panel_stats(d):
    w, h = 560, 268
    rows = [
        ("merged upstream PRs", str(d["merged"]), "OpenTelemetry - oxc - lo"),
        ("contributions (365d)", f"{d['contribs']:,}", "this account, live"),
        ("stars", str(d["stars"]), "this account, live"),
        ("public repositories", str(d["repos"]), ""),
        ("followers", str(d["followers"]), ""),
        ("stars, all projects", AGG_STARS, "incl. private + earlier accounts"),
    ]
    p = [head(w, h, "stats"), chrome(w, h, "vignesh2027 - stats")]
    p.append(typed("cs", 24, 62, f"gh api users/{USER} --stats", 0.25))
    y, t = 92, 1.05
    for k, v, note in rows:
        dots = "." * max(2, 26 - len(k))
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="24" y="{y}" font-family="{MONO}" font-size="13" fill="{DIM}">'
                 f'{esc(k)} <tspan fill="#16324f">{dots}</tspan> '
                 f'<tspan fill="{TEXT}" font-weight="600">{esc(v)}</tspan>'
                 + (f'  <tspan fill="{FAINT}" font-size="10.5">{esc(note)}</tspan>' if note else "")
                 + '</text></g>')
        y += 26
        t += 0.16
    p.append(cursor(24, y + 6, t + 0.1))
    p.append("</svg>")
    return "".join(p)


def panel_langs(d):
    w, h = 560, 268
    total = d.get("lang_total") or 1
    p = [head(w, h, "languages"), chrome(w, h, "vignesh2027 - languages")]
    p.append(typed("cl", 24, 62, "tokei --languages --sort code", 0.25))
    y, t = 86, 1.05
    for name, v in d["langs"]:
        pct = v["size"] / total * 100
        bw = max(4, round(pct / 100 * 322))
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="24" y="{y+11}" font-family="{MONO}" font-size="12.5" fill="{TEXT}">{esc(name)}</text>'
                 f'<rect x="152" y="{y+1}" width="322" height="11" rx="5.5" fill="#0d1c30"/>'
                 f'<rect x="152" y="{y+1}" width="{bw}" height="11" rx="5.5" fill="{v["color"]}">'
                 + anim("width", str(bw), t + 0.1, 0.75) + '</rect>'
                 f'<text x="486" y="{y+11}" font-family="{MONO}" font-size="12" fill="{DIM}">{pct:.1f}%</text>'
                 f'</g>')
        y += 27
        t += 0.18
    p.append(cursor(24, y + 8, t + 0.1))
    p.append("</svg>")
    return "".join(p)


def panel_identity():
    """Top-left terminal, sized to sit beside the portrait panel."""
    w, h = 668, 556
    rows = [
        ("NAME", "Vigneshwar L", TEXT),
        ("ROLE", "Backend & Systems Engineer", TEXT),
        ("FOCUS", "Go - Rust - Python", DIM),
        ("UPSTREAM", "OpenTelemetry (CNCF) - Helm - oxc - ripgrep", DIM),
        ("WORK", "AI trainer & evaluator - Shipd, Handshake AI", DIM),
        ("BUILT", "FluxDB - rustkvd - TemporalMesh Transformer", DIM),
        ("LIVE", "craftezmyresume.com", DIM),
        ("ENGLISH", "Cambridge Linguaskill C1 (185)", DIM),
        ("BASED", "Tamil Nadu, India", DIM),
        ("STATUS", "open to backend / systems / cloud-native", BLUE),
    ]
    p = [head(w, h, "identity"), chrome(w, h, "vigneshwar@github ~ %")]
    p.append(typed("ci", 26, 68, "cat /etc/profile", 0.2))
    y, t = 112, 0.95
    for k, v, col in rows:
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="26" y="{y}" font-family="{MONO}" font-size="13.5" '
                 f'fill="{BLUE_D}">{esc(k)}</text>'
                 f'<text x="150" y="{y}" font-family="{MONO}" font-size="13.5" '
                 f'fill="{col}">{esc(v)}</text></g>')
        y += 34
        t += 0.17
    p.append(f'<g opacity="1">{fade(t)}'
             f'<text x="26" y="{y+16}" font-family="{MONO}" font-size="11.5" fill="{FAINT}">'
             f'11 merged pull requests upstream &#183; ~$2k earned authoring '
             f'frontier-model training data</text></g>')
    p.append(cursor(26, y + 46, t + 0.15))
    p.append("</svg>")
    return "".join(p)


def panel_history():
    """Second terminal: how it started. Static - no API data required."""
    w, h = 1140, 272
    rows = [
        ("2023", "B.Tech CSE, Takshashila University", DIM),
        ("2024", "first systems code - C++, then Rust", DIM),
        ("2025", "FluxDB - time-series engine written from scratch in Rust", DIM),
        ("2026", "merged into OpenTelemetry (CNCF) - Go compile-time instrumentation", TEXT),
        ("2026", "AI trainer & model evaluator - Shipd (Datacurve), Handshake AI", TEXT),
        ("2026", "CraftezMyResume - shipped solo, live in production", DIM),
    ]
    p = [head(w, h, "history"), chrome(w, h, "vignesh2027 - how it started")]
    p.append(typed("ch", 24, 62, "git log --reverse --oneline --author=vigneshwar", 0.2))
    y, t = 92, 1.15
    for year, txt, col in rows:
        p.append(f'<g opacity="1">{fade(t)}'
                 f'<text x="24" y="{y}" font-family="{MONO}" font-size="13" fill="{BLUE_D}">{year}</text>'
                 f'<text x="76" y="{y}" font-family="{MONO}" font-size="13" fill="{FAINT}">|</text>'
                 f'<text x="98" y="{y}" font-family="{MONO}" font-size="13" fill="{col}">{esc(txt)}</text>'
                 f'</g>')
        y += 25
        t += 0.22
    p.append(f'<g opacity="1">{fade(t)}'
             f'<text x="24" y="{y+8}" font-family="{MONO}" font-size="11" fill="{FAINT}">'
             f'~$2k earned to date authoring frontier-model training data '
             f'&#183; Cambridge Linguaskill C1 (185)</text></g>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    data = fetch()
    os.makedirs("assets", exist_ok=True)
    panels = (("panel-identity.svg", panel_identity()),
              ("panel-stats.svg", panel_stats(data)),
              ("panel-langs.svg", panel_langs(data)),
              ("panel-history.svg", panel_history()))
    for name, svg in panels:
        with open(f"assets/{name}", "w") as fh:
            fh.write(svg)
        print(f"wrote assets/{name} ({len(svg)} bytes)")
    print(json.dumps({k: v for k, v in data.items() if k != "langs"}))
