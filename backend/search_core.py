"""
Búsqueda de precios reutilizable (web API + bot Telegram).
"""
from __future__ import annotations

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
    fetch_eia_state_averages,
    fetch_zyla_stations,
    fetch_zyla_zip_prices,
    merge_zyla_prices_into_stations,
    price_meta,
)
from backend.stations import stations_near


def run_search(
    *,
    lat: float | None = None,
    lon: float | None = None,
    zip: str | None = None,
    radius_mi: float = 5.0,
    fuel: str = "regular",
    limit: int = 30,
    track: bool = True,
) -> dict:
    """Misma lógica que GET /api/search. Lanza ValueError si ZIP inválido."""
    label = DEFAULT_LABEL
    state = "CO"
    zip_code = None
    if zip:
        g = geocode_zip(zip)
        if not g:
            raise ValueError(f"ZIP {zip} no encontrado")
        lat, lon = g["lat"], g["lon"]
        label = g["label"]
        state = g.get("state") or "CO"
        zip_code = g.get("zip") or zip
    elif lat is not None and lon is not None:
        rev = reverse_geocode(float(lat), float(lon))
        if rev:
            label = rev["label"]
            state = rev.get("state") or "CO"
            zip_code = rev.get("zip")
        else:
            label = f"Tu ubicación ({float(lat):.3f}, {float(lon):.3f})"
            state = "CO"
    else:
        lat, lon = DEFAULT_LAT, DEFAULT_LON
        label = DEFAULT_LABEL
        state = "CO"

    try:
        fetch_eia_state_averages(state)
    except Exception:
        pass

    zyla = None
    zyla_stations: list = []
    if zip_code:
        try:
            zyla_stations = fetch_zyla_stations(str(zip_code), fuel=fuel) or []
        except Exception as e:
            print(f"[search] zyla stations: {e}")
            zyla_stations = []
        try:
            zyla = fetch_zyla_zip_prices(str(zip_code), fuel=fuel)
        except Exception as e:
            print(f"[search] zyla avg: {e}")
            zyla = None
        if (not zyla or not zyla.get("ok")) and zyla_stations:
            vals = [float(s["price"]) for s in zyla_stations if s.get("price")]
            if vals:
                avg_z = sum(vals) / len(vals)
                zyla = {
                    "regular": round(avg_z, 3),
                    "mid": round(avg_z + 0.30, 3),
                    "premium": round(avg_z + 0.55, 3),
                    "diesel": round(avg_z + 0.40, 3),
                    "source": "zyla",
                    "ok": True,
                }

    gb_stations: list = []
    try:
        from backend.gasbuddy_src import fetch_gasbuddy_stations

        gb_stations = fetch_gasbuddy_stations(
            zip_code=str(zip_code) if zip_code else None,
            lat=float(lat) if lat is not None else None,
            lon=float(lon) if lon is not None else None,
            fuel=fuel,
            limit=min(int(limit), 15),
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
        if dist > float(radius_mi) + 1.0:
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
        return {
            "id": sid,
            "name": name,
            "brand": brand,
            "lat": float(src["lat"]),
            "lon": float(src["lon"]),
            "address": src.get("address"),
            "maps_query": f"{name}, {src.get('address') or ''}".strip(", "),
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

    priced: list = []
    if zyla_stations:
        for zs in zyla_stations:
            row = _live_row(zs, "zyla")
            if row:
                priced.append(row)
        priced.sort(
            key=lambda x: (round(float(x["price"]), 3), float(x["distance_mi"]))
        )

    if len(priced) < 8 and gb_stations:
        seen_ids = {s["id"] for s in priced}
        for gs in gb_stations:
            if gs.get("lat") is None or gs.get("lon") is None:
                continue
            row = _live_row(gs, "gasbuddy")
            if not row or row["id"] in seen_ids:
                continue
            near = False
            for p in priced:
                try:
                    if (
                        haversine_miles(
                            float(p["lat"]),
                            float(p["lon"]),
                            float(row["lat"]),
                            float(row["lon"]),
                        )
                        < 0.12
                    ):
                        near = True
                        break
                except Exception:
                    pass
            if near:
                continue
            seen_ids.add(row["id"])
            priced.append(row)
        priced.sort(
            key=lambda x: (
                round(float(x["price"]), 3),
                0 if x.get("price_source") in ("zyla", "gasbuddy", "user") else 1,
                float(x["distance_mi"]),
            )
        )

    if len(priced) < 8:
        stations = stations_near(float(lat), float(lon), radius_mi=radius_mi, limit=limit)
        osm_priced = attach_prices(stations, state=state, fuel=fuel) if stations else []
        if zyla_stations and osm_priced:
            osm_priced = merge_zyla_prices_into_stations(
                osm_priced, zyla_stations, fuel=fuel
            )
        seen = {s["id"] for s in priced}
        for item in osm_priced:
            low = f"{item.get('name')} {item.get('brand') or ''}".lower()
            if any(x in low for x in ("dispensary", "cannabis", "marijuana", "weed")):
                continue
            if item["id"] in seen:
                continue
            near_z = False
            for z in priced:
                try:
                    if (
                        haversine_miles(
                            float(item["lat"]),
                            float(item["lon"]),
                            float(z["lat"]),
                            float(z["lon"]),
                        )
                        < 0.12
                    ):
                        near_z = True
                        break
                except Exception:
                    pass
            if near_z:
                continue
            seen.add(item["id"])
            if (
                zyla
                and zyla.get("ok")
                and item.get("price_source") not in ("user", "zyla")
            ):
                zreg = float(zyla.get(fuel) or zyla.get("regular") or 0)
                if zreg > 1:
                    meta_avg = (price_meta(state, fast=True).get("state_avg") or {}).get(
                        fuel
                    )
                    old = float(item.get("price") or zreg)
                    adj = old - float(meta_avg) if meta_avg else 0.0
                    item["price"] = round(zreg + adj, 3)
                    item["price_source"] = "zyla_estimate"
                    item["price_confidence"] = "medium"
            priced.append(item)
        priced.sort(
            key=lambda x: (
                round(float(x.get("price") or 99), 3),
                0 if x.get("price_source") == "zyla" else 1,
                float(x.get("distance_mi") or 99),
            )
        )

    if not priced:
        stations = stations_near(float(lat), float(lon), radius_mi=radius_mi, limit=limit)
        priced = attach_prices(stations, state=state, fuel=fuel) if stations else []

    best = cheapest_summary(priced) if priced else None
    meta = price_meta(state, fast=True)
    if zyla and zyla.get("ok"):
        meta = dict(meta)
        meta["avg_source"] = "zyla"
        meta["zyla_ok"] = True
        meta["state_avg"] = {
            "regular": zyla.get("regular"),
            "mid": zyla.get("mid"),
            "premium": zyla.get("premium"),
            "diesel": zyla.get("diesel"),
        }
        avg = meta["state_avg"]
    else:
        avg = meta["state_avg"]
    avg_fuel = avg.get(fuel) or avg.get("regular")

    if best and avg_fuel:
        best["savings_vs_avg"] = round(float(avg_fuel) - float(best["price"]), 3)
        best["state_avg_fuel"] = avg_fuel

    eia_txt = ""
    zyla_hits = sum(1 for s in priced if s.get("price_source") == "zyla")
    gb_hits = sum(1 for s in priced if s.get("price_source") == "gasbuddy")
    if zyla_hits:
        eia_txt = f" {zyla_hits} precios vía Zyla Labs."
    elif gb_hits:
        eia_txt = f" {gb_hits} precios vía GasBuddy (comunidad)."
    elif zyla and zyla.get("ok"):
        eia_txt = " Promedio de zona vía Zyla Labs."
    elif meta.get("eia_ok") and meta.get("eia_period"):
        eia_txt = f" Promedio estatal EIA (semana {meta['eia_period']})."
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

    return {
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
        "disclaimer": (
            "Estaciones reales (OpenStreetMap). "
            "Precios: reportes de la comunidad o estimación EIA + marca."
            f"{eia_txt} "
            "No es precio de bomba en vivo — reporta el precio real al pasar."
            f"{note}"
        ),
    }
