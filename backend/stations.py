"""Estaciones de gasolina cerca de un punto (OpenStreetMap Overpass)."""
from __future__ import annotations

import hashlib
from functools import lru_cache

import httpx

from backend.geo import haversine_miles

# Pocos mirrors y timeout corto: si falla, sugerencias rápidas (no colgar la app)
OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
]
OVERPASS_TIMEOUT = 5.0  # si falla → sugerencias al instante

def _station_id(lat: float, lon: float, name: str) -> str:
    raw = f"{lat:.5f}|{lon:.5f}|{name.lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _guess_brand(name: str) -> str:
    n = (name or "").lower()
    brands = [
        "shell", "chevron", "exxon", "mobil", "bp", "arco", "costco",
        "sam's club", "sams club", "walmart", "safeway", "king soopers",
        "circle k", "7-eleven", "7 eleven", "conoco", "phillips 66",
        "phillips66", "sinclair", "valero", "marathon", "speedway",
        "quiktrip", "qt", "murphy", "maverik", "holiday", "cenex",
        "texaco", "kroger", "albertsons", "smith's",
    ]
    for b in brands:
        if b in n:
            return (
                b.title()
                .replace("Sams Club", "Sam's Club")
                .replace("7 Eleven", "7-Eleven")
            )
    return "Independiente"


def _parse_elements(elements: list, user_lat: float, user_lon: float) -> list[dict]:
    stations = []
    for el in elements:
        tags = el.get("tags") or {}
        if el.get("type") in ("way", "relation"):
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

        maps_query = name
        if street:
            maps_query = f"{name}, {street}"
            if city:
                maps_query += f", {city}"
            if state:
                maps_query += f" {state}"
            if postcode:
                maps_query += f" {postcode}"

        dist = haversine_miles(user_lat, user_lon, float(slat), float(slon))
        stations.append(
            {
                "id": _station_id(float(slat), float(slon), name),
                "name": name,
                "brand": brand,
                "lat": float(slat),
                "lon": float(slon),
                "address": address,
                "maps_query": maps_query,
                "distance_mi": dist,
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "osm_id": el.get("id"),
                "source": "openstreetmap",
                "is_demo": False,
            }
        )
    return stations


@lru_cache(maxsize=64)
def fetch_stations_osm(lat: float, lon: float, radius_m: int = 8000) -> tuple:
    # query simple y timeout corto
    query = f"""
    [out:json][timeout:8];
    (
      node["amenity"="fuel"](around:{radius_m},{lat},{lon});
      way["amenity"="fuel"](around:{radius_m},{lat},{lon});
    );
    out center tags 40;
    """
    data = None
    last_err = None
    for url in OVERPASS_URLS:
        try:
            r = httpx.post(url, data={"data": query}, timeout=OVERPASS_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                break
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
            continue

    if not data:
        print(f"[stations] OSM skip ({last_err})")
        return tuple(), tuple()

    elements = data.get("elements") or []
    stations = _parse_elements(elements, lat, lon)
    if not stations:
        return tuple(), tuple()

    seen = set()
    unique = []
    for s in sorted(stations, key=lambda x: x["distance_mi"]):
        if s["id"] in seen:
            continue
        seen.add(s["id"])
        unique.append(s)

    return tuple(s["id"] for s in unique), tuple(
        tuple(sorted(s.items())) for s in unique
    )


def stations_near(
    lat: float, lon: float, radius_mi: float = 5.0, limit: int = 40
) -> list[dict]:
    radius_m = int(min(max(radius_mi, 1) * 1609.34, 25000))
    lat_r = round(lat, 3)
    lon_r = round(lon, 3)

    try:
        result = fetch_stations_osm(lat_r, lon_r, radius_m)
    except Exception as e:
        print(f"[stations] error {e}")
        result = (tuple(), tuple())

    stations: list[dict] = []
    try:
        if (
            isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[1], tuple)
            and result[1]
        ):
            stations = [dict(items) for items in result[1]]
    except Exception:
        stations = []

    for s in stations:
        s["distance_mi"] = haversine_miles(lat, lon, float(s["lat"]), float(s["lon"]))
        s["lat"] = float(s["lat"])
        s["lon"] = float(s["lon"])
        s["is_demo"] = False
        s["source"] = s.get("source") or "openstreetmap"
        if not s.get("maps_query"):
            s["maps_query"] = s.get("name") or "gas station"

    stations = [s for s in stations if s["distance_mi"] <= radius_mi + 0.2]
    stations.sort(key=lambda x: x["distance_mi"])

    if stations:
        return stations[:limit]

    # Rápido: sugerencias de búsqueda (no coords inventadas)
    return _search_suggestions(lat, lon, limit=min(limit, 8))


def _search_suggestions(lat: float, lon: float, limit: int = 8) -> list[dict]:
    brands = [
        "Costco Gasoline",
        "Sam's Club Fuel",
        "King Soopers Fuel",
        "Safeway Fuel",
        "Shell",
        "Chevron",
        "Conoco",
        "Circle K",
        "7-Eleven",
        "Maverik",
    ]
    out = []
    for name in brands[:limit]:
        brand = _guess_brand(name)
        q = f"{name} near {lat:.5f},{lon:.5f}"
        out.append(
            {
                "id": _station_id(lat, lon, f"suggest-{name}"),
                "name": name,
                "brand": brand,
                "lat": float(lat),
                "lon": float(lon),
                "address": "Buscar en el mapa (cerca de ti)",
                "maps_query": q,
                "distance_mi": 0.0,
                "phone": None,
                "website": None,
                "osm_id": None,
                "source": "search_suggest",
                "is_demo": True,
                "nav_mode": "search",
            }
        )
    return out
