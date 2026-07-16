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


# Marcas conocidas (orden: más específicas primero)
_BRAND_PATTERNS: list[tuple[str, str]] = [
    ("sam's club", "Sam's Club"),
    ("sams club", "Sam's Club"),
    ("king soopers", "King Soopers"),
    ("7-eleven", "7-Eleven"),
    ("7 eleven", "7-Eleven"),
    ("circle k", "Circle K"),
    ("phillips 66", "Phillips 66"),
    ("murphy usa", "Murphy USA"),
    ("kum & go", "Kum & Go"),
    ("flying j", "Flying J"),
    ("quiktrip", "QuikTrip"),
    ("quicktrip", "QuikTrip"),
    ("shell", "Shell"),
    ("chevron", "Chevron"),
    ("exxon", "Exxon"),
    ("mobil", "Mobil"),
    ("arco", "Arco"),
    ("costco", "Costco"),
    ("walmart", "Walmart"),
    ("safeway", "Safeway"),
    ("conoco", "Conoco"),
    ("sinclair", "Sinclair"),
    ("valero", "Valero"),
    ("maverik", "Maverik"),
    ("holiday", "Holiday"),
    ("cenex", "Cenex"),
    ("texaco", "Texaco"),
    ("kroger", "Kroger"),
    ("murphy", "Murphy"),
    ("speedway", "Speedway"),
    ("love's", "Love's"),
    ("loves", "Love's"),
    ("pilot", "Pilot"),
    ("bp", "BP"),
    ("qt", "QuikTrip"),
]

_STREET_WORDS = (
    "road", "rd", "avenue", "ave", "street", "st", "drive", "dr", "blvd",
    "boulevard", "lane", "ln", "way", "hwy", "highway", "circle", "court",
    "ct", "parkway", "pkwy", "place", "pl", "trail", "loop",
)


def _guess_brand(name: str) -> str:
    n = (name or "").lower()
    for needle, label in _BRAND_PATTERNS:
        # word-ish match: avoid "bp" matching random substrings mid-word
        if needle == "bp":
            if re_search_brand_bp(n):
                return label
            continue
        if needle in n:
            return label
    return "Gasolinera"


def re_search_brand_bp(text: str) -> bool:
    import re

    return bool(re.search(r"(?:^|[^a-z])bp(?:[^a-z]|$)", text))


def _looks_like_street(name: str) -> bool:
    n = (name or "").strip().lower()
    if not n or len(n) < 3:
        return True
    # "Airport Road", "South Nevada Avenue", etc.
    words = n.replace(".", "").split()
    if any(w in _STREET_WORDS for w in words):
        return True
    # solo número de calle
    if n.replace(" ", "").isdigit():
        return True
    return False


def _pretty_station_name(raw_name: str, brand: str, display: str = "") -> str:
    """Evita nombres genéricos tipo 'Airport Road' cuando hay marca."""
    name = (raw_name or "").strip() or "Gas Station"
    brand = (brand or "Gasolinera").strip()

    # Si el nombre ya es la marca, listo
    if name.lower() == brand.lower():
        return brand

    # Si el "nombre" es una calle y hay marca conocida → usar marca
    if brand != "Gasolinera" and _looks_like_street(name):
        return brand

    # Si el nombre es genérico
    generic = {"gas station", "fuel", "petrol", "gas", "station", "fuel station"}
    if name.lower() in generic:
        if brand != "Gasolinera":
            return brand
        # intentar marca desde display completo
        guessed = _guess_brand(display or name)
        return guessed if guessed != "Gasolinera" else "Gasolinera"

    # Nombre de marca + algo extra → mantener nombre
    return name


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
    raw_name = display.split(",")[0].strip() if display else "Gas Station"
    brand = _guess_brand(raw_name + " " + display)
    name = _pretty_station_name(raw_name, brand, display)
    # dirección: trozos del display (omitir el nombre corto si coincide)
    parts = [p.strip() for p in display.split(",") if p.strip()]
    if parts and parts[0].lower() in (raw_name.lower(), name.lower()):
        address = ", ".join(parts[1:5]) if len(parts) > 1 else display
    else:
        address = ", ".join(parts[:4]) if parts else display
    # limpiar dirección muy larga
    if address and len(address) > 90:
        address = address[:87] + "…"
    maps_query = display if display else name
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
                raw_name = (
                    tags.get("name")
                    or tags.get("brand")
                    or tags.get("operator")
                    or "Gas Station"
                )
                brand_tag = (tags.get("brand") or "").strip()
                brand = brand_tag or _guess_brand(
                    f"{raw_name} {tags.get('operator', '')}"
                )
                name = _pretty_station_name(raw_name, brand, raw_name)
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
        # recalcular distancias y normalizar nombres antiguos en caché
        for s in cached:
            s["distance_mi"] = haversine_miles(
                lat_f, lon_f, float(s["lat"]), float(s["lon"])
            )
            s["is_demo"] = False
            brand = s.get("brand") or _guess_brand(
                f"{s.get('name', '')} {s.get('address', '')}"
            )
            s["brand"] = brand
            s["name"] = _pretty_station_name(
                s.get("name") or "Gas Station",
                brand,
                f"{s.get('name', '')}, {s.get('address', '')}",
            )
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
