"""
Estaciones de gasolina REALES cerca de un punto.

Fuente principal: OpenStreetMap vía Nominatim (rápido y fiable).
Respaldo: Overpass (si responde).
Caché en disco para no repetir llamadas.
Nunca inventa coordenadas falsas tipo "demo".
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from functools import lru_cache
from pathlib import Path

import httpx

from backend.geo import haversine_miles

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_DIR = DATA_DIR / "stations_cache"
CACHE_TTL = 6 * 3600  # 6 horas

USER_AGENT = "GasRadar/1.1 (https://github.com/tecnologiameridahd-debug/gasradar; contact@gasradarapp.com)"

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]


def _station_id(lat: float, lon: float, name: str) -> str:
    raw = f"{lat:.5f}|{lon:.5f}|{(name or '').lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _guess_brand(name: str) -> str:
    n = (name or "").lower()
    brands = [
        "shell", "chevron", "exxon", "mobil", "bp", "arco", "costco",
        "sam's club", "sams club", "walmart", "safeway", "king soopers",
        "circle k", "7-eleven", "7 eleven", "conoco", "phillips 66",
        "sinclair", "valero", "quiktrip", "maverik", "holiday", "cenex",
        "texaco", "kroger", "murphy", "speedway",
    ]
    for b in brands:
        if b in n:
            return (
                b.title()
                .replace("Sams Club", "Sam's Club")
                .replace("7 Eleven", "7-Eleven")
            )
    return "Gasolinera"


def _viewbox(lat: float, lon: float, radius_mi: float) -> str:
    """left,top,right,bottom para Nominatim."""
    dlat = max(radius_mi, 2) / 69.0
    dlon = max(radius_mi, 2) / (69.0 * max(0.2, math.cos(math.radians(lat))))
    left = lon - dlon
    right = lon + dlon
    top = lat + dlat
    bottom = lat - dlat
    return f"{left},{top},{right},{bottom}"


def _cache_path(lat: float, lon: float, radius_mi: float) -> Path:
    key = f"{round(lat, 2)}_{round(lon, 2)}_{int(radius_mi)}"
    return CACHE_DIR / f"{key}.json"


def _load_cache(lat: float, lon: float, radius_mi: float) -> list[dict] | None:
    path = _cache_path(lat, lon, radius_mi)
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(obj.get("ts", 0)) > CACHE_TTL:
            return None
        return obj.get("stations") or None
    except Exception:
        return None


def _save_cache(lat: float, lon: float, radius_mi: float, stations: list[dict]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(lat, lon, radius_mi)
        path.write_text(
            json.dumps({"ts": time.time(), "stations": stations}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[stations] cache save fail: {e}")


def _from_nominatim_item(item: dict, user_lat: float, user_lon: float) -> dict | None:
    try:
        slat = float(item["lat"])
        slon = float(item["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    display = (item.get("display_name") or "").strip()
    # nombre corto: primera parte del display_name
    name = display.split(",")[0].strip() if display else "Gas Station"
    # filtrar basura no-gas si aparece
    low = display.lower()
    if not any(
        k in low
        for k in (
            "gas",
            "fuel",
            "shell",
            "chevron",
            "conoco",
            "costco",
            "circle k",
            "7-eleven",
            "petrol",
            "station",
            "king soopers",
            "safeway",
            "maverik",
            "phillips",
            "arco",
            "exxon",
            "mobil",
            "sinclair",
            "valero",
            "quiktrip",
            "murphy",
        )
    ):
        # amenity type check
        if item.get("type") not in ("fuel", "fuel_station", "gas") and item.get(
            "class"
        ) not in ("amenity",):
            # still allow if class amenity
            pass

    brand = _guess_brand(name + " " + display)
    # dirección: trozos 2–5 del display
    parts = [p.strip() for p in display.split(",") if p.strip()]
    address = ", ".join(parts[1:5]) if len(parts) > 1 else display
    maps_query = display if display else f"{name}"
    dist = haversine_miles(user_lat, user_lon, slat, slon)
    return {
        "id": _station_id(slat, slon, name),
        "name": name,
        "brand": brand,
        "lat": slat,
        "lon": slon,
        "address": address,
        "maps_query": maps_query,
        "distance_mi": dist,
        "phone": None,
        "website": None,
        "osm_id": item.get("osm_id"),
        "source": "openstreetmap",
        "is_demo": False,
        "nav_mode": "coords",
    }


def _fetch_nominatim(lat: float, lon: float, radius_mi: float) -> list[dict]:
    """POIs reales de gas cerca del usuario."""
    vb = _viewbox(lat, lon, radius_mi)
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en"}
    queries = [
        {"q": "gas station", "viewbox": vb, "bounded": 1, "countrycodes": "us", "limit": 30},
        {"q": "fuel", "viewbox": vb, "bounded": 1, "countrycodes": "us", "limit": 20},
        # amenity search (algunos servidores lo soportan)
        {
            "amenity": "fuel",
            "viewbox": vb,
            "bounded": 1,
            "countrycodes": "us",
            "limit": 30,
            "format": "json",
        },
    ]
    seen: set[str] = set()
    out: list[dict] = []

    for params in queries:
        params = dict(params)
        params.setdefault("format", "json")
        try:
            r = httpx.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=headers,
                timeout=8.0,
            )
            if r.status_code != 200:
                continue
            items = r.json()
            if not isinstance(items, list):
                continue
            for item in items:
                st = _from_nominatim_item(item, lat, lon)
                if not st:
                    continue
                if st["id"] in seen:
                    continue
                if st["distance_mi"] > radius_mi + 0.5:
                    continue
                seen.add(st["id"])
                out.append(st)
        except Exception as e:
            print(f"[stations] nominatim fail: {e}")
            continue
        # política Nominatim: ~1 req/s
        time.sleep(1.05)
        if len(out) >= 12:
            break

    out.sort(key=lambda x: x["distance_mi"])
    return out


def _fetch_overpass(lat: float, lon: float, radius_mi: float) -> list[dict]:
    radius_m = int(min(max(radius_mi, 1) * 1609.34, 20000))
    query = (
        f'[out:json][timeout:12];'
        f'('
        f'node["amenity"="fuel"](around:{radius_m},{lat},{lon});'
        f'way["amenity"="fuel"](around:{radius_m},{lat},{lon});'
        f');'
        f"out center tags 40;"
    )
    for url in OVERPASS_URLS:
        try:
            r = httpx.get(url, params={"data": query}, timeout=10.0)
            if r.status_code != 200:
                continue
            elements = r.json().get("elements") or []
            if not elements:
                continue
            stations = []
            for el in elements:
                tags = el.get("tags") or {}
                if el.get("type") in ("way", "relation"):
                    center = el.get("center") or {}
                    slat, slon = center.get("lat"), center.get("lon")
                else:
                    slat, slon = el.get("lat"), el.get("lon")
                if slat is None or slon is None:
                    continue
                name = (
                    tags.get("name")
                    or tags.get("brand")
                    or tags.get("operator")
                    or "Gas Station"
                )
                brand = tags.get("brand") or _guess_brand(name)
                street = " ".join(
                    p
                    for p in [
                        tags.get("addr:housenumber", ""),
                        tags.get("addr:street", ""),
                    ]
                    if p
                ).strip()
                city = tags.get("addr:city", "")
                state = tags.get("addr:state", "")
                postcode = tags.get("addr:postcode", "")
                address = (
                    ", ".join(p for p in [street, city, state, postcode] if p) or None
                )
                maps_query = name
                if street:
                    maps_query = f"{name}, {street}"
                    if city:
                        maps_query += f", {city}"
                dist = haversine_miles(lat, lon, float(slat), float(slon))
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
                        "website": tags.get("website"),
                        "osm_id": el.get("id"),
                        "source": "openstreetmap",
                        "is_demo": False,
                        "nav_mode": "coords",
                    }
                )
            if stations:
                stations.sort(key=lambda x: x["distance_mi"])
                return stations
        except Exception as e:
            print(f"[stations] overpass fail: {e}")
            continue
    return []


def stations_near(
    lat: float, lon: float, radius_mi: float = 5.0, limit: int = 40
) -> list[dict]:
    """
    Lista estaciones REALES cerca de lat/lon.
    Orden: caché → Nominatim → Overpass.
    """
    lat_f, lon_f = float(lat), float(lon)
    radius_mi = float(radius_mi)

    cached = _load_cache(lat_f, lon_f, radius_mi)
    if cached:
        # recalcular distancias al punto exacto
        for s in cached:
            s["distance_mi"] = haversine_miles(
                lat_f, lon_f, float(s["lat"]), float(s["lon"])
            )
            s["is_demo"] = False
        cached = [s for s in cached if s["distance_mi"] <= radius_mi + 0.5]
        cached.sort(key=lambda x: x["distance_mi"])
        if cached:
            return cached[:limit]

    stations = _fetch_nominatim(lat_f, lon_f, radius_mi)

    if len(stations) < 5:
        # sumar Overpass si hay pocos
        extra = _fetch_overpass(lat_f, lon_f, radius_mi)
        seen = {s["id"] for s in stations}
        for s in extra:
            if s["id"] not in seen and s["distance_mi"] <= radius_mi + 0.5:
                stations.append(s)
                seen.add(s["id"])
        stations.sort(key=lambda x: x["distance_mi"])

    if stations:
        _save_cache(lat_f, lon_f, radius_mi, stations[:60])
        return stations[:limit]

    # Sin inventar: lista vacía (el frontend/API mostrará mensaje claro)
    print("[stations] sin resultados reales en Nominatim/Overpass")
    return []
