"""Documentation content for Jigidi Automagic Solver (Norwegian).

Single source for both the PDF and the documentation on the web page. Content is written against a
small "kit" (K) that each renderer implements:

    K.h1(text)  K.h2(text)  K.p(text)  K.note(text)  K.caption(text)
    K.bullets([text, ...])  K.table(rows, widths_mm)  K.code(intro, code)  K.image(path, width_mm, aspect)
    K.c(text) -> inline code markup

Inline markup in text: <b>, <i>, and K.c(...) for code. Escape < and > as &lt; &gt;.
"""

SITE = 'https://knutos.github.io/jigidi-solver/'
REPO = 'https://github.com/knutos/jigidi-solver'
FILE = 'jigidi-automagic-solver.user.js'


def build(K, version, image_path):
    c = K.c

    K.h1('1. Oversikt')
    K.p('Jigidi Automagic Solver er et brukerskript (userscript) som legger puslespill på jigidi.com automatisk. '
        'Skriptet leser hvor hver brikke hører hjemme direkte fra spillets egen tegnekode, og drar deretter '
        'brikkene på plass én etter én med syntetiske musehendelser. Det trengs ingen bildegjenkjenning.')
    K.p(f'Skriptet, denne dokumentasjonen og installasjonssiden ligger på GitHub: <b>{REPO}</b>. '
        f'Installasjonssiden er <b>{SITE}</b>.')

    K.h1('2. Installasjon og oppdatering')
    K.p('Skriptet krever en brukerskript-utvidelse i nettleseren, for eksempel <b>Tampermonkey</b> eller '
        '<b>Violentmonkey</b>.')
    K.bullets([
        'Installer utvidelsen fra nettleserens utvidelsesbutikk.',
        f'Åpne installasjonssiden ({SITE}) og trykk <b>Installer</b>. Utvidelsen viser da en installasjonsdialog.',
        'Bekreft installasjonen. Skriptet kjører automatisk på puslespillsider på jigidi.com.',
    ])
    K.note('<b>Viktig:</b> Skriptet må kjøre ved <i>document-start</i> og i sidens egen kontekst '
           f'({c("@inject-into page")}), ellers rekker det ikke å koble seg på spillet før det starter. '
           'Har du en annen Jigidi-utvidelse aktiv (f.eks. «Bingo Solver»), bør den slås av.')

    K.h2('2.1 Oppdatering')
    K.bullets([
        '<b>Automatisk:</b> Tampermonkey og Violentmonkey ser etter nye versjoner på GitHub med jevne mellomrom '
        f'(via {c("@updateURL")}) og oppdaterer skriptet selv.',
        '<b>Med en gang:</b> Åpne installasjonssiden. Den viser hvilken versjon du har installert og hva som er nyeste. '
        'Er det en nyere versjon, trykker du <b>Oppdater</b>.',
        '<b>Fra utvidelsen:</b> I Tampermonkey: Kontrollpanel → velg skriptet → «Se etter oppdateringer».',
    ])
    K.p('Installasjonssiden kan bare se den installerte versjonen hvis utvidelsen får kjøre skriptet på siden. '
        'Skriptet gjør ingenting der annet enn å melde fra om versjonen.')

    K.h2('2.2 iPad og iPhone (Safari)')
    K.p('Safari på iPad og iPhone kan kjøre brukerskript med appen <b>Userscripts</b> (gratis i App Store). '
        '<b>Tampermonkey</b> finnes også for Safari, og fungerer på samme måte som på datamaskin.')
    K.bullets([
        'Installer <b>Userscripts</b> fra App Store og åpne appen én gang. Velg en mappe der skriptene skal ligge '
        '(f.eks. en mappe «Userscripts» i iCloud Drive).',
        'Slå på utvidelsen: <b>Innstillinger → Safari → Utvidelser → Userscripts</b> (på nyere iPadOS: '
        '<b>Innstillinger → Apper → Safari → Utvidelser</b>). Gi den tilgang til jigidi.com, eller til alle nettsteder.',
        f'Åpne installasjonssiden i Safari og trykk <b>Installer</b>. Skriptet åpnes som tekst. Trykk på {c("&lt;/&gt;")}-ikonet '
        'i adressefeltet og velg installer.',
        f'Åpne et puslespill på jigidi.com. Trykk på {c("&lt;/&gt;")}-ikonet og sjekk at <b>Jigidi Automagic Solver</b> er slått på.',
    ])
    K.p('For å oppdatere på iPad: åpne installasjonssiden og installer på nytt på samme måte. '
        'Panelet brukes som på datamaskin: trykk <b>Solve</b>, trykk <b>Stop</b> for å avbryte (Esc finnes bare med tastatur), '
        'dra panelet med fingeren, og trykk på ringen for å minimere.')

    K.h1('3. Bruk')
    K.p('Kontrollpanelet er en liten mørk «pille» nede i venstre hjørne. Til venstre er en ring som viser fremdriften, '
        'i midten status, og til høyre en knapp. Bildet viser panelet i de ulike tilstandene:')
    K.image(image_path, 62, 800 / 720)
    K.caption('Panelets tilstander, ovenfra: laster, klar, løser, ferdig og minimert.')
    K.h2('3.1 Slik løser du et puslespill')
    K.bullets([
        'Åpne et puslespill på jigidi.com. Mens brikkene lastes, snurrer ringen og knappen er grå («<i>Loading puzzle…</i>»).',
        'Når panelet viser «<i>N pieces · ready</i>», trykker du <b>Solve</b>.',
        'Under løsingen fylles ringen etter hvert som brikker legges, og statuslinjen viser for eksempel '
        '«<i>271/500 · 107.0/s · 3s left</i>»: lagte brikker, brikker per sekund og anslått tid igjen.',
        'Knappen blir rød og heter <b>Stop</b>. Trykk på den, eller trykk <b>Esc</b>, for å avbryte. '
        'Brikker som allerede er lagt, blir liggende.',
        'Når skriptet er ferdig, viser panelet antall lagte brikker, tidsbruk og brikker per sekund.',
    ])
    K.h2('3.2 Farger og symboler')
    K.table([['Tilstand', 'Utseende', 'Betydning'],
             ['Laster', 'Snurrende ring, grå knapp', 'Brikkene er ikke ferdig registrert ennå.'],
             ['Klar', 'Grønn knapp «Solve»', 'Puslespillet er gjenkjent og kan løses.'],
             ['Løser', 'Ringen fylles, rød knapp «Stop»', 'Løsingen pågår. Ekte museinput mot spillet blokkeres.'],
             ['Ferdig', 'Grønn hake, full ring', 'Alle brikker ligger riktig.'],
             ['Delvis', 'Gul farge', 'Løsingen ble stoppet, eller noen brikker feilet.'],
             ['Feil', 'Rød farge og feilmelding', 'Se kapittel 7.']],
            [26, 52, 92])
    K.h2('3.3 Flytte og minimere panelet')
    K.bullets([
        '<b>Flytt:</b> Dra panelet hvor som helst på skjermen. Det holder seg alltid innenfor vinduet.',
        '<b>Minimer:</b> Klikk på ringen for å krympe panelet til bare ringen. Klikk igjen for å vise hele panelet. '
        'Ringen oppdateres også i minimert tilstand, og holder du musen over den, vises status som verktøytips.',
        f'<b>Huskes:</b> Plassering og minimert tilstand lagres i nettleseren (nøkkelen {c("jas-ui")} i localStorage) '
        'og gjenopprettes neste gang.',
    ])
    K.p('Mens skriptet arbeider, blokkeres ekte mus-, peker- og berøringshendelser mot spillet, slik at du '
        'ikke ved et uhell flytter brikker. Panelet selv kan fortsatt brukes. Panelet ligger i en egen Shadow DOM, '
        'slik at Jigidis stilark ikke kan påvirke utseendet.')

    K.h1('4. Slik virker det')
    K.h2('4.1 Kroker (hooks)')
    K.p('Ved sidelasting erstatter skriptet noen innebygde nettleserfunksjoner med egne versjoner som '
        'registrerer data og deretter kaller originalen. All informasjon lagres i det globale objektet '
        f'{c("window.__jas")}.')
    K.table([['Funksjon', 'Hva skriptet fanger opp'],
             [c('addEventListener'), 'Alle mus-, peker- og berøringslyttere spillet registrerer, slik at skriptet kan kalle dem direkte.'],
             [c('iframe.contentWindow'), 'Kobler seg også på addEventListener i iframes, slik at spillet ikke kan omgå krokene '
                                        'ved å hente en «ren» kopi av funksjonen fra en iframe.'],
             [c('removeEventListener'), 'Fjerner lyttere fra listen igjen, så skriptet aldri kaller utdaterte lyttere.'],
             [c('setPointerCapture'), 'Etterligner pekerfangst for skriptets egne pekerhendelser. Uten dette ville nettleseren '
                                      'kaste en feil, fordi det ikke finnes noen ekte aktiv peker.'],
             [c('putImageData'), 'Markerer at en ny brikke klippes ut på spillets kladdelerret.'],
             [c('drawImage'), 'Tre tilfeller: (1) kildeforskyvning for brikken i originalbildet, (2) hvilket lerret som '
                              'holder hvilken brikke, (3) hvor brikken tegnes på skjermen (posisjon, skala, midtpunkt).']],
            [42, 128])
    K.p('Fordi Jigidi klipper brikkene i fasit-rekkefølge (rad for rad), gir rekkefølgen og kildeforskyvningen '
        'til sammen den fullstendige fasiten.')

    K.h2('4.2 Løseren')
    K.p('Når du trykker <b>Solve</b>, går løseren gjennom disse trinnene:')
    K.table([['Trinn', 'Beskrivelse'],
             ['Gjenkjenning', 'Leser dimensjonene fra teksten «(kolonner × rader)» på siden og kontrollerer at '
                              'antallet stemmer med antall utklipte brikker.'],
             ['Zoom', 'Zoomer ut med «−»-knappen til det ferdige puslespillet tar under halvparten av brettet, under 75 % av bredden '
                      'og får plass i høyden. Får det fortsatt ikke plass, stopper skriptet med en melding.'],
             ['Fortsett', 'Finnes det allerede en sammensatt del (fra en tidligere kjøring eller lagt for hånd), bygger skriptet videre på '
                          'den største. Ligger den delvis utenfor brettet, ryddes først plassen den skal flyttes til, og så dras hele delen inn.'],
             ['Velg anker', 'Ellers prøver skriptet hver brikke som fast utgangspunkt, og velger den der det ferdige puslespillet får plass '
                            'på brettet og det ligger færrest løse brikker i målområdet. Ankerbrikken flyttes ikke.'],
             ['Legg brikker', 'Legger brikkene i bredde-først-rekkefølge utover fra ankeret, så hver brikke slippes '
                              'ved siden av en allerede lagt nabo og smekker på plass med én gang.'],
             ['Rydd underveis', 'Rett før en brikke legges, fjernes løse brikker som ligger på eller rett ved plassen dens, '
                                'øverste først. Kan en slik brikke allerede legges på sin egen plass (den har en lagt nabo), '
                                'legges den dit direkte. Ellers parkeres den utenfor målområdet.'],
             ['Nytt forsøk', 'Brikker som feilet, prøves på nytt i en ny runde (standard 2 runder, inntil 12 forsøk per brikke).'],
             ['Opptelling', 'Teller til slutt hvor mange brikker som faktisk ligger riktig i forhold til naboene.']],
            [34, 136])

    K.h2('4.3 Feilgrep og korrigering')
    K.bullets([
        '<b>Gripepunkt:</b> Skriptet griper i midten av brikken, ikke i et gjennomsiktig hjørne. Dekkes midten av '
        'en brikke som ligger over, prøves opptil åtte andre punkter.',
        '<b>Feil brikke flyttet:</b> Flyttes en løs brikke ved en feil, parkeres den utenfor målområdet.',
        '<b>Ferdig del flyttet:</b> Flyttes det sammensatte puslespillet ved en feil, dras det straks tilbake.',
        '<b>Tilfeldig treff:</b> Smekker en brikke på plass av seg selv, registreres den som lagt.',
    ])

    K.h2('4.4 Inndatamodus')
    K.p('Jigidi finnes i flere varianter som tar imot input på ulik måte. Ved starten av hver løsing sjekker '
        'skriptet hvilke lyttere spillet har registrert, og velger modus automatisk:')
    K.table([['Modus', 'Når den brukes', 'Hvordan skriptet drar brikker'],
             [c('mouse'), f'Spillet har en {c("mousedown")}-lytter på brettet (den opprinnelige varianten).',
              f'{c("mousedown")} på brettet, {c("mousemove")} på dokumentet, {c("mouseup")} på vinduet.'],
             [c('pointer'), 'Spillet bruker bare pekerhendelser, f.eks. på et DIV-element rundt brettet.',
              f'{c("pointerdown")}, {c("pointermove")} og {c("pointerup")} sendes gjennom en egen hendelsesformidler '
              'som etterligner nettleseren: treffpunkt, fangst-, mål- og boblefase, stopPropagation og pekerfangst. '
              f'Håndterere satt som egenskaper ({c("onpointerdown = …")}) kalles også.'],
             [c('native'), 'Skriptet kjenner ingen av spillets lyttere, f.eks. fordi det ble lastet for sent.',
              f'Ekte hendelser sendes med {c("dispatchEvent")}: pekerhendelser og deretter musehendelser, slik nettleseren gjør. '
              f'Virker så lenge spillet ikke krever {c("isTrusted")}.']],
            [20, 62, 88])
    K.p('Reagerer ikke spillet på tre drag på rad, prøver skriptet de andre modusene før det går ned i hastighet. '
        'Dette skjer bare så lenge ingen modus har virket ennå. Når en modus har flyttet brikker, beholdes den resten av '
        'løsingen, og også neste gang du trykker Solve på samme side. Skriptets egne panellyttere regnes ikke med.')
    K.p('Valgt modus skrives til nettleserkonsollen som «<i>[Automagic Solver] input mode: pointer</i>» (eller <i>mouse</i> / <i>native</i>). '
        'Zoomknappen finnes via id, etikett eller et alene-stående «−», og trykkes først via kjente lyttere og deretter med vanlige '
        'nettleserhendelser. Musehjulet brukes ikke, fordi det kan flytte brettet i stedet for å zoome.')

    K.h1('5. Hastighetsnivåer')
    K.p('Skriptet starter på raskeste nivå og går automatisk ned ett nivå dersom drag gjentatte ganger ikke flytter noe. '
        'Panelet viser da «<i>Switching to speed level …</i>».')
    K.table([['Nivå', 'Metode', 'Typisk tid per drag'],
             ['0', 'Hele draget sendes i én synkron serie (ned, én bevegelse, opp). Ventetiden etterpå tilpasses spillet, se under.', 'ca. 2–25 ms'],
             ['1', 'Én skjermoppdatering (animation frame) mellom hver hendelse.', 'ca. 80–120 ms'],
             ['2', 'Den opprinnelige tidsstyrte metoden fra 1.4.1 (faste pauser).', 'ca. 170 ms +']],
            [16, 116, 38])
    K.h2('5.1 Ventemodus')
    K.p('På nivå 0 måler skriptet de første åtte dragene hvor lenge spillet trenger på å tegne resultatet, og '
        'velger deretter den raskeste ventemodusen som aldri gikk glipp av en endring:')
    K.table([['Ventemodus', 'Når den velges', 'Venting etter hvert drag'],
             [c('sync'), 'Spillet tegner brettet på nytt med en gang brikken slippes.', 'Ingen.'],
             [c('f1'), 'Spillet tegner på neste skjermoppdatering.', 'Én skjermoppdatering (ca. 17 ms ved 60 Hz).'],
             [c('full'), 'Spillet animerer brikkene over flere skjermoppdateringer.', 'Til ingenting beveger seg lenger.']],
            [28, 78, 64])
    K.p('Ser skriptet likevel en endring etter at det sluttet å vente (tre ganger), går det over til neste, tryggere '
        'modus. Valgt modus skrives til nettleserkonsollen som «<i>[Automagic Solver] wait mode: sync</i>». '
        'I en skjult fane faller ventingen tilbake til en 60 ms-tidtaker.')
    K.p('Målt på en testkopi av spillet med 300 brikker tok versjon 1.6.1 ca. 15 sekunder. Fra versjon 1.7.0 tar det '
        'ca. 1,4 sekunder når spillet tegner med en gang, og ca. 7 sekunder når det tegner på neste skjermoppdatering. '
        'Hvor raskt det går på jigidi.com, avhenger av hvordan spillet tegner og skjermens oppdateringsfrekvens.')

    K.h1('6. Innstillinger')
    K.code(f'Innstillingene sendes som et objekt til {c("__jas.solve()")}. Panelet bruker standardverdiene, men '
           'du kan kalle løseren direkte fra nettleserkonsollen:',
           "await __jas.solve({\n  level: 1,          // start på nivå 1 i stedet for 0\n  maxTries: 20,\n"
           "  log: console.log,\n});")
    K.table([['Innstilling', 'Standard', 'Betydning'],
             [c('level'), '0', 'Startnivå for hastighet (0–2).'],
             [c('wait'), "'cal'", f'Ventemodus på nivå 0: {c("cal")} (mål automatisk), {c("sync")}, {c("f1")} eller {c("full")}.'],
             [c('stepDelay'), '12', 'Pause i ms mellom hendelser på nivå 2.'],
             [c('moveSteps'), '5', 'Antall musebevegelser per drag på nivå 2 (nivå 0 bruker 1, nivå 1 bruker 2).'],
             [c('settle'), '60', 'Ekstra pause i ms etter slipp på nivå 2.'],
             [c('margin'), '20', 'Avstand i lerretspiksler fra brettkanten til målområdet.'],
             [c('maxTries'), '12', 'Maks antall forsøk per brikke per runde.'],
             [c('passes'), '2', 'Antall runder gjennom brikker som ikke er lagt.'],
             [c('log'), '–', 'Funksjon som mottar statusmeldinger.'],
             [c('stop'), '–', 'Funksjon som returnerer true når løseren skal stoppe.'],
             [c('onProgress'), '–', 'Kalles etter hver brikke med (plassert, totalt, ok).']],
            [32, 20, 118])
    K.p(f'Returverdien er et objekt: {c("{ placed, total, stopped, level, wait }")}, der {c("level")} er hastighetsnivået '
        f'og {c("wait")} ventemodusen løseren endte på.')

    K.h1('7. Feilmeldinger og feilsøking')
    K.table([['Melding / symptom', 'Årsak og løsning'],
             ['Loading puzzle… (ringen snurrer)', 'Brikkene er ikke tegnet ennå. Vent, eller last siden på nytt. Blir den stående, '
              'kjørte skriptet trolig ikke ved document-start – sjekk utvidelsens innstillinger. '
              'Slå også av andre Jigidi-skript (f.eks. «Bingo Solver»).'],
             ['Still loading…', 'Ikke alle brikker er registrert ennå. Vent litt og trykk Solve igjen.'],
             ['Puzzle not recognized', 'Fant ikke teksten «(kolonner × rader)», eller den stemmer ikke med antall brikker. '
              'Jigidi kan ha endret sidens oppsett.'],
             ['Puzzle too small', 'Puslespill med bare én rad eller kolonne støttes ikke.'],
             ['Game board not found', 'Fant ikke spillets lerret (canvas bredere enn 200 piksler).'],
             ['Switching to speed level …', 'Ikke en feil: spillet trenger langsommere input, og skriptet tilpasser seg.'],
             ["The game ignores the solver's input", 'Åtte drag på rad på laveste hastighet flyttet ingenting, så skriptet '
              'stoppet i stedet for å prøve i det uendelige. Jigidi har trolig endret hvordan spillet tar imot input. '
              'Se nettleserkonsollen for valgt modus (avsnitt 4.4).'],
             ["The game ignores the solver's input – the script was injected too late", 'Brukerskript-utvidelsen lastet skriptet etter at '
              'spillet hadde startet, og spillet godtar ikke hendelser som ikke kommer fra en ekte mus. Last siden på nytt. Skjer det igjen: '
              'i Tampermonkey, sett Innstillinger → Konfigurasjonsmodus «Avansert» → Eksperimentelt → Injiseringsmodus til «Instant» (hvis tilgjengelig).'],
             ["The puzzle doesn't fit on the board", 'Skriptet fikk ikke zoomet ut nok. Trykk «−» i Jigidi til hele puslespillet får plass, og trykk Solve igjen.'],
             ['Could not move the assembled part onto the board', 'Den sammensatte delen ligger utenfor brettet og kunne ikke dras inn. '
              'Dra den inn selv og trykk Solve igjen.'],
             ['Panelet er gult etter løsing', 'Noen brikker ble ikke lagt, eller du stoppet løsingen. Trykk Solve igjen for å fortsette.'],
             ['Panelet vises ikke på iPad', f'Sjekk at Userscripts-utvidelsen har tilgang til jigidi.com, og at skriptet er slått på under '
              f'{c("&lt;/&gt;")}-ikonet. Last siden på nytt.'],
             ['Panelet er borte', f'Det kan ha havnet utenfor skjermen etter endring av vindusstørrelse. Slett {c("jas-ui")} i localStorage '
              'og last siden på nytt.'],
             ['Installasjonssiden viser «ikke funnet»', 'Utvidelsen kjører ikke skriptet på installasjonssiden (f.eks. Userscripts uten tilgang '
              'til github.io). Skriptet kan likevel være installert; sjekk versjonen i utvidelsen.'],
             ['Mange «FAILED»-brikker', 'Prøv ' + c("__jas.solve({ wait: 'full' })") + ' fra konsollen. Hjelper ikke det, prøv å starte på '
              'nivå 1 eller 2, eller øk maxTries. Sjekk også om brikkene er rotert – rotasjon støttes ikke.']],
            [52, 118])

    K.h1('8. Begrensninger')
    K.bullets([
        '<b>Rotasjon:</b> Puslespill med roterte brikker støttes ikke.',
        '<b>Avhengig av Jigidis oppbygning:</b> Skriptet forutsetter at brikkene klippes i fasit-rekkefølge med 2D-canvas, '
        'at det finnes en zoomknapp («−») og at dimensjonene står som «(k × r)» på siden. '
        'Endrer Jigidi noe av dette, slutter skriptet å virke til det oppdateres.',
        '<b>WebGL / Web Workers:</b> Tegner Jigidi med WebGL eller OffscreenCanvas i en worker, ser krokene ingenting.',
        '<b>Oppdagelse:</b> Svært jevne, rettlinjede og raske drag skiller seg tydelig fra menneskelig bruk. '
        'Dersom Jigidi logger tidsbruk eller bevegelsesmønster på serveren, kan løsninger fra skriptet oppdages. '
        'Høyere hastighet gjør dette signalet tydeligere.',
        '<b>Bruksvilkår:</b> Bruk av automatisering kan være i strid med Jigidis vilkår. Brukeren er selv ansvarlig.',
    ])

    K.h1('9. Endringslogg')
    K.h2('Versjon 1.8.1')
    K.bullets([
        f'Nytt hjem: {REPO}. Automatiske oppdateringer kommer nå derfra.',
        f'Ny installasjonsside ({SITE}) med installer-/oppdater-knapp, versjonssjekk og dokumentasjon.',
        'Skriptet melder fra om installert versjon på installasjonssiden, og gjør ingenting annet der.',
        'Dokumentasjonen bygges fra én kilde til både PDF og nettside.',
    ])
    K.h2('Versjon 1.8.0')
    K.bullets([
        'Rettet: store puslespill stoppet midtveis. Zoom virket ikke på nyere Jigidi, så det ferdige puslespillet fikk ikke plass, '
        'og brikker skulle legges utenfor brettet.',
        'Zoomknappen finnes nå også uten kjent id, og trykkes med vanlige nettleserhendelser når lytterne er ukjente.',
        'Fjernet musehjul som zoom-reserve; det kunne flytte hele brettet.',
        'Sjekker før start at puslespillet får plass, og gir en tydelig melding hvis ikke.',
        'Bygger videre på en allerede sammensatt del, og flytter den inn på brettet om nødvendig (etter å ha ryddet plassen).',
        'Testet på iPad med Safari, og på kopi av spillet med 594 brikker (27 × 22) som må zoomes ut: ferdig på ca. 7 sekunder.',
    ])
    K.h2('Versjon 1.7.2')
    K.bullets([
        "Rettet: løsingen kunne stoppe midtveis med «The game ignores the solver's input». Etter noen tilfeldige drag "
        'uten effekt byttet skriptet bort fra en inndatamodus som virket, og kom aldri tilbake til den.',
        'En modus som har flyttet brikker, beholdes nå resten av løsingen og ved neste Solve på samme side.',
    ])
    K.h2('Versjon 1.7.1')
    K.bullets([
        "Rettet: «The game ignores the solver's input» når skriptet ikke fanget opp spillets lyttere. Skriptets egne "
        'panellyttere ble feilaktig tolket som spillets, slik at feil modus ble valgt.',
        'Ny modus «native» som sender ekte hendelser med dispatchEvent når spillets lyttere er ukjente.',
        'Støtte for håndterere satt som egenskaper (onpointerdown = …).',
        'Kroker også i iframes, så en «ren» addEventListener fra en iframe ikke omgår skriptet.',
        'Prøver de andre modusene automatisk før hastigheten senkes.',
        'Varsel i konsollen når skriptet er lastet for sent.',
    ])
    K.h2('Versjon 1.7.0')
    K.bullets([
        'Adaptiv ventemodus (sync / f1 / full): skriptet måler hvor raskt spillet tegner, og venter ikke lenger enn nødvendig.',
        'Automatisk nedgradering til tryggere ventemodus hvis en endring dukker opp for sent.',
        'Rydding skjer rett før hver brikke legges i stedet for på forhånd. Løse brikker som kan legges, legges direkte i stedet for å parkeres først.',
        'Én musebevegelse per drag på nivå 0 (før 2).',
        'Ny innstilling: wait.',
        'Målt på testkopi med 300 brikker: fra ca. 15 s til ca. 1,4 s (spill som tegner med en gang) eller ca. 7 s (spill som tegner på neste skjermoppdatering).',
    ])
    K.h2('Versjon 1.6.1')
    K.bullets([
        'Støtte for Jigidi-varianter som bare bruker pekerhendelser. Rettet en feil der skriptet hang på enkelte PC-er.',
        'Automatisk valg av inndatamodus (mouse eller pointer) ved hver løsing.',
        'Etterligning av pekerfangst (setPointerCapture) for skriptets egne hendelser.',
        'Skriptet stopper med en tydelig feilmelding når spillet ikke reagerer, i stedet for å prøve i det uendelige.',
    ])
    K.h2('Versjon 1.6.0')
    K.bullets([
        'Nytt navn: <b>Jigidi Automagic Solver</b> (tidligere Jigidi Auto Solver).',
        'Nytt kompakt kontrollpanel: fremdriftsring, tidsanslag og brikker per sekund underveis.',
        'Fargekodet status (grønn, gul, rød) og hake når puslespillet er ferdig.',
        'Panelet kan flyttes og minimeres. Plassering og tilstand huskes.',
        'Esc stopper løsingen.',
        'Panelet ligger i Shadow DOM og påvirkes ikke av Jigidis stilark.',
    ])
    K.h2('Versjon 1.5.0')
    K.bullets([
        'Adaptiv venting etter hvert drag (skjermoppdatering + bevegelsesdeteksjon) i stedet for faste pauser.',
        'Tre hastighetsnivåer med automatisk nedtrapping.',
        'Smart valg av ankerbrikke som lar puslespillet bygges der det allerede ligger færrest løse brikker.',
        'Gripepunkt i brikkens midte, med unngåelse av brikker som ligger over.',
        'Bredde-først-rekkefølge utover fra ankeret.',
        'Mellomlagring av spillets lerret og hendelseslyttere; sjeldnere statusoppdateringer.',
        'Zoom venter på at brettet står stille i stedet for fast 600 ms.',
    ])
    K.h2('Versjon 1.4.1')
    K.p('Utgangspunktet: «Jigidi Auto Solver» av WorlockM, med fast tidsstyrte drag og byggeområde øverst til venstre.')
