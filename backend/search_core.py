"""
Búsqueda de precios reutilizable (web API + bot Telegram).
GasBuddy VPS + OSM/AAA. Sin Zyla.
"""
from __future__ import annotations

import time

from backend.geo import (
    DEFAULT_LABEL,
    DEFAULT_LAT,
    DEFAULT_LON,
    geocode_zip,
    reverse_geocode,
)
from backend.prices import (
    attach_prices,
    cheapest_summary,
    price_meta,
)
from backend.stations import stations_near

# Cache de resultados completos (misma zona / fuel / radio)
_SEARCH_CACHE: dict[str, dict] = {}
_SEARCH_CACHE_TTL = 10 * 60  # 10 min
_SEARCH_CACHE_MAX = 80


def _search_cache_key(
    *,
    zip_code: str | None,
    lat: float | None,
    lon: float | None,
    radius_mi: float,
    fuel: str,
    limit: int,
    quick: bool,
) -> str:
    if zip_code:
        loc = f"z:{zip_code}"
    elif lat is not None and lon is not None:
        loc = f"g:{round(float(lat), 3)},{round(float(lon), 3)}"
    else:
        loc = "default"
    return f"{loc}|{fuel}|{round(float(radius_mi), 1)}|{int(limit)}|{'q' if quick else 'f'}"


def _cache_get(key: str) -> dict | None:
    hit = _SEARCH_CACHE.get(key)
    if not hit:
        return None
    if time.time() - float(hit.get("ts") or 0) > _SEARCH_CACHE_TTL:
        _SEARCH_CACHE.pop(key, None)
        return None
    data = hit.get("data")
    if isinstance(data, dict):
        out = dict(data)
        out["cached"] = True
        return out
    return None


def _cache_put(key: str, data: dict) -> None:
    if len(_SEARCH_CACHE) >= _SEARCH_CACHE_MAX:
        # borrar entradas más viejas
        oldest = sorted(_SEARCH_CACHE.items(), key=lambda kv: kv[1].get("ts") or 0)
        for k, _ in oldest[: max(1, _SEARCH_CACHE_MAX // 4)]:
            _SEARCH_CACHE.pop(k, None)
    _SEARCH_CACHE[key] = {"ts": time.time(), "data": data}


def run_search(
    *,
    lat: float | None = None,
    lon: float | None = None,
    zip: str | None = None,
    radius_mi: float = 5.0,
    fuel: str = "regular",
    limit: int = 30,
    track: bool = True,
    quick: bool = False,
) -> dict:
    """Misma lógica que GET /api/search. Lanza ValueError si ZIP inválido.

    quick=True: modo bot Telegram (sin GasBuddy, menos estaciones, más rápido).
    """
    label = DEFAULT_LABEL
    state = "CO"
    zip_code = None
    city = None
    if zip:
        g = geocode_zip(zip)
        if not g:
            raise ValueError(f"ZIP {zip} no encontrado")
        lat, lon = g["lat"], g["lon"]
        label = g["label"]
        state = g.get("state") or "CO"
        zip_code = g.get("zip") or zip
        city = g.get("city") or None
    elif lat is not None and lon is not None:
        rev = reverse_geocode(float(lat), float(lon))
        if rev:
            label = rev["label"]
            state = rev.get("state") or "CO"
            zip_code = rev.get("zip")
            city = rev.get("city") or None
        else:
            label = f"Tu ubicación ({float(lat):.3f}, {float(lon):.3f})"
            state = "CO"
    else:
        lat, lon = DEFAULT_LAT, DEFAULT_LON
        label = DEFAULT_LABEL
        state = "CO"
        city = "Denver"

    if quick:
        limit = min(int(limit), 12)
    else:
        limit = min(int(limit), 22)

    # Respuesta instantánea si ya buscamos esta zona hace poco
    ck = _search_cache_key(
        zip_code=str(zip_code) if zip_code else None,
        lat=float(lat) if lat is not None else None,
        lon=float(lon) if lon is not None else None,
        radius_mi=radius_mi,
        fuel=fuel,
        limit=limit,
        quick=quick,
    )
    cached = _cache_get(ck)
    if cached is not None:
        if track:
            try:
                from backend.analytics import track_event

                track_event(
                    "search_cache",
                    path="/api/search",
                    detail=str(zip_code or "gps")[:40],
                )
            except Exception:
                pass
        return cached

    # EIA/AAA: price_meta(fast=True) más abajo. Sin Zyla.

    # Precios + dirección: VPS GasBuddy (todo USA, por ZIP/GPS)
    gb_stations: list = []
    if not quick:
        try:
            from backend.vps_scraper_client import fetch_vps_stations

            gb_stations = fetch_vps_stations(
                zip_code=str(zip_code) if zip_code else None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None,
                fuel=fuel,
                limit=min(max(int(limit), 25), 40),
            )
        except Exception as e:
            print(f"[search] vps_scraper: {e}")
            gb_stations = []
        if not gb_stations:
            try:
                from backend.gasbuddy_src import _enabled as gasbuddy_enabled
                from backend.gasbuddy_src import fetch_gasbuddy_stations

                if gasbuddy_enabled():
                    gb_stations = fetch_gasbuddy_stations(
                        zip_code=str(zip_code) if zip_code else None,
                        lat=float(lat) if lat is not None else None,
                        lon=float(lon) if lon is not None else None,
                        fuel=fuel,
                        limit=min(int(limit), 20),
                    )
            except Exception as e:
                print(f"[search] gasbuddy: {e}")
                gb_stations = []

    from backend.geo import haversine_miles
    from backend.stations import _display_brand, _pretty_station_name, _station_id

    def _live_row(src: dict, source_tag: str) -> dict | None:
        if src.get("lat") is None or src.get("lon") is None or src.get("price") is None:
            return None
        dist = src.get("distance_mi")
        if dist is None:
            dist = haversine_miles(
                float(lat), float(lon), float(src["lat"]), float(src["lon"])
            )
        if dist > float(radius_mi) + 1.5:
            return None
        name = _pretty_station_name(
            src.get("name") or "Gas Station",
            src.get("brand"),
            src.get("name") or "",
            src.get("address"),
        )
        low = f"{name} {src.get('brand') or ''}".lower()
        if any(x in low for x in ("dispensary", "cannabis", "marijuana", "weed")):
            return None
        brand = _display_brand(src.get("brand"), name)
        sid = _station_id(float(src["lat"]), float(src["lon"]), name)
        addr = (src.get("address") or "").strip() or None
        maps_q = f"{name}, {addr}".strip(", ") if addr else f"{name} @{float(src['lat']):.5f},{float(src['lon']):.5f}"
        return {
            "id": sid,
            "name": name,
            "brand": brand,
            "lat": float(src["lat"]),
            "lon": float(src["lon"]),
            "address": addr,
            "maps_query": maps_q,
            "distance_mi": float(dist),
            "phone": None,
            "website": None,
            "source": source_tag,
            "is_demo": False,
            "nav_mode": "coords",
            "price": float(src["price"]),
            "price_source": source_tag,
            "price_confidence": "high",
            "price_age_hours": None,
            "reports_count": 0,
            "prices": {
                fuel: {
                    "price": float(src["price"]),
                    "source": source_tag,
                    "confidence": "high",
                    "reports_count": 0,
                    "age_hours": None,
                }
            },
        }

    def _near(a: dict, b: dict, mi: float = 0.15) -> bool:
        try:
            return (
                haversine_miles(
                    float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"])
                )
                < mi
            )
        except Exception:
            return False

    priced: list = []

    # 1) PRIORIDAD: GasBuddy/VPS (nombre + dirección + precio real) en cualquier ZIP USA
    if gb_stations:
        for gs in gb_stations:
            row = _live_row(gs, "gasbuddy")
            if not row:
                continue
            if any(_near(row, p, 0.12) for p in priced):
                continue
            priced.append(row)
        print(f"[search] gasbuddy primary n={len(priced)}")

    # 2) OSM + AAA solo si GasBuddy no trajo lista sólida
    # Con 8+ GasBuddy (nombre+dir+precio) no mezclamos basura OSM ("Gas station")
    gb_n = sum(1 for p in priced if p.get("price_source") == "gasbuddy")
    need_osm = gb_n < 8

    if need_osm and len(priced) < max(8, min(int(limit), 15)):
        stations = stations_near(
            float(lat), float(lon), radius_mi=radius_mi, limit=min(int(limit), 20)
        )
        osm_priced = (
            attach_prices(stations, state=state, fuel=fuel, city=city) if stations else []
        )
        for item in osm_priced:
            if (item.get("address") or "").strip():
                continue
            for gb in priced:
                if gb.get("price_source") != "gasbuddy":
                    continue
                if not (gb.get("address") or "").strip():
                    continue
                if _near(item, gb, 0.2):
                    item["address"] = gb["address"]
                    item["maps_query"] = f"{item.get('name') or 'Gas'}, {gb['address']}"
                    if item.get("price_source") not in ("user", "gasbuddy"):
                        item["price"] = gb["price"]
                        item["price_source"] = "gasbuddy"
                        item["price_confidence"] = "high"
                        item["prices"] = dict(gb.get("prices") or {})
                    break

        for item in osm_priced:
            low = f"{item.get('name')} {item.get('brand') or ''}".lower()
            if any(x in low for x in ("dispensary", "cannabis", "marijuana", "weed")):
                continue
            # Evitar relleno basura: "Gas station" sin marca ni dirección
            nm = (item.get("name") or "").strip().lower()
            if nm in ("gas station", "gas", "fuel") and not (item.get("address") or "").strip():
                continue
            if "maybe closed" in nm or "tacos" in nm:
                continue
            if any(_near(item, p, 0.12) for p in priced):
                continue
            priced.append(item)

    priced.sort(
        key=lambda x: (
            round(float(x.get("price") or 99), 3),
            0 if x.get("price_source") in ("gasbuddy", "user") else 1,
            float(x.get("distance_mi") or 99),
        )
    )

    if not priced:
        stations = stations_near(float(lat), float(lon), radius_mi=radius_mi, limit=limit)
        priced = (
            attach_prices(stations, state=state, fuel=fuel, city=city) if stations else []
        )

    best = cheapest_summary(priced) if priced else None
    meta = price_meta(state, fast=True, city=city)
    avg = meta["state_avg"]
    avg_fuel = avg.get(fuel) or avg.get("regular")

    if best and avg_fuel:
        best["savings_vs_avg"] = round(float(avg_fuel) - float(best["price"]), 3)
        best["state_avg_fuel"] = avg_fuel

    eia_txt = ""
    gb_hits = sum(1 for s in priced if s.get("price_source") == "gasbuddy")
    if gb_hits:
        eia_txt = f" {gb_hits} precios vía GasBuddy (scraper)."
    elif meta.get("eia_ok") and meta.get("eia_period"):
        eia_txt = f" Promedio estatal EIA (semana {meta['eia_period']})."
    elif meta.get("avg_source") in ("aaa", "aaa_metro"):
        eia_txt = " Promedio AAA / zona."
    else:
        eia_txt = " Precios de referencia (estimados). Reporta al pasar por la bomba."

    note = ""
    if not priced:
        note = (
            " No se encontraron estaciones reales cerca. "
            "Prueba un radio mayor (10 mi) o otro ZIP."
        )

    user_reports = sum(1 for s in priced if s.get("price_source") == "user")

    if track:
        try:
            from backend.analytics import track_event

            detail = zip_code or (zip or "") or ("gps" if lat is not None else "")
            track_event("search", path="/api/search", detail=str(detail)[:40])
        except Exception:
            pass

    out = {
        "center": {
            "lat": lat,
            "lon": lon,
            "label": label,
            "state": state,
            "zip": zip_code,
        },
        "fuel": fuel,
        "radius_mi": radius_mi,
        "state_avg": avg,
        "price_meta": meta,
        "count": len(priced),
        "user_reports_count": user_reports,
        "cheapest": best,
        "stations": priced,
        "cached": False,
        "disclaimer": (
            "Estaciones reales (OpenStreetMap). "
            "Precios: reportes de la comunidad o estimación EIA + marca."
            f"{eia_txt} "
            "No es precio de bomba en vivo — reporta el precio real al pasar."
            f"{note}"
        ),
    }
    try:
        _cache_put(ck, out)
    except Exception:
        pass
    return out
