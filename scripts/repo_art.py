"""README illustrations for the project repositories, in this profile's visual system.

Usage:
    python scripts/repo_art.py <slug> <output folder>
    python scripts/repo_art.py all <folder containing the cloned repositories>

Slugs: acc, community, vault, gym, mapper. Each run writes three illustrations
into the output folder (normally the repository's docs/img):

- banner:  title, one-line pitch, the project's figure and a title block
           (8 files: desktop/phone x dark/light x animated/still)
- flow:    how the project works, in four numbered steps (4 files)
- board:   two columns, usually "on main today" vs "not on main yet",
           taken from portfolio/projects.json so it matches the profile (4 files)

All text is English. Diagrams are illustrations, not screenshots.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import (  # noqa: E402
    DATA, FIGURES, MOBILE_W, MOTION_CSS, STATUS_LABEL, THEMES, WIDTH, Fonts, crop_marks,
    hairline, label, svg_doc, text, text_width, wrap, write_svg,
)

REPO_DIRS = {"acc": "agent-command-center", "community": "gta-6-espermacoding",
             "vault": "vault-shift", "gym": "gym-management-system",
             "mapper": "project-structure-mapper"}


# ------------------------------------------------------------- gym figure ---
def fig_gym(fonts, t, x, y, w, h, labels=True):
    """Terminal menu -> SQLite file -> reports with charts."""
    s = []
    lb = (lambda *a, **k: label(fonts, t, *a, **k)) if labels else (lambda *a, **k: "")
    # terminal menu
    mx, my, mw, mh = x + 4, y + 30, 132, 150
    s.append(lb("terminal menu", mx, y + 18))
    s.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="5" fill="{t["surface"]}" stroke="{t["line"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{mx}" y1="{my + 18}" x2="{mx + mw}" y2="{my + 18}" stroke="{t["frame"]}"/>')
    for i in range(3):
        s.append(f'<circle cx="{mx + 10 + i * 9}" cy="{my + 9}" r="2.5" fill="{t["frame"]}"/>')
    for i, bw in enumerate([70, 58, 84, 64, 46]):
        ry = my + 38 + i * 21
        s.append(text(fonts, "mono", str(i + 1), mx + 12, ry + 4, 11, t["muted"]))
        s.append(f'<line x1="{mx + 28}" y1="{ry}" x2="{mx + 28 + bw}" y2="{ry}" stroke="{t["frame"]}" stroke-width="3" stroke-linecap="round"/>')
    s.append(f'<rect class="sel" x="{mx + 6}" y="{my + 29}" width="{mw - 12}" height="18" rx="3" fill="none" stroke="{t["accent"]}" stroke-width="1.5"/>')
    # database cylinder
    cx, cy, rx, ry, ch = x + 214, y + 80, 34, 10, 70
    s.append(f'<path d="M{mx + mw + 8},{y + 105} H{cx - rx - 8}" stroke="{t["line"]}" stroke-width="1.5" stroke-dasharray="3 5"/>')
    s.append(f'<path d="M{cx - rx},{cy} v{ch} a{rx},{ry} 0 0 0 {2 * rx},0 v-{ch}" fill="{t["surface"]}" stroke="{t["line"]}" stroke-width="1.5"/>')
    s.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{t["faint"]}" stroke="{t["line"]}" stroke-width="1.5"/>')
    for k in (1, 2):
        s.append(f'<path d="M{cx - rx},{cy + k * 23} a{rx},{ry} 0 0 0 {2 * rx},0" fill="none" stroke="{t["frame"]}"/>')
    s.append(f'<path class="row" d="M{cx - 16},{cy + 34} h32" stroke="{t["accent"]}" stroke-width="3" stroke-linecap="round"/>')
    s.append(lb("SQLite file", cx, cy + ch + 34, "middle"))
    # reports: a pie and a bar chart
    rxx = x + w - 136
    s.append(f'<path d="M{cx + rx + 8},{y + 105} C{cx + rx + 40},{y + 105} {rxx - 34},{y + 70} {rxx - 8},{y + 70}" stroke="{t["line"]}" stroke-width="1.5" fill="none"/>')
    s.append(f'<path d="M{cx + rx + 8},{y + 105} C{cx + rx + 40},{y + 105} {rxx - 34},{y + 170} {rxx - 8},{y + 170}" stroke="{t["line"]}" stroke-width="1.5" fill="none"/>')
    s.append(lb("reports and charts", rxx, y + 18))
    for top in (y + 30, y + 130):
        s.append(f'<rect x="{rxx}" y="{top}" width="130" height="84" rx="4" fill="{t["surface"]}" stroke="{t["line"]}" stroke-width="1.5"/>')
    pcx, pcy, pr = rxx + 40, y + 72, 26
    s.append(f'<circle cx="{pcx}" cy="{pcy}" r="{pr}" fill="{t["faint"]}" stroke="{t["line"]}" stroke-width="1.5"/>')
    s.append(f'<path class="slice" d="M{pcx},{pcy} V{pcy - pr} A{pr},{pr} 0 1 1 {pcx - pr * 0.95:.1f},{pcy + pr * 0.31:.1f} Z" fill="{t["accent"]}" fill-opacity=".85"/>')
    for k, lw in enumerate([34, 26, 30]):
        s.append(f'<line x1="{rxx + 80}" y1="{pcy - 12 + k * 12}" x2="{rxx + 80 + lw}" y2="{pcy - 12 + k * 12}" stroke="{t["frame"]}" stroke-width="3" stroke-linecap="round"/>')
    base = y + 200
    for k, bh in enumerate([38, 22, 50, 30]):
        fill = t["accent"] if k == 2 else t["line"]
        s.append(f'<rect class="bar" style="animation-delay:{k * .12:.2f}s" x="{rxx + 18 + k * 26}" y="{base - bh}" width="16" height="{bh}" rx="2" fill="{fill}"/>')
    s.append(f'<line x1="{rxx + 12}" y1="{base}" x2="{rxx + 118}" y2="{base}" stroke="{t["line"]}"/>')
    css = (".sel{animation:sel 8s steps(1) infinite;}"
           "@keyframes sel{0%{transform:none}25%{transform:translateY(21px)}50%{transform:translateY(42px)}"
           "75%{transform:translateY(63px)}100%{transform:none}}"
           ".bar{transform-box:fill-box;transform-origin:center bottom;animation:gbar 8s cubic-bezier(.2,.7,.2,1) infinite both;}"
           "@keyframes gbar{0%,20%{transform:scaleY(0)}34%,92%{transform:none}100%{transform:scaleY(0)}}"
           ".row{animation:grow 8s ease-in-out infinite;}"
           "@keyframes grow{0%,12%{opacity:.2}20%,90%{opacity:1}100%{opacity:.2}}")
    return "".join(s), css


ALL_FIGURES = dict(FIGURES, gym=fig_gym)


# ------------------------------------------------------------------ specs ---
SPECS = {
    "acc": {
        "kicker": "Local orchestrator for AI coding agents",
        "title": ["Agent", "Command", "Center"],
        "tagline": "Queue coding tasks, give each one its own Git worktree and review every change before it reaches main.",
        "block": [("runs on", "Windows · Python 3.11+"), ("listens", "127.0.0.1 only"), ("main", "core dashboard and queue")],
        "flag": "real agent not tested yet",
        "flow_title": "How a task moves",
        "flow": [
            ("Register a project", "Point the dashboard at the root folder of a local Git repository."),
            ("Queue a task", "Give it a title and instructions. One task runs at a time, in order."),
            ("Work in isolation", "Each task gets its own branch, agent/task-<id>, and a worktree under .workspace/."),
            ("Stop for review", "A finished task waits as needs_review. Nothing is pushed, merged or deployed."),
        ],
        "board_pending": ["Validation on a physical Windows PC with an authenticated agent CLI"],
    },
    "community": {
        "kicker": "Mobile-first community web app",
        "title": ["GTA VI", "Community"],
        "tagline": "An independent, Portuguese-language fan community for GTA VI, built as a progressive web app.",
        "block": [("stack", "Next.js · Supabase"), ("main", "project scaffold only"), ("features", "integration branches")],
        "flag": "not deployed",
        "flow_title": "Planned flow (features live on integration branches)",
        "flow": [
            ("Create an account", "Email sign-up, sign-in and password reset through Supabase Auth."),
            ("Post and react", "Posts, likes and comments in a paginated feed designed for phones first."),
            ("Open a mystery", "A shared board where members propose clues about a theory."),
            ("Author decides", "Only the author accepts clues. Row-level security enforces ownership."),
        ],
        "board_pending": [],
    },
    "vault": {
        "kicker": "Multiplayer sci-fi arena game for Roblox",
        "title": ["VAULT//SHIFT"],
        "tagline": "Two teams fight over energy cores while SHIFT walls rise and fall, reshaping the arena.",
        "block": [("engine", "Roblox · Luau · Rojo"), ("main", "server-side combat, arena"), ("state", "not published")],
        "flag": "multiplayer test pending",
        "flow_title": "Who decides what in combat",
        "flow": [
            ("Client sends intent", "Input becomes a request to fire, swing or dash. It never carries damage values."),
            ("Server validates", "Range, angle, cooldowns and rate limits are checked on the server."),
            ("Server applies", "Damage, ammo, health and match state change only on the server."),
            ("Clients show it", "The HUD, health bars and hit effects draw the result for every player."),
        ],
        "board_pending": ["Tests with two players, on a phone and with a controller"],
    },
    "gym": {
        "kicker": "Command-line member management",
        "title": ["Gym", "Management", "System"],
        "tagline": "Register, search and report on gym members with Python, SQLite and Matplotlib.",
        "block": [("language", "Python 3.10+"), ("database", "SQLite, local file"), ("tests", "51, CI on 3.10–3.13")],
        "flag": "Windows smoke test pending",
        "flow_title": "How the app works",
        "flow": [
            ("Pick an option", "A numbered terminal menu. The interface text is in Portuguese."),
            ("Validate input", "Non-numeric, out-of-range and blank answers are asked again."),
            ("Store safely", "Parameterized SQL in a local SQLite file; older schemas upgrade on startup."),
            ("Report", "Totals, averages and Matplotlib charts, even for an empty database."),
        ],
        "board_pending": ["Manual smoke test on Windows"],
    },
    "mapper": {
        "kicker": "Local, read-only code mapping tool",
        "title": ["Project", "Structure", "Mapper"],
        "tagline": "Understand how a codebase is organised without opening it file by file.",
        "block": [("runs on", "Windows 10/11 · Python 3.8+"), ("project", "read-only, offline"), ("version", "v2.1.0 on main")],
        "flag": "tested on Windows",
        "flow_title": "Using the assistant",
        "flow": [
            ("Start it", "Double-click INICIAR_WINDOWS.bat, or drop a project folder onto it."),
            ("Pick the folder", "Paste a path or choose the folder in a picker window."),
            ("Pick a mode", "A public summary to share, or a private report for internal use."),
            ("Get the reports", "A new folder outside the project, with Markdown, JSON and a ZIP."),
        ],
        "board": {
            "title": "Public vs. private report",
            "left": ("Public mode", "accent", [
                "File counts by type",
                "Likely technologies, such as ASP.NET Web Forms, C# or Python",
                "How many sensitive files were skipped",
                "No project, folder or file names",
            ]),
            "right": ("Private mode, internal use only", "under-review", [
                "Everything in the public report",
                "Project name and the full file tree (arvore.txt)",
                "Master Page usage and references by status",
                "Static links between pages, code-behind files and controls",
            ]),
        },
    },
}


def project(slug: str) -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    return next(p for p in data["projects"] if p["slug"] == slug)


def board_spec(slug: str) -> dict:
    spec = SPECS[slug]
    if "board" in spec:
        return spec["board"]
    p = project(slug)
    right = list(p.get("in_review", [])) + spec["board_pending"]
    left = p["on_main"] or [p.get("main_note", "Project scaffold only")]
    return {"title": "Where it stands", "left": ("On main today", "accent", left),
            "right": ("Not on main yet, or still to validate", "under-review", right)}


def title_size(words: list[str], max_w: float, start: float) -> float:
    size = start
    while size > 30 and max(text_width(w, "serif", size) for w in words) > max_w:
        size -= 2
    return size


# ---------------------------------------------------------------- banner ---
def banner(slug: str, theme: str) -> str:
    spec, t, fonts = SPECS[slug], THEMES[theme], Fonts()
    p_ = project(slug)
    W, H = WIDTH, 420
    p = [crop_marks(t, 6, 6, W - 12, H - 12)]
    p.append(text(fonts, "sans", spec["kicker"], 2, 50, 14, t["muted"], extra='class="fade"'))
    size = title_size(spec["title"], 380, 74)
    lh = size * 0.89
    y = 56 + lh
    for i, word in enumerate(spec["title"]):
        p.append(text(fonts, "serif", word, -3, y, size, t["text"],
                      extra=f'letter-spacing="-1" class="rise" style="animation-delay:{.05 + i * .12:.2f}s"'))
        y += lh
    y += 2
    for i, line in enumerate(wrap(spec["tagline"], "sans", 18, 370)):
        p.append(text(fonts, "sans", line, 2, y + i * 26, 18, t["text"],
                      extra=f'class="fade" style="animation-delay:{.5 + i * .1:.2f}s"'))
    fig, css = ALL_FIGURES[slug](fonts, t, 410, 40, 432, 240)
    p.append(f'<g class="fade" style="animation-delay:.6s">{fig}</g>')
    color = t["status"][p_["status"]]
    rows = spec["block"] + [("status", f'{STATUS_LABEL[p_["status"]]} · {spec["flag"]}')]
    bx, by, bw, rh = 410, 292, W - 416, 28
    p.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{rh * len(rows)}" fill="none" stroke="{t["frame"]}"/>')
    p.append(hairline(t, bx + 78, by, bx + 78, by + rh * len(rows)))
    for i, (k, v) in enumerate(rows):
        ry = by + i * rh
        if i:
            p.append(hairline(t, bx, ry, bx + bw, ry))
        p.append(text(fonts, "mono", k, bx + 10, ry + 18, 11, t["muted"]))
        p.append(text(fonts, "sans", v, bx + 90, ry + 19, 14, color if k == "status" else t["text"]))
    desc = (f'{" ".join(spec["title"])}. {spec["kicker"]}. {spec["tagline"]} '
            + " ".join(f"{k}: {v}." for k, v in spec["block"])
            + f' Status: {STATUS_LABEL[p_["status"]]}, {spec["flag"]}.')
    return svg_doc(W, H, " ".join(spec["title"]), desc, fonts, MOTION_CSS + css, "".join(p))


def banner_mobile(slug: str, theme: str) -> str:
    spec, t, fonts = SPECS[slug], THEMES[theme], Fonts()
    p_ = project(slug)
    W, M = MOBILE_W, 20
    p = [text(fonts, "sans", spec["kicker"], M, 40, 14, t["muted"], extra='class="fade"')]
    size = title_size(spec["title"], W - 2 * M, 62)
    lh = size * 0.9
    y = 44 + lh
    for i, word in enumerate(spec["title"]):
        p.append(text(fonts, "serif", word, M - 3, y, size, t["text"],
                      extra=f'letter-spacing="-1" class="rise" style="animation-delay:{.05 + i * .12:.2f}s"'))
        y += lh
    y -= 4
    for line in wrap(spec["tagline"], "sans", 17, W - 2 * M):
        p.append(text(fonts, "sans", line, M, y, 17, t["text"], extra='class="fade" style="animation-delay:.5s"'))
        y += 24
    fw, fh = 432, 240
    k = (W - 2 * M) / fw
    fig, css = ALL_FIGURES[slug](fonts, t, 0, 0, fw, fh, labels=False)
    p.append(f'<g transform="translate({M},{y - 6}) scale({k:.4f})">{fig}</g>')
    y += fh * k + 10
    rows = spec["block"] + [("status", f'{STATUS_LABEL[p_["status"]]}')]
    rh = 34
    p.append(f'<rect x="{M}" y="{y}" width="{W - 2 * M}" height="{rh * len(rows)}" fill="none" stroke="{t["frame"]}"/>')
    p.append(hairline(t, M + 84, y, M + 84, y + rh * len(rows)))
    for i, (key, v) in enumerate(rows):
        ry = y + i * rh
        if i:
            p.append(hairline(t, M, ry, W - M, ry))
        p.append(text(fonts, "mono", key, M + 10, ry + 22, 12, t["muted"]))
        c = t["status"][p_["status"]] if key == "status" else t["text"]
        p.append(text(fonts, "sans", v, M + 96, ry + 22, 14, c))
    y += rh * len(rows) + 10
    p.append(text(fonts, "sans", (spec["flag"][0].upper() + spec["flag"][1:]), M, y + 14, 13, t["status"][p_["status"]]))
    H = y + 40
    body = crop_marks(t, 6, 6, W - 12, H - 12) + "".join(p)
    return svg_doc(W, H, " ".join(spec["title"]), f'{" ".join(spec["title"])}. {spec["tagline"]}',
                   fonts, MOTION_CSS + css, body)


# ------------------------------------------------------------------ flow ---
def flow(slug: str, theme: str, mobile: bool = False) -> str:
    spec, t, fonts = SPECS[slug], THEMES[theme], Fonts()
    steps = spec["flow"]
    s = []
    if not mobile:
        W, M, gap = WIDTH, 24, 26
        cw = (W - 2 * M - gap * (len(steps) - 1)) / len(steps)
        s.append(label(fonts, t, spec["flow_title"], M, 32))
        s.append(hairline(t, M, 46, W - M, 46))
        y0 = 70
        bodies = [wrap(b, "sans", 13.5, cw - 28) for _, b in steps]
        titles = [wrap(ti, "sans-medium", 16, cw - 28) for ti, _ in steps]
        ch = 70 + max(len(a) * 22 + len(b) * 20 for a, b in zip(titles, bodies))
        for i, ((ti, _), tl, bl) in enumerate(zip(steps, titles, bodies)):
            x = M + i * (cw + gap)
            s.append(f'<rect x="{x}" y="{y0}" width="{cw}" height="{ch}" rx="4" fill="{t["surface"]}" stroke="{t["frame"]}"/>')
            s.append(text(fonts, "mono", f"{i + 1:02d}", x + 14, y0 + 28, 12, t["accent"]))
            yy = y0 + 56
            for line in tl:
                s.append(text(fonts, "sans-medium", line, x + 14, yy, 16, t["text"]))
                yy += 22
            yy += 4
            for line in bl:
                s.append(text(fonts, "sans", line, x + 14, yy, 13.5, t["muted"]))
                yy += 20
            if i < len(steps) - 1:
                ax = x + cw + 4
                s.append(f'<path d="M{ax},{y0 + 24} h{gap - 10} m-5,-4 l5,4 l-5,4" stroke="{t["line"]}" stroke-width="1.5" fill="none"/>')
        H = y0 + ch + 28
    else:
        W, M = MOBILE_W, 20
        s.append(text(fonts, "mono", spec["flow_title"] if len(spec["flow_title"]) < 40 else spec["flow_title"].split(" (")[0],
                      M, 32, 12, t["muted"]))
        s.append(hairline(t, M, 46, W - M, 46))
        y = 82
        lx = M + 8
        tops = []
        for i, (ti, b) in enumerate(steps):
            tops.append(y)
            s.append(text(fonts, "mono", f"{i + 1:02d}", lx + 22, y - 20, 12, t["accent"]))
            for line in wrap(ti, "sans-medium", 17, W - lx - 22 - M):
                s.append(text(fonts, "sans-medium", line, lx + 22, y, 17, t["text"]))
                y += 23
            for line in wrap(b, "sans", 15, W - lx - 22 - M):
                s.append(text(fonts, "sans", line, lx + 22, y, 15, t["muted"]))
                y += 21
            y += 34
        s.insert(2, f'<path d="M{lx},{tops[0] - 24} V{tops[-1] - 24}" stroke="{t["line"]}" stroke-width="2"/>')
        for ty in tops:
            s.append(f'<circle cx="{lx}" cy="{ty - 24}" r="5" fill="{t["surface"]}" stroke="{t["accent"]}" stroke-width="2"/>')
        H = y - 10
    desc = spec["flow_title"] + ". " + " ".join(f"{i + 1}. {a}: {b}" for i, (a, b) in enumerate(steps))
    return svg_doc(W, H, spec["flow_title"], desc, fonts, "", "".join(s))


# ----------------------------------------------------------------- board ---
def board(slug: str, theme: str, mobile: bool = False) -> str:
    b, t, fonts = board_spec(slug), THEMES[theme], Fonts()
    cols = [b["left"], b["right"]]
    s = []
    if not mobile:
        W, M, gap = WIDTH, 24, 24
        cw = (W - 2 * M - gap) / 2
        heights = []
        parts = []
        for i, (head, ckey, items) in enumerate(cols):
            x = M + i * (cw + gap)
            color = t[ckey] if ckey in t else t["status"][ckey]
            part = [f'<rect x="{x}" y="64" width="{cw}" height="4" fill="{color}"/>',
                    text(fonts, "sans-medium", head, x, 98, 16, t["text"])]
            yy = 132
            for item in items:
                lines = wrap(item, "sans", 14, cw - 22)
                part.append(f'<circle cx="{x + 4}" cy="{yy - 5}" r="2.5" fill="{color}"/>')
                for line in lines:
                    part.append(text(fonts, "sans", line, x + 18, yy, 14, t["muted"]))
                    yy += 21
                yy += 9
            heights.append(yy)
            parts.append(part)
        s.append(label(fonts, t, b["title"], M, 32))
        s.append(hairline(t, M, 46, W - M, 46))
        for part in parts:
            s.extend(part)
        H = max(heights) + 10
    else:
        W, M = MOBILE_W, 20
        s.append(text(fonts, "mono", b["title"], M, 32, 12, t["muted"]))
        s.append(hairline(t, M, 46, W - M, 46))
        yy = 64
        for head, ckey, items in cols:
            color = t[ckey] if ckey in t else t["status"][ckey]
            s.append(f'<rect x="{M}" y="{yy}" width="{W - 2 * M}" height="4" fill="{color}"/>')
            yy += 32
            for line in wrap(head, "sans-medium", 17, W - 2 * M):
                s.append(text(fonts, "sans-medium", line, M, yy, 17, t["text"]))
                yy += 23
            yy += 10
            for item in items:
                s.append(f'<circle cx="{M + 4}" cy="{yy - 5}" r="2.5" fill="{color}"/>')
                for line in wrap(item, "sans", 15, W - 2 * M - 18):
                    s.append(text(fonts, "sans", line, M + 18, yy, 15, t["muted"]))
                    yy += 21
                yy += 9
            yy += 20
        H = yy
    desc = b["title"] + ". " + " ".join(f'{h}: {"; ".join(items)}.' for h, _, items in cols)
    return svg_doc(W, H, b["title"], desc, fonts, "", "".join(s))


# ---------------------------------------------------------------- output ---
def picture4(base: str, alt: str) -> str:
    """Phone/desktop x dark/light, for still images."""
    from html import escape
    return "\n".join([
        "<picture>",
        f'  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="{base}-mobile-dark.svg">',
        f'  <source media="(max-width: 600px)" srcset="{base}-mobile-light.svg">',
        f'  <source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg">',
        f'  <img src="{base}-light.svg" width="{WIDTH}" alt="{escape(alt, quote=True)}">',
        "</picture>",
    ])


def render(slug: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.svg"):
        old.unlink()
    for theme in THEMES:
        write_svg(out / f"banner-{theme}.svg", banner(slug, theme))
        write_svg(out / f"banner-mobile-{theme}.svg", banner_mobile(slug, theme))
        for name, fn in (("flow", flow), ("board", board)):
            (out / f"{name}-{theme}.svg").write_text(fn(slug, theme), encoding="utf-8")
            (out / f"{name}-mobile-{theme}.svg").write_text(fn(slug, theme, mobile=True), encoding="utf-8")
    print(f"{slug}: {len(list(out.glob('*.svg')))} SVGs in {out}")


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in (*SPECS, "all"):
        raise SystemExit("usage: python scripts/repo_art.py <" + "|".join(SPECS) + "|all> <folder>")
    if sys.argv[1] == "all":
        root = Path(sys.argv[2])
        for slug, folder in REPO_DIRS.items():
            render(slug, root / folder / "docs" / "img")
    else:
        render(sys.argv[1], Path(sys.argv[2]))


if __name__ == "__main__":
    main()
