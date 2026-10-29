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


# ------------------------------------------------------------------ hero ---
def build_hero(projects: list[dict], theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = WIDTH, 452
    parts = []

    # Name, tagline, role. One typographic statement, left aligned.
    parts.append(text(fonts, "serif", "Mateus Engeroff", 0, 112, 96, t["text"],
                      extra='class="fade" style="animation-delay:0s" letter-spacing="-1"'))
    parts.append(text(fonts, "sans", "Building real software while learning how it should be built.",
                      2, 162, 24, t["text"], extra='class="fade" style="animation-delay:.25s"'))
    parts.append(text(fonts, "sans",
                      "Software development intern at CABERGS and computer science student at Unisinos.",
                      2, 196, 17, t["muted"], extra='class="fade" style="animation-delay:.4s"'))
    parts.append(text(fonts, "sans", "Porto Alegre, Brazil", W - 4, 30, 15, t["muted"], "end"))
    parts.append(text(fonts, "sans", "Open to roles in Brazil and abroad", W - 4, 52, 15, t["accent"], "end"))

    # Graph: columns are stages on the road to main.
    y_main = 420
    col_x = [300, 470, 640, 840]
    for i, label in enumerate(HERO_STAGE_TEXT):
        x = col_x[i]
        parts.append(f'<line x1="{x}" y1="252" x2="{x}" y2="{y_main - 8}" stroke="{t["faint"]}" '
                     f'stroke-width="1" stroke-dasharray="2 4"/>')
        parts.append(text(fonts, "mono", label, W - 4 if i == 3 else x, 240, 13, t["muted"], "end" if i == 3 else "middle"))

    parts.append(f'<path class="draw" style="animation-delay:.2s" pathLength="1" d="M0,{y_main} H{W}" '
                 f'stroke="{t["line"]}" stroke-width="2" fill="none"/>')
    parts.append(text(fonts, "mono", "main", W - 4, y_main + 24, 13, t["muted"], "end"))

    ordered = sorted(
        [p for p in projects if p["status"] != "planned"],
        key=lambda p: STAGES.index(p["status"]), reverse=True,
    )
    lane_y = [278, 312, 346, 380]
    for i, p in enumerate(ordered[:4]):
        stage = STAGES.index(p["status"])
        color = t["status"][p["status"]]
        x0, y = 28 + i * 28, lane_y[i]
        x_end = col_x[stage]
        delay = 0.6 + i * 0.25
        if p["status"] == "completed":
            d = branch_path(x0, y_main, y, x_end - 22) + f" Q{x_end},{y} {x_end},{y + 22} V{y_main}"
            parts.append(f'<path class="draw" style="animation-delay:{delay}s" pathLength="1" d="{d}" '
                         f'stroke="{color}" stroke-width="2" fill="none"/>')
            parts.append(f'<circle cx="{x0}" cy="{y_main}" r="4" fill="{color}"/>')
            parts.append(text(fonts, "mono", p["branch_label"], x0 + 30, y - 9, 13, t["text"],
                              extra=f'class="fade" style="animation-delay:{delay + .6}s"'))
            continue
        # road still ahead, drawn faint and dashed
        ahead = merge_path(x_end, y, col_x[3], y_main)
        parts.append(f'<path d="{ahead}" stroke="{t["line"]}" stroke-width="1.5" '
                     f'stroke-dasharray="3 5" fill="none" class="fade" style="animation-delay:{delay + .6}s"/>')
        parts.append(f'<path class="draw" style="animation-delay:{delay}s" pathLength="1" '
                     f'd="{branch_path(x0, y_main, y, x_end)}" stroke="{color}" stroke-width="2" fill="none"/>')
        parts.append(f'<circle cx="{x0}" cy="{y_main}" r="4" fill="{color}" class="fade" '
                     f'style="animation-delay:{delay}s"/>')
        parts.append(f'<circle cx="{x_end}" cy="{y}" r="6" fill="none" stroke="{color}" stroke-width="2" '
                     f'class="fade" style="animation-delay:{delay + .55}s"/>')
        parts.append(text(fonts, "mono", p["branch_label"], x_end + 14, y + 5, 14, t["text"],
                          extra=f'class="fade" style="animation-delay:{delay + .6}s"'))

    style = (
        ".draw{stroke-dasharray:1;animation:draw 1.1s cubic-bezier(.6,0,.2,1) both;}"
        "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
        ".fade{animation:fade .7s ease-out both;}"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
    )
    names = ", ".join(f'{p["name"]} ({STATUS_LABEL[p["status"]].lower()})' for p in ordered)
    return svg_doc(
        W, H, "Mateus Engeroff",
        "Mateus Engeroff. Building real software while learning how it should be built. "
        "Software development intern at CABERGS and computer science student at Unisinos, "
        "Porto Alegre, Brazil. Open to roles in Brazil and abroad. "
        f"A branch diagram shows current projects and how close each is to main: {names}.",
        fonts, style, "".join(parts),
    )


# ------------------------------------------------------------------ card ---
def build_card(p: dict, theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = WIDTH, 200
    color = t["status"][p["status"]]
    parts = []

    parts.append(text(fonts, "serif", p["name"], 0, 52, 46, t["text"]))
    vis = "Public repository" if p["visibility"] == "public" else "Private repository"
    parts.append(text(fonts, "sans", vis, W - 4, 24, 15, t["muted"], "end"))
    parts.append(text(fonts, "sans-medium", STATUS_LABEL[p["status"]], W - 4, 50, 19, color, "end"))

    y_main, y_lane = 150, 104
    col_x = [250, 450, 650, 850]
    parts.append(f'<line x1="0" y1="{y_main}" x2="{W}" y2="{y_main}" stroke="{t["line"]}" stroke-width="2"/>')

    for i, label in enumerate(STAGE_TEXT):
        x = col_x[i]
        current = p["status"] != "planned" and STAGES.index(p["status"]) == i
        anchor = "end" if i == 3 else "middle"
        fill = color if current else t["muted"]
        parts.append(text(fonts, "mono", label, x if i < 3 else W - 4, y_main + 28, 13, fill, anchor))
        parts.append(f'<line x1="{x if i < 3 else W - 2}" y1="{y_main - 5}" x2="{x if i < 3 else W - 2}" '
                     f'y2="{y_main + 5}" stroke="{t["line"]}" stroke-width="2"/>')

    if p["status"] == "planned":
        parts.append(f'<path d="{merge_path(40, y_lane, col_x[3] - 2, y_main)}" stroke="{t["line"]}" '
                     f'stroke-width="1.5" stroke-dasharray="3 5" fill="none"/>')
    else:
        stage = STAGES.index(p["status"])
        x_end = col_x[stage] if stage < 3 else W - 2
        if p["status"] == "completed":
            d = branch_path(40, y_main, y_lane, x_end - 22) + \
                f" Q{x_end},{y_lane} {x_end},{y_lane + 22} V{y_main}"
            parts.append(f'<path d="{d}" stroke="{color}" stroke-width="2" fill="none"/>')
        else:
            parts.append(f'<path d="{merge_path(x_end, y_lane, W - 2, y_main)}" stroke="{t["line"]}" '
                         f'stroke-width="1.5" stroke-dasharray="3 5" fill="none"/>')
            parts.append(f'<path d="{branch_path(40, y_main, y_lane, x_end)}" stroke="{color}" '
                         f'stroke-width="2" fill="none"/>')
            parts.append(f'<circle cx="{x_end}" cy="{y_lane}" r="7" fill="none" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<circle cx="40" cy="{y_main}" r="4.5" fill="{color}"/>')
        parts.append(text(fonts, "mono", p["branch_label"], 58, y_lane - 12, 13, t["muted"]))

    return svg_doc(
        W, H, p["name"],
        f'{p["name"]}. Status: {STATUS_LABEL[p["status"]]}. {vis}. {p["summary"]}',
        fonts, "", "".join(parts),
    )


# ---------------------------------------------------------------- footer ---
def build_footer(theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = WIDTH, 96
    y = 40
    parts = [
        f'<line x1="0" y1="{y}" x2="{W - 300}" y2="{y}" stroke="{t["line"]}" stroke-width="2"/>',
        f'<circle cx="{W - 300}" cy="{y}" r="7" fill="none" stroke="{t["accent"]}" stroke-width="2"/>',
        text(fonts, "mono", "HEAD", W - 300, y + 28, 12, t["muted"], "middle"),
        text(fonts, "sans", "Still building.", W - 276, y + 6, 18, t["text"]),
    ]
    return svg_doc(W, H, "Still building", "Still building.", fonts, "", "".join(parts))


# ---------------------------------------------------------------- README ---
def picture(base: str, alt: str, width: int = WIDTH) -> str:
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg">\n'
        f'  <img src="{base}-light.svg" width="{width}" alt="{escape(alt, quote=True)}">\n'
        "</picture>"
    )


def readme_projects(projects: list[dict]) -> str:
    out = []
    for p in projects:
        out.append(picture(f"assets/projects/{p['slug']}", f"{p['name']}: {STATUS_LABEL[p['status']]}"))
        out.append("")
        out.append(p["summary"])
        out.append("")
        out.append(f"**Status:** {STATUS_LABEL[p['status']]}. {p['status_note']}  ")
        out.append("**Stack:** " + ", ".join(p["stack"]))
        out.append("")
        out.append("<details>\n<summary><b>Case study</b></summary>\n")
        out.append("**On the main branch today**\n")
        if p["on_main"]:
            out += [f"- {c}" for c in p["on_main"]]
        if p.get("main_note"):
            out.append(("\n" if p["on_main"] else "") + p["main_note"])
        if p.get("in_review"):
            out.append("\n**In open pull requests, not merged yet**\n")
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
        (ASSETS / f"hero-{theme}.svg").write_text(build_hero(projects, theme), encoding="utf-8")
        (ASSETS / f"footer-{theme}.svg").write_text(build_footer(theme), encoding="utf-8")
        for p in projects:
            (ASSETS / "projects" / f"{p['slug']}-{theme}.svg").write_text(
                build_card(p, theme), encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
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
