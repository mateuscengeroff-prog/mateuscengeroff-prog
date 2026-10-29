"""Render the brand images that live outside the README.

Usage:  python scripts/brand.py
Needs:  fonttools and playwright (pip install playwright && playwright install chromium)

Outputs (in brand/):
  social-preview.png   1280x640  GitHub repository social preview (LinkedIn reads it)
  linkedin-banner.png  1584x396  LinkedIn personal cover image
plus the SVG sources next to them.
"""
from __future__ import annotations

import json
from pathlib import Path

from build import (DATA, STAGES, THEMES, Fonts, branch_path, merge_path, svg_doc, text)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "brand"
BG = "#12171C"  # graphite ink; the README itself stays transparent
T = THEMES["dark"]


def graph(fonts: Fonts, projects: list[dict], x_left: float, x_right: float, y_main: float,
          lane_top: float, lane_gap: float, labels: bool, size: float = 14) -> list[str]:
    span = x_right - x_left
    col_x = [x_left + span * f for f in (0.36, 0.56, 0.76, 1.0)]
    parts = [f'<line x1="0" y1="{y_main}" x2="2000" y2="{y_main}" '
             f'stroke="{T["line"]}" stroke-width="2"/>']
    ordered = sorted([p for p in projects if p["status"] != "planned"],
                     key=lambda p: STAGES.index(p["status"]), reverse=True)
    for i, p in enumerate(ordered[:4]):
        color = T["status"][p["status"]]
        x0, y = x_left + i * 30, lane_top + i * lane_gap
        x_end = col_x[STAGES.index(p["status"])]
        parts.append(f'<path d="{merge_path(x_end, y, col_x[3], y_main)}" stroke="{T["line"]}" '
                     f'stroke-width="1.5" stroke-dasharray="3 5" fill="none"/>')
        parts.append(f'<path d="{branch_path(x0, y_main, y, x_end)}" stroke="{color}" stroke-width="2" fill="none"/>')
        parts.append(f'<circle cx="{x0}" cy="{y_main}" r="4.5" fill="{color}"/>')
        parts.append(f'<circle cx="{x_end}" cy="{y}" r="7" fill="{BG}" stroke="{color}" stroke-width="2"/>')
        if labels:
            parts.append(text(fonts, "mono", p["branch_label"], x_end + 16, y + 5, size, T["muted"]))
    return parts


def social_preview(projects: list[dict]) -> str:
    fonts = Fonts()
    W, H = 1280, 640
    parts = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    parts.append(text(fonts, "serif", "Mateus Engeroff", 80, 190, 128, T["text"], extra='letter-spacing="-1"'))
    parts.append(text(fonts, "sans", "Building real software while learning how it should be built.",
                      84, 252, 30, T["text"]))
    parts.append(text(fonts, "sans", "Software development intern and computer science student",
                      84, 296, 22, T["muted"]))
    parts += graph(fonts, projects, 84, 1130, 560, 380, 40, labels=True, size=17)
    parts.append(text(fonts, "mono", "github.com/mateuscengeroff-prog", W - 80, 610, 17, T["accent"], "end"))
    return svg_doc(W, H, "Mateus Engeroff, GitHub portfolio",
                   "Mateus Engeroff. Building real software while learning how it should be built.",
                   fonts, "", "".join(parts))


def linkedin_banner(projects: list[dict]) -> str:
    """Profile photo covers the lower left on desktop and the centre-left on mobile,
    so everything that matters sits right of x=560 and between y=70 and y=330."""
    fonts = Fonts()
    W, H = 1584, 396
    parts = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    parts += graph(fonts, projects, 640, 1340, 338, 196, 30, labels=False)
    parts.append(text(fonts, "serif", "Building real software while", 640, 98, 46, T["text"]))
    parts.append(text(fonts, "serif", "learning how it should be built.", 640, 146, 46, T["text"]))
    parts.append(text(fonts, "mono", "github.com/mateuscengeroff-prog", 1520, 374, 16, T["muted"], "end"))
    return svg_doc(W, H, "LinkedIn banner", "Building real software while learning how it should be built.",
                   fonts, "", "".join(parts))


def main() -> None:
    from playwright.sync_api import sync_playwright

    projects = json.loads(DATA.read_text(encoding="utf-8"))["projects"]
    OUT.mkdir(exist_ok=True)
    jobs = {
        "social-preview": (social_preview(projects), 1280, 640),
        "linkedin-banner": (linkedin_banner(projects), 1584, 396),
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, (svg, w, h) in jobs.items():
            src = OUT / f"{name}.svg"
            src.write_text(svg, encoding="utf-8")
            page = browser.new_page(viewport={"width": w, "height": h}, reduced_motion="reduce")
            page.goto(src.as_uri())
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / f"{name}.png"))
            page.close()
            print(f"brand/{name}.png  {(OUT / f'{name}.png').stat().st_size / 1024:.0f} KB")
        browser.close()


if __name__ == "__main__":
    main()
