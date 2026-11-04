"""Illustrations for project READMEs, in the same visual system as this profile.

Usage:
    python scripts/repo_art.py mapper <output folder>

Writes SVGs into the output folder (for example the docs/img folder of the
Project Structure Mapper repository). The terminal and report images reproduce
a real run of the Mapper on a fictitious project ("LojaExemplo"); if the tool's
messages change, update TRANSCRIPT and the REPORT_* blocks below and re-run.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import (  # noqa: E402
    MOBILE_W, MOTION_CSS, THEMES, WIDTH, Fonts, crop_marks, fig_mapper,
    hairline, svg_doc, text, text_width, wrap, write_svg,
)

STATUS = "under-review"

# ---------------------------------------------------------------- banner ---
TAGLINE = "Entenda a estrutura de projetos de código sem abrir arquivo por arquivo."
BLOCK = [
    ("roda em", "Windows 10/11 · Python 3.8+"),
    ("projeto", "somente leitura, offline"),
    ("versão", "v2.1.0 na main"),
]


def banner(theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, H = WIDTH, 400
    p = [crop_marks(t, 6, 6, W - 12, H - 12)]
    p.append(text(fonts, "sans", "Ferramenta local de leitura de código", 2, 50, 14, t["muted"], extra='class="fade"'))
    y = 128
    for i, word in enumerate(("Project", "Structure", "Mapper")):
        p.append(text(fonts, "serif", word, -3, y, 74, t["text"],
                      extra=f'letter-spacing="-1" class="rise" style="animation-delay:{.05 + i * .12:.2f}s"'))
        y += 66
    y += 6
    for i, line in enumerate(wrap(TAGLINE, "sans", 18, 360)):
        p.append(text(fonts, "sans", line, 2, y + i * 26, 18, t["text"],
                      extra=f'class="fade" style="animation-delay:{.5 + i * .1:.2f}s"'))
    # figure on the right
    fx, fy, fw, fh = 410, 40, 432, 240
    fig, css = fig_mapper(fonts, t, fx, fy, fw, fh, lang="pt")
    p.append(f'<g class="fade" style="animation-delay:.6s">{fig}</g>')
    # title block
    bx, by, bw, rh = 410, 300, W - 416, 30
    p.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{rh * 3}" fill="none" stroke="{t["frame"]}"/>')
    p.append(hairline(t, bx + 78, by, bx + 78, by + rh * 3))
    for i, (k, v) in enumerate(BLOCK):
        ry = by + i * rh
        if i:
            p.append(hairline(t, bx, ry, bx + bw, ry))
        p.append(text(fonts, "mono", k, bx + 10, ry + 19, 11, t["muted"]))
        p.append(text(fonts, "sans", v, bx + 90, ry + 20, 14, t["text"]))
    p.append(text(fonts, "sans-medium", "falta teste num Windows físico", bx + bw - 10, by + 2 * rh + 20, 13,
                  t["status"][STATUS], "end"))
    return svg_doc(W, H, "Project Structure Mapper",
                   "Project Structure Mapper. " + TAGLINE + " Diagrama: a pasta do projeto é lida sem alterações "
                   "e gera um resumo público ou um relatório privado, salvos fora do projeto com um ZIP. "
                   "Windows 10/11, Python 3.8+, somente leitura e offline. Versão 2.1.0 na main; "
                   "falta teste num Windows físico.",
                   fonts, MOTION_CSS + css, "".join(p))


def banner_mobile(theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, M = MOBILE_W, 20
    p = []
    p.append(text(fonts, "sans", "Ferramenta local de leitura de código", M, 40, 14, t["muted"], extra='class="fade"'))
    y = 104
    for i, word in enumerate(("Project", "Structure", "Mapper")):
        p.append(text(fonts, "serif", word, M - 3, y, 62, t["text"],
                      extra=f'letter-spacing="-1" class="rise" style="animation-delay:{.05 + i * .12:.2f}s"'))
        y += 56
    y -= 8
    for line in wrap(TAGLINE, "sans", 17, W - 2 * M):
        p.append(text(fonts, "sans", line, M, y, 17, t["text"], extra='class="fade" style="animation-delay:.5s"'))
        y += 24
    y += 10
    fw, fh = 432, 240
    k = (W - 2 * M) / fw
    fig, css = fig_mapper(fonts, t, 0, 0, fw, fh, labels=False, lang="pt")
    p.append(f'<g transform="translate({M},{y}) scale({k:.4f})">{fig}</g>')
    y += fh * k + 20
    rh = 34
    p.append(f'<rect x="{M}" y="{y}" width="{W - 2 * M}" height="{rh * 4}" fill="none" stroke="{t["frame"]}"/>')
    p.append(hairline(t, M + 84, y, M + 84, y + rh * 4))
    rows = BLOCK + [("status", "falta teste no Windows")]
    for i, (key, v) in enumerate(rows):
        ry = y + i * rh
        if i:
            p.append(hairline(t, M, ry, W - M, ry))
        p.append(text(fonts, "mono", key, M + 10, ry + 22, 12, t["muted"]))
        c = t["status"][STATUS] if key == "status" else t["text"]
        p.append(text(fonts, "sans", v, M + 96, ry + 22, 14, c))
    H = y + rh * 4 + 24
    body = crop_marks(t, 6, 6, W - 12, H - 12) + "".join(p)
    return svg_doc(W, H, "Project Structure Mapper", "Project Structure Mapper. " + TAGLINE,
                   fonts, MOTION_CSS + css, body)


# -------------------------------------------------------------- terminal ---
# Real run (pseudo-terminal, Linux) on the fictitious project LojaExemplo.
# ">" marks what the user typed; it is drawn in the accent colour.
TRANSCRIPT = """\
============================================================
   PROJECT STRUCTURE MAPPER  v2.1.0
   Entenda a estrutura de um projeto em 3 passos
============================================================

1) Mapear um projeto
2) O que essa ferramenta faz?
0) Sair
Escolha uma opção [Enter = 1]: >1

PASSO 1/3 — Qual projeto vamos analisar?
Cole o caminho da pasta ou pressione Enter para procurar: >/home/demo/projetos/LojaExemplo

PASSO 2/3 — Qual relatório você quer?
1) Público/resumido: só números e tecnologias, sem nomes (mais seguro)
2) Privado/detalhado: nomes de arquivos, árvore e referências (uso interno)
Escolha 1 ou 2 [Enter = 1]: >2

PASSO 3/3 — Onde salvar o relatório? (sempre FORA do projeto)
Pasta de saída [Enter = /home/demo/ProjectStructureReports]: >(Enter)

AVISO: nomes internos podem ser confidenciais. Não publique esse ZIP.
Iniciar análise? [S/n]: >s

[1/3] Lendo a estrutura (o projeto NÃO é alterado)...
[2/3] Organizando as informações...
[3/3] Gerando o ZIP...

✓ Concluído! 15 arquivo(s) indexado(s).
✓ 16 referência(s) estática(s) registrada(s).
✓ 1 arquivo(s) sensível(is) omitido(s) por segurança.
✓ O código do projeto NÃO foi copiado para o ZIP."""


def terminal(theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, size, lh = WIDTH, 12.5, 19
    lines = TRANSCRIPT.split("\n")
    top = 46
    H = top + 22 + len(lines) * lh + 40
    s = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{t["surface"]}" stroke="{t["frame"]}"/>']
    for i in range(3):
        s.append(f'<circle cx="{22 + i * 16}" cy="20" r="4.5" fill="none" stroke="{t["line"]}" stroke-width="1.5"/>')
    s.append(text(fonts, "mono", "INICIAR_WINDOWS.bat  ·  assistente", W / 2, 24, 11, t["muted"], "middle"))
    s.append(hairline(t, 0, 38, W, 38))
    y = top + 18
    for line in lines:
        x = 24
        prompt, _, typed = line.partition(">") if ">" in line and not line.startswith("=") else (line, "", "")
        if prompt.startswith("PASSO") or prompt.startswith("   PROJECT"):
            color, key = t["text"], "mono"
        elif prompt.startswith("✓"):
            color, key = t["status"]["completed"], "mono"
        elif prompt.startswith("AVISO"):
            color, key = t["status"]["under-review"], "mono"
        elif prompt.startswith("="):
            color, key = t["line"], "mono"
        else:
            color, key = t["muted"], "mono"
        if prompt:
            s.append(text(fonts, key, prompt, x, y, size, color, extra='xml:space="preserve"'))
        if typed:
            tx = x + text_width(prompt, "mono", size)
            s.append(text(fonts, "mono", typed, tx, y, size, t["accent"]))
        y += lh
    s.append(hairline(t, 0, H - 30, W, H - 30))
    s.append(text(fonts, "mono", "Trechos de uma execução real (terminal Linux, projeto fictício). "
                  "Em destaque: o que foi digitado.", 24, H - 11, 11, t["muted"]))
    return svg_doc(W, H, "Assistente do Project Structure Mapper",
                   "Transcrição de uma execução real do assistente: menu, três passos (pasta, tipo de relatório, "
                   "pasta de saída), aviso de confidencialidade e resultado com 15 arquivos indexados, 16 referências "
                   "estáticas e 1 arquivo sensível omitido.",
                   fonts, "", "".join(s))


# ---------------------------------------------------------------- report ---
# Excerpts of relatorio.md from the same run, public and private modes.
REPORT_PUBLIC = """\
# Project Structure Mapper
- Modo: público/resumido
- Arquivos indexados: 15
- Arquivos sensíveis omitidos: 1
## Tecnologias prováveis
- ASP.NET Web Forms
- C# / .NET
- JavaScript
## Tipos de arquivo
- .aspx: 3 · .ascx: 2 · .master: 1
- .cs: 6 · .csproj: 1 · .css: 1 · .js: 1
## Proteção de privacidade
- Omite nomes de projetos, pastas, arquivos e dependências.
- Revise antes de publicar."""

REPORT_PRIVATE = """\
# Project Structure Mapper
- Modo: privado/detalhado
- Arquivos indexados: 15
## Projeto: LojaExemplo
## Uso de Master Pages
- Site.master: 3 página(s)
## Referências por status
- localizado: 13 · contextual: 2 · nao_encontrado: 1
## Algumas relações estáticas
- Default.aspx → Site.master (masterpage)
- Default.aspx → Controles/Vitrine.ascx (registro_controle)
- Site.master → Controles/Menu.ascx (uso_controle)
- Site.master → Scripts/app.js (javascript; contextual)
- Carrinho.aspx → Controles/ResumoPedido.ascx (nao_encontrado)
- …"""


def _sheet(fonts, t, md: str, x: float, y: float, w: float) -> tuple[list[str], float]:
    out, yy = [], y + 40
    for line in md.split("\n"):
        if line.startswith("# "):
            out.append(text(fonts, "serif", line[2:], x + 20, yy, 24, t["text"]))
            yy += 14
            out.append(hairline(t, x + 20, yy, x + w - 20, yy))
            yy += 24
        elif line.startswith("## "):
            yy += 8
            out.append(text(fonts, "sans-medium", line[3:], x + 20, yy, 14, t["text"]))
            yy += 22
        else:
            body = line[2:]
            color = t["status"]["under-review"] if "nao_encontrado)" in body else t["muted"]
            for j, part in enumerate(wrap(body, "sans", 12.5, w - 58)):
                if j == 0:
                    out.append(f'<circle cx="{x + 24}" cy="{yy - 4}" r="1.8" fill="{t["line"]}"/>')
                out.append(text(fonts, "sans", part, x + 34, yy, 12.5, color))
                yy += 18
    return out, yy + 12


def report(theme: str) -> str:
    t = THEMES[theme]
    fonts = Fonts()
    W, gap = WIDTH, 20
    sw = (W - gap) / 2
    s = []
    heights = []
    parts = []
    for i, (md, tag, color) in enumerate(((REPORT_PUBLIC, "modo público", t["accent"]),
                                          (REPORT_PRIVATE, "modo privado · uso interno", t["status"]["under-review"]))):
        x = i * (sw + gap)
        body, h = _sheet(fonts, t, md, x, 28, sw)
        heights.append(h)
        parts.append((x, body, tag, color))
    H = max(heights) + 40
    for x, body, tag, color in parts:
        s.append(text(fonts, "mono", "relatorio.md", x, 16, 11, t["muted"]))
        s.append(text(fonts, "mono", tag, x + sw, 16, 11, color, "end"))
        s.append(f'<path d="M{x + .5},28.5 h{sw - 19} l18,18 V{H - 40} H{x + .5} z" fill="{t["surface"]}" '
                 f'stroke="{t["frame"]}" stroke-linejoin="round"/>')
        s.append(f'<path d="M{x + sw - 18.5},28.5 v18 h18" fill="none" stroke="{t["frame"]}"/>')
        s.extend(body)
    s.append(text(fonts, "mono", "Trechos reais de relatorio.md, gerados a partir do mesmo projeto fictício.",
                  0, H - 12, 11, t["muted"]))
    return svg_doc(W, H, "Relatórios público e privado",
                   "Dois trechos de relatorio.md lado a lado. O público mostra só contagens e tecnologias "
                   "(ASP.NET Web Forms, C#, JavaScript) e omite nomes. O privado mostra o nome do projeto, "
                   "uso de Master Pages, referências por status e relações estáticas entre arquivos, "
                   "incluindo uma referência não encontrada.",
                   fonts, "", "".join(s))


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] != "mapper":
        raise SystemExit("usage: python scripts/repo_art.py mapper <output folder>")
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        write_svg(out / f"banner-{theme}.svg", banner(theme))
        write_svg(out / f"banner-mobile-{theme}.svg", banner_mobile(theme))
        (out / f"assistente-{theme}.svg").write_text(terminal(theme), encoding="utf-8")
        (out / f"relatorios-{theme}.svg").write_text(report(theme), encoding="utf-8")
    for f in sorted(out.glob("*.svg")):
        print(f"{f.name}  {f.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
