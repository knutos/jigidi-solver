#!/usr/bin/env python3
"""Build the release files from the userscript and the documentation source.

    python3 tools/build.py

Writes (all relative to the repository root):
    jigidi-automagic-solver.meta.js                 header only, for cheap update checks
    docs/jigidi-automagic-solver-dokumentasjon.pdf  documentation (PDF)
    index.html                                      install/update page with the documentation

Needs: Python 3, reportlab (pip install reportlab), DejaVu fonts.
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import docs_content  # noqa: E402

SCRIPT = os.path.join(ROOT, docs_content.FILE)
META = os.path.join(ROOT, 'jigidi-automagic-solver.meta.js')
PDF = os.path.join(ROOT, 'docs', 'jigidi-automagic-solver-dokumentasjon.pdf')
PDF_REL = 'docs/jigidi-automagic-solver-dokumentasjon.pdf'
IMAGE_REL = 'docs/panel.png'
TEMPLATE = os.path.join(ROOT, 'tools', 'site_template.html')
INDEX = os.path.join(ROOT, 'index.html')


def read_script():
    src = open(SCRIPT, encoding='utf-8').read()
    header = src[:src.index('// ==/UserScript==') + len('// ==/UserScript==')] + '\n'
    version = re.search(r'^// @version\s+(\S+)', header, re.M).group(1)
    const = re.search(r"const JAS_VERSION = '([^']+)'", src)
    if not const or const.group(1) != version:
        sys.exit(f'Version mismatch: @version {version} but JAS_VERSION {const and const.group(1)}')
    return header, version


# ---------------------------------------------------------------- HTML renderer
class HtmlKit:
    def __init__(self):
        self.out, self.toc, self.n = [], [], 0

    @staticmethod
    def c(t):
        return f'<code>{t}</code>'

    def h1(self, t):
        self.n += 1
        sid = f'd{self.n}'
        self.toc.append((sid, re.sub(r'^\d+\.\s*', '', t)))
        self.out.append(f'<h2 id="{sid}">{t}</h2>')

    def h2(self, t):
        self.out.append(f'<h3>{t}</h3>')

    def p(self, t):
        self.out.append(f'<p>{t}</p>')

    def note(self, t):
        self.out.append(f'<p class="note">{t}</p>')

    def caption(self, t):
        self.out.append(f'<p class="cap">{t}</p>')

    def bullets(self, items):
        self.out.append('<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>')

    def table(self, rows, widths):
        head = ''.join(f'<th>{x}</th>' for x in rows[0])
        body = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in r) + '</tr>' for r in rows[1:])
        self.out.append(f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')

    def code(self, intro, code):
        self.p(intro)
        self.out.append(f'<pre><code>{html.escape(code)}</code></pre>')

    def image(self, path, width_mm, aspect):
        self.out.append(f'<img class="shot" src="{path}" width="360" height="{round(360 * aspect)}" '
                        'alt="Kontrollpanelet i tilstandene laster, klar, løser, ferdig og minimert" loading="lazy">')


def build_html(version):
    k = HtmlKit()
    docs_content.build(k, version, IMAGE_REL)
    toc = ''.join(f'<li><a href="#{sid}">{html.escape(t)}</a></li>' for sid, t in k.toc)
    page = open(TEMPLATE, encoding='utf-8').read()
    for key, val in {'{{VERSION}}': version, '{{FILE}}': docs_content.FILE, '{{PDF}}': PDF_REL,
                     '{{REPO}}': docs_content.REPO, '{{TOC}}': toc, '{{DOCS}}': '\n'.join(k.out)}.items():
        page = page.replace(key, val)
    open(INDEX, 'w', encoding='utf-8').write(page)


# ---------------------------------------------------------------- PDF renderer
def build_pdf(version):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                    Preformatted, KeepTogether, Image)

    fonts = '/usr/share/fonts/truetype/dejavu/'
    for name, f in [('S', 'DejaVuSans.ttf'), ('SB', 'DejaVuSans-Bold.ttf'), ('SI', 'DejaVuSans-Oblique.ttf'),
                    ('M', 'DejaVuSansMono.ttf')]:
        pdfmetrics.registerFont(TTFont(name, fonts + f))
    registerFontFamily('S', normal='S', bold='SB', italic='SI', boldItalic='SB')

    INK = colors.HexColor('#1f2937'); ACC = colors.HexColor('#15803d'); MUTE = colors.HexColor('#6b7280')
    LINE = colors.HexColor('#d1d5db'); CODEBG = colors.HexColor('#f3f4f6'); HEAD = colors.HexColor('#e5efe8')
    body = ParagraphStyle('b', fontName='S', fontSize=9.8, leading=14, textColor=INK, spaceAfter=6)
    small = ParagraphStyle('s', parent=body, fontSize=8.6, leading=11.5, spaceAfter=0)
    smallb = ParagraphStyle('sb', parent=small, fontName='SB')
    h1 = ParagraphStyle('h1', fontName='SB', fontSize=14, leading=18, textColor=ACC, spaceBefore=14, spaceAfter=6, keepWithNext=1)
    h2 = ParagraphStyle('h2', fontName='SB', fontSize=11, leading=14, textColor=INK, spaceBefore=8, spaceAfter=4, keepWithNext=1)
    title = ParagraphStyle('t', fontName='SB', fontSize=24, leading=29, textColor=INK, spaceAfter=4)
    sub = ParagraphStyle('st', fontName='S', fontSize=11.5, leading=15, textColor=MUTE, spaceAfter=14)
    bul = ParagraphStyle('bl', parent=body, leftIndent=14, bulletIndent=3, spaceAfter=3)
    code = ParagraphStyle('c', fontName='M', fontSize=8.3, leading=11, textColor=INK, backColor=CODEBG,
                          borderPadding=(6, 6, 6, 6), leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=10)
    note = ParagraphStyle('n', parent=body, backColor=colors.HexColor('#fef9c3'), borderPadding=(6, 8, 6, 8),
                          leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=10)
    cap = ParagraphStyle('cap', parent=small, textColor=MUTE, spaceAfter=8, alignment=1)

    class PdfKit:
        def __init__(self):
            self.s = []

        @staticmethod
        def c(t):
            return f'<font name="M" size="8.8">{t}</font>'

        def h1(self, t): self.s.append(Paragraph(t, h1))
        def h2(self, t): self.s.append(Paragraph(t, h2))
        def p(self, t): self.s.append(Paragraph(t, body))
        def note(self, t): self.s.append(Paragraph(t, note))
        def caption(self, t): self.s.append(Paragraph(t, cap))

        def bullets(self, items):
            self.s.extend(Paragraph(i, bul, bulletText='•') for i in items)

        def table(self, rows, widths):
            data = [[Paragraph(x, smallb if r == 0 else small) for x in row] for r, row in enumerate(rows)]
            t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
            t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, LINE), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                                   ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                   ('BACKGROUND', (0, 0), (-1, 0), HEAD)]))
            self.s += [t, Spacer(1, 6)]

        def code(self, intro, text):
            self.s.append(KeepTogether([Paragraph(intro, body), Preformatted(text, code)]))

        def image(self, path, width_mm, aspect):
            self.s += [Image(os.path.join(ROOT, path), width=width_mm * mm, height=width_mm * mm * aspect), Spacer(1, 4)]

    k = PdfKit()
    k.s += [Paragraph('Jigidi Automagic Solver', title),
            Paragraph(f'Brukerveiledning og teknisk dokumentasjon · versjon {version}', sub)]
    docs_content.build(k, version, IMAGE_REL)

    def footer(cv, doc):
        cv.saveState(); cv.setFont('S', 8); cv.setFillColor(MUTE)
        cv.drawString(20 * mm, 12 * mm, f'Jigidi Automagic Solver {version} – dokumentasjon')
        cv.drawRightString(190 * mm, 12 * mm, f'Side {doc.page}')
        cv.setStrokeColor(LINE); cv.line(20 * mm, 16 * mm, 190 * mm, 16 * mm); cv.restoreState()

    doc = SimpleDocTemplate(PDF, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                            bottomMargin=22 * mm, title='Jigidi Automagic Solver – dokumentasjon', author='Knut Olav Sunde',
                            subject=f'Brukerveiledning og teknisk dokumentasjon, versjon {version}', lang='nb-NO')
    doc.build(k.s, onFirstPage=footer, onLaterPages=footer)


def main():
    header, version = read_script()
    open(META, 'w', encoding='utf-8').write(header)
    build_pdf(version)
    build_html(version)
    print(f'Built version {version}: meta.js, PDF, index.html')


if __name__ == '__main__':
    main()
