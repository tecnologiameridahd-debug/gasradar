"""Geocoding ZIP / reverse geo (Nominatim / Zippopotam.us)."""
from __future__ import annotations

import re
from functools import lru_cache

import httpx

# Default: Denver downtown
DEFAULT_LAT = 39.7392
DEFAULT_LON = -104.9903
DEFAULT_LABEL = "Denver, CO"


@lru_cache(maxsize=256)
def geocode_zip(zip_code: str) -> dict | None:
    z = re.sub(r"[^0-9]", "", zip_code)[:5]
    if len(z) != 5:
        return None
    try:
        r = httpx.get(f"https://api.zippopotam.us/us/{z}", timeout=12.0)
        if r.status_code != 200:
            return None
        data = r.json()
        places = data.get("places") or []
        if not places:
            return None
        p = places[0]
        return {
            "lat": float(p["latitude"]),
            "lon": float(p["longitude"]),
            "label": f"{p.get('place name', '')}, {p.get('state abbreviation', '')} {z}".strip(),
            "zip": z,
            "state": p.get("state abbreviation", ""),
            "city": p.get("place name", ""),
        }
    except Exception:
        return None


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 3958.8  # Earth radius miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(2 * r * asin(sqrt(a)), 2)
