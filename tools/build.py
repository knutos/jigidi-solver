#!/usr/bin/env python3
"""Build the release files from the userscript and the documentation source.

    python3 tools/build.py

Writes (all relative to the repository root):
    jigidi-automagic-solver.meta.js                   header only, for cheap update checks
    docs/jigidi-automagic-solver-dokumentasjon.pdf    documentation, Norwegian (PDF)
    docs/jigidi-automagic-solver-documentation.pdf    documentation, English (PDF)
    index.html / en.html                              install/update page with the documentation (nb / en)

Needs: Python 3, reportlab (pip install reportlab), DejaVu fonts.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import docs_content  # noqa: E402
import docs_content_en  # noqa: E402

SCRIPT = os.path.join(ROOT, docs_content.FILE)
META = os.path.join(ROOT, 'jigidi-automagic-solver.meta.js')
IMAGE_REL = 'docs/panel.png'
TEMPLATE = os.path.join(ROOT, 'tools', 'site_template.html')
REPO_LINK = f'<a href="{docs_content.REPO}">{docs_content.REPO}</a>'

# Per language: documentation source, output files and the page's own text.
LANGS = {
    'nb': {
        'content': docs_content, 'page': 'index.html', 'pdf': 'docs/jigidi-automagic-solver-dokumentasjon.pdf',
        'pdf_title': 'Jigidi Automagic Solver – dokumentasjon', 'pdf_sub': 'Brukerveiledning og teknisk dokumentasjon',
        'pdf_foot': 'dokumentasjon', 'pdf_page': 'Side', 'pdf_lang': 'nb-NO',
        'img_alt': 'Kontrollpanelet i tilstandene laster, klar, løser, ferdig og minimert',
        't': {
            'meta': 'Brukerskript som legger Jigidi-puslespill automatisk. Installer, oppdater og les dokumentasjonen.',
            'tag': 'Brukerskript som legger Jigidi-puslespill automatisk.', 'langLabel': 'Språk',
            'installLabel': 'Installasjon', 'checking': 'Sjekker installert versjon…',
            'latest': 'Nyeste versjon', 'installed': 'Installert', 'install': 'Installer', 'pdf': 'Dokumentasjon (PDF)',
            'hintStart': 'Krever en brukerskript-utvidelse (se under). Last siden på nytt etter installasjon for å se den installerte versjonen.',
            'start': 'Kom i gang', 'device': 'Enhet', 'pc': 'Datamaskin', 'ios': 'iPad og iPhone',
            'pc1h': 'Installer en utvidelse', 'pc1': '<b>Tampermonkey</b> eller <b>Violentmonkey</b> fra nettleserens utvidelsesbutikk.',
            'pc2h': 'Installer skriptet', 'pc2': 'Trykk <b>Installer</b> over og bekreft i dialogen som utvidelsen viser.',
            'pc3h': 'Løs et puslespill', 'pc3': 'Åpne et puslespill på jigidi.com og trykk <b>Solve</b> i panelet nede til venstre.',
            'ios1h': 'Installer Userscripts', 'ios1': 'Gratis i App Store. Åpne appen og velg en mappe for skriptene. Slå på utvidelsen under '
                     '<b>Innstillinger → Safari → Utvidelser</b> (nyere iPadOS: <b>Apper → Safari → Utvidelser</b>).',
            'ios2h': 'Installer skriptet', 'ios2': 'Trykk <b>Installer</b> over. Skriptet åpnes som tekst. Trykk på <code>&lt;/&gt;</code>-ikonet '
                     'i adressefeltet og velg installer.',
            'ios3h': 'Løs et puslespill', 'ios3': 'Åpne et puslespill på jigidi.com, sjekk under <code>&lt;/&gt;</code> at skriptet er på, og trykk <b>Solve</b>.',
            'update': '<b>Oppdatering:</b> Tampermonkey og Violentmonkey oppdaterer skriptet automatisk fra GitHub. Vil du ha en ny versjon '
                      'med en gang, eller bruker du iPad, åpner du denne siden og trykker <b>Oppdater</b> når den vises.',
            'docs': 'Dokumentasjon', 'contents': 'Innhold', 'pdfDownload': 'Last ned PDF',
            'foot1': f'Kildekode og feilmeldinger: {REPO_LINK} · MIT-lisens · Basert på «Jigidi Auto Solver» av WorlockM.',
            'foot2': 'Bruk av automatisering kan være i strid med Jigidis vilkår. Brukeren er selv ansvarlig.',
        },
        'js': {
            'notFound': 'ikke funnet', 'install': 'Installer', 'updateTo': 'Oppdater til', 'reinstall': 'Installer på nytt',
            'stNone': 'Ikke funnet på denne enheten', 'stNew': 'Ny versjon tilgjengelig', 'stOk': 'Oppdatert',
            'stNewer': 'Nyere enn publisert versjon',
            'hintNone': 'Krever en brukerskript-utvidelse (se under). Er skriptet allerede installert, men utvidelsen ikke kjører det '
                        'på denne siden, vises det som «ikke funnet».',
            'hintNew': 'Trykk Oppdater og bekreft i utvidelsen. Last siden på nytt etterpå for å sjekke.',
            'hintOk': 'Du har nyeste versjon. Utvidelsen ser selv etter oppdateringer.',
        },
    },
    'en': {
        'content': docs_content_en, 'page': 'en.html', 'pdf': 'docs/jigidi-automagic-solver-documentation.pdf',
        'pdf_title': 'Jigidi Automagic Solver – documentation', 'pdf_sub': 'User guide and technical documentation',
        'pdf_foot': 'documentation', 'pdf_page': 'Page', 'pdf_lang': 'en',
        'img_alt': 'The control panel in its loading, ready, solving, done and minimised states',
        't': {
            'meta': 'A userscript that solves Jigidi jigsaw puzzles automatically. Install, update and read the documentation.',
            'tag': 'A userscript that solves Jigidi jigsaw puzzles automatically.', 'langLabel': 'Language',
            'installLabel': 'Installation', 'checking': 'Checking installed version…',
            'latest': 'Latest version', 'installed': 'Installed', 'install': 'Install', 'pdf': 'Documentation (PDF)',
            'hintStart': 'Needs a userscript extension (see below). Reload the page after installing to see the installed version.',
            'start': 'Get started', 'device': 'Device', 'pc': 'Computer', 'ios': 'iPad and iPhone',
            'pc1h': 'Install an extension', 'pc1': "<b>Tampermonkey</b> or <b>Violentmonkey</b> from your browser's extension store.",
            'pc2h': 'Install the script', 'pc2': 'Press <b>Install</b> above and confirm in the dialog the extension shows.',
            'pc3h': 'Solve a puzzle', 'pc3': 'Open a puzzle on jigidi.com and press <b>Solve</b> in the panel at the bottom left.',
            'ios1h': 'Install Userscripts', 'ios1': 'Free on the App Store. Open the app and choose a folder for the scripts. Turn on the extension under '
                     '<b>Settings → Safari → Extensions</b> (newer iPadOS: <b>Apps → Safari → Extensions</b>).',
            'ios2h': 'Install the script', 'ios2': 'Press <b>Install</b> above. The script opens as text. Tap the <code>&lt;/&gt;</code> icon '
                     'in the address bar and choose install.',
            'ios3h': 'Solve a puzzle', 'ios3': 'Open a puzzle on jigidi.com, check under <code>&lt;/&gt;</code> that the script is on, and press <b>Solve</b>.',
            'update': '<b>Updating:</b> Tampermonkey and Violentmonkey update the script automatically from GitHub. If you want a new version '
                      'right away, or you use an iPad, open this page and press <b>Update</b> when it appears.',
            'docs': 'Documentation', 'contents': 'Contents', 'pdfDownload': 'Download PDF',
            'foot1': f'Source code and issues: {REPO_LINK} · MIT licence · Based on "Jigidi Auto Solver" by WorlockM.',
            'foot2': "Using automation may be against Jigidi's terms. You are responsible for your own use.",
        },
        'js': {
            'notFound': 'not found', 'install': 'Install', 'updateTo': 'Update to', 'reinstall': 'Reinstall',
            'stNone': 'Not found on this device', 'stNew': 'New version available', 'stOk': 'Up to date',
            'stNewer': 'Newer than the published version',
            'hintNone': "Needs a userscript extension (see below). If the script is already installed but the extension doesn't run it "
                        'on this page, it shows as "not found".',
            'hintNew': 'Press Update and confirm in the extension. Reload the page afterwards to check.',
            'hintOk': 'You have the latest version. The extension checks for updates by itself.',
        },
    },
}


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
    def __init__(self, img_alt):
        self.out, self.toc, self.n, self.img_alt = [], [], 0, img_alt

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
                        f'alt="{self.img_alt}" loading="lazy">')


def build_html(version, lang):
    L = LANGS[lang]
    k = HtmlKit(L['img_alt'])
    L['content'].build(k, version, IMAGE_REL)
    toc = ''.join(f'<li><a href="#{sid}">{html.escape(t)}</a></li>' for sid, t in k.toc)
    page = open(TEMPLATE, encoding='utf-8').read()
    for key, val in L['t'].items():
        page = page.replace('{{t.' + key + '}}', val)
    cur = ' aria-current="page"'
    for key, val in {'{{VERSION}}': version, '{{LANG}}': lang, '{{FILE}}': docs_content.FILE, '{{PDF}}': L['pdf'],
                     '{{REPO}}': docs_content.REPO, '{{TOC}}': toc, '{{DOCS}}': '\n'.join(k.out),
                     '{{CUR_NB}}': cur if lang == 'nb' else '', '{{CUR_EN}}': cur if lang == 'en' else '',
                     '{{JS}}': json.dumps(L['js'], ensure_ascii=False)}.items():
        page = page.replace(key, val)
    left = re.findall(r'\{\{[^}]+\}\}', page)
    if left:
        sys.exit(f'Unfilled placeholders in {L["page"]}: {sorted(set(left))}')
    open(os.path.join(ROOT, L['page']), 'w', encoding='utf-8').write(page)


# ---------------------------------------------------------------- PDF renderer
def build_pdf(version, lang):
    L = LANGS[lang]
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
    ver = 'versjon' if lang == 'nb' else 'version'
    k.s += [Paragraph('Jigidi Automagic Solver', title),
            Paragraph(f'{L["pdf_sub"]} · {ver} {version}', sub)]
    L['content'].build(k, version, IMAGE_REL)

    def footer(cv, doc):
        cv.saveState(); cv.setFont('S', 8); cv.setFillColor(MUTE)
        cv.drawString(20 * mm, 12 * mm, f'Jigidi Automagic Solver {version} – {L["pdf_foot"]}')
        cv.drawRightString(190 * mm, 12 * mm, f'{L["pdf_page"]} {doc.page}')
        cv.setStrokeColor(LINE); cv.line(20 * mm, 16 * mm, 190 * mm, 16 * mm); cv.restoreState()

    doc = SimpleDocTemplate(os.path.join(ROOT, L['pdf']), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                            bottomMargin=22 * mm, title=L['pdf_title'], author='Knut Olav Sunde',
                            subject=f'{L["pdf_sub"]}, {ver} {version}', lang=L['pdf_lang'])
    doc.build(k.s, onFirstPage=footer, onLaterPages=footer)


def main():
    header, version = read_script()
    open(META, 'w', encoding='utf-8').write(header)
    for lang in LANGS:
        build_pdf(version, lang)
        build_html(version, lang)
    print(f'Built version {version}: meta.js, ' + ', '.join(f'{L["page"]} + PDF ({lang})' for lang, L in LANGS.items()))


if __name__ == '__main__':
    main()
