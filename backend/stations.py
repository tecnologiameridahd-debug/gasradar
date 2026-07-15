"""Estaciones de gasolina cerca de un punto (OpenStreetMap Overpass)."""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import httpx

from backend.geo import haversine_miles

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def _station_id(lat: float, lon: float, name: str) -> str:
    raw = f"{lat:.5f}|{lon:.5f}|{name.lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _guess_brand(name: str) -> str:
    n = (name or "").lower()
    brands = [
        "shell",
        "chevron",
        "exxon",
        "mobil",
        "bp",
        "arco",
        "costco",
        "sam's club",
        "sams club",
        "walmart",
        "safeway",
        "king soopers",
        "circle k",
        "7-eleven",
        "7 eleven",
        "conoco",
        "phillips 66",
        "phillips66",
        "sinclair",
        "valero",
        "marathon",
        "speedway",
        "quiktrip",
        "qt",
        "murphy",
        "wawa",
        "racetrac",
        "casey's",
        "kum & go",
        "loaf 'n jug",
        "maverik",
        "holiday",
        "cenex",
        "texaco",
        "gulf",
        "sunoco",
        "getgo",
        "meijer",
        "kroger",
        "albertsons",
        "smith's",
    ]
    for b in brands:
        if b in n:
            return b.title().replace("Sams Club", "Sam's Club").replace("7 Eleven", "7-Eleven")
    return "Independiente"


@lru_cache(maxsize=64)
def fetch_stations_osm(lat: float, lon: float, radius_m: int = 8000) -> tuple:
    """
    Devuelve tuple de estaciones (hashable para caché).
    radius_m: radio de búsqueda (default ~5 millas).
    """
    # Overpass around point
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="fuel"](around:{radius_m},{lat},{lon});
      way["amenity"="fuel"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """
    data = None
    last_err = None
    for url in OVERPASS_URLS:
        try:
            r = httpx.post(url, data={"data": query}, timeout=12.0)
            if r.status_code == 200:
                data = r.json()
                break
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
            continue
    if not data:
        # Fallback demo stations around point if OSM fails / timeout
        print(f"[stations] OSM fallback demo ({last_err})")
        return _demo_stations(lat, lon)

    elements = data.get("elements") or []
    stations = []
    for el in elements:
        tags = el.get("tags") or {}
        if el.get("type") == "way" or el.get("type") == "relation":
            center = el.get("center") or {}
            slat = center.get("lat")
            slon = center.get("lon")
        else:
            slat = el.get("lat")
            slon = el.get("lon")
        if slat is None or slon is None:
            continue
        name = (
            tags.get("name")
            or tags.get("brand")
            or tags.get("operator")
            or "Gas Station"
        )
        brand = tags.get("brand") or _guess_brand(name)
        addr_parts = [
            tags.get("addr:housenumber", ""),
            tags.get("addr:street", ""),
        ]
        street = " ".join(p for p in addr_parts if p).strip()
        city = tags.get("addr:city", "")
        state = tags.get("addr:state", "")
        postcode = tags.get("addr:postcode", "")
        address = ", ".join(p for p in [street, city, state, postcode] if p) or None
        dist = haversine_miles(lat, lon, float(slat), float(slon))
        stations.append(
            {
                "id": _station_id(float(slat), float(slon), name),
                "name": name,
                "brand": brand,
                "lat": float(slat),
                "lon": float(slon),
                "address": address,
                "distance_mi": dist,
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "osm_id": el.get("id"),
                "source": "openstreetmap",
            }
        )

    # dedupe by id
    seen = set()
    unique = []
    for s in sorted(stations, key=lambda x: x["distance_mi"]):
        if s["id"] in seen:
            continue
        seen.add(s["id"])
        unique.append(s)

    if not unique:
        return _demo_stations(lat, lon)
    return tuple(s["id"] for s in unique), tuple(
        tuple(sorted(s.items())) for s in unique
    )


def stations_near(lat: float, lon: float, radius_mi: float = 5.0, limit: int = 40) -> list[dict]:
    radius_m = int(min(max(radius_mi, 1) * 1609.34, 25000))
    # round coords for cache hits
    lat_r = round(lat, 3)
    lon_r = round(lon, 3)
    result = fetch_stations_osm(lat_r, lon_r, radius_m)
    if not result:
        return _demo_stations_list(lat, lon)

    # Cacheable form: (ids_tuple, serialized_stations_tuple)
    stations: list[dict] = []
    try:
        if (
            isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[1], tuple)
        ):
            serialized = result[1]
            stations = [dict(items) for items in serialized]
        else:
            stations = [dict(x) for x in result]  # type: ignore[arg-type]
    except Exception:
        stations = _demo_stations_list(lat, lon)

    # recompute distance from exact user point
    for s in stations:
        s["distance_mi"] = haversine_miles(lat, lon, float(s["lat"]), float(s["lon"]))
        s["lat"] = float(s["lat"])
        s["lon"] = float(s["lon"])
    stations = [s for s in stations if s["distance_mi"] <= radius_mi + 0.15]
    stations.sort(key=lambda x: x["distance_mi"])
    return stations[:limit]


def _demo_stations(lat: float, lon: float):
    lst = _demo_stations_list(lat, lon)
    return tuple(s["id"] for s in lst), tuple(tuple(sorted(s.items())) for s in lst)


def _demo_stations_list(lat: float, lon: float) -> list[dict]:
    """Fallback si Overpass cae — estaciones demo cerca del punto."""
    offsets = [
        (0.012, 0.008, "Costco Gasoline", "Costco"),
        (0.018, -0.010, "Shell", "Shell"),
        (-0.009, 0.015, "King Soopers Fuel", "King Soopers"),
        (0.005, -0.018, "Safeway Fuel", "Safeway"),
        (-0.015, -0.006, "Conoco", "Conoco"),
        (0.022, 0.004, "Circle K", "Circle K"),
        (-0.006, 0.022, "7-Eleven", "7-Eleven"),
        (0.008, 0.012, "Chevron", "Chevron"),
        (-0.020, 0.010, "Sam's Club Fuel", "Sam's Club"),
        (0.014, -0.014, "Phillips 66", "Phillips 66"),
    ]
    out = []
    for dlat, dlon, name, brand in offsets:
        slat, slon = lat + dlat, lon + dlon
        out.append(
            {
                "id": _station_id(slat, slon, name),
                "name": name,
                "brand": brand,
                "lat": slat,
                "lon": slon,
                "address": None,
                "distance_mi": haversine_miles(lat, lon, slat, slon),
                "phone": None,
                "website": None,
                "osm_id": None,
                "source": "demo",
            }
        )
    return sorted(out, key=lambda x: x["distance_mi"])
