#!/usr/bin/env python3
"""Render the contact / sponsor buttons as local SVGs.

These were shields.io badges. They are generated here instead so the profile has
no third-party image dependency left except the view counter -- shields.io can
rate-limit or go down, and a profile that breaks when someone else's service
breaks is not finished.

Each icon declares the grid it was authored on, because they come from
different sources (GitHub's mark is a 16x16 path, the rest are 24x24). Scaling
them all by one constant is what turned the envelope into a solid block and the
GitHub mark into a crescent.

Run:  python3 scripts/gen_buttons.py
"""

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

H = 36              # compact: the first cut at 46px read as oversized
FS = 12.5
CHAR = FS * 0.605   # monospace advance
TEXT_X = 38
PAD_R = 15
ICON_BOX = 17.0     # every icon is normalised to this height

# (authoring grid size, markup). {a} is replaced with the accent colour.
ICONS = {
    "linkedin": (24,
        '<path fill="{a}" d="M20.45 20.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45'
        '-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45'
        'v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56'
        'v11.45z"/>'),
    # stroked, so it reads as an envelope instead of a filled rectangle
    "email": (24,
        '<g fill="none" stroke="{a}" stroke-width="2" stroke-linejoin="round">'
        '<rect x="1.5" y="4.5" width="21" height="15" rx="2.5"/>'
        '<path d="M2.5 6 12 13.2 21.5 6"/></g>'),
    # Octicon "repo" on a 16x16 grid. The compact GitHub octocat mark was tried
    # first and rendered as a blob -- its implicit curve repetitions are easy to
    # transcribe wrong, and this one has explicit separators.
    "repos": (16,
        '<path fill="{a}" fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75'
        'v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1'
        '-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9'
        'h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087'
        'a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/>'),
    "coffee": (24,
        '<path d="M2.5 4h15v9.5A5.5 5.5 0 0 1 12 19H8a5.5 5.5 0 0 1-5.5-5.5z" fill="url(#cup)"/>'
        '<path d="M17.5 6.5h2.4a3.6 3.6 0 0 1 0 7.2h-2.4" fill="none" stroke="url(#cup)" '
        'stroke-width="2"/>'
        '<rect x="0.5" y="20.5" width="19" height="2.2" rx="1.1" fill="url(#cup)" opacity=".85"/>'
        '<g stroke="{a}" stroke-width="1.6" stroke-linecap="round" opacity=".75">'
        '<path d="M7 1.5c0 -1.6 -1.6 -2 -1.6 -3.6">'
        '<animate attributeName="opacity" values=".2;.9;.2" dur="2.8s" repeatCount="indefinite"/>'
        '</path>'
        '<path d="M12.5 1c0 -2 -1.6 -2.4 -1.6 -4.2">'
        '<animate attributeName="opacity" values=".9;.2;.9" dur="2.8s" repeatCount="indefinite"/>'
        '</path></g>'),
}

CUP_DEFS = ('<defs><linearGradient id="cup" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0%" stop-color="#ffc233"/>'
            '<stop offset="100%" stop-color="#ff9d2e"/></linearGradient></defs>')

BUTTONS = {
    "btn-linkedin.svg": ("LinkedIn",        "linkedin", "#d8dade", "#0e0f12", ""),
    "btn-email.svg":    ("Email",           "email",    "#d8dade", "#0e0f12", ""),
    "btn-repos.svg":    ("Repositories",    "repos",    "#d8dade", "#0e0f12", ""),
    "btn-sponsor.svg":  ("Buy me a coffee", "coffee",   "#f0b429", "#14110a", CUP_DEFS),
}


def button(label, icon_key, accent, fill, defs):
    grid, markup = ICONS[icon_key]
    scale = ICON_BOX / grid
    ty = (H - ICON_BOX) / 2
    w = round(TEXT_X + len(label) * CHAR + PAD_R)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" '
            f'height="{H}" role="img" aria-label="{label}">{defs}'
            f'<rect x="1" y="1" width="{w-2}" height="{H-2}" rx="9" fill="{fill}" '
            f'stroke="{accent}" stroke-opacity=".5"/>'
            f'<g transform="translate(12,{ty:.1f}) scale({scale:.4f})">'
            f'{markup.replace("{a}", accent)}</g>'
            f'<text x="{TEXT_X}" y="{H/2+4.5}" font-family="{MONO}" font-size="{FS}" '
            f'fill="#f0f6fc" font-weight="700">{label}</text></svg>')


if __name__ == "__main__":
    for name, (label, icon, accent, fill, defs) in BUTTONS.items():
        with open(f"assets/{name}", "w") as fh:
            fh.write(button(label, icon, accent, fill, defs))
        print(f"wrote assets/{name}")
