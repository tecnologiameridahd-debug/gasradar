"""
Búsqueda de precios reutilizable (web API + bot Telegram).
GasBuddy VPS + OSM/AAA. Sin Zyla.
"""
from __future__ import annotations

import re
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
_SEARCH_CACHE_TTL = 25 * 60  # 25 min — reabrir mismo ZIP / ciudad es instantáneo
_SEARCH_CACHE_MAX = 120


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
        loc = f"g:{round(float(lat), 2)},{round(float(lon), 2)}"
    else:
        loc = "default"
    return f"{loc}|{fuel}|{round(float(radius_mi), 1)}|{int(limit)}|{'q' if quick else 'f'}"


def _mem_get(key: str) -> dict | None:
    hit = _SEARCH_CACHE.get(key)
    if not hit:
        return None
    if time.time() - float(hit.get("ts") or 0) > _SEARCH_CACHE_TTL:
        _SEARCH_CACHE.pop(key, None)
        return None
    data = hit.get("data")
    if not isinstance(data, dict):
        return None
    out = dict(data)
    out["cached"] = True
    return out


def _cache_get(key: str) -> dict | None:
    hit = _SEARCH_CACHE.get(key)
    if hit and time.time() - float(hit.get("ts") or 0) <= _SEARCH_CACHE_TTL:
        data = hit.get("data")
        if isinstance(data, dict):
            out = dict(data)
            out["cached"] = True
            return out
    elif hit:
        _SEARCH_CACHE.pop(key, None)
    # Caché aparte (Postgres): sobrevive al redeploy y a que un VPS se caiga
    try:
        from backend.price_cache import get as db_get

        disk = db_get(f"search:{key}", ttl=_SEARCH_CACHE_TTL)
        if isinstance(disk, dict) and (disk.get("stations") or disk.get("cheapest")):
            _SEARCH_CACHE[key] = {"ts": time.time(), "data": disk}
            out = dict(disk)
            out["cached"] = True
            return out
    except Exception:
        pass
    return None


def peek_cached_search(zip_code: str | None, fuel: str = "regular") -> dict | None:
    """Caché en memoria de ese ZIP (sin 16 idas a Postgres: eso colgaba 16s)."""
    z = (str(zip_code or "").strip())[:5]
    if len(z) != 5:
        return None
    now = time.time()
    for radius in (5.0, 8.0):
        for limit in (12, 16, 22, 30):
            for quick in (True, False):
                key = _search_cache_key(
                    zip_code=z,
                    lat=None,
                    lon=None,
                    radius_mi=radius,
                    fuel=fuel,
                    limit=limit,
                    quick=quick,
                )
                hit = _SEARCH_CACHE.get(key)
                if not hit or now - float(hit.get("ts") or 0) > _SEARCH_CACHE_TTL:
                    continue
                data = hit.get("data")
                if not isinstance(data, dict):
                    continue
                stations = data.get("stations") or []
                if any(s.get("price") is not None for s in stations) or data.get("cheapest"):
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
    try:
        from backend.price_cache import put as db_put

        db_put(f"search:{key}", data)
    except Exception:
        pass


def _overlay_reports(result: dict, fuel: str) -> dict:
    """Sobre un resultado cacheado: el reporte fresco gana al precio de 3 h."""
    try:
        from backend.prices import apply_user_reports, cheapest_summary

        stations = apply_user_reports(list(result.get("stations") or []), fuel)
        stations.sort(
            key=lambda x: (
                round(float(x.get("price") or 99), 3),
                float(x.get("distance_mi") or 99),
            )
        )
        out = dict(result)
        out["stations"] = stations
        out["count"] = len(stations)
        out["user_reports_count"] = sum(
            1 for s in stations if s.get("price_source") == "user"
        )
        out["cheapest"] = cheapest_summary(stations) if stations else out.get("cheapest")
        avg_fuel = None
        try:
            avg = out.get("state_avg") or {}
            avg_fuel = avg.get(fuel) or avg.get("regular")
        except Exception:
            avg_fuel = None
        if avg_fuel is not None:
            for s in stations:
                try:
                    s["vs_avg"] = round(float(s["price"]) - float(avg_fuel), 3)
                except Exception:
                    pass
            if out.get("cheapest"):
                out["cheapest"]["vs_avg"] = out["cheapest"].get("vs_avg")
                try:
                    out["cheapest"]["savings_vs_avg"] = round(
                        float(avg_fuel) - float(out["cheapest"]["price"]), 3
                    )
                    out["cheapest"]["source"] = out["cheapest"].get("source")
                except Exception:
                    pass
        return out
    except Exception as e:
        print(f"[search] overlay reports: {e}")
        return result


# Techo para precios REALES (VPS). Corto: si el scraper se cuelga, la app no se queda 20s en blanco.
_SEARCH_HARD_DEADLINE_S = 10.0


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
    client_ip: str = "",
    client_country: str = "",
) -> dict:
    """Misma lógica que GET /api/search. Lanza ValueError si ZIP inválido.

    quick=True: modo bot Telegram — menos estaciones, deadline más corto,
    pero SÍ intenta VPS/GasBuddy (antes se saltaba y el bot quedaba sin datos).
    Si no hay VPS, rellena con estimados AAA/EIA (bot). Web (quick=False):
    solo precios reales GasBuddy/reportes.
    """
    t_start = time.time()
    hard_deadline = 12.0 if quick else 8.0

    def _budget_left() -> float:
        return max(0.0, hard_deadline - (time.time() - t_start))

    label = DEFAULT_LABEL
    state = "CO"
    zip_code = None
    city = None
    if zip:
        z = re.sub(r"[^0-9]", "", str(zip))[:5]
        if len(z) != 5:
            raise ValueError(f"ZIP {zip} no encontrado")
        zip_code = z
        label = f"ZIP {z}"
    elif lat is not None and lon is not None:
        label = f"Tu ubicación ({float(lat):.3f}, {float(lon):.3f})"
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
    cached = _mem_get(ck)
    if cached is not None:
        # No servir cache solo de estimados si pedimos precios reales
        st0 = cached.get("stations") or []
        live0 = sum(
            1
            for s in st0
            if s.get("price_source") in ("gasbuddy", "user")
        )
        if live0 > 0 or quick:
            if track:
                try:
                    from backend.analytics import track_event, search_detail

                    track_event(
                        "search_cache",
                        path="/api/search",
                        detail=search_detail(zip_code=zip_code or zip, lat=lat, lon=lon),
                        ip=client_ip,
                        ip_country=client_country,
                    )
                except Exception:
                    pass
            return _overlay_reports(cached, fuel)

    from concurrent.futures import ThreadPoolExecutor, wait

    from backend.geo import haversine_miles
    from backend.stations import _display_brand, _pretty_station_name, _station_id

    gb_stations: list = []
    stations: list = []
    partial = False
    live_only = not quick  # web: solo precios reales; bot puede usar estimados

    def _job_vps() -> list:
        # Importante: el bot (quick) también necesita VPS — si se omite, a menudo
        # no hay datos (OSM/estimados fallan o llegan vacíos en Render).
        try:
            from backend.vps_scraper_client import fetch_vps_stations

            lim = min(max(int(limit), 15), 30) if quick else min(max(int(limit), 22), 30)
            return fetch_vps_stations(
                zip_code=str(zip_code) if zip_code else None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None,
                fuel=fuel,
                limit=lim,
                timeout_s=min(6.5, max(2.5, _budget_left() - 0.3)),
            )
        except Exception as e:
            print(f"[search] vps_scraper: {e}")
            return []

    def _job_geo() -> dict | None:
        try:
            if zip_code:
                return geocode_zip(str(zip_code))
            if lat is not None and lon is not None:
                return reverse_geocode(float(lat), float(lon))
        except Exception as e:
            print(f"[search] geo: {e}")
        return None

    t0 = time.time()
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        fut_vps = pool.submit(_job_vps)
        fut_geo = pool.submit(_job_geo)
        vps_wait = min(6.5, max(2.0, _budget_left() - 0.4))
        wait([fut_vps], timeout=vps_wait)
        try:
            if fut_vps.done():
                gb_stations = fut_vps.result(timeout=0.05) or []
            else:
                print("[search] vps still running after wait — no retry")
                gb_stations = []
        except Exception as e:
            print(f"[search] vps fail: {e}")
            gb_stations = []
        try:
            if fut_geo.done():
                g = fut_geo.result(timeout=0.05)
                if g:
                    if lat is None and g.get("lat") is not None:
                        lat, lon = g["lat"], g["lon"]
                    label = g.get("label") or label
                    state = g.get("state") or state
                    zip_code = g.get("zip") or zip_code
                    city = g.get("city") or city
        except Exception:
            pass
    finally:
        try:
            pool.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            pool.shutdown(wait=False)

    if (lat is None or lon is None) and gb_stations:
        try:
            lat = float(gb_stations[0]["lat"])
            lon = float(gb_stations[0]["lon"])
        except Exception:
            pass
    if lat is None or lon is None:
        lat, lon = DEFAULT_LAT, DEFAULT_LON

    if not gb_stations and zip_code and _budget_left() > 0.4:
        peeked = peek_cached_search(str(zip_code), fuel=fuel)
        if peeked and (peeked.get("stations") or peeked.get("cheapest")):
            print("[search] vps miss — using nearby zip cache")
            out = _overlay_reports(peeked, fuel)
            out["partial"] = True
            out["cached"] = True
            return out

    if not gb_stations and not quick:
        partial = True  # sin precios en vivo aún
    print(
        f"[search] vps={len(gb_stations)} osm={len(stations)} "
        f"live_only={live_only} in {time.time() - t0:.1f}s"
    )

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

    # 1) SOLO precios REALES del VPS/GasBuddy (y reportes de usuario si hay)
    if gb_stations:
        for gs in gb_stations:
            row = _live_row(gs, "gasbuddy")
            if not row:
                continue
            if any(_near(row, p, 0.12) for p in priced):
                continue
            priced.append(row)
        print(f"[search] live gasbuddy n={len(priced)}")

    # 2) Web (live_only): NO añadir estimados AAA/EIA de OSM
    #    Bot Telegram (quick): sí puede rellenar con estimados si no hay VPS
    if (not live_only or not priced) and stations and (quick or not live_only):
        osm_priced = attach_prices(stations, state=state, fuel=fuel, city=city)
        for item in osm_priced:
            low = f"{item.get('name')} {item.get('brand') or ''}".lower()
            if any(x in low for x in ("dispensary", "cannabis", "marijuana", "weed")):
                continue
            if any(_near(item, p, 0.12) for p in priced):
                continue
            try:
                if float(item.get("distance_mi") or 99) > float(radius_mi) + 0.35:
                    continue
            except Exception:
                pass
            priced.append(item)

    # Solo live en web
    if live_only:
        priced = [
            p
            for p in priced
            if p.get("price_source") in ("gasbuddy", "user")
        ]

    # Reportes de usuarios pisan el precio de esa estación (aunque el caché tenga 3 h)
    try:
        from backend.prices import apply_user_reports

        priced = apply_user_reports(priced, fuel)
    except Exception as e:
        print(f"[search] apply_user_reports: {e}")

    priced.sort(
        key=lambda x: (
            round(float(x.get("price") or 99), 3),
            float(x.get("distance_mi") or 99),
        )
    )
    if len(priced) > int(limit):
        priced = priced[: int(limit)]

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
        eia_txt = f" {gb_hits} precios en vivo (GasBuddy)."
    elif quick:
        eia_txt = " Precios de referencia (bot)."
    else:
        eia_txt = ""

    note = ""
    if not priced and live_only:
        note = (
            " No hay precios en vivo cerca ahora. "
            "Prueba de nuevo en unos segundos o sube el radio a 10 mi."
        )
        partial = True
    elif not priced:
        note = (
            " No se encontraron estaciones reales cerca. "
            "Prueba un radio mayor (10 mi) o otro ZIP."
        )

    user_reports = sum(1 for s in priced if s.get("price_source") == "user")

    # Analytics en background: no sumar latencia de Neon a la búsqueda
    if track:
        def _bg_track() -> None:
            try:
                from backend.analytics import track_event, search_detail

                track_event(
                    "search",
                    path="/api/search",
                    detail=search_detail(zip_code=zip_code or zip, lat=lat, lon=lon),
                    ip=client_ip,
                    ip_country=client_country,
                )
            except Exception:
                pass

        try:
            import threading

            threading.Thread(target=_bg_track, daemon=True).start()
        except Exception:
            _bg_track()

    elapsed = round(time.time() - t_start, 2)
    print(f"[search] done total={elapsed}s stations={len(priced)} partial={partial}")

    from backend.min_wage import wage_for_state

    out = {
        "center": {
            "lat": lat,
            "lon": lon,
            "label": label,
            "state": state,
            "zip": zip_code,
        },
        "min_wage": wage_for_state(state),
        "fuel": fuel,
        "radius_mi": radius_mi,
        "partial": partial,
        "elapsed_s": elapsed,
        "state_avg": avg,
        "price_meta": meta,
        "count": len(priced),
        "user_reports_count": user_reports,
        "cheapest": best,
        "stations": priced,
        "cached": False,
        "disclaimer": (
            (
                "Precios en vivo del scraper GasBuddy cerca de ti."
                f"{eia_txt} "
                "Pueden variar en la bomba; reporta el precio real al pasar."
                if gb_hits
                else (
                    "Sin precios en vivo en esta búsqueda."
                    f"{eia_txt} "
                    "Toca Buscar de nuevo o amplía el radio."
                )
            )
            + f"{note}"
        ),
        "live_prices": bool(gb_hits),
    }
    try:
        # No cachear vacío: si no, el usuario reintenta y “no busca”
        if priced:
            _cache_put(ck, out)
        else:
            _SEARCH_CACHE.pop(ck, None)
    except Exception:
        pass
    return out
