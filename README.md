# Calendar ortodox pentru Google Calendar

Calendar ortodox românesc (stil nou) în trei variante, ca fișiere `.ics` gata de importat în
Google Calendar, Apple Calendar sau Outlook. Intervalul acoperit: **1 octombrie 2026 până la 31 ianuarie 2028**.

## Variantele

| Fișier | Conține | Evenimente |
|---|---|---|
| [`calendar-ortodox-1-cruci-rosii-si-posturi.ics`](dist/calendar-ortodox-1-cruci-rosii-si-posturi.ics) | Sărbătorile cu cruce roșie și începutul și sfârșitul celor patru posturi mari | 62 |
| [`calendar-ortodox-2-detaliat.ics`](dist/calendar-ortodox-2-detaliat.ics) | Fiecare zi: sfinți, cruce roșie sau neagră, citiri, glas, voscresnă, rânduiala zilei (post, dezlegări) | 488 |
| [`calendar-ortodox-3-cruci-rosii-cu-traditii.ics`](dist/calendar-ortodox-3-cruci-rosii-cu-traditii.ics) | Sărbătorile cu cruce roșie, cu semnificație, obiceiuri și tradiții, cei care își sărbătoresc ziua | 53 |

Crucea roșie apare în titlu ca **✝**, cea neagră (doar în varianta 2) ca **†**.
Posturile mari: Postul Mare (Paștelui), Postul Sfinților Apostoli, Postul Adormirii, Postul Crăciunului.

## Import în Google Calendar

Importul se face de pe computer (aplicația de telefon nu are această opțiune).

1. Descarcă fișierul dorit din folderul [`dist/`](dist/).
2. În Google Calendar: **Altele > Creează calendar nou** (recomandat câte unul pentru fiecare variantă, ca să-l poți șterge ușor).
3. **Setări (roata) > Import și export > Import**, alege fișierul `.ics` și calendarul creat la pasul 2.

Reimportul aceluiași fișier nu dublează evenimentele: fiecare are un identificator stabil (UID).

## Regenerare și perpetuitate

```bash
pip install -e ".[dev]"
python -m calortodox build -o dist                                   # intervalul implicit
python -m calortodox build --start 2030-01-01 --end 2031-12-31 -o out  # alt interval
```

Variantele 1 și 3 se **calculează** pentru orice an între 1900 și 2099: Paștele ortodox (algoritmul
lui Meeus) și toate sărbătorile și posturile care depind de el. Varianta 2 (nume de sfinți pe zile)
există doar pentru zilele din `data/days.csv`. Pentru alți ani vezi [CONTRIBUTING.md](CONTRIBUTING.md).

## Structura proiectului

```
calortodox/     codul: calculul Paștelui (pascha.py), evenimentele (events.py), scriitorul .ics (ics.py)
data/           days.csv (zilele extrase), traditions.json (sărbători cu cruce roșie și tradiții),
                overrides.json (corecturi la sursă, cu motiv), diacritics.json
scripts/        extract_from_pdf.py (PDF lunar > days.csv)
dist/           fișierele .ics gata de importat
tests/          teste (pytest)
```

## Sursa datelor și corectitudine

Numele sfinților, crucile, citirile și rânduiala zilei sunt extrase din calendarele lunare PDF de pe
[crestinortodox.ro](https://www.crestinortodox.ro/). PDF-urile nu sunt incluse în depozit.

Sursa are pe unele date fixe etichete de sărbători mobile din alt an (de exemplu „Floriile” pe 5 aprilie
2027, când Floriile sunt pe 25 aprilie) și unele cruci roșii greșite. Corecturile sunt documentate, una
câte una, în [`data/overrides.json`](data/overrides.json). Sărbătorile și posturile mobile sunt calculate
în cod, iar un test compară regulile cu sursa corectată.

Verifică întotdeauna datele importante (de exemplu zilele libere legale) în calendarul oficial al Bisericii
Ortodoxe Române și în actele normative. Textele de obiceiuri și tradiții din varianta 3 sunt scrise pentru
acest proiect și redau datini populare, nu învățătură de credință. Corecturile sunt binevenite.

## Licență

[MIT](LICENSE) pentru cod și texte.
