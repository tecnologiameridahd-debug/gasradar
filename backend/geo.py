"""Geocoding ZIP / reverse geo (Nominatim / Zippopotam.us)."""
from __future__ import annotations

import re
from functools import lru_cache

import httpx

# Solo si el usuario no da GPS ni ZIP (fallback)
DEFAULT_LAT = 39.7392
DEFAULT_LON = -104.9903
DEFAULT_LABEL = "Denver, CO (predeterminado)"


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


@lru_cache(maxsize=512)
def reverse_geocode(lat: float, lon: float) -> dict | None:
    """
    Convierte lat/lon en ciudad + estado.
    Timeout corto: si falla, la app sigue (no se queda cargando).
    """
    lat_r = round(float(lat), 3)
    lon_r = round(float(lon), 3)
    try:
        r = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat_r,
                "lon": lon_r,
                "format": "jsonv2",
                "zoom": 10,
                "addressdetails": 1,
            },
            headers={
                "User-Agent": "GasRadar/1.0 (contact@gasradarapp.com)",
                "Accept-Language": "en",
            },
            timeout=3.0,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        addr = data.get("address") or {}
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality")
            or addr.get("county")
            or ""
        )
        state = addr.get("state") or ""
        state_code = addr.get("ISO3166-2-lvl4") or ""
        if state_code and "-" in state_code:
            state_abbr = state_code.split("-")[-1]
        else:
            state_abbr = _state_abbr(state) or ""
        postcode = (addr.get("postcode") or "").split(";")[0][:5]
        parts = [p for p in [city, state_abbr or state, postcode] if p]
        label = ", ".join(parts) if parts else f"{lat_r}, {lon_r}"
        return {
            "lat": float(lat),
            "lon": float(lon),
            "label": label,
            "zip": postcode or None,
            "state": state_abbr or "CO",
            "city": city,
        }
    except Exception:
        return None


def _state_abbr(name: str) -> str:
    table = {
        "colorado": "CO",
        "california": "CA",
        "texas": "TX",
        "new york": "NY",
        "florida": "FL",
        "arizona": "AZ",
        "new mexico": "NM",
        "utah": "UT",
        "wyoming": "WY",
        "kansas": "KS",
        "nebraska": "NE",
    }
    return table.get((name or "").strip().lower(), "")


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 3958.8  # Earth radius miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(2 * r * asin(sqrt(a)), 2)
