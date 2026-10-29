# Maintaining this profile

Everything visual is generated from one file: `portfolio/projects.json`.

## Update a project

1. Edit the project in `portfolio/projects.json`.
2. Run `python scripts/build.py` (needs `pip install fonttools`).
3. Check `git diff` and commit the JSON, the regenerated SVGs and `README.md` together.

`build.py` rewrites only the block between `<!-- PROJECTS:START -->` and `<!-- PROJECTS:END -->` in `README.md`. Everything else in the README is written by hand.

## Status rules

| Status | Use it when |
|---|---|
| `planned` | The idea is written down, but there is no code yet |
| `prototype` | Something runs, but core flows are not tested end to end |
| `in-development` | Core flows exist and are being built out on branches |
| `under-review` | Feature work is done; it is being audited, fixed or reviewed |
| `completed` | Merged, tested by a human, and someone else could run it from the README |

Change a status only after the milestone is validated (tests passed on a real machine, PR merged, manual check done). Commits, CI runs or agent reports alone are not enough.

Never set `repo` on a private project. The build stops if you do.

## Activity vs. validated status

- **Automatic**: GitHub's own contribution graph and pinned repositories update by themselves. Nothing in this repo needs a scheduled workflow.
- **Manual**: project statuses and case studies. They change only through an edit to `projects.json`.

## Brand images

`python scripts/brand.py` renders `brand/social-preview.png` (repository social preview) and `brand/linkedin-banner.png`. It needs Playwright with Chromium.

## Checks

- `python scripts/contrast.py` confirms every text colour reaches WCAG AA (4.5:1) on GitHub's light and dark backgrounds.
- Colours live in `THEMES` inside `scripts/build.py`.

## Fonts

Instrument Serif, JetBrains Mono and Inter, all under the SIL Open Font License (see `scripts/fonts/`). Each SVG embeds only the glyphs it uses, because GitHub shows README SVGs as images and those cannot load web fonts.

## GitHub rendering limits

- No JavaScript runs in a README. Interaction comes from links and `<details>` blocks.
- SVG animation (CSS keyframes) does run inside images. The hero draws once and then stays still; `prefers-reduced-motion` turns it off.
- Light and dark versions are switched with `<picture>` and `prefers-color-scheme`.
