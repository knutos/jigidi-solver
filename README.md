# Jigidi Automagic Solver

Brukerskript som legger puslespill på [jigidi.com](https://www.jigidi.com) automatisk.
*A userscript that solves Jigidi jigsaw puzzles automatically (documentation in Norwegian).*

**Installer, oppdater og les dokumentasjonen:** https://knutos.github.io/jigidi-solver/ (norsk) · https://knutos.github.io/jigidi-solver/en.html (English)

| Fil | Innhold |
|---|---|
| `jigidi-automagic-solver.user.js` | Selve skriptet |
| `jigidi-automagic-solver.meta.js` | Bare skripthodet, for oppdateringssjekk (genereres) |
| `index.html`, `en.html` | Installasjonsside med dokumentasjon, norsk og engelsk (genereres) |
| `docs/` | Dokumentasjon som PDF på norsk og engelsk (genereres) og skjermbilde av panelet |
| `tools/` | Dokumentasjonskilde (`docs_content.py` norsk, `docs_content_en.py` engelsk), sidemal og byggeskript med sidetekstene |

## Ny versjon

1. Endre skriptet, og øk både `@version` og `JAS_VERSION` øverst i `jigidi-automagic-solver.user.js`.
2. Legg til en linje i endringsloggen i `tools/docs_content.py` og `tools/docs_content_en.py`.
3. Kjør `python3 tools/build.py` (krever `pip install reportlab`). Det skriver `meta.js`, begge PDF-ene, `index.html` og `en.html`.
4. Commit og push til `main`. GitHub Pages publiserer siden, og Tampermonkey/Violentmonkey henter oppdateringen.

Basert på «Jigidi Auto Solver» av WorlockM (MIT).
