from datetime import date

import pytest

from calortodox.pascha import movable_dates, orthodox_easter

KNOWN = {  # Pastele ortodox (surse: calendare oficiale)
    2020: date(2020, 4, 19), 2021: date(2021, 5, 2), 2022: date(2022, 4, 24),
    2023: date(2023, 4, 16), 2024: date(2024, 5, 5), 2025: date(2025, 4, 20),
    2026: date(2026, 4, 12), 2027: date(2027, 5, 2), 2028: date(2028, 4, 16),
    2029: date(2029, 4, 8), 2030: date(2030, 4, 28),
}


@pytest.mark.parametrize("year,expected", KNOWN.items())
def test_easter(year, expected):
    assert orthodox_easter(year) == expected
    assert expected.weekday() == 6   # duminica


def test_range():
    with pytest.raises(ValueError):
        orthodox_easter(1850)


def test_movable_2027():
    m = movable_dates(2027)
    assert m["inceput_postul_pastelui"] == date(2027, 3, 15)
    assert m["lasatul_secului_carne"] == date(2027, 3, 7)
    assert m["mosii_de_iarna"] == date(2027, 3, 6)
    assert m["floriile"] == date(2027, 4, 25)
    assert m["inaltarea"] == date(2027, 6, 10)
    assert m["rusalii"] == date(2027, 6, 20)
    assert m["mosii_de_vara"] == date(2027, 6, 19)
    assert m["inceput_postul_apostolilor"] == date(2027, 6, 28)


@pytest.mark.parametrize("year", range(1990, 2100))
def test_weekdays(year):
    m = movable_dates(year)
    assert m["lasatul_secului_carne"].weekday() == 6
    assert m["lasatul_secului_branza"].weekday() == 6
    assert m["inceput_postul_pastelui"].weekday() == 0
    assert m["floriile"].weekday() == 6
    assert m["inaltarea"].weekday() == 3
    assert m["rusalii"].weekday() == 6
    assert m["mosii_de_iarna"].weekday() == 5 and m["mosii_de_vara"].weekday() == 5
