"""Typed, validated readers for the CSV files in data/ (the scenario parameters are read by params.py).

Structural problems (missing column, non-numeric value, out-of-range value, duplicate key) raise ValueError.
`problems()` lists data-quality findings that are not structural, such as shares that do not add up.
"""
import csv

from .paths import ROOT

DATA = ROOT / "data"
SHARE_TOLERANCE = 0.5   # percentage points


def _read(name, columns):
    with open(DATA / name, newline="") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames != list(columns):
            raise ValueError(f"{name}: columns {rd.fieldnames} != expected {list(columns)}")
        rows = list(rd)
    if not rows:
        raise ValueError(f"{name}: no rows")
    return rows


def _num(name, i, row, col, lo, hi):
    try:
        x = float(row[col])
    except (TypeError, ValueError):
        raise ValueError(f"{name} row {i}: {col}={row[col]!r} is not a number") from None
    if not lo <= x <= hi:
        raise ValueError(f"{name} row {i}: {col}={x} outside [{lo}, {hi}]")
    return x


def _unique(name, keys):
    seen = set()
    for k in keys:
        if k in seen:
            raise ValueError(f"{name}: duplicate row {k}")
        seen.add(k)


def carcass_shares():
    """[{animal, part, live_weight_pct, value_pct}], in file order."""
    name = "carcass_weight_and_value_shares.csv"
    out = []
    for i, r in enumerate(_read(name, ["animal", "part", "share_of_live_weight_pct", "share_of_value_pct"]), 2):
        out.append(dict(animal=r["animal"], part=r["part"],
                        live_weight_pct=_num(name, i, r, "share_of_live_weight_pct", 0, 100),
                        value_pct=_num(name, i, r, "share_of_value_pct", 0, 100)))
    _unique(name, [(r["animal"], r["part"]) for r in out])
    return out


def whey_prices():
    """[{month 'YYYY-MM', series, usd_per_lb}], in file order."""
    name = "whey_prices_central_us_2022_2026.csv"
    out = []
    for i, r in enumerate(_read(name, ["month", "series", "usd_per_lb"]), 2):
        m = r["month"]
        if len(m) != 7 or m[4] != "-" or not (m[:4].isdigit() and m[5:].isdigit() and 1 <= int(m[5:]) <= 12):
            raise ValueError(f"{name} row {i}: month {m!r} is not YYYY-MM")
        out.append(dict(month=m, series=r["series"], usd_per_lb=_num(name, i, r, "usd_per_lb", 0, 100)))
    _unique(name, [(r["month"], r["series"]) for r in out])
    return out


def reachability():
    """[{product, reachability (1..4), df_3_5_years}], in file order."""
    name = "technical_reachability.csv"
    out = []
    for i, r in enumerate(_read(name, ["product", "reachability_1_to_4", "df_3_5_years"]), 2):
        level = _num(name, i, r, "reachability_1_to_4", 1, 4)
        if level != int(level):
            raise ValueError(f"{name} row {i}: reachability {level} is not a whole number")
        out.append(dict(product=r["product"], reachability=int(level), df_3_5_years=_num(name, i, r, "df_3_5_years", 0, 1)))
    _unique(name, [r["product"] for r in out])
    return out


def problems():
    """Data-quality findings: carcass shares per animal that do not add to 100%."""
    found = []
    animals = {}
    for r in carcass_shares():
        animals.setdefault(r["animal"], []).append(r)
    for animal, rows in animals.items():
        for col, label in (("live_weight_pct", "live weight"), ("value_pct", "value")):
            total = sum(r[col] for r in rows)
            if abs(total - 100.0) > SHARE_TOLERANCE:
                found.append(f"{animal}: {label} shares add to {total:.1f}%, not 100%")
    return found
