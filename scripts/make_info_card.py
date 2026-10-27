#!/usr/bin/env python3
"""
Render a neofetch-style info card as a terminal-window SVG that sits beside
edgar-ascii.svg. Same 840 x 880 canvas as the portrait so the two panels line
up when the README shows them side by side at equal widths.

Each line types itself in (left-to-right clip wipe, staggered top -> bottom),
then a row of neofetch color blocks fades in. GitHub runs SMIL inside <img>
SVGs but never JS, so everything is declarative.

Edit INFO below and re-run:  python scripts/make_info_card.py
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")

USER_HOST = "edgar@serverlys"

# (key, value). key=None -> blank spacer line
INFO = [
    ("Name", "Edgar Martinez"),
    ("Role", "Founder · Full-Stack Engineer · AI Architect"),
    ("Company", "Serverlys"),
    (None, None),
    ("Building", "ConvoAI: AI employees for website chat"),
    ("", "and WhatsApp"),
    ("", "Voice AI agents for service businesses"),
    ("", "Hosting + automation platform"),
    (None, None),
    ("Languages", "TypeScript, Python, PHP, Go"),
    ("Frameworks", "Next.js, React, Node.js, Django"),
    ("AI", "Claude, OpenAI, Retell AI, n8n"),
    ("Infra", "Docker, PostgreSQL, Redis, Stripe"),
    (None, None),
    ("Motto", "If a human repeats it, I automate it."),
    ("Site", "serverlys.com"),
]

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
KEY = "#5fb4ff"
ACCENT = "#2f6bff"

W, H = 840, 880                      # == edgar-ascii.svg canvas
PAD = 28
TITLEBAR_H = 30
FONT = 22
LINE_H = 38
KEY_W = 184                          # key column width
CHAR_W = FONT * 0.6                  # monospace advance

# timing (seconds)
START = 0.4
LINE_DUR = 0.35
STAGGER = 0.28

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<style>'
    '.f{opacity:0;animation:in .5s ease-out both}'
    '@keyframes in{to{opacity:1}}'
    '@media (prefers-reduced-motion: reduce){.f{opacity:1!important;animation:none!important}}'
    '</style>',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{20 + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">{USER_HOST}: ~$ neofetch</text>')

# header: user@host + underline, like neofetch
lines = [("hdr", None, None), ("sep", None, None)] + [("kv", k, v) for k, v in INFO]

y0 = TITLEBAR_H + PAD + FONT
for i, (kind, k, v) in enumerate(lines):
    y = y0 + i * LINE_H
    if kind == "kv" and k is None:
        continue
    delay = START + i * STAGGER

    if kind == "hdr":
        user, host = USER_HOST.split("@")
        body = (f'<tspan fill="{KEY}" font-weight="700">{user}</tspan>'
                f'<tspan fill="{INK}">@</tspan>'
                f'<tspan fill="{KEY}" font-weight="700">{host}</tspan>')
        n_chars = len(USER_HOST)
    elif kind == "sep":
        body = f'<tspan fill="{MUTED}">{"-" * len(USER_HOST)}</tspan>'
        n_chars = len(USER_HOST)
    else:
        key = f'{html.escape(k)}:' if k else ""
        body = (f'<tspan fill="{KEY}" font-weight="700">{key}</tspan>'
                f'<tspan x="{PAD + KEY_W}" fill="{INK}">{html.escape(v)}</tspan>')
        n_chars = len(v) + KEY_W / CHAR_W

    wipe_w = n_chars * CHAR_W + 8
    top = y - FONT
    parts.append(
        f'<clipPath id="l{i}"><rect x="{PAD}" y="{top:.1f}" height="{LINE_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{wipe_w:.1f}" begin="{delay:.2f}s" '
        f'dur="{LINE_DUR}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(f'<g clip-path="url(#l{i})"><text x="{PAD}" y="{y}" font-size="{FONT}">{body}</text></g>')

# neofetch color blocks
blocks_y = y0 + len(lines) * LINE_H - FONT + 8
blocks_delay = START + len(lines) * STAGGER
colors = ["#161b22", "#ff5f56", "#27c93f", "#ffbd2e", ACCENT, "#bc8cff", "#39c5cf", INK]
bw = 44
parts.append(f'<g class="f" style="animation-delay:{blocks_delay:.2f}s">')
for i, c in enumerate(colors):
    parts.append(f'<rect x="{PAD + i*bw}" y="{blocks_y}" width="{bw}" height="26" fill="{c}"/>')
parts.append('</g>')

# prompt with a steady blinking cursor
prompt_y = H - PAD
parts.append(f'<text class="f" style="animation-delay:{blocks_delay + 0.3:.2f}s" x="{PAD}" y="{prompt_y}" '
             f'fill="{MUTED}" font-size="{FONT}">{USER_HOST}:~$</text>')
cx = PAD + (len(USER_HOST) + 4) * CHAR_W
parts.append(f'<rect x="{cx:.1f}" y="{prompt_y - FONT + 4}" width="12" height="{FONT}" fill="{INK}" opacity="0">'
             f'<set attributeName="opacity" to="1" begin="{blocks_delay + 0.3:.2f}s"/>'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" begin="{blocks_delay + 0.3:.2f}s" repeatCount="indefinite"/></rect>')

parts.append('</svg>')
svg = "".join(parts)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg)//1024} KB")
