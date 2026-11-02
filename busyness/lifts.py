"""A lift's capacity and speed, from the best evidence it has (busyness-lift-estimates; docs/decisions/013).

Recorded values first, then seats (recorded, or read from the name), then the lift type's typical value. The name
patterns here are also what prototypes/lift_capacity.py fits its tables on, so the two can't drift apart.
"""

import re

from . import params as P

# Names in French (TSD/TSF), German (KSB, 6er-SB, Doppelsessel), Doppelmayr codes (CLD/CLF), Italian (-posto),
# Croatian/Bosnian (-sjed), Japanese (高速 high speed, ペア/ロマンス pair, トリプル, クワッド) and English.
FAST_RE = re.compile(r"express|xpress|high[ -]?speed|\btsd|\bcld|\bksb\b|kuppelbar|d[ée]bray|detach|\btcd|高速"
                     r"|super ?chair|\bsuper\b|bubble", re.I)
FIXED_RE = re.compile(r"\btsf|\bclf|\bfixed\b|\bfixe\b|\bdsb\b", re.I)
SEATS_RE = [(re.compile(p, re.I), n) for p, n in (
    (r"\bts[df]?\s?-?(\d)\b", None), (r"\b(\d)\s?er\b", None), (r"\b(\d)\s?-?(?:sb|ksb|clf|cld)\b", None),
    (r"\b(\d)[ -]?(?:seat|sitz|place|posti)", None), (r"(\d)人乗り", None), (r"\bsingle\b|monoposto", 1),
    (r"\b(?:double|pair|dsb)\b|doppel(?!mayr)|biposto|dvosjed|ペア|ロマンス|\bromance\b", 2),
    (r"\btriple\b|triposto|trosjed|トリプル", 3),
    (r"\bquad(?:ruple)?\b|\bvierer|quadriposto|četverosjed|cetverosjed|クワッド", 4),
    (r"\bsix(?:[ -]?pack)?\b|\bsechser|esaposto|šestosjed|sestosjed", 6))]


def name_hints(name: str | None) -> tuple[str | None, int | None]:
    """From a lift's name: 'fast', 'fixed' or None, and a seat count or None (TSD6, 4er, Quad, ...)."""
    name = name or ""
    speed = "fast" if FAST_RE.search(name) else "fixed" if FIXED_RE.search(name) else None
    for rx, n in SEATS_RE:
        if m := rx.search(name):
            return speed, n or int(m.group(1))
    return speed, None


def plausible_seats(seats, lift_type: str) -> bool:
    """Seats from 1 to the type's maximum: bigger values are usually the capacity typed into the seats tag."""
    return bool(seats) and 1 <= seats <= P.SEATS_MAX.get(lift_type, 2)


def seats(p: dict) -> tuple[int | None, str | None]:
    """A lift's seats and where they came from: 'seats' (recorded), 'name', or (None, None)."""
    if plausible_seats(p.get("occupancy"), p["liftType"]):
        return int(p["occupancy"]), "seats"
    n = name_hints(p.get("name"))[1]
    return (n, "name") if plausible_seats(n, p["liftType"]) else (None, None)


def _lookup(table: dict, seats: int, flag: bool):
    """A (seats, flag) cell, else the same seats' other cell: seats say more than the flag."""
    return table.get((seats, flag), table.get((seats, not flag)))


def estimate(p: dict, length: float) -> tuple[float, str, float, str]:
    """A lift's capacity (an hour) and speed (m/s), each with its source: 'recorded', 'seats', 'name' or 'type'.
    `p` is the lift's OpenSkiMap properties; `length` its length in metres."""
    t = p["liftType"]
    n, src = seats(p)
    if t == "cable_car" and n and n < P.CABLE_MIN_SEATS:
        t = "gondola"  # small cabins: a gondola tagged wrongly
    fast = name_hints(p.get("name"))[0] == "fast"

    cap = p.get("capacity")
    if cap and P.CAP_RANGE[0] <= cap <= P.CAP_RANGE[1]:
        cap, cap_src = float(cap), "recorded"
    else:
        cap = None
        if n and t == "chair_lift":
            cap = _lookup(P.CHAIR_CAP, n, fast)
        elif n and t == "gondola":
            cap = P.GONDOLA_CAP.get(n)
        elif n and t == "cable_car":
            cap = n * 3600 / (length / P.CABLE_SPEED + P.CABLE_LOAD_S)
        cap, cap_src = (float(cap), src) if cap else (float(P.CAP_BY_TYPE.get(t, 1000)), "type")

    dur = p.get("duration")
    if dur and P.DURATION_RANGE[0] <= dur <= P.DURATION_RANGE[1]:
        return cap, cap_src, length / dur, "recorded"
    speed = _lookup(P.CHAIR_SPEED, n, length >= P.LONG_M) if n and t == "chair_lift" else None
    if speed:
        return cap, cap_src, speed, src
    return cap, cap_src, P.LIFT_SPEED.get(t, P.DEFAULT_LIFT_SPEED), "type"
