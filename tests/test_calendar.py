import re
from datetime import date, timedelta

import pytest

from calortodox.events import (clean_readings, fasts, load_days, load_feasts,
                               red_feast_days, restore_diacritics, variant1,
                               variant2, variant3)

START, END = date(2026, 10, 1), date(2028, 1, 31)


@pytest.fixture(scope="module")
def days():
    return load_days()


def test_data_is_continuous(days):
    expected = [START + timedelta(n) for n in range((END - START).days + 1)]
    assert sorted(days) == expected


def test_every_day_has_name(days):
    assert all(r["name"].strip() for r in days.values())


def test_diacritics_applied(days):
    text = " ".join(r["name"] for r in days.values())
    assert not re.search(r"\bSfantul\b|\bSfintii\b|\bCraciun", text)
    assert restore_diacritics("Sfantul Apostol loan") == "Sfântul Apostol Ioan"
    assert restore_diacritics("Buna Vestire") == "Buna Vestire"   # nu 'Bună'


def test_rules_match_source_red_crosses(days):
    """Regulile (fixe + calculate) trebuie sa dea aceleasi cruci rosii ca sursa corectata.

    Singurele diferente permise sunt sarbatorile mobile din 2027, pe care sursa le
    are gresit (etichete din alt an) si le calculam din data Pastelui."""
    src = {d for d, r in days.items() if r["cross"] == "rosie"}
    rules = {d for y in (2026, 2027, 2028) for d, _, _ in red_feast_days(y) if START <= d <= END}
    assert src - rules == set()
    mobile_2027 = {date(2027, 4, 25), date(2027, 4, 30), date(2027, 5, 2), date(2027, 5, 3),
                   date(2027, 5, 4), date(2027, 5, 7), date(2027, 6, 10), date(2027, 6, 20),
                   date(2027, 6, 21)}
    assert rules - src == mobile_2027


def test_traditions_complete():
    for f in load_feasts():
        assert f["title"] and f["meaning"], f["id"]
        assert "fixed" in f["match"] or "pascha" in f["match"]


def test_fasts_2027():
    got = {f["key"]: (f["start"], f["end"]) for f in fasts(2027)}
    assert got["post-paste"] == (date(2027, 3, 15), date(2027, 5, 1))
    assert got["post-apostoli"] == (date(2027, 6, 28), date(2027, 6, 28))
    assert got["post-adormire"] == (date(2027, 8, 1), date(2027, 8, 14))
    assert got["post-craciun"] == (date(2027, 11, 15), date(2027, 12, 24))


def test_variants_sizes_and_uids(days):
    years = range(2026, 2029)
    v1, v3, v2 = variant1(years), variant3(years), variant2(days)
    assert len(v2) == len(days)
    for evs in (v1, v2, v3):
        uids = [(e.day, e.key) for e in evs]
        assert len(uids) == len(set(uids))
    assert {e.day for e in v3} <= {e.day for e in v1}


def test_v3_has_customs_for_main_feasts():
    by_day = {e.day: e for e in variant3([2027])}
    assert "Obiceiuri" in by_day[date(2027, 12, 25)].description
    assert "colind" in by_day[date(2027, 12, 25)].description.lower()
    assert "Hristos a înviat" in by_day[date(2027, 5, 2)].description


def test_perpetual_other_years():
    from calortodox.pascha import orthodox_easter
    easter = orthodox_easter(2035)
    days_2035 = {e.day: e for e in variant1([2035])}
    assert "Învierea Domnului" in days_2035[easter].summary
    assert len(days_2035) >= 40


def test_clean_readings():
    raw = "Ap. II Corinteni XI, 31-33XII, 1-9Ev. Luca VI, 31- 36glas 1, voscr. 7"
    assert clean_readings(raw) == "Ap. II Corinteni XI, 31-33; XII, 1-9; Ev. Luca VI, 31-36"
