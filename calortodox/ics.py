"""Scriitor minimal de fisiere iCalendar (RFC 5545) pentru evenimente de o zi."""
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, NamedTuple, Optional


class Event(NamedTuple):
    day: date                  # prima zi
    key: str                   # identificator stabil (pentru UID)
    summary: str
    description: str = ""
    categories: str = ""
    end: Optional[date] = None  # ultima zi inclusiv (implicit aceeasi zi)


def escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\n").replace("\n", "\\n"))


def fold(line: str) -> str:
    """Imparte linia la maximum 75 de octeti, fara sa taie caractere UTF-8."""
    out, cur, size = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        limit = 75 if not out else 74   # continuarile incep cu un spatiu
        if size + n > limit:
            out.append(cur)
            cur, size = "", 0
        cur += ch
        size += n
    out.append(cur)
    return "\r\n ".join(out)


def build_ics(events: Iterable[Event], name: str, description: str = "",
              now: Optional[datetime] = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//calendar-ortodox//RO",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape(name)}",
        "X-WR-TIMEZONE:Europe/Bucharest",
    ]
    if description:
        lines.append(f"X-WR-CALDESC:{escape(description)}")
    for ev in sorted(events, key=lambda e: (e.day, e.key)):
        last = ev.end or ev.day
        lines += [
            "BEGIN:VEVENT",
            f"UID:{ev.day:%Y%m%d}-{ev.key}@calendar-ortodox",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{ev.day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{last + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{escape(ev.summary)}",
        ]
        if ev.description:
            lines.append(f"DESCRIPTION:{escape(ev.description)}")
        if ev.categories:
            lines.append(f"CATEGORIES:{escape(ev.categories)}")
        lines += ["TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"
