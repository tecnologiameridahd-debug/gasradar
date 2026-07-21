"""
Estaciones de gasolina REALES cerca de un punto.

Orden de fuentes (nube / Render):
1) Overpass OSM (POST, varios mirrors) — principal en servidores
2) Photon (Komoot) — respaldo rápido
3) Nominatim — suele fallar desde IPs de datacenter

Caché en disco. Nunca inventa coordenadas demo.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import httpx

from backend.geo import haversine_miles

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_DIR = DATA_DIR / "stations_cache"
CACHE_TTL = 6 * 3600  # 6 horas

USER_AGENT = (
    "GasRadar/1.3 (https://gasradarapp.com; contact@gasradarapp.com)"
)
HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en",
}

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
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
    ("7-11", "7-Eleven"),
    ("circle k", "Circle K"),
    ("phillips 66", "Phillips 66"),
    ("phillip 66", "Phillips 66"),
    ("phillips66", "Phillips 66"),
    ("diamond shamrock", "Diamond Shamrock"),
    ("murphy usa", "Murphy USA"),
    ("kum & go", "Kum & Go"),
    ("kum and go", "Kum & Go"),
    ("flying j", "Flying J"),
    ("loaf 'n jug", "Loaf 'N Jug"),
    ("loaf n jug", "Loaf 'N Jug"),
    ("loaf'n jug", "Loaf 'N Jug"),
    ("quiktrip", "QuikTrip"),
    ("quicktrip", "QuikTrip"),
    ("u pump it", "U Pump It"),
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
    ("marathon", "Marathon"),
    ("sunoco", "Sunoco"),
    ("casey's", "Casey's"),
    ("caseys", "Casey's"),
    ("wawa", "Wawa"),
    ("sheetz", "Sheetz"),
    ("citgo", "Citgo"),
    ("racetrac", "RaceTrac"),
    ("race trac", "RaceTrac"),
    ("getgo", "GetGo"),
    ("bp", "BP"),
    ("qt", "QuikTrip"),
]

_STREET_WORDS = (
    "road", "rd", "avenue", "ave", "street", "st", "drive", "dr", "blvd",
    "boulevard", "lane", "ln", "way", "hwy", "highway", "circle", "court",
    "ct", "parkway", "pkwy", "place", "pl", "trail", "loop",
)


def _guess_brand(name: str) -> str | None:
    """Devuelve marca conocida o None si no hay."""
    n = (name or "").lower()
    for needle, label in _BRAND_PATTERNS:
        # word-ish match: avoid "bp" matching random substrings mid-word
        if needle == "bp":
            if re_search_brand_bp(n):
                return label
            continue
        if needle in n:
            return label
    return None


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


def _short_street(address: str | None, raw_name: str = "") -> str:
    """Saca un trozo de calle legible para el nombre de pantalla."""
    if raw_name and _looks_like_street(raw_name) and not raw_name.replace(" ", "").isdigit():
        return raw_name.strip()
    if not address:
        return ""
    # primera parte suele ser la calle
    part = address.split(",")[0].strip()
    if part and len(part) < 48:
        return part
    return part[:45] + "…" if part else ""


def _pretty_station_name(
    raw_name: str, brand: str | None, display: str = "", address: str | None = None
) -> str:
    """
    Nombre para la app:
    - Con marca → Shell, Circle K…
    - Sin marca en OSM → 'Gas · Airport Road' (no 'Gasolinera' solo)
    """
    name = (raw_name or "").strip() or "Gas Station"
    brand = (brand or "").strip() or None
    if not brand or brand == "Gasolinera":
        brand = _guess_brand(f"{name} {display}")

    generic = {
        "gas station",
        "fuel",
        "petrol",
        "gas",
        "station",
        "fuel station",
        "gasolinera",
    }

    # Marca conocida
    if brand:
        if name.lower() == brand.lower() or name.lower() in generic or _looks_like_street(name):
            return brand
        # "Shell Station" etc.
        if brand.lower() in name.lower():
            return brand
        return name

    # Sin marca: no devolver "Gasolinera" ni solo un número
    if name.lower() in generic or name.replace(" ", "").isdigit():
        street = _short_street(
            address or display,
            name if _looks_like_street(name) and name.lower() not in generic else "",
        )
        if (
            street
            and not street.replace(" ", "").isdigit()
            and street.lower() not in generic
            and "gas station" not in street.lower()
        ):
            return f"Gas · {street}"
        return "Gas station"

    if _looks_like_street(name):
        return f"Gas · {name}"

    # Nombre propio tipo "Everyday Fuel", "North Murray Gas"
    return name


def _display_brand(brand: str | None, name: str) -> str | None:
    """Brand para UI: None si genérico (no mostrar 'Gasolinera')."""
    b = (brand or "").strip()
    if not b or b.lower() in ("gasolinera", "gas station", "independent", "independiente"):
        # si el nombre ES la marca conocida
        guessed = _guess_brand(name)
        return guessed
    return b


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
    # dirección: trozos del display (omitir el nombre corto si coincide)
    parts = [p.strip() for p in display.split(",") if p.strip()]
    if parts and parts[0].lower() in (raw_name.lower(),):
        address = ", ".join(parts[1:5]) if len(parts) > 1 else display
    else:
        address = ", ".join(parts[:4]) if parts else display
    # limpiar dirección muy larga
    if address and len(address) > 90:
        address = address[:87] + "…"
    name = _pretty_station_name(raw_name, brand, display, address)
    brand = _display_brand(brand, name)
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
    """POIs reales de gas cerca del usuario (a menudo bloqueado en la nube)."""
    vb = _viewbox(lat, lon, radius_mi)
    queries = [
        {"q": "gas station", "viewbox": vb, "bounded": 1, "countrycodes": "us", "limit": 30},
        {"q": "fuel", "viewbox": vb, "bounded": 1, "countrycodes": "us", "limit": 20},
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
                headers=HTTP_HEADERS,
                timeout=12.0,
            )
            if r.status_code != 200:
                print(f"[stations] nominatim status={r.status_code}")
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
        time.sleep(1.05)
        if len(out) >= 12:
            break

    out.sort(key=lambda x: x["distance_mi"])
    if out:
        print(f"[stations] nominatim OK {len(out)}")
    return out


def _station_from_osm_tags(
    lat: float,
    lon: float,
    slat: float,
    slon: float,
    tags: dict,
    osm_id=None,
) -> dict | None:
    raw_name = (
        tags.get("name")
        or tags.get("brand")
        or tags.get("operator")
        or "Gas Station"
    )
    brand_tag = (tags.get("brand") or "").strip()
    brand = brand_tag or _guess_brand(f"{raw_name} {tags.get('operator', '')}")
    # OSM a veces usa variantes de addr:* (muchas gasolineras en LV no tienen nada)
    street = " ".join(
        p
        for p in [
            tags.get("addr:housenumber", "") or tags.get("addr:house_number", ""),
            tags.get("addr:street", "")
            or tags.get("addr:place", "")
            or tags.get("addr:suburb", ""),
        ]
        if p
    ).strip()
    city = (
        tags.get("addr:city", "")
        or tags.get("addr:town", "")
        or tags.get("addr:suburb", "")
        or ""
    )
    state = tags.get("addr:state", "") or ""
    postcode = tags.get("addr:postcode", "") or ""
    full = (tags.get("addr:full") or tags.get("address") or "").strip()
    address = full or (
        ", ".join(p for p in [street, city, state, postcode] if p) or None
    )
    name = _pretty_station_name(raw_name, brand, raw_name, address)
    brand = _display_brand(brand, name)
    maps_query = name
    if address:
        maps_query = f"{name}, {address}"
    elif street:
        maps_query = f"{name}, {street}"
        if city:
            maps_query += f", {city}"
    else:
        # Sin addr en OSM: Maps abre por coordenadas
        maps_query = f"{name} @{float(slat):.5f},{float(slon):.5f}"
    dist = haversine_miles(lat, lon, float(slat), float(slon))
    return {
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
        "osm_id": osm_id,
        "source": "openstreetmap",
        "is_demo": False,
        "nav_mode": "coords",
    }


def _fetch_overpass(lat: float, lon: float, radius_mi: float) -> list[dict]:
    """Overpass POST — más fiable desde Render que Nominatim."""
    radius_m = int(min(max(radius_mi, 1) * 1609.34, 25000))
    # timeout moderado: si un mirror tarda, pasamos al siguiente / Photon
    query = (
        f'[out:json][timeout:18];'
        f'('
        f'node["amenity"="fuel"](around:{radius_m},{lat},{lon});'
        f'way["amenity"="fuel"](around:{radius_m},{lat},{lon});'
        f');'
        f"out center tags 50;"
    )
    for url in OVERPASS_URLS:
        try:
            r = httpx.post(
                url,
                data={"data": query},
                headers=HTTP_HEADERS,
                timeout=16.0,
            )
            if r.status_code != 200:
                print(f"[stations] overpass {url} status={r.status_code}")
                continue
            elements = (r.json() or {}).get("elements") or []
            if not elements:
                print(f"[stations] overpass {url} empty")
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
                st = _station_from_osm_tags(
                    lat, lon, float(slat), float(slon), tags, el.get("id")
                )
                if st and st["distance_mi"] <= radius_mi + 0.6:
                    stations.append(st)
            if stations:
                stations.sort(key=lambda x: x["distance_mi"])
                print(f"[stations] overpass OK {len(stations)} via {url.split('/')[2]}")
                return stations
        except Exception as e:
            print(f"[stations] overpass fail {url}: {e}")
            continue
    return []


def _fetch_photon(lat: float, lon: float, radius_mi: float) -> list[dict]:
    """Photon (Komoot) — respaldo cuando Overpass/Nominatim fallan en la nube."""
    out: list[dict] = []
    seen: set[str] = set()
    queries = ("gas station", "fuel", "petrol")
    for q in queries:
        try:
            r = httpx.get(
                "https://photon.komoot.io/api/",
                params={
                    "q": q,
                    "lat": lat,
                    "lon": lon,
                    "limit": 25,
                    "lang": "en",
                },
                headers=HTTP_HEADERS,
                timeout=12.0,
            )
            if r.status_code != 200:
                continue
            for feat in (r.json() or {}).get("features") or []:
                props = feat.get("properties") or {}
                geom = feat.get("geometry") or {}
                coords = geom.get("coordinates") or []
                if len(coords) < 2:
                    continue
                slon, slat = float(coords[0]), float(coords[1])
                # filtrar amenity fuel si viene en osm
                osm_key = (props.get("osm_key") or "").lower()
                osm_val = (props.get("osm_value") or "").lower()
                name_raw = props.get("name") or props.get("street") or "Gas Station"
                blob = f"{name_raw} {props.get('type', '')} {osm_key} {osm_val}".lower()
                if osm_val and osm_val not in ("fuel", "gas", "fuel_station"):
                    # permitir si el nombre parece gasolinera
                    if not any(
                        k in blob
                        for k in (
                            "gas",
                            "fuel",
                            "shell",
                            "chevron",
                            "exxon",
                            "mobil",
                            "circle",
                            "costco",
                            "valero",
                            "conoco",
                            "phillips",
                            "arco",
                            "maverik",
                            "quik",
                            "murphy",
                            "7-eleven",
                            "bp",
                            "sinclair",
                        )
                    ):
                        continue
                brand = _guess_brand(name_raw + " " + str(props.get("type", "")))
                street = " ".join(
                    p
                    for p in [
                        str(props.get("housenumber") or ""),
                        str(props.get("street") or ""),
                    ]
                    if p
                ).strip()
                city = props.get("city") or props.get("town") or ""
                state = props.get("state") or ""
                postcode = props.get("postcode") or ""
                address = (
                    ", ".join(p for p in [street, city, state, postcode] if p) or None
                )
                name = _pretty_station_name(name_raw, brand, name_raw, address)
                brand = _display_brand(brand, name)
                dist = haversine_miles(lat, lon, slat, slon)
                if dist > radius_mi + 0.6:
                    continue
                sid = _station_id(slat, slon, name)
                if sid in seen:
                    continue
                seen.add(sid)
                maps_query = name
                if street:
                    maps_query = f"{name}, {street}" + (f", {city}" if city else "")
                out.append(
                    {
                        "id": sid,
                        "name": name,
                        "brand": brand,
                        "lat": slat,
                        "lon": slon,
                        "address": address,
                        "maps_query": maps_query,
                        "distance_mi": dist,
                        "phone": None,
                        "website": None,
                        "osm_id": props.get("osm_id"),
                        "source": "photon",
                        "is_demo": False,
                        "nav_mode": "coords",
                    }
                )
        except Exception as e:
            print(f"[stations] photon fail: {e}")
            continue
        if len(out) >= 12:
            break
        time.sleep(0.15)
    out.sort(key=lambda x: x["distance_mi"])
    if out:
        print(f"[stations] photon OK {len(out)}")
    return out


def _merge_stations(*lists: list[dict], radius_mi: float) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for lst in lists:
        for s in lst or []:
            if s["id"] in seen:
                continue
            if s.get("distance_mi", 999) > radius_mi + 0.6:
                continue
            seen.add(s["id"])
            out.append(s)
    out.sort(key=lambda x: x["distance_mi"])
    return out


def _enrich_missing_addresses(
    stations: list[dict], *, max_lookups: int = 12
) -> list[dict]:
    """
    Si OSM/Photon no traen calle, rellena con reverse Nominatim (calle).
    Límite de lookups para no alargar la búsqueda en ciudades con muchos huecos.
    """
    from backend.geo import reverse_geocode_street

    n = 0
    for s in stations:
        if (s.get("address") or "").strip():
            continue
        if n >= max_lookups:
            # fallback suave: al menos ciudad no queda en blanco en UI
            if not s.get("maps_query"):
                s["maps_query"] = (
                    f"{s.get('name') or 'Gas'} "
                    f"@{float(s['lat']):.5f},{float(s['lon']):.5f}"
                )
            continue
        try:
            addr = reverse_geocode_street(float(s["lat"]), float(s["lon"]))
        except Exception:
            addr = None
        n += 1
        if addr:
            s["address"] = addr
            s["maps_query"] = f"{s.get('name') or 'Gas Station'}, {addr}"
        else:
            s["maps_query"] = (
                f"{s.get('name') or 'Gas'} "
                f"@{float(s['lat']):.5f},{float(s['lon']):.5f}"
            )
    return stations


def stations_near(
    lat: float, lon: float, radius_mi: float = 5.0, limit: int = 40
) -> list[dict]:
    """
    Lista estaciones REALES cerca de lat/lon.
    Orden: caché → Overpass → Photon → Nominatim.
    """
    lat_f, lon_f = float(lat), float(lon)
    radius_mi = float(radius_mi)

    cached = _load_cache(lat_f, lon_f, radius_mi)
    if cached:
        for s in cached:
            s["distance_mi"] = haversine_miles(
                lat_f, lon_f, float(s["lat"]), float(s["lon"])
            )
            s["is_demo"] = False
            raw = s.get("name") or "Gas Station"
            brand = s.get("brand") or _guess_brand(
                f"{raw} {s.get('address', '')}"
            )
            s["name"] = _pretty_station_name(
                raw,
                brand,
                f"{raw}, {s.get('address', '')}",
                s.get("address"),
            )
            s["brand"] = _display_brand(brand, s["name"])
        cached = [s for s in cached if s["distance_mi"] <= radius_mi + 0.5]
        cached.sort(key=lambda x: x["distance_mi"])
        if cached:
            # Caché vieja puede no tener address: enriquecer huecos
            return _enrich_missing_addresses(cached[:limit])[:limit]

    # Parallel-ish fail-over rápido: Photon primero (rápido en nube),
    # luego Overpass, luego Nominatim.
    stations = _fetch_photon(lat_f, lon_f, radius_mi)

    if len(stations) < 8:
        stations = _merge_stations(
            stations, _fetch_overpass(lat_f, lon_f, radius_mi), radius_mi=radius_mi
        )

    if len(stations) < 5:
        stations = _merge_stations(
            stations, _fetch_nominatim(lat_f, lon_f, radius_mi), radius_mi=radius_mi
        )

    if stations:
        stations = _enrich_missing_addresses(stations[:60])
        _save_cache(lat_f, lon_f, radius_mi, stations[:60])
        return stations[:limit]

    print("[stations] sin resultados: overpass/photon/nominatim vacíos")
    return []
