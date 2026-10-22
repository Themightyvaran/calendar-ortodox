"""Linie de comanda: python -m calortodox build [--from AN --to AN] [-o dist]"""
import argparse
from datetime import date, datetime, timezone
from pathlib import Path

from . import __version__
from .events import load_days, variant1, variant2, variant3
from .ics import build_ics

RELEASE_STAMP = datetime(2026, 10, 22, tzinfo=timezone.utc)   # DTSTAMP fix: fisiere reproductibile
DEFAULT_START, DEFAULT_END = date(2026, 10, 1), date(2028, 1, 31)   # intervalul din data/days.csv

DESC = "Calendar ortodox (stil nou, Biserica Ortodoxă Română). Sursa datelor: crestinortodox.ro."


def build(start, end, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    years = range(start.year, end.year + 1)
    days = {d: r for d, r in load_days().items() if start <= d <= end}
    inside = lambda evs: [e for e in evs if start <= e.day <= end]
    files = {
        "calendar-ortodox-1-cruci-rosii-si-posturi.ics": (
            "Calendar ortodox: cruci roșii și posturi", inside(variant1(years))),
        "calendar-ortodox-2-detaliat.ics": (
            "Calendar ortodox: detaliat", variant2(days)),
        "calendar-ortodox-3-cruci-rosii-cu-traditii.ics": (
            "Calendar ortodox: cruci roșii cu tradiții", inside(variant3(years))),
    }
    for name, (title, events) in files.items():
        text = build_ics(events, title, DESC, now=RELEASE_STAMP)
        (out / name).write_text(text, encoding="utf-8", newline="")
        print(f"{name}: {len(events)} evenimente")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="calortodox", description=__doc__)
    ap.add_argument("command", choices=["build"])
    ap.add_argument("--start", type=date.fromisoformat, default=DEFAULT_START,
                    help="prima zi, AAAA-LL-ZZ (implicit 2026-10-01)")
    ap.add_argument("--end", type=date.fromisoformat, default=DEFAULT_END,
                    help="ultima zi, AAAA-LL-ZZ (implicit 2028-01-31). Varianta 2 exista doar "
                         "pentru zilele din data/days.csv; variantele 1 si 3 se calculeaza pentru orice an 1900-2099")
    ap.add_argument("-o", "--output", default="dist")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)
    build(args.start, args.end, args.output)
