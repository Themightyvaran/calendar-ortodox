#!/usr/bin/env python3
"""Extrage zilele din PDF-urile salvate de pe crestinortodox.ro in data/days.csv.

Folosire:
    python3 scripts/extract_from_pdf.py <folder_cu_pdf-uri> [-o data/days.csv]

Din fiecare PDF (o luna) se citesc: data, ziua saptamanii, tipul crucii
(rosie / neagra / fara), numele sfintilor, numele duminicii, glasul,
voscresna, citirile (text brut) si nota de post (Post, Dezlegare la peste etc.).
Culoarea crucii se citeste din culoarea textului din PDF.
"""
import argparse
import calendar
import csv
import re
import sys
from pathlib import Path

import pdfplumber

MONTHS = {
    "Ianuarie": 1, "Februarie": 2, "Martie": 3, "Aprilie": 4, "Mai": 5,
    "Iunie": 6, "Iulie": 7, "August": 8, "Septembrie": 9, "Octombrie": 10,
    "Noiembrie": 11, "Decembrie": 12,
}
WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"]  # luni=0


def is_red(col):
    return col is not None and len(col) == 3 and col[0] > 0.9 and col[1] < 0.15 and col[2] < 0.15


def month_from_name(name):
    m = re.search(r"Calendar_ortodox_(\d{4})_-_([A-Za-z]+)___", name)
    if m:
        return int(m.group(1)), MONTHS[m.group(2)]
    # pagina principala (luna curenta a site-ului, octombrie 2026)
    if name.startswith("Calendar_Ortodox_2026_calendar_crestin"):
        return 2026, 10
    raise ValueError(f"Nu pot deduce luna din numele fisierului: {name}")


def group_lines(words, tol=2.5):
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        for ln in lines:
            if abs(ln["top"] - w["top"]) <= tol:
                ln["words"].append(w)
                break
        else:
            lines.append({"top": w["top"], "words": [w]})
    for ln in lines:
        ln["words"].sort(key=lambda w: w["x0"])
    return sorted(lines, key=lambda ln: ln["top"])


def extract_month(path, year, month):
    ndays = calendar.monthrange(year, month)[1]
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        all_words = page.extract_words(
            x_tolerance=1.5, y_tolerance=2, extra_attrs=["non_stroking_color", "size"]
        )
        rects = list(page.rects)
    side = [w for w in all_words if w["text"].startswith("Afiseaza")]
    sidebar_x = min(w["x0"] for w in side) if side else 10_000

    def sz(w, v):
        return abs(w["size"] - v) < 0.15

    body = [w for w in all_words if w["x0"] < sidebar_x - 4]
    # numerele zilelor: cifre (gri sau rosii) in coloana din stanga a tabelului
    digit_words = [w for w in body if sz(w, 6.0) and re.fullmatch(r"\d{1,2}", w["text"])
                   and w["non_stroking_color"] != (0.0, 0.0, 0.0)]
    singles = [round(w["x0"]) for w in digit_words if len(w["text"]) == 1]
    if not singles:
        raise RuntimeError(f"Nu am gasit numere de zile in {path}")
    x_mode = max(set(singles), key=singles.count)   # x al cifrelor 1..9
    head_limit = x_mode + 17       # sub aceasta limita: numar, litera zilei, cruce
    title_x = x_mode + 21          # de aici incep titlurile principale

    cand = [w for w in digit_words if abs(w["x0"] - x_mode) <= 4]
    cand.sort(key=lambda w: w["top"])
    day_rows, expect = [], 1
    for w in cand:
        if int(w["text"]) == expect:
            day_rows.append({"day": expect, "y": w["top"]})
            expect += 1
        if expect > ndays:
            break
    if len(day_rows) != ndays:
        raise RuntimeError(f"{path}: gasite {len(day_rows)} zile din {ndays}")

    for i, r in enumerate(day_rows):
        r["lo"] = r["y"] - 6
        if i + 1 < len(day_rows):
            r["hi"] = day_rows[i + 1]["y"] - 6
    last = day_rows[-1]
    wd_last = calendar.weekday(year, month, ndays)
    last["hi"] = last["y"] + (32 if wd_last == 6 else 10)

    table_top, table_bottom = day_rows[0]["lo"], last["hi"]

    def row_of_y(y):
        for r in day_rows:
            if r["lo"] <= y < r["hi"]:
                return r
        return None

    out = {r["day"]: {"main": [], "sub": [], "note": [], "head": []} for r in day_rows}
    note_words = []

    for w in body:
        if not (table_top <= w["top"] < table_bottom):
            continue
        if sz(w, 5.5):
            # nota de post: aliniata pe verticala cu numarul zilei
            if w["x0"] > title_x:
                note_words.append(w)
            continue
        if not sz(w, 6.0):
            continue
        r = row_of_y(w["top"])
        if r is None:
            continue
        near_number_line = abs(w["top"] - r["y"]) <= 3.0 and w["x0"] < head_limit + 1
        if near_number_line:
            out[r["day"]]["head"].append(w)
        else:
            out[r["day"]]["sub" if w["x0"] < title_x - 2 and w["x0"] < head_limit + 1 else "main"].append(w)

    # Notele de post stau in celule albe (dreptunghiuri) care pot acoperi mai multe
    # zile la rand (ex. "Post" pentru joi+vineri, sau "Dezlegare la peste" pentru
    # sambata+duminica). Gasim celula fiecarui cuvant-nota si atribuim textul
    # tuturor zilelor acoperite de celula.
    def is_white(col):
        return col is not None and len(col) == 3 and min(col) > 0.98

    cells = [r for r in rects if is_white(r.get("non_stroking_color"))
             and 20 < (r["x1"] - r["x0"]) < 60 and r["x0"] > title_x + 200
             and r["x1"] < sidebar_x and r["height"] >= 8
             and table_top - 3 <= r["top"] < table_bottom]
    by_cell = {}
    for w in note_words:
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        inside = [c for c in cells if c["x0"] - 1 <= cx <= c["x1"] + 1 and c["top"] - 1 <= cy <= c["bottom"] + 1]
        if inside:
            c = min(inside, key=lambda c: (c["x1"] - c["x0"]) * c["height"])
            by_cell.setdefault((round(c["top"], 1), round(c["bottom"], 1)), []).append(w)
        else:  # fara celula: cea mai apropiata zi
            near = min(day_rows, key=lambda r: abs(r["y"] + 3 - cy))
            out[near["day"]]["note"].append(w)
    for (top, bottom), words in by_cell.items():
        covered = [r for r in day_rows if top - 1 <= r["y"] + 3 <= bottom + 1]
        if not covered:
            covered = [min(day_rows, key=lambda r: abs(r["y"] + 3 - (top + bottom) / 2))]
        for r in covered:
            out[r["day"]]["note"].extend(words)

    # linii care incep sub title_x (subtitluri de duminica) vs titluri principale
    results = []
    for r in day_rows:
        d = r["day"]
        data = out[d]
        head_txt = " ".join(w["text"] for w in data["head"])
        cross = None
        for w in data["head"]:
            if "†" in w["text"]:
                if w["text"] == "†" or w["text"].endswith("†"):
                    cross = "rosie" if is_red(w["non_stroking_color"]) else "neagra"
        weekday = WEEKDAYS[calendar.weekday(year, month, d)]

        lines = group_lines(data["main"] + data["sub"])
        main_parts, sub_parts, main_red = [], [], []
        for ln in lines:
            first_x = ln["words"][0]["x0"]
            txt = " ".join(w["text"] for w in ln["words"])
            red = all(is_red(w["non_stroking_color"]) for w in ln["words"])
            if first_x < title_x - 2:
                sub_parts.append(txt)
            else:
                main_parts.append(txt)
                main_red.append(red)
        notes = sorted(data["note"], key=lambda w: (round(w["top"]), w["x0"]))
        note_txt = " ".join(w["text"] for w in notes)
        note_red = any(is_red(w["non_stroking_color"]) for w in notes)

        results.append({
            "date": f"{year:04d}-{month:02d}-{d:02d}",
            "weekday": weekday,
            "cross": cross or "",
            "title_red": int(bool(main_red) and all(main_red)),
            "title": " ".join(main_parts).strip(),
            "sub": " | ".join(sub_parts).strip(),
            "note": note_txt.strip(),
            "note_red": int(note_red),
            "head_check": head_txt,
        })
    return results


def split_title(title):
    """Desparte 'nume sfinti - Ap. ... Ev. ... glas X, voscr. Y' in (nume, citiri, glas, voscr)."""
    glas = voscr = ""
    m = re.search(r"glas\s+(\d+),\s*voscr\.\s*(\d+)", title)
    if m:
        glas, voscr = m.group(1), m.group(2)
    name, readings = title, ""
    m2 = re.search(r"\s-\s(Ap\.\s.*)$", title)
    if m2:
        name = title[: m2.start()].strip()
        readings = m2.group(1).strip()
    return name, readings, glas, voscr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_dir")
    ap.add_argument("-o", "--output", default="data/days.csv")
    args = ap.parse_args()

    files = sorted(Path(args.pdf_dir).glob("*.pdf"))
    rows = []
    for f in files:
        year, month = month_from_name(f.name)
        rows.extend(extract_month(f, year, month))
        print(f"{year}-{month:02d}: ok ({f.name[:50]})", file=sys.stderr)
    rows.sort(key=lambda r: r["date"])

    # un singur rand per data
    seen = {}
    for r in rows:
        seen[r["date"]] = r
    rows = [seen[k] for k in sorted(seen)]

    fields = ["date", "weekday", "cross", "title_red", "name", "sunday_name", "readings",
              "glas", "voscr", "note", "note_red"]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        for r in rows:
            name, readings, glas, voscr = split_title(r["title"])
            sunday_name = ""
            if r["sub"]:
                sub_lines = [s.strip() for s in r["sub"].split("|")]
                body = [s for s in sub_lines if not s.startswith("Duminica nr")]
                sunday_name = split_title(" ".join(body))[0] if body else ""
                if not readings and body:
                    _, rd, g2, v2 = split_title(" ".join(body))
                    readings, glas, voscr = rd, glas or g2, voscr or v2
            wr.writerow({
                "date": r["date"], "weekday": r["weekday"], "cross": r["cross"],
                "title_red": r["title_red"], "name": name, "sunday_name": sunday_name,
                "readings": readings, "glas": glas, "voscr": voscr,
                "note": r["note"], "note_red": r["note_red"],
            })
    print(f"Scrise {len(rows)} zile in {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
