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

Put only merged work in `on_main`. Anything not merged into main yet (open pull request or integration branch) goes in `in_review` (optionally with `review_link`). If `on_main` is empty, explain why in `main_note`.

Never set `repo` on a private project. The build stops if you do.

Projects with `"featured": true` get a full plate (card, figure, case study) in the order they appear in the JSON. Each plate's diagram is a function in `FIGURES` inside `scripts/build.py`; a new featured project needs its own figure, otherwise its plate shows text only. Projects with `"featured": false` appear as a short `note` under *Earlier work* and are left out of the hero and brand images.

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

## Image variants

Every graphic is written in eight files: desktop or phone, dark or light, animated or still (`-static`). The README's `<picture>` picks one with media queries:

- `(max-width: 600px)` serves the phone composition (400 px wide, vertical layout, figure legend in text).
- `(prefers-color-scheme: dark)` serves the dark version.
- `(prefers-reduced-motion: reduce)` serves the still version. This lives in `<picture>`, not only inside the SVG, because a media query inside an SVG loaded as `<img>` was not applied in Chromium.

`build.py` rewrites the hero and footer `<picture>` blocks as well as the project block, so the README stays in sync. Running it twice must produce no diff; check with `git status` after a build.

## GitHub rendering limits

- No JavaScript runs in a README. Interaction comes from links and `<details>` blocks.
- SVG animation (CSS keyframes) does run inside images. The hero draws once and then stays still; plates loop slowly. Reduced motion is handled by the still variants above.
- GitHub keeps `<picture>`, `<source media>` (including combined queries) and `<details>` when it sanitizes the README.
