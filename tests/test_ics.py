from datetime import date, datetime, timezone

from calortodox.ics import Event, build_ics, escape, fold

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_escape():
    assert escape("a,b;c\nd\\") == r"a\,b\;c\nd\\"


def test_fold_keeps_utf8_and_length():
    line = "SUMMARY:" + "ăîșț✝" * 40
    folded = fold(line)
    parts = folded.split("\r\n")
    assert all(len(p.encode("utf-8")) <= 75 for p in parts)
    assert "".join([parts[0]] + [p[1:] for p in parts[1:]]) == line


def test_structure():
    text = build_ics([Event(date(2026, 12, 25), "craciun", "✝ Crăciun", "Hristos", "x")],
                     "Test", now=NOW)
    assert text.startswith("BEGIN:VCALENDAR\r\n") and text.endswith("END:VCALENDAR\r\n")
    assert "DTSTART;VALUE=DATE:20261225" in text
    assert "DTEND;VALUE=DATE:20261226" in text
    assert "UID:20261225-craciun@calendar-ortodox" in text
    assert "DTSTAMP:20260101T000000Z" in text
    assert "\n" not in text.replace("\r\n", "")


def test_multi_day_end_is_exclusive():
    text = build_ics([Event(date(2026, 12, 30), "k", "s", end=date(2027, 1, 2))], "T", now=NOW)
    assert "DTEND;VALUE=DATE:20270103" in text
