"""Construieste evenimentele celor trei variante de calendar."""
import csv
import json
import re
from datetime import date, timedelta
from pathlib import Path

from .ics import Event
from .pascha import movable_dates

DATA = Path(__file__).resolve().parent.parent / "data"

RED = "✝"      # ✝ cruce rosie
BLACK = "†"    # † cruce neagra


def _json(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- diacritice
_DIA = None


def restore_diacritics(text: str) -> str:
    """Pune diacriticele corecte, cuvant cu cuvant (sursa nu are diacritice)."""
    global _DIA
    if _DIA is None:
        _DIA = _json("diacritics.json")
    words, ocr = _DIA["words"], _DIA["ocr_fixes"]

    def fix(m):
        w = m.group(0)
        if w.lower() in ocr:        # greseli de recunoastere (l in loc de I)
            return ocr[w.lower()]
        low = w.lower()
        new = words.get(low, low)
        if w.isupper() and len(w) > 1:
            return new.upper()
        if w[0].isupper():
            return new[0].upper() + new[1:]
        return new

    return re.sub(r"[A-Za-z]+", fix, text)


def clean_readings(text: str) -> str:
    """Face citirile biblice lizibile ('...33XII, 1-9Ev. Luca...' -> '...33; XII, 1-9; Ev. Luca...')."""
    text = re.sub(r"\s*glas\s+\d+,\s*voscr\.\s*\d+\s*$", "", text)
    text = re.sub(r"(?<=\d)(?=Ev\.)", "; ", text)
    text = re.sub(r"(?<=\d)(?=[IVXL]+,\s)", "; ", text)
    text = re.sub(r"(?<=\d)(?=[A-Z][a-zăâîșț]+\s[IVXL]+,)", "; ", text)
    return re.sub(r"(\d)-\s+(\d)", r"\1-\2", text).strip()


# --------------------------------------------------------------- date sursa
def load_days() -> dict:
    """Zilele din data/days.csv cu corectiile din data/overrides.json aplicate."""
    ov = _json("overrides.json")
    name_fixes = {f["date"]: f for f in ov["name_fixes"]}
    cross_fixes = {f["date"]: f["cross"] for f in ov.get("cross_fixes", [])}
    days = {}
    with open(DATA / "days.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            d = date.fromisoformat(r["date"])
            if r["date"] in name_fixes:
                fx = name_fixes[r["date"]]
                r["name"] = fx["name"]
                if "cross" in fx:
                    r["cross"] = fx["cross"]
            if r["date"] in cross_fixes:
                r["cross"] = cross_fixes[r["date"]]
            r["name"] = restore_diacritics(r["name"])
            sunday = restore_diacritics(r["sunday_name"])
            r["sunday_name"] = "" if sunday.startswith("Predica") else sunday   # titlu de predica, nu nume de duminica
            r["readings"] = clean_readings(r["readings"])
            r["note"] = restore_diacritics(r["note"])
            days[d] = r
    return days


# -------------------------------------------------------------- sarbatori
def load_feasts() -> list:
    return _json("traditions.json")["feasts"]


def red_feast_days(year: int) -> list:
    """Sarbatorile cu cruce rosie dintr-un an: lista de (data, sarbatoare, index)."""
    mov = movable_dates(year)
    p = mov["pascha"]
    out = []
    for f in load_feasts():
        m = f["match"]
        if "fixed" in m:
            mm, dd = map(int, m["fixed"].split("-"))
            out.append((date(year, mm, dd), f, 0))
        else:
            for i, off in enumerate(m["pascha"]):
                out.append((p + timedelta(days=off), f, i))
    return sorted(out, key=lambda t: t[0])


def _pick(value, i):
    if isinstance(value, list):
        return value[i] if i < len(value) else False
    return bool(value)


def feast_title(f, i):
    return f["titles"][i] if "titles" in f and i < len(f["titles"]) else f["title"]


def feast_description(f, i, detailed):
    lines = []
    if detailed:
        lines.append(f["meaning"])
        if f.get("greeting"):
            lines.append("Salut: " + f["greeting"])
        if f.get("customs"):
            lines.append("")
            lines.append("Obiceiuri și tradiții:")
            lines += ["• " + c for c in f["customs"]]
        if f.get("names"):
            lines.append("")
            lines.append("La mulți ani celor care poartă numele: " + ", ".join(f["names"]) + ".")
        if _pick(f.get("legal", False), i):
            lines.append("")
            lines.append("Zi liberă legală în România (verifică lista oficială a anului).")
    else:
        lines.append(f["meaning"])
    return "\n".join(lines)


# ------------------------------------------------------------------ posturi
def fasts(year: int) -> list:
    """Cele patru posturi mari: lista de dict(key, name, start, end)."""
    m = movable_dates(year)
    out = [
        {"key": "post-paste", "name": "Postul Mare (Postul Paștelui)",
         "start": m["inceput_postul_pastelui"], "end": m["pascha"] - timedelta(days=1)},
        {"key": "post-adormire", "name": "Postul Adormirii Maicii Domnului",
         "start": m["inceput_postul_adormirii"], "end": m["sfarsit_postul_adormirii"]},
        {"key": "post-craciun", "name": "Postul Crăciunului",
         "start": m["inceput_postul_craciunului"], "end": m["sfarsit_postul_craciunului"]},
    ]
    if m["inceput_postul_apostolilor"] <= m["sfarsit_postul_apostolilor"]:
        out.append({"key": "post-apostoli", "name": "Postul Sfinților Apostoli Petru și Pavel",
                    "start": m["inceput_postul_apostolilor"], "end": m["sfarsit_postul_apostolilor"]})
    return sorted(out, key=lambda f: f["start"])


FAST_HINT = ("În post se evită carnea, laptele și ouăle. Dezlegările la pește, ulei și vin "
             "sunt trecute în varianta detaliată a calendarului.")


def fast_events(year: int) -> list:
    evs = []
    for f in fasts(year):
        n = (f["end"] - f["start"]).days + 1
        if n == 1:
            evs.append(Event(f["start"], f["key"] + "-zi", f"{f['name']} (o singură zi, {f['start']:%d.%m})",
                             f"{FAST_HINT}", "Post"))
            continue
        evs.append(Event(f["start"], f["key"] + "-start", f"Începe {f['name']}",
                         f"Durează până pe {f['end']:%d.%m.%Y} ({n} zile).\n{FAST_HINT}", "Post"))
        evs.append(Event(f["end"], f["key"] + "-sfarsit", f"Se încheie {f['name']}",
                         f"Ultima zi de post. {FAST_HINT}", "Post"))
    return evs


# ---------------------------------------------------------------- variante
def _feast_events(year, detailed):
    evs = []
    for d, f, i in red_feast_days(year):
        evs.append(Event(d, f"{f['id']}-{i}", f"{RED} {feast_title(f, i)}",
                         feast_description(f, i, detailed), "Sărbătoare cu cruce roșie"))
    return evs


def variant1(years) -> list:
    """Sarbatori cu cruce rosie + inceput si sfarsit de post."""
    evs = []
    for y in years:
        evs += _feast_events(y, detailed=False) + fast_events(y)
    return evs


def variant3(years) -> list:
    """Sarbatori cu cruce rosie, cu semnificatie, obiceiuri si traditii."""
    evs = []
    for y in years:
        evs += _feast_events(y, detailed=True)
    return evs


def _short(name: str, limit=90) -> str:
    parts = [p.strip() for p in name.split(";") if p.strip()]
    s = parts[0] if parts else name
    for p in parts[1:]:
        if len(s) + 2 + len(p) > limit:
            break
        s += "; " + p
    return s


MOVABLE_LABELS = [  # (cheie, eticheta) adaugate in varianta detaliata cand lipsesc din sursa
    ("lasatul_secului_carne", "Lăsatul secului pentru Postul Mare (carne)"),
    ("mosii_de_iarna", "Sâmbăta morților - Moșii de iarnă"),
    ("lasatul_secului_branza", "Lăsatul secului pentru Postul Mare (brânză)"),
    ("sambata_lui_lazar", "Sâmbăta lui Lazăr"),
    ("floriile", "Intrarea Domnului în Ierusalim (Floriile)"),
    ("joia_mare", "Joia Mare"),
    ("sambata_mare", "Sâmbăta Mare"),
    ("pascha", "Învierea Domnului (Sfintele Paști)"),
    ("rusalii", "Pogorârea Duhului Sfânt (Rusaliile)"),
    ("mosii_de_vara", "Sâmbăta morților - Moșii de vară"),
    ("duminica_tuturor_sfintilor", "Duminica Tuturor Sfinților"),
]
FIXED_LABELS = [  # (MM-DD, cheie, eticheta)
    ("11-14", "lasatul-craciun", "Lăsatul secului pentru Postul Crăciunului"),
]


def _has(label, text):
    norm = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("ă", "a").replace("â", "a")
                            .replace("î", "i").replace("ș", "s").replace("ț", "t"))
    key = " ".join(norm(label).split()[:2])
    return key in norm(text)


def variant2(days=None) -> list:
    """Varianta detaliata: fiecare zi din intervalul din data/days.csv."""
    days = days or load_days()
    years = sorted({d.year for d in days})
    extra = {}   # data -> lista de etichete mobile
    for y in range(years[0] - 1, years[-1] + 1):
        m = movable_dates(y)
        for k, label in MOVABLE_LABELS:
            extra.setdefault(m[k], []).append(label)
        for mmdd, _, label in FIXED_LABELS:
            mm, dd = map(int, mmdd.split("-"))
            extra.setdefault(date(y, mm, dd), []).append(label)
        for f in fast_events(y):
            extra.setdefault(f.day, []).append(f.summary)
    red = {d: (f, i) for y in years for d, f, i in red_feast_days(y)}

    evs = []
    for d, r in sorted(days.items()):
        labels = [l for l in extra.get(d, []) if not _has(l, r["name"])]
        cross = "rosie" if d in red else r["cross"]
        if cross == "rosie" and d not in red:
            cross = "neagra"      # cruce rosie neconfirmata de reguli
        mark = RED + " " if cross == "rosie" else (BLACK + " " if cross == "neagra" else "")
        parts = []
        if d in red:
            parts.append(feast_title(*[red[d][0], red[d][1]]))
        if r["sunday_name"]:
            parts.append(r["sunday_name"])
        parts += labels + [r["name"]]
        title_src = ""
        for part in parts:
            if not title_src or not _has(part, title_src):
                title_src += ("; " if title_src else "") + part
        desc = []
        if r["sunday_name"]:
            desc.append(r["sunday_name"])
        desc += labels
        desc.append(r["name"])
        if r["readings"]:
            desc.append("Citiri: " + r["readings"])
        if r["glas"]:
            desc.append(f"Glasul {r['glas']}, voscresna {r['voscr']}")
        if r["note"]:
            desc.append("Rânduială: " + r["note"])
        if d in red:
            f, i = red[d]
            desc.append("")
            desc.append(feast_description(f, i, detailed=False))
        evs.append(Event(d, "zi", mark + _short(title_src), "\n".join(desc),
                         {"rosie": "Cruce roșie", "neagra": "Cruce neagră"}.get(cross, "Zi")))
    return evs
