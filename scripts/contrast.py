"""Check WCAG contrast of the README palette against GitHub's page backgrounds.

Usage:  python scripts/contrast.py
Text colours must reach 4.5:1 (normal text); line colours only need to be visible.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import THEMES  # noqa: E402

GITHUB_BG = {"dark": "#0d1117", "light": "#ffffff"}


def luminance(hex_color: str) -> float:
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main() -> int:
    failed = False
    for theme, colors in THEMES.items():
        bg = GITHUB_BG[theme]
        checks = {"text": colors["text"], "muted": colors["muted"], "accent": colors["accent"]}
        checks.update({f"status:{k}": v for k, v in colors["status"].items()})
        for name, color in checks.items():
            r = ratio(color, bg)
            ok = r >= 4.5
            failed |= not ok
            print(f"{theme:5} {name:22} {color}  {r:5.2f}:1  {'ok' if ok else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
