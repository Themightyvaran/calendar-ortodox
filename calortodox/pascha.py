"""Calculul Pastelui ortodox si al sarbatorilor si posturilor mobile.

Pastele se calculeaza cu algoritmul lui Meeus pentru calendarul iulian, apoi
data se converteste in calendarul gregorian (+13 zile in 1900-2099).
Calendarul folosit in Romania este stil nou (revizuit) pentru sarbatorile fixe
si iulian pentru Paste si sarbatorile legate de el.
"""
from datetime import date, timedelta


def orthodox_easter(year: int) -> date:
    """Pastele ortodox in calendarul gregorian, pentru anii 1900-2099."""
    if not 1900 <= year <= 2099:
        raise ValueError("Algoritmul este valabil pentru anii 1900-2099")
    a = year % 4
    b = year % 7
    c = year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = (d + e + 114) % 31 + 1
    return date(year, month, day) + timedelta(days=13)


def movable_dates(year: int) -> dict:
    """Dictionar {cheie: data} cu sarbatorile si posturile mobile ale anului."""
    p = orthodox_easter(year)
    rusalii = p + timedelta(days=49)
    # Postul Sfintilor Apostoli: de luni dupa Duminica Tuturor Sfintilor, pana pe 28 iunie
    all_saints = rusalii + timedelta(days=7)
    apostles_start = all_saints + timedelta(days=1)
    return {
        "pascha": p,
        "lasatul_secului_branza": p - timedelta(days=49),    # duminica, seara se incepe Postul Mare
        "inceput_postul_pastelui": p - timedelta(days=48),   # lunea curata
        "sambata_lui_lazar": p - timedelta(days=8),
        "floriile": p - timedelta(days=7),
        "joia_mare": p - timedelta(days=3),
        "vinerea_mare": p - timedelta(days=2),
        "sambata_mare": p - timedelta(days=1),
        "lasatul_secului_carne": p - timedelta(days=56),     # duminica
        "mosii_de_iarna": p - timedelta(days=57),            # sambata dinaintea lasatului de carne
        "inaltarea": p + timedelta(days=39),
        "rusalii": rusalii,
        "lunea_rusaliilor": rusalii + timedelta(days=1),
        "duminica_tuturor_sfintilor": all_saints,
        "inceput_postul_apostolilor": apostles_start,
        "sfarsit_postul_apostolilor": date(year, 6, 28),
        "mosii_de_vara": rusalii - timedelta(days=1),
        "inceput_postul_adormirii": date(year, 8, 1),
        "sfarsit_postul_adormirii": date(year, 8, 14),
        "inceput_postul_craciunului": date(year, 11, 15),
        "sfarsit_postul_craciunului": date(year, 12, 24),
    }
