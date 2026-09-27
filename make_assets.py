#!/usr/bin/env python3
"""
make_assets.py — regenerates every visual asset in assets/.

    python3 make_assets.py

Stdlib only. Writes:
    assets/boot.svg    — animated system boot sequence (SMIL, no JS)
    assets/header.svg  — identity panel (pixel wordmark, status, terrain)
    assets/dot.svg     — pulsing status dot (inline, 16x16)

Design:
    The profile README behaves like a small OS. Every SVG is a "screen":
    near-black bg, thin frame, HUD corner ticks, faint scanlines.
    Palette is deliberately small: one green, one amber, muted greys.
"""

import pathlib
import xml.dom.minidom

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- palette
BG    = "#0a0e13"   # near-black, faint blue
LINE  = "#1d2937"   # frame / dividers
TXT   = "#dbe4ec"   # off-white
DIM   = "#647a92"   # muted grey-blue
GREEN = "#3fd487"   # primary accent — terminal green, muted
AMBER = "#d9a05b"   # secondary accent — muted amber
CYAN  = "#4cc9e0"   # one-shot glitch ghost only
RED   = "#e06056"   # one-shot glitch ghost only

FONT = "ui-monospace, 'SF Mono', 'Cascadia Mono', 'DejaVu Sans Mono', Menlo, Consolas, monospace"

# ------------------------------------------------------------- pixel font
# 5x7 block glyphs. Only the letters the design needs — keep it lean.
GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
}


def pixel_block(text, x, y, px, fill, opacity=1.0):
    """Render `text` as 5x7 pixel blocks. Returns (svg, total_width)."""
    parts = []
    cx = x
    for ch in text:
        rows = GLYPHS[ch.upper()]
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == "1":
                    parts.append(
                        f'<rect x="{cx + rx * px}" y="{y + ry * px}" '
                        f'width="{px}" height="{px}" fill="{fill}" opacity="{opacity}"/>'
                    )
        cx += 6 * px
    return "".join(parts), 6 * px * len(text) - px


# ----------------------------------------------------------------- chrome
def screen_open(w, h):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img">'
        f'<rect width="{w}" height="{h}" fill="{BG}"/>'
        f'<defs><pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1" fill="#ffffff" opacity="0.018"/></pattern></defs>'
        f'<rect width="{w}" height="{h}" fill="url(#scan)"/>'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" fill="none" stroke="{LINE}"/>'
    )


def corner_ticks(w, h, length=14, inset=6):
    t = []
    # top-left, top-right, bottom-left, bottom-right
    t.append(f'<path d="M {inset} {inset + length} L {inset} {inset} L {inset + length} {inset}" fill="none" stroke="{GREEN}" stroke-width="2" opacity="0.9"/>')
    t.append(f'<path d="M {w - inset - length} {inset} L {w - inset} {inset} L {w - inset} {inset + length}" fill="none" stroke="{GREEN}" stroke-width="2" opacity="0.9"/>')
    t.append(f'<path d="M {inset} {h - inset - length} L {inset} {h - inset} L {inset + length} {h - inset}" fill="none" stroke="{GREEN}" stroke-width="2" opacity="0.9"/>')
    t.append(f'<path d="M {w - inset - length} {h - inset} L {w - inset} {h - inset} L {w - inset} {h - inset - length}" fill="none" stroke="{GREEN}" stroke-width="2" opacity="0.9"/>')
    return "".join(t)


def text(x, y, s, size, fill, ls=0, anchor="start", opacity=1.0, weight="normal"):
    style = f' font-family="{FONT}" font-size="{size}" fill="{fill}"'
    if ls:
        style += f' letter-spacing="{ls}"'
    if opacity != 1.0:
        style += f' opacity="{opacity}"'
    if weight != "normal":
        style += f' font-weight="{weight}"'
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}"{style}>{s}</text>'


# ------------------------------------------------------------ boot screen
def build_boot():
    W, H = 720, 336
    s = [screen_open(W, H), corner_ticks(W, H)]

    # top bar
    s.append(text(44, 24, "RKH//OS — personal build interface", 11, DIM, ls=1))
    s.append(
        f'<circle cx="598" cy="20" r="3" fill="{GREEN}">'
        f'<animate attributeName="opacity" values="1;0.3;1" dur="1.8s" repeatCount="indefinite"/>'
        f"</circle>"
    )
    s.append(text(608, 24, "BLR · IST", 11, DIM, ls=1))
    s.append(f'<line x1="0" y1="36.5" x2="{W}" y2="36.5" stroke="{LINE}"/>')

    # boot lines — each revealed left-to-right inside an animated clip
    lines = [
        ("init user/rakshan", [("ok", GREEN)]),
        ("scan /builds", [("08", GREEN), (" found", DIM)]),
        ("mount toolkit [py·c·ts·sql]", [("ok", GREEN)]),
        ("calibrate overthink module", [("ok", GREEN)]),
        ("open comms [gh·in·ig·mail]", [("ok", GREEN)]),
        ("set locale", [("blr/ist", AMBER)]),
    ]
    y0, step, fs = 76, 26, 13
    clips, body = [], []
    for i, (prefix, value) in enumerate(lines):
        dots = "·" * max(0, 44 - len(prefix) - 2)
        plain = f"> {prefix} {dots}"
        width = len(plain) + sum(len(v) for v, _ in value)
        cy = y0 + i * step
        clip_w = int(width * 8.0) + 12
        clips.append(
            f'<clipPath id="b{i}"><rect x="44" y="{cy - 16}" width="0" height="22">'
            f'<animate attributeName="width" from="0" to="{clip_w}" '
            f'dur="{max(0.22, width * 0.014):.2f}s" begin="{0.35 + i * 0.42:.2f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        tspans = "".join(f'<tspan fill="{c}">{v}</tspan>' for v, c in value)
        body.append(
            f'<g clip-path="url(#b{i})">'
            f'<text x="44" y="{cy}" font-family="{FONT}" font-size="{fs}">'
            f'<tspan fill="{DIM}">{plain}</tspan>{tspans}</text></g>'
        )
    s.append("<defs>" + "".join(clips) + "</defs>")
    s.extend(body)

    # progress
    s.append(text(44, 244, "> rendering display", 11, DIM))
    s.append(f'<rect x="44" y="254" width="336" height="9" fill="none" stroke="{LINE}"/>')
    s.append(
        f'<rect x="45" y="255" width="0" height="7" fill="{GREEN}">'
        f'<animate attributeName="width" from="0" to="334" dur="0.95s" begin="2.75s" fill="freeze"/>'
        f"</rect>"
    )

    # SYSTEM ONLINE — flicker in, one-shot glitch ghosts, blinking cursor
    s.append(
        f'<text x="46" y="302" font-family="{FONT}" font-size="19" letter-spacing="3" fill="{CYAN}" opacity="0">'
        f"SYSTEM ONLINE"
        f'<animate attributeName="opacity" values="0;0.35;0" dur="0.3s" begin="3.85s" fill="freeze"/>'
        f"</text>"
    )
    s.append(
        f'<text x="42" y="302" font-family="{FONT}" font-size="19" letter-spacing="3" fill="{RED}" opacity="0">'
        f"SYSTEM ONLINE"
        f'<animate attributeName="opacity" values="0;0.3;0" dur="0.3s" begin="3.85s" fill="freeze"/>'
        f"</text>"
    )
    s.append(
        f'<text x="44" y="302" font-family="{FONT}" font-size="19" letter-spacing="3" fill="{GREEN}" opacity="0">'
        f"SYSTEM ONLINE"
        f'<animate attributeName="opacity" values="0;1;0.35;1" keyTimes="0;0.35;0.65;1" dur="0.4s" begin="3.8s" fill="freeze"/>'
        f"</text>"
    )
    s.append(
        f'<rect x="238" y="287" width="11" height="17" fill="{GREEN}" opacity="0">'
        f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1.06s" '
        f'begin="4.4s" repeatCount="indefinite"/>'
        f"</rect>"
    )
    s.append(text(676, 302, "rakshan@blr:~$", 11, DIM, anchor="end"))

    return f'{"".join(s)}</svg>'


# ---------------------------------------------------------- header screen
def _lcg(seed):
    state = seed
    while True:
        state = (state * 1103515245 + 12345) % (2 ** 31)
        yield state % 100


def build_header():
    W, H = 720, 224
    s = [screen_open(W, H), corner_ticks(W, H)]

    # top bar
    s.append(text(44, 24, "user/rakshan", 11, DIM, ls=1))
    blr, _ = pixel_block("BLR", W - 44 - 51, 9, 3, GREEN, opacity=0.55)
    s.append(blr)
    s.append(f'<line x1="0" y1="36.5" x2="{W}" y2="36.5" stroke="{LINE}"/>')

    # pixel wordmark + blinking block cursor
    word, word_w = pixel_block("RAKSHAN", 44, 56, 7, GREEN)
    s.append(word)
    s.append(
        f'<rect x="{44 + word_w + 10}" y="{56 + 6 * 7}" width="7" height="7" fill="{GREEN}" opacity="1">'
        f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1.1s" repeatCount="indefinite"/>'
        f"</rect>"
    )

    # handle
    s.append(text(46, 142, "silicon-rationalist", 15, "#7d90a6", ls=4))

    # status panel
    s.append(f'<line x1="470.5" y1="52" x2="470.5" y2="140" stroke="{LINE}"/>')
    s.append(text(494, 74, "STATUS", 10.5, DIM, ls=2))
    s.append(
        f'<circle cx="568" cy="70" r="3" fill="{GREEN}">'
        f'<animate attributeName="opacity" values="1;0.35;1" dur="2.4s" repeatCount="indefinite"/>'
        f"</circle>"
    )
    s.append(text(578, 74, "BUILDING", 12, GREEN, ls=2))
    s.append(text(494, 100, "ACTIVE", 10.5, DIM, ls=2))
    s.append(text(574, 100, "ANTARA", 12, TXT, ls=2))
    s.append(text(494, 126, "LOCALE", 10.5, DIM, ls=2))
    s.append(text(574, 126, "BLR · IN", 12, TXT, ls=2))

    # terrain strip — generated, deterministic, on purpose
    rng = _lcg(7)
    blocks = []
    x = 44
    i = 0
    while x + 8 <= W - 44:
        h = 2 + next(rng) % 15
        if i % 9 == 4:
            blocks.append(f'<rect x="{x}" y="{192 - h}" width="8" height="{h}" fill="{AMBER}" opacity="0.4"/>')
        else:
            blocks.append(f'<rect x="{x}" y="{192 - h}" width="8" height="{h}" fill="{GREEN}" opacity="0.22"/>')
        x += 10
        i += 1
    s.append("".join(blocks))
    s.append(text(44, 212, "terrain // seed: rakshan — not finished", 10, DIM))
    s.append(text(W - 44, 212, "profile v1.3", 10, DIM, anchor="end"))

    return f'{"".join(s)}</svg>'


# ------------------------------------------------------------------ dot
def build_dot():
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" role="img">'
        f'<circle cx="8" cy="8" r="6.5" fill="none" stroke="{GREEN}" opacity="0.3" stroke-width="1"/>'
        f'<circle cx="8" cy="8" r="3.5" fill="{GREEN}">'
        f'<animate attributeName="opacity" values="1;0.35;1" dur="1.8s" repeatCount="indefinite"/>'
        f"</circle></svg>"
    )


# ----------------------------------------------------------------- main
def main():
    files = {
        "boot.svg": build_boot(),
        "header.svg": build_header(),
        "dot.svg": build_dot(),
    }
    for name, svg in files.items():
        path = OUT / name
        path.write_text(svg, encoding="utf-8")
        # validate: must be well-formed XML
        xml.dom.minidom.parseString(svg)
        print(f"  wrote {path.relative_to(ROOT)}  ({len(svg)} bytes, valid xml)")
    print("done. open the profile repo and refresh.")


if __name__ == "__main__":
    main()
