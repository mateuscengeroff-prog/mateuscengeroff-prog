"""Build the profile README graphics from portfolio/projects.json.

Usage:  python scripts/build.py

What it does
  1. Reads portfolio/projects.json (the single source of truth for projects).
  2. Writes light and dark SVGs to assets/ (hero, one card per project, footer).
  3. Rewrites the block between the PROJECTS markers in README.md.

Fonts are subset to the characters each SVG uses and embedded as base64 WOFF,
because GitHub renders README SVGs as <img>, which cannot load external fonts.
Requires: fonttools (pip install fonttools). No network access needed.
"""
from __future__ import annotations

import base64
import io
import json
import re
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
ASSETS = ROOT / "assets"
DATA = ROOT / "portfolio" / "projects.json"
README = ROOT / "README.md"

WIDTH = 860  # close to GitHub's README column, so desktop renders near 1:1

FONT_FILES = {
    "serif": "InstrumentSerif-Regular.ttf",
    "mono": "JetBrainsMono-Regular.ttf",
    "sans": "Inter-Regular.otf",
    "sans-medium": "Inter-Medium.otf",
}
FONT_FAMILY = {
    "serif": "PSerif",
    "mono": "PMono",
    "sans": "PSans",
    "sans-medium": "PSansMedium",
}

# Colours sit on GitHub's own page background (transparent SVGs).
# GitHub dark page: #0d1117, light page: #ffffff. Checked with scripts/contrast.py.
THEMES = {
    "dark": {
        "text": "#E3E7E4",
        "muted": "#8F989E",
        "line": "#3B434B",
        "faint": "#262C33",
        "surface": "#11161D",
        "frame": "#2B333C",
        "accent": "#7DB8A3",
        "status": {
            "planned": "#8F989E",
            "prototype": "#AFA2D6",
            "in-development": "#7DB8A3",
            "under-review": "#D9B068",
            "completed": "#A6CF86",
        },
    },
    "light": {
        "text": "#1B2127",
        "muted": "#59626A",
        "line": "#C3CACF",
        "faint": "#E4E8EB",
        "surface": "#F6F8F7",
        "frame": "#D3DADE",
        "accent": "#2D7560",
        "status": {
            "planned": "#59626A",
            "prototype": "#61529E",
            "in-development": "#2D7560",
            "under-review": "#8C5F0E",
            "completed": "#3F7A1F",
        },
    },
}

STATUS_LABEL = {
    "planned": "Planned",
    "prototype": "Prototype",
    "in-development": "In development",
    "under-review": "Under review",
    "completed": "Completed",
}
# Position on the road to main. "planned" has no branch yet.
STAGES = ["prototype", "in-development", "under-review", "completed"]
STAGE_TEXT = ["prototype", "in development", "under review", "merged into main"]
HERO_STAGE_TEXT = ["prototype", "in development", "under review", "merged"]


# ---------------------------------------------------------------- fonts ----
_font_cache: dict[str, TTFont] = {}


def font(key: str) -> TTFont:
    if key not in _font_cache:
        _font_cache[key] = TTFont(FONTS / FONT_FILES[key])
    return _font_cache[key]


def text_width(s: str, key: str, size: float) -> float:
    f = font(key)
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    upm = f["head"].unitsPerEm
    total = 0
    for ch in s:
        glyph = cmap.get(ord(ch))
        total += hmtx[glyph][0] if glyph else upm * 0.5
    return total * size / upm


class Fonts:
    """Collects the characters used per font, then emits @font-face rules."""

    def __init__(self) -> None:
        self.used: dict[str, set[str]] = {}

    def use(self, key: str, s: str) -> str:
        self.used.setdefault(key, set()).update(s)
        return FONT_FAMILY[key]

    def css(self) -> str:
        rules = []
        for key, chars in sorted(self.used.items()):
            opts = subset.Options()
            opts.flavor = "woff"
            opts.layout_features = ["kern", "liga"]
            opts.name_IDs = []
            opts.notdef_outline = True
            sub = subset.Subsetter(opts)
            f = TTFont(FONTS / FONT_FILES[key], recalcTimestamp=False)  # deterministic output
            sub.populate(text="".join(sorted(chars)) + " ")
            sub.subset(f)
            buf = io.BytesIO()
            f.flavor = "woff"
            f.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            rules.append(
                f"@font-face{{font-family:{FONT_FAMILY[key]};"
                f"src:url(data:font/woff;base64,{b64}) format('woff');}}"
            )
        return "".join(rules)


def wrap(s: str, key: str, size: float, max_w: float) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if text_width(trial, key, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text(fonts: Fonts, key: str, s: str, x: float, y: float, size: float,
         fill: str, anchor: str = "start", extra: str = "") -> str:
    fam = fonts.use(key, s)
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def svg_doc(w: int, h: int, title: str, desc: str, fonts: Fonts, style: str, body: str) -> str:
    base_css = (
        fonts.css()
        + style
        + "@media (prefers-reduced-motion: reduce){*{animation:none!important;}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
        f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f"<style>{base_css}</style>{body}</svg>\n"
    )


# ---------------------------------------------------------------- shapes ---
def branch_path(x0: float, y_main: float, y_lane: float, x_end: float, r: float = 22) -> str:
    """Leaves main at x0, rises to the lane with a soft corner, runs to x_end."""
    return (f"M{x0},{y_main} V{y_lane + r} "
            f"Q{x0},{y_lane} {x0 + r},{y_lane} H{x_end}")


def merge_path(x_from: float, y_lane: float, x_to: float, y_main: float, r: float = 22) -> str:
    return f"M{x_from},{y_lane} H{x_to - r} Q{x_to},{y_lane} {x_to},{y_lane + r} V{y_main}"


# ------------------------------------------------------------- drafting ---
# Visual language: each graphic is a "drawing sheet". Hairline frames, crop
# marks, a title block for metadata and one figure per project that tells its
# story with a single slow, looping motion. Reduced motion shows a still frame
# that still makes sense (the base attributes are the meaningful pose).

def crop_marks(t: dict, x: float, y: float, w: float, h: float, n: float = 9, gap: float = 5) -> str:
    c = t["frame"]
    segs = []
    for cx, cy, dx, dy in ((x, y, -1, -1), (x + w, y, 1, -1), (x, y + h, -1, 1), (x + w, y + h, 1, 1)):
        segs.append(f"M{cx + dx * gap},{cy} h{dx * n} M{cx},{cy + dy * gap} v{dy * n}")
    return f'<path d="{" ".join(segs)}" stroke="{c}" stroke-width="1" fill="none"/>'


def hairline(t: dict, x1: float, y1: float, x2: float, y2: float, dash: str = "") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{t["frame"]}" stroke-width="1"{d}/>'


def label(fonts: "Fonts", t: dict, s: str, x: float, y: float, anchor: str = "start",
          fill: str | None = None, size: float = 11) -> str:
    return text(fonts, "mono", s, x, y, size, fill or t["muted"], anchor)


MOTION_CSS = (
    ".draw{stroke-dasharray:1;animation:draw 1.2s cubic-bezier(.6,0,.2,1) both;}"
    "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
    ".fade{animation:fade .8s ease-out both;}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    ".rise{animation:rise 1s cubic-bezier(.2,.7,.2,1) both;}"
    "@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
    ".ring{transform-box:fill-box;transform-origin:center;animation:ring 1.6s ease-out both;}"
    "@keyframes ring{0%{opacity:0;transform:scale(.2)}40%{opacity:1}100%{opacity:0;transform:scale(2.6)}}"
)


# ------------------------------------------------------------------ hero ---
def build_hero(projects: list[dict], theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = WIDTH, 520
    p = []
    p.append(crop_marks(t, 6, 6, W - 12, H - 12))

    # Left: the typographic statement.
    p.append(text(fonts, "sans", "Software engineering portfolio", 2, 54, 14, t["muted"],
                  extra='class="fade"'))
    p.append(text(fonts, "serif", "Mateus", -4, 178, 138, t["text"],
                  extra='letter-spacing="-2" class="rise" style="animation-delay:.05s"'))
    p.append(text(fonts, "serif", "Engeroff", -4, 300, 138, t["text"],
                  extra='letter-spacing="-2" class="rise" style="animation-delay:.18s"'))
    for i, line in enumerate(wrap("Building real software while learning how it should be built.", "sans", 23, 450)):
        p.append(text(fonts, "sans", line, 2, 356 + i * 32, 23, t["text"],
                      extra=f'class="fade" style="animation-delay:{.45 + i * .1:.2f}s"'))
    p.append(text(fonts, "sans", "Software development intern at CABERGS", 2, 444, 15, t["muted"],
                  extra='class="fade" style="animation-delay:.7s"'))
    p.append(text(fonts, "sans", "Computer science student at Unisinos", 2, 466, 15, t["muted"],
                  extra='class="fade" style="animation-delay:.75s"'))

    # Right: a vertical "git log --graph" of the featured work. Newest at the top.
    featured = [x for x in projects if x.get("featured", True) and x["status"] != "planned"][:3]
    tx, top, bottom = 584, 40, 366
    p.append(f'<path class="draw" style="animation-delay:.3s" pathLength="1" d="M{tx},{bottom} V{top + 26}" '
             f'stroke="{t["line"]}" stroke-width="2" fill="none"/>')
    p.append(f'<path d="M{tx},{top + 22} V{top}" stroke="{t["line"]}" stroke-width="2" '
             f'stroke-dasharray="2 5" fill="none" class="fade" style="animation-delay:1.3s"/>')
    p.append(f'<circle cx="{tx}" cy="{bottom}" r="4.5" fill="{t["line"]}"/>')
    p.append(label(fonts, t, "main", tx + 14, bottom + 4))
    rows = [86, 178, 270]
    for i, (proj, y) in enumerate(zip(featured, rows)):
        color = t["status"][proj["status"]]
        delay = 0.7 + i * 0.28
        fork = y + 52
        d = f"M{tx},{fork} C{tx},{fork - 30} {tx + 32},{y + 22} {tx + 32},{y}"
        p.append(f'<path class="draw" style="animation-delay:{delay}s" pathLength="1" d="{d}" '
                 f'stroke="{color}" stroke-width="2" fill="none"/>')
        p.append(f'<circle cx="{tx}" cy="{fork}" r="3.5" fill="{color}" class="fade" style="animation-delay:{delay}s"/>')
        p.append(f'<circle cx="{tx + 32}" cy="{y}" r="7" fill="none" stroke="{color}" stroke-width="2" '
                 f'class="fade" style="animation-delay:{delay + .5}s"/>')
        p.append(f'<circle cx="{tx + 32}" cy="{y}" r="7" fill="none" stroke="{color}" stroke-width="1" '
                 f'class="ring" style="animation-delay:{delay + .5}s"/>')
        for j, line in enumerate(wrap(proj["name"], "serif", 27, 210)):
            p.append(text(fonts, "serif", line, tx + 54, y + 9 + j * 27, 27, t["text"],
                          extra=f'class="fade" style="animation-delay:{delay + .55}s"'))
        p.append(text(fonts, "mono", STATUS_LABEL[proj["status"]].lower(), tx + 55, y - 16, 12, color,
                      extra=f'class="fade" style="animation-delay:{delay + .6}s"'))

    # Title block: the sheet's metadata, as on a technical drawing.
    bx, by, bw, rh = 568, 400, W - 574, 34
    rows_tb = [("based in", "Porto Alegre, Brazil", t["text"]),
               ("open to", "Roles in Brazil and abroad", t["accent"]),
               ("revised", "October 2026", t["text"])]
    p.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{rh * 3}" fill="none" stroke="{t["frame"]}" '
             f'class="fade" style="animation-delay:1.2s"/>')
    p.append(hairline(t, bx + 78, by, bx + 78, by + rh * 3))
    for i, (k, v, c) in enumerate(rows_tb):
        y = by + i * rh
        if i:
            p.append(hairline(t, bx, y, bx + bw, y))
        p.append(label(fonts, t, k, bx + 10, y + 21))
        p.append(text(fonts, "sans", v, bx + 90, y + 22, 14, c))

    names = ", ".join(f'{x["name"]} ({STATUS_LABEL[x["status"]].lower()})' for x in featured)
    return svg_doc(
        W, H, "Mateus Engeroff",
        "Mateus Engeroff, software engineering portfolio. Building real software while learning how it "
        "should be built. Software development intern at CABERGS and computer science student at Unisinos. "
        "Based in Porto Alegre, Brazil, open to roles in Brazil and abroad. "
        f"A vertical branch graph lists the featured projects: {names}.",
        fonts, MOTION_CSS, "".join(p),
    )


# --------------------------------------------------------------- figures ---
# Each figure is drawn inside the box (x, y, w, h) and returns (svg, css, caption).
FIG_CAPTION = {
    "acc": "Diagram of the review flow, not a screenshot",
    "community": "Diagram of the main flows, not a screenshot",
    "vault": "Design sketch; the match loop is in a draft PR",
}


def fig_acc(fonts, t, x, y, w, h, labels=True):
    """Tasks leave a queue, each in its own worktree, and stop at a human review gate."""
    s = []
    lb = (lambda *a, **k: label(fonts, t, *a, **k)) if labels else (lambda *a, **k: "")
    lanes = [y + 52, y + 112, y + 172]
    qx = x + 8
    s.append(lb("queue", qx, y + 18))
    for i in range(4):
        s.append(f'<rect x="{qx}" y="{y + 34 + i * 26}" width="34" height="18" rx="3" fill="none" '
                 f'stroke="{t["line"]}" stroke-width="1.5"/>')
    gx = x + w - 104
    s.append(lb("one worktree per task", x + 70, y + 18))
    for ly in lanes:
        s.append(f'<path d="M{qx + 40},{y + 70} C{x + 64},{y + 70} {x + 64},{ly} {x + 88},{ly} H{gx - 8}" '
                 f'stroke="{t["line"]}" stroke-width="1.5" fill="none"/>')
        s.append(f'<path d="M{x + 92},{ly - 9} h-5 v18 h5" stroke="{t["frame"]}" fill="none"/>')
    # the review gate
    s.append(f'<rect class="gate" x="{gx}" y="{y + 30}" width="10" height="{h - 70}" rx="2" '
             f'fill="none" stroke="{t["accent"]}" stroke-width="1.5"/>')
    s.append(lb("human review", gx + 5, y + 18, "middle"))
    s.append(f'<path d="M{gx + 10},{lanes[1]} H{x + w - 6}" stroke="{t["line"]}" stroke-width="1.5" '
             f'stroke-dasharray="3 5" fill="none"/>')
    s.append(lb("main", x + w - 6, lanes[1] - 10, "end"))
    s.append(lb("after", x + w - 6, lanes[1] + 22, "end"))
    s.append(lb("approval", x + w - 6, lanes[1] + 36, "end"))
    # parked tasks: one waiting at the gate, one halfway
    s.append(f'<rect x="{gx - 34}" y="{lanes[0] - 9}" width="26" height="18" rx="3" fill="{t["line"]}"/>')
    s.append(f'<rect x="{x + 150}" y="{lanes[2] - 9}" width="26" height="18" rx="3" fill="{t["line"]}"/>')
    # the moving task: base pose = waiting at the gate (reduced motion)
    s.append(f'<rect class="task" x="{gx - 34}" y="{lanes[1] - 9}" width="26" height="18" rx="3" fill="{t["accent"]}"/>')
    travel = gx - 34 - (x + 96)
    css = (f".task{{animation:task 8s cubic-bezier(.45,0,.2,1) infinite;}}"
           f"@keyframes task{{0%{{transform:translateX(-{travel}px);opacity:0}}6%{{opacity:1}}"
           f"42%{{transform:none}}92%{{transform:none;opacity:1}}100%{{transform:none;opacity:0}}}}"
           f".gate{{animation:gate 8s ease-in-out infinite;}}"
           f"@keyframes gate{{0%,40%{{stroke-width:1.5}}48%{{stroke-width:3}}60%,100%{{stroke-width:1.5}}}}")
    return "".join(s), css


def fig_community(fonts, t, x, y, w, h, labels=True):
    """A phone-sized feed next to a shared board where a proposed clue gets accepted."""
    s = []
    lb = (lambda *a, **k: label(fonts, t, *a, **k)) if labels else (lambda *a, **k: "")
    px, py, pw, ph = x + 6, y + 2, 112, h - 32
    s.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="none" stroke="{t["line"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{px + 42}" y1="{py + 12}" x2="{px + pw - 42}" y2="{py + 12}" stroke="{t["line"]}" stroke-width="3" stroke-linecap="round"/>')
    for i in range(3):
        cy = py + 30 + i * 58
        s.append(f'<rect x="{px + 10}" y="{cy}" width="{pw - 20}" height="48" rx="6" fill="none" stroke="{t["frame"]}"/>')
        s.append(f'<circle cx="{px + 22}" cy="{cy + 13}" r="5" fill="{t["frame"]}"/>')
        s.append(f'<line x1="{px + 32}" y1="{cy + 13}" x2="{px + 70}" y2="{cy + 13}" stroke="{t["line"]}" stroke-width="3" stroke-linecap="round"/>')
        s.append(f'<line x1="{px + 16}" y1="{cy + 28}" x2="{px + pw - 18}" y2="{cy + 28}" stroke="{t["frame"]}" stroke-width="3" stroke-linecap="round"/>')
        s.append(f'<line x1="{px + 16}" y1="{cy + 38}" x2="{px + pw - 42}" y2="{cy + 38}" stroke="{t["frame"]}" stroke-width="3" stroke-linecap="round"/>')
    s.append(lb("paginated feed", px + pw / 2, py + ph + 16, "middle"))
    # board
    bx = x + 150
    nodes = [(bx + 40, y + 52), (bx + 150, y + 30), (bx + 112, y + 118), (bx + 22, y + 160)]
    edges = [(0, 1), (1, 2), (0, 2), (2, 3)]
    for a, b in edges:
        s.append(f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}" stroke="{t["line"]}" stroke-width="1.5"/>')
    for nx, ny in nodes:
        s.append(f'<rect x="{nx - 22}" y="{ny - 14}" width="44" height="28" rx="4" fill="{t["surface"]}" stroke="{t["line"]}" stroke-width="1.5"/>')
        s.append(f'<line x1="{nx - 13}" y1="{ny - 3}" x2="{nx + 13}" y2="{ny - 3}" stroke="{t["frame"]}" stroke-width="3" stroke-linecap="round"/>')
        s.append(f'<line x1="{nx - 13}" y1="{ny + 6}" x2="{nx + 4}" y2="{ny + 6}" stroke="{t["frame"]}" stroke-width="3" stroke-linecap="round"/>')
    s.append(lb("shared mystery board", bx + 8, y + h - 14))
    # proposed clue: slides in, gets connected, then accepted (base pose = accepted)
    cx_, cy_ = bx + 222, y + 150
    s.append(f'<line class="link" pathLength="1" x1="{nodes[2][0]}" y1="{nodes[2][1]}" x2="{cx_}" y2="{cy_}" '
             f'stroke="{t["accent"]}" stroke-width="1.5"/>')
    s.append(f'<g class="clue"><rect x="{cx_ - 24}" y="{cy_ - 15}" width="48" height="30" rx="4" fill="{t["surface"]}" '
             f'stroke="{t["accent"]}" stroke-width="1.5" class="cluebox"/>'
             f'<path class="tick" d="M{cx_ - 8},{cy_} l5,5 l10,-11" stroke="{t["accent"]}" stroke-width="2" fill="none" '
             f'stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></g>')
    s.append(lb("clue accepted by the author", cx_ + 26, cy_ + 34, "end", t["accent"]))
    css = (".clue{animation:clue 9s cubic-bezier(.3,0,.2,1) infinite;}"
           "@keyframes clue{0%{transform:translateX(60px);opacity:0}12%,100%{transform:none;opacity:1}}"
           ".link{stroke-dasharray:1;animation:link 9s ease-in-out infinite;}"
           "@keyframes link{0%,14%{stroke-dashoffset:1}30%,100%{stroke-dashoffset:0}}"
           ".tick{stroke-dasharray:1;animation:tick 9s ease-out infinite;}"
           "@keyframes tick{0%,36%{stroke-dashoffset:1}46%,100%{stroke-dashoffset:0}}"
           ".cluebox{animation:cb 9s linear infinite;}"
           "@keyframes cb{0%,30%{stroke-dasharray:4 3}31%,100%{stroke-dasharray:none}}")
    return "".join(s), css


def _iso(ox, oy, gx, gy, gz=0.0, s=21.0):
    return ox + (gx - gy) * s * 0.866, oy + (gx + gy) * s * 0.5 - gz * s


def _poly(pts, fill, stroke, extra=""):
    return f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1.2" stroke-linejoin="round" {extra}/>'


def _box(ox, oy, x0, y0, x1, y1, z, t, extra=""):
    I = lambda a, b, c=0.0: _iso(ox, oy, a, b, c)
    top = [I(x0, y0, z), I(x1, y0, z), I(x1, y1, z), I(x0, y1, z)]
    right = [I(x1, y0, 0), I(x1, y1, 0), I(x1, y1, z), I(x1, y0, z)]
    front = [I(x0, y1, 0), I(x1, y1, 0), I(x1, y1, z), I(x0, y1, z)]
    return (f'<g {extra}>' + _poly(right, t["frame"], t["line"]) + _poly(front, t["surface"], t["line"])
            + _poly(top, t["faint"], t["line"]) + "</g>")


def fig_vault(fonts, t, x, y, w, h, labels=True):
    """Isometric arena: two bases, a core in the middle and SHIFT walls that swap routes."""
    s = []
    lb = (lambda *a, **k: label(fonts, t, *a, **k)) if labels else (lambda *a, **k: "")
    ox, oy = x + w / 2 + 10, y + 6
    G = 9
    I = lambda a, b, c=0.0: _iso(ox, oy, a, b, c)
    s.append(_poly([I(0, 0), I(G, 0), I(G, G), I(0, G)], "none", t["line"]))
    for k in range(1, G):
        a, b = I(k, 0), I(k, G)
        s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{t["frame"]}" stroke-width="1"/>')
        a, b = I(0, k), I(G, k)
        s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{t["frame"]}" stroke-width="1"/>')
    team_a, team_b = t["accent"], t["status"]["under-review"]
    s.append(_poly([I(0, 0), I(2, 0), I(2, 2), I(0, 2)], team_a, team_a, 'fill-opacity=".28"'))
    s.append(_poly([I(G - 2, G - 2), I(G, G - 2), I(G, G), I(G - 2, G)], team_b, team_b, 'fill-opacity=".28"'))
    # SHIFT walls swap the open route; base pose shows wall A up.
    # Painter's order: wall A (behind the core), core, then wall B (in front).
    s.append(_box(ox, oy, 2.6, 2.3, 2.9, 5.2, 1.5, t, 'class="wallA"'))
    # the core
    gx_, gy_ = I(G / 2, G / 2)
    s.append(f'<ellipse cx="{gx_:.1f}" cy="{gy_:.1f}" rx="14" ry="7" fill="none" stroke="{t["line"]}"/>')
    cx, cy = I(G / 2, G / 2, 0.9)
    s.append(f'<path class="core" d="M{cx:.1f},{cy - 13:.1f} l9,13 l-9,13 l-9,-13 z" fill="none" stroke="{t["text"]}" stroke-width="1.5"/>')
    s.append(_box(ox, oy, 6.1, 3.8, 6.4, 6.7, 1.5, t, 'class="wallB"'))
    la = I(G, 0)
    s.append(lb("team A", I(0, 2)[0] - 40, I(0, 2)[1] + 4, "end", team_a))
    s.append(lb("team B", I(G, G - 2)[0] + 34, I(G, G - 2)[1] + 4, "start", team_b))
    s.append(lb("walls rise and fall on SHIFT,", x, y + h - 28, "start"))
    s.append(lb("swapping the open route", x, y + h - 14, "start"))
    s.append(lb("energy core", cx + 14, cy - 12, "start", t["text"]))
    css = (".wallA{animation:wa 10s cubic-bezier(.6,0,.3,1) infinite;}"
           "@keyframes wa{0%,40%{transform:none;opacity:1}50%,90%{transform:translateY(14px);opacity:0}100%{transform:none;opacity:1}}"
           ".wallB{opacity:0;transform:translateY(14px);animation:wb 10s cubic-bezier(.6,0,.3,1) infinite;}"
           "@keyframes wb{0%,40%{transform:translateY(14px);opacity:0}50%,90%{transform:none;opacity:1}100%{transform:translateY(14px);opacity:0}}"
           ".core{transform-box:fill-box;transform-origin:center;animation:core 5s ease-in-out infinite;}"
           "@keyframes core{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}")
    return "".join(s), css


FIGURES = {"acc": fig_acc, "community": fig_community, "vault": fig_vault}


# ------------------------------------------------------------------ card ---
def maturity_track(fonts, t, p, x, y, w) -> str:
    """Compact branch: solid up to the current stage, dashed beyond it."""
    color = t["status"][p["status"]]
    s = []
    stage = -1 if p["status"] == "planned" else STAGES.index(p["status"])
    xs = [x + w * k / 3 for k in range(4)]
    s.append(f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y}" stroke="{t["line"]}" stroke-width="1.5" stroke-dasharray="3 5"/>')
    if stage >= 0:
        s.append(f'<line x1="{x}" y1="{y}" x2="{xs[stage]}" y2="{y}" stroke="{color}" stroke-width="2.5"/>')
    for k, xx in enumerate(xs):
        if k == stage:
            s.append(f'<circle cx="{xx}" cy="{y}" r="6" fill="{t["surface"]}" stroke="{color}" stroke-width="2"/>')
        else:
            s.append(f'<circle cx="{xx}" cy="{y}" r="2.5" fill="{color if k < stage else t["line"]}"/>')
    names = ["prototype", "building", "review", "merged"]
    for k, xx in enumerate(xs):
        anchor = "start" if k == 0 else "end" if k == 3 else "middle"
        s.append(label(fonts, t, names[k], xx, y + 22, anchor, color if k == stage else None))
    return "".join(s)


def build_card(p: dict, theme: str, index: int = 1) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = WIDTH, 360
    color = t["status"][p["status"]]
    s = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="3" fill="{t["surface"]}" stroke="{t["frame"]}"/>']
    vis = "Public repository" if p["visibility"] == "public" else "Private repository"
    s.append(label(fonts, t, f"Fig. {index}", 28, 34))
    s.append(text(fonts, "sans", vis, W - 28, 34, 13, t["muted"], "end"))
    s.append(hairline(t, 28, 48, W - 28, 48))

    # left column: title, one-line pitch, status
    lx, colw = 28, 330
    y = 104
    for line in wrap(p["name"], "serif", 44, colw):
        s.append(text(fonts, "serif", line, lx - 2, y, 44, t["text"], extra='letter-spacing="-.5"'))
        y += 44
    y += 6
    for line in wrap(p.get("pitch", p["summary"]), "sans", 15, colw)[:4]:
        s.append(text(fonts, "sans", line, lx, y, 15, t["muted"]))
        y += 22
    s.append(text(fonts, "sans-medium", STATUS_LABEL[p["status"]], lx, H - 82, 16, color))
    s.append(maturity_track(fonts, t, p, lx + 4, H - 56, colw - 30))

    # right column: the project's own figure
    fx, fy, fw, fh = 400, 70, W - 428, H - 120
    css = ""
    if p["slug"] in FIGURES:
        fig, css = FIGURES[p["slug"]](fonts, t, fx, fy, fw, fh)
        s.append(fig)
        s.append(hairline(t, fx, H - 34, W - 28, H - 34))
        s.append(label(fonts, t, FIG_CAPTION[p["slug"]], W - 28, H - 16, "end"))
    return svg_doc(
        W, H, p["name"],
        f'{p["name"]}. Status: {STATUS_LABEL[p["status"]]}. {vis}. {p["summary"]}',
        fonts, css, "".join(s),
    )


# ---------------------------------------------------------------- footer ---
def build_footer(theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = WIDTH, 120
    s = [crop_marks(t, 6, 6, W - 12, H - 12)]
    x = 584
    s.append(f'<path d="M{x},{H - 6} V44" stroke="{t["line"]}" stroke-width="2" fill="none"/>')
    s.append(f'<circle cx="{x}" cy="40" r="7" fill="none" stroke="{t["accent"]}" stroke-width="2"/>')
    s.append(f'<circle class="ring" cx="{x}" cy="40" r="7" fill="none" stroke="{t["accent"]}" stroke-width="1" '
             f'style="animation-iteration-count:infinite;animation-duration:3.2s"/>')
    s.append(label(fonts, t, "HEAD", x - 16, 44, "end"))
    s.append(text(fonts, "serif", "Still building.", x + 24, 50, 30, t["text"]))
    return svg_doc(W, H, "Still building", "Still building.", fonts, MOTION_CSS, "".join(s))


# ---------------------------------------------------------------- mobile ---
# Phones get their own compositions instead of a shrunken 860 px sheet. They are
# drawn on a 400 px canvas (shown at roughly 0.9x on a 360-390 px screen), so
# the smallest text stays near 12 px. Figures are reused without their in-figure
# labels; the same information moves into a legend set in readable text.
MOBILE_W = 400

FIG_LEGEND = {
    "acc": ["Tasks wait in a queue", "Each task gets its own Git worktree",
            "Every change stops at a human review gate", "Only approved work reaches main"],
    "community": ["A paginated feed, designed for phones first",
                  "Members propose clues on a shared board", "The author accepts the clues that fit"],
    "vault": ["Two teams and one energy core in the middle",
              "SHIFT raises and lowers walls, swapping the open route"],
}


def build_hero_mobile(projects: list[dict], theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, M = MOBILE_W, 20
    p = []
    y = 40
    p.append(text(fonts, "sans", "Software engineering portfolio", M, y, 15, t["muted"], extra='class="fade"'))
    y += 84
    p.append(text(fonts, "serif", "Mateus", M - 3, y, 92, t["text"],
                  extra='letter-spacing="-1.5" class="rise" style="animation-delay:.05s"'))
    y += 82
    p.append(text(fonts, "serif", "Engeroff", M - 3, y, 92, t["text"],
                  extra='letter-spacing="-1.5" class="rise" style="animation-delay:.18s"'))
    y += 46
    for i, line in enumerate(wrap("Building real software while learning how it should be built.", "sans", 20, W - 2 * M)):
        p.append(text(fonts, "sans", line, M, y, 20, t["text"], extra=f'class="fade" style="animation-delay:{.45 + i * .1:.2f}s"'))
        y += 28
    y += 8
    for line in ("Software development intern at CABERGS", "Computer science student at Unisinos"):
        p.append(text(fonts, "sans", line, M, y, 15, t["muted"], extra='class="fade" style="animation-delay:.7s"'))
        y += 22
    y += 22

    # vertical branch graph, full width
    featured = [x for x in projects if x.get("featured", True) and x["status"] != "planned"][:3]
    tx, top = M + 6, y
    rows = []
    yy = top + 34
    for proj in featured:
        lines = wrap(proj["name"], "serif", 26, W - (tx + 54) - M)
        rows.append((proj, yy, lines))
        yy += 34 + 26 * len(lines) + 10
    bottom = yy + 4
    p.append(f'<path class="draw" style="animation-delay:.3s" pathLength="1" d="M{tx},{bottom} V{top + 6}" '
             f'stroke="{t["line"]}" stroke-width="2" fill="none"/>')
    p.append(f'<circle cx="{tx}" cy="{bottom}" r="4.5" fill="{t["line"]}"/>')
    p.append(text(fonts, "mono", "main", tx + 14, bottom + 5, 13, t["muted"]))
    for i, (proj, ry, lines) in enumerate(rows):
        color = t["status"][proj["status"]]
        delay = 0.7 + i * 0.28
        fork = ry + 40
        d = f"M{tx},{fork} C{tx},{fork - 26} {tx + 30},{ry + 18} {tx + 30},{ry}"
        p.append(f'<path class="draw" style="animation-delay:{delay}s" pathLength="1" d="{d}" stroke="{color}" stroke-width="2" fill="none"/>')
        p.append(f'<circle cx="{tx}" cy="{fork}" r="3.5" fill="{color}"/>')
        p.append(f'<circle cx="{tx + 30}" cy="{ry}" r="7" fill="none" stroke="{color}" stroke-width="2" class="fade" style="animation-delay:{delay + .5}s"/>')
        p.append(text(fonts, "mono", STATUS_LABEL[proj["status"]].lower(), tx + 52, ry - 16, 13, color,
                      extra=f'class="fade" style="animation-delay:{delay + .5}s"'))
        for j, line in enumerate(lines):
            p.append(text(fonts, "serif", line, tx + 51, ry + 9 + j * 26, 26, t["text"],
                          extra=f'class="fade" style="animation-delay:{delay + .55}s"'))
    y = bottom + 34

    # title block, full width
    rh = 38
    rows_tb = [("based in", "Porto Alegre, Brazil", t["text"]),
               ("open to", "Roles in Brazil and abroad", t["accent"]),
               ("revised", "October 2026", t["text"])]
    p.append(f'<rect x="{M}" y="{y}" width="{W - 2 * M}" height="{rh * 3}" fill="none" stroke="{t["frame"]}"/>')
    p.append(hairline(t, M + 92, y, M + 92, y + rh * 3))
    for i, (k, v, c) in enumerate(rows_tb):
        ry = y + i * rh
        if i:
            p.append(hairline(t, M, ry, W - M, ry))
        p.append(text(fonts, "mono", k, M + 10, ry + 24, 13, t["muted"]))
        p.append(text(fonts, "sans", v, M + 104, ry + 25, 15, c))
    H = y + rh * 3 + 24
    body = crop_marks(t, 6, 6, W - 12, H - 12) + "".join(p)
    names = ", ".join(f'{x["name"]} ({STATUS_LABEL[x["status"]].lower()})' for x in featured)
    return svg_doc(W, H, "Mateus Engeroff",
                   "Mateus Engeroff, software engineering portfolio. Building real software while learning how it "
                   "should be built. Software development intern at CABERGS and computer science student at Unisinos. "
                   "Based in Porto Alegre, Brazil, open to roles in Brazil and abroad. "
                   f"A vertical branch graph lists the featured projects: {names}.",
                   fonts, MOTION_CSS, body)


def build_card_mobile(p: dict, theme: str, index: int = 1) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, M = MOBILE_W, 20
    color = t["status"][p["status"]]
    s = []
    vis = "Public repository" if p["visibility"] == "public" else "Private repository"
    s.append(text(fonts, "mono", f"Fig. {index}", M, 32, 13, t["muted"]))
    s.append(text(fonts, "sans", vis, W - M, 32, 14, t["muted"], "end"))
    s.append(hairline(t, M, 46, W - M, 46))
    y = 92
    for line in wrap(p["name"], "serif", 38, W - 2 * M):
        s.append(text(fonts, "serif", line, M - 2, y, 38, t["text"], extra='letter-spacing="-.5"'))
        y += 38
    y += 4
    for line in wrap(p.get("pitch", p["summary"]), "sans", 16, W - 2 * M):
        s.append(text(fonts, "sans", line, M, y, 16, t["muted"]))
        y += 23
    y += 12
    css = ""
    if p["slug"] in FIGURES:
        fw, fh = 432, 240  # the figure's native box, same as on desktop
        k = (W - 2 * M) / fw
        fig, css = FIGURES[p["slug"]](fonts, t, 0, 0, fw, fh, labels=False)
        s.append(f'<g transform="translate({M},{y}) scale({k:.4f})">{fig}</g>')
        y += fh * k + 18
        for item in FIG_LEGEND.get(p["slug"], []):
            lines = wrap(item, "sans", 15, W - 2 * M - 18)
            s.append(f'<line x1="{M}" y1="{y - 5}" x2="{M + 8}" y2="{y - 5}" stroke="{t["accent"]}" stroke-width="2"/>')
            for line in lines:
                s.append(text(fonts, "sans", line, M + 18, y, 15, t["text"]))
                y += 21
            y += 5
        y += 4
        s.append(text(fonts, "mono", FIG_CAPTION[p["slug"]], M, y, 12, t["muted"]))
        y += 18
    s.append(hairline(t, M, y, W - M, y))
    y += 34
    s.append(text(fonts, "sans-medium", STATUS_LABEL[p["status"]], M, y, 17, color))
    y += 26
    s.append(maturity_track_mobile(fonts, t, p, M + 4, y, W - 2 * M - 8))
    H = y + 44
    frame = f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="3" fill="{t["surface"]}" stroke="{t["frame"]}"/>'
    return svg_doc(W, H, p["name"], f'{p["name"]}. Status: {STATUS_LABEL[p["status"]]}. {vis}. {p["summary"]}',
                   fonts, css, frame + "".join(s))


def maturity_track_mobile(fonts, t, p, x, y, w) -> str:
    color = t["status"][p["status"]]
    s = []
    stage = -1 if p["status"] == "planned" else STAGES.index(p["status"])
    xs = [x + w * k / 3 for k in range(4)]
    s.append(f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y}" stroke="{t["line"]}" stroke-width="1.5" stroke-dasharray="3 5"/>')
    if stage >= 0:
        s.append(f'<line x1="{x}" y1="{y}" x2="{xs[stage]}" y2="{y}" stroke="{color}" stroke-width="2.5"/>')
    for k, xx in enumerate(xs):
        if k == stage:
            s.append(f'<circle cx="{xx}" cy="{y}" r="6" fill="{t["surface"]}" stroke="{color}" stroke-width="2"/>')
        else:
            s.append(f'<circle cx="{xx}" cy="{y}" r="2.5" fill="{color if k < stage else t["line"]}"/>')
    for k, (xx, name) in enumerate(zip(xs, ["prototype", "building", "review", "merged"])):
        anchor = "start" if k == 0 else "end" if k == 3 else "middle"
        s.append(text(fonts, "mono", name, xx, y + 24, 13, color if k == stage else t["muted"], anchor))
    return "".join(s)


def build_footer_mobile(theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = MOBILE_W, 110
    x = 46
    s = [crop_marks(t, 6, 6, W - 12, H - 12),
         f'<path d="M{x},{H - 6} V44" stroke="{t["line"]}" stroke-width="2" fill="none"/>',
         f'<circle cx="{x}" cy="40" r="7" fill="none" stroke="{t["accent"]}" stroke-width="2"/>',
         f'<circle class="ring" cx="{x}" cy="40" r="7" fill="none" stroke="{t["accent"]}" stroke-width="1" '
         f'style="animation-iteration-count:infinite;animation-duration:3.2s"/>',
         text(fonts, "mono", "HEAD", x, 22, 13, t["muted"], "middle"),
         text(fonts, "serif", "Still building.", x + 26, 50, 32, t["text"])]
    return svg_doc(W, H, "Still building", "Still building.", fonts, MOTION_CSS, "".join(s))



STATIC_RULE = "*{animation:none!important;}"


def write_svg(path: Path, svg: str) -> None:
    """Write the animated SVG and a "-static" twin with every animation removed.

    Reduced motion is chosen in the README's <picture> (evaluated by the page),
    because a media query *inside* an SVG loaded as <img> is not reliably applied.
    The still frame is the base pose each animation was designed around.
    """
    path.write_text(svg, encoding="utf-8")
    static = svg.replace("<style>", "<style>" + STATIC_RULE, 1)
    path.with_name(path.stem + "-static.svg").write_text(static, encoding="utf-8")


# ---------------------------------------------------------------- README ---
MOBILE_QUERY = "(max-width: 600px)"


def picture(base: str, alt: str, width: int = WIDTH) -> str:
    """Eight variants: phone/desktop x dark/light x animated/still.

    The browser takes the first <source> whose media query matches, so the most
    specific rules come first. GitHub keeps <picture>/<source media> when it
    sanitizes the README (checked through its Markdown API).
    """
    rm, dark, ph = "(prefers-reduced-motion: reduce)", "(prefers-color-scheme: dark)", MOBILE_QUERY
    rows = [
        (f"{ph} and {rm} and {dark}", "-mobile-dark-static"),
        (f"{ph} and {rm}", "-mobile-light-static"),
        (f"{ph} and {dark}", "-mobile-dark"),
        (ph, "-mobile-light"),
        (f"{rm} and {dark}", "-dark-static"),
        (rm, "-light-static"),
        (dark, "-dark"),
    ]
    out = ["<picture>"]
    out += [f'  <source media="{q}" srcset="{base}{suffix}.svg">' for q, suffix in rows]
    out.append(f'  <img src="{base}-light.svg" width="{width}" alt="{escape(alt, quote=True)}">')
    out.append("</picture>")
    return "\n".join(out)


def replace_picture(readme: str, base: str) -> str:
    """Rewrite a hand-placed <picture> (hero, footer) in place, keeping its alt text."""
    pat = re.compile(r"<picture>\n(?:  <source[^\n]*\n)+  <img src=\"" + re.escape(base)
                     + r"-light\.svg\" width=\"\d+\" alt=\"([^\"]*)\">\n</picture>")
    m = pat.search(readme)
    if not m:
        raise SystemExit(f"README.md has no <picture> for {base}")
    alt = m.group(1).replace("&quot;", '"').replace("&amp;", "&")
    return readme[:m.start()] + picture(base, alt) + readme[m.end():]


def readme_projects(projects: list[dict]) -> str:
    out = []
    for p in projects:
        if not p.get("featured", True):
            name = f"[{p['name']}]({p['repo']})" if p["repo"] else p["name"]
            out.extend([
                "### Earlier work", "",
                f"**{name}** · " + " · ".join(p["stack"][:3]) + f" · {STATUS_LABEL[p['status']]}", "",
                p.get("note", p["summary"]), "",
            ])
            continue
        out.append(picture(f"assets/projects/{p['slug']}", f"{p['name']}: {STATUS_LABEL[p['status']]}"))
        out.append("")
        out.append(p["summary"])
        out.append("")
        out.append(f"**Status:** {STATUS_LABEL[p['status']]}. {p['status_note']}  ")
        out.append("**Stack:** " + ", ".join(p["stack"]))
        out.append("")
        out.append("<details>\n<summary><b>Inside the project</b></summary>\n")
        out.append("**On the main branch today**\n")
        if p["on_main"]:
            out += [f"- {c}" for c in p["on_main"]]
        if p.get("main_note"):
            out.append(("\n" if p["on_main"] else "") + p["main_note"])
        if p.get("in_review"):
            out.append("\n**Not on main yet**\n")
            out += [f"- {c}" for c in p["in_review"]]
            if p.get("review_link"):
                out.append(f"\nReview: [{p['review_link'].removeprefix('https://github.com/')}]({p['review_link']})")
        out.append("\n**My role**\n")
        out.append(p["role"])
        out.append("\n**Engineering challenges**\n")
        out += [f"- {c}" for c in p["challenges"]]
        out.append("")
        if p["repo"]:
            out.append(f"**Code:** [{p['repo'].removeprefix('https://github.com/')}]({p['repo']})")
        else:
            out.append("**Code:** private repository. Happy to walk through it in an interview.")
        if p.get("demo"):
            out.append(f"  \n**Demo:** [{p['demo']}]({p['demo']})")
        out.append("\n</details>\n")
        out.append("<br>\n")
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    projects = data["projects"]
    for p in projects:
        if p["status"] not in data["status_scale"]:
            raise SystemExit(f"Unknown status {p['status']!r} in {p['slug']}")
        if p["visibility"] == "private" and p["repo"]:
            raise SystemExit(f"{p['slug']} is private but has a repo link. Remove it.")

    (ASSETS / "projects").mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        write_svg(ASSETS / f"hero-{theme}.svg", build_hero(projects, theme))
        write_svg(ASSETS / f"footer-{theme}.svg", build_footer(theme))
        write_svg(ASSETS / f"hero-mobile-{theme}.svg", build_hero_mobile(projects, theme))
        write_svg(ASSETS / f"footer-mobile-{theme}.svg", build_footer_mobile(theme))
        featured = [p for p in projects if p.get("featured", True)]
        for i, p in enumerate(featured, start=1):
            write_svg(ASSETS / "projects" / f"{p['slug']}-{theme}.svg", build_card(p, theme, i))
            write_svg(ASSETS / "projects" / f"{p['slug']}-mobile-{theme}.svg", build_card_mobile(p, theme, i))

    readme = README.read_text(encoding="utf-8")
    readme = replace_picture(readme, "assets/hero")
    readme = replace_picture(readme, "assets/footer")
    block = readme_projects(projects)
    new, n = re.subn(
        r"(<!-- PROJECTS:START.*?-->\n).*?(<!-- PROJECTS:END -->)",
        lambda m: m.group(1) + "\n" + block + "\n" + m.group(2),
        readme, flags=re.S,
    )
    if n != 1:
        raise SystemExit("README.md must contain exactly one PROJECTS:START/END block")
    README.write_text(new, encoding="utf-8")

    for f in sorted(ASSETS.rglob("*.svg")):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
