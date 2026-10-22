# Cum poți contribui

Orice corectură este binevenită, mai ales la date (cruci, nume, tradiții).

## Configurare

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m calortodox build -o dist   # regenerează fișierele .ics
```

După orice schimbare în `data/` sau în `calortodox/`, rulează `build` și include în commit
fișierele din `dist/`. CI-ul verifică asta.

## Ce poți corecta

| Vrei să corectezi | Unde |
|---|---|
| Un obicei, o tradiție, o semnificație sau numele sărbătoriților | `data/traditions.json` |
| Un nume de sfânt sau o cruce greșită în sursă | `data/overrides.json` (cu motivul) |
| Un cuvânt fără diacritice | `data/diacritics.json` |
| Calculul Paștelui sau al posturilor | `calortodox/pascha.py` + test în `tests/` |

## Reguli pentru date

- O sărbătoare cu cruce roșie nu se adaugă sau scoate fără o sursă verificabilă (calendarul
  oficial al Bisericii Ortodoxe Române). Pune sursa în descrierea PR-ului.
- Textele de tradiții trebuie să fie scurte și verificabile. Nu include superstiții prezentate
  ca învățătură a Bisericii: separă clar „obiceiul popular” de rânduiala bisericească.
- Folosește diacritice corecte (ș, ț cu virgulă, nu cu sedilă).

## Extinderea datelor

Varianta detaliată (nume de sfinți pentru fiecare zi) vine din `data/days.csv`, extras din PDF-urile
lunare de pe crestinortodox.ro cu `scripts/extract_from_pdf.py`:

```bash
pip install -e ".[extract]"
python scripts/extract_from_pdf.py folder_cu_pdf-uri -o data/days.csv
```

Sursa are uneori etichete de sărbători mobile din alt an pe date fixe. Verifică rezultatul și
adaugă corecturile în `data/overrides.json`.
