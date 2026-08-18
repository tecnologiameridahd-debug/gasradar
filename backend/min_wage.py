"""Sueldo mínimo estatal (USA) y horas para llenar el tanque.

Cifras generales de 2026 (DOL / leyes estatales). Si el estado está
por debajo del federal, usamos $7.25. Algunas ciudades pagan más;
esto es el mínimo estatal general, no el de cada municipio.
"""
from __future__ import annotations

FEDERAL = 7.25
AS_OF = "2026-07"

# USD / hora · statewide general (no city add-ons)
WAGES: dict[str, float] = {
    "AL": 7.25, "AK": 14.00, "AZ": 15.15, "AR": 11.00, "CA": 16.90,
    "CO": 15.16, "CT": 16.94, "DE": 15.00, "FL": 14.00, "GA": 7.25,
    "HI": 16.00, "ID": 7.25, "IL": 15.00, "IN": 7.25, "IA": 7.25,
    "KS": 7.25, "KY": 7.25, "LA": 7.25, "ME": 15.10, "MD": 15.00,
    "MA": 15.00, "MI": 13.73, "MN": 11.41, "MS": 7.25, "MO": 15.00,
    "MT": 10.85, "NE": 15.00, "NV": 12.00, "NH": 7.25, "NJ": 15.92,
    "NM": 12.00, "NY": 16.00, "NC": 7.25, "ND": 7.25, "OH": 10.70,
    "OK": 7.25, "OR": 15.55, "PA": 7.25, "RI": 16.00, "SC": 7.25,
    "SD": 11.50, "TN": 7.25, "TX": 7.25, "UT": 7.25, "VT": 14.01,
    "VA": 12.41, "WA": 16.66, "WV": 8.75, "WI": 7.25, "WY": 7.25,
    "DC": 18.40,
}


def wage_for_state(state: str | None) -> dict | None:
    st = (state or "").strip().upper()
    if len(st) != 2:
        return None
    raw = WAGES.get(st)
    if raw is None:
        hourly = FEDERAL
        kind = "federal"
    else:
        hourly = max(float(raw), FEDERAL)
        kind = "federal" if hourly <= FEDERAL + 0.001 else "state"
    return {
        "state": st,
        "hourly": round(hourly, 2),
        "kind": kind,
        "as_of": AS_OF,
        "federal": FEDERAL,
    }


def tank_work(*, price: float, gallons: float, hourly: float) -> dict:
    g = max(1.0, min(40.0, float(gallons)))
    p = max(0.5, float(price))
    w = max(0.01, float(hourly))
    cost = round(p * g, 2)
    hours = cost / w
    return {
        "gallons": round(g, 1),
        "price": round(p, 3),
        "cost": cost,
        "hours": round(hours, 2),
        "minutes": int(round(hours * 60)),
    }
