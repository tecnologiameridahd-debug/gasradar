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


# Techo duro total de la búsqueda (ZIP nuevo). No superar ~10s de reloj.
_SEARCH_HARD_DEADLINE_S = 9.0


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

    quick=True: modo bot Telegram (sin GasBuddy, menos estaciones, más rápido).
    Techo ~9s: si VPS/mapa van lentos, devuelve lo que haya (nunca 30s).
    """
    t_start = time.time()

    def _budget_left() -> float:
        return max(0.0, _SEARCH_HARD_DEADLINE_S - (time.time() - t_start))

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
        # Reverse geo es lento; solo si hay presupuesto (evita +3s en GPS)
        rev = None
        if _budget_left() > 2.5:
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
        return cached

    # VPS + OSM en paralelo, techo duro (ZIP nuevo ≤ ~10s)
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

    from backend.geo import haversine_miles
    from backend.stations import _display_brand, _pretty_station_name, _station_id

    gb_stations: list = []
    stations: list = []
    partial = False

    def _job_vps() -> list:
        if quick:
            return []
        try:
            from backend.vps_scraper_client import fetch_vps_stations

            return fetch_vps_stations(
                zip_code=str(zip_code) if zip_code else None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None,
                fuel=fuel,
                limit=min(max(int(limit), 25), 40),
            )
        except Exception as e:
            print(f"[search] vps_scraper: {e}")
            return []

    def _job_osm() -> list:
        try:
            return stations_near(
                float(lat),
                float(lon),
                radius_mi=radius_mi,
                limit=min(int(limit) + 10, 30),
                enrich=False,
            )
        except Exception as e:
            print(f"[search] stations_near: {e}")
            return []

    t0 = time.time()
    # wait=False: no bloquear la respuesta aunque VPS siga en segundo plano
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        fut_vps = pool.submit(_job_vps)
        fut_osm = pool.submit(_job_osm)
        # Máx. ~5.5s de espera a fuentes externas (dentro del techo de 9s)
        wait_cap = min(5.5, max(0.5, _budget_left() - 1.2))
        wait([fut_vps, fut_osm], timeout=wait_cap, return_when=FIRST_COMPLETED)
        remain = min(2.0, max(0.3, _budget_left() - 0.8))
        wait([fut_vps, fut_osm], timeout=remain)
        try:
            if fut_vps.done():
                gb_stations = fut_vps.result(timeout=0.05) or []
            else:
                print("[search] vps skip (deadline) — respuesta rápida sin VPS")
                gb_stations = []
                partial = True
        except Exception as e:
            print(f"[search] vps timeout/fail: {e}")
            gb_stations = []
            partial = True
        try:
            if fut_osm.done():
                stations = fut_osm.result(timeout=0.05) or []
            else:
                print("[search] osm skip (deadline)")
                stations = []
                partial = True
        except Exception as e:
            print(f"[search] osm timeout/fail: {e}")
            stations = []
            partial = True
    finally:
        try:
            pool.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            pool.shutdown(wait=False)
    print(
        f"[search] parallel vps={len(gb_stations)} osm={len(stations)} "
        f"partial={partial} in {time.time() - t0:.1f}s budget_left={_budget_left():.1f}s"
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

    # 2) OSM + AAA: rellenar huecos (ya cargado en paralelo arriba)
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
        nm = (item.get("name") or "").strip().lower()
        brand = (item.get("brand") or "").strip().lower()
        # Basura: sin marca y sin nombre útil
        if nm in ("gas station", "gas", "fuel", "") and not brand:
            if not (item.get("address") or "").strip():
                continue
        if "maybe closed" in nm or "tacos" in nm:
            continue
        # Duplicado de un live GasBuddy muy cerca → no añadir otra ficha
        if any(_near(item, p, 0.12) for p in priced):
            continue
        # Fuera de radio del usuario
        try:
            if float(item.get("distance_mi") or 99) > float(radius_mi) + 0.35:
                continue
        except Exception:
            pass
        priced.append(item)

    # Orden: más barato primero, pero live/GB antes que estimado a mismo precio;
    # distancia como desempate (la Conoco a 0.7 mi no se “pierde” del todo)
    priced.sort(
        key=lambda x: (
            round(float(x.get("price") or 99), 3),
            0 if x.get("price_source") in ("gasbuddy", "user") else 1,
            float(x.get("distance_mi") or 99),
        )
    )
    # Cap final: preferir las más cercanas entre las baratas del top
    if len(priced) > int(limit):
        # Mantener todos los gasbuddy; completar con cercanos
        gb_keep = [p for p in priced if p.get("price_source") == "gasbuddy"]
        rest = [p for p in priced if p.get("price_source") != "gasbuddy"]
        rest.sort(key=lambda x: float(x.get("distance_mi") or 99))
        room = max(0, int(limit) - len(gb_keep))
        priced = gb_keep + rest[:room]
        priced.sort(
            key=lambda x: (
                round(float(x.get("price") or 99), 3),
                0 if x.get("price_source") in ("gasbuddy", "user") else 1,
                float(x.get("distance_mi") or 99),
            )
        )

    # NUNCA re-llamar stations_near aquí (duplicaba 15–30s y causaba "Tardó mucho")
    if not priced and stations:
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
    elif partial and not gb_hits:
        note = (
            " Resultados rápidos (precios de referencia). "
            "Vuelve a buscar en unos segundos para precios en vivo si el scraper responde."
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
