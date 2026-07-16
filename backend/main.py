"""
GasRadar — API + web app
Radar de precios de gasolina USA. Precio más barato cerca de ti.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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
    report_price,
)
from backend.stations import stations_near

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

APP_VERSION = "0.3.2"

app = FastAPI(title="GasRadar", version=APP_VERSION)


@app.middleware("http")
async def add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-App"] = "GasRadar"
    response.headers["X-App-Version"] = APP_VERSION
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    # HTML/CSS/JS sin cache agresivo (beta: los cambios se ven al recargar)
    path = request.url.path
    if path.startswith("/static/"):
        if path.endswith((".png", ".svg", ".jpg", ".webp", ".ico")):
            response.headers["Cache-Control"] = "public, max-age=86400"
        elif path.endswith((".css", ".js")):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
    elif path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


class ReportBody(BaseModel):
    station_id: str
    fuel: str = "regular"
    price: float = Field(..., gt=1.0, lt=12.0)
    note: str | None = None


@app.get("/api/health")
def health():
    """Healthcheck para Render y keep-alive (cron / script)."""
    from datetime import datetime, timezone

    from backend.db import db_status

    return {
        "ok": True,
        "app": "gasradar",
        "version": APP_VERSION,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "alive",
        "db": db_status(),
    }


@app.get("/api/geo/zip/{zip_code}")
def api_geocode(zip_code: str):
    g = geocode_zip(zip_code)
    if not g:
        raise HTTPException(404, "ZIP no encontrado")
    return g


@app.get("/api/search")
def api_search(
    lat: float | None = None,
    lon: float | None = None,
    zip: str | None = Query(None, alias="zip"),
    radius_mi: float = Query(5.0, ge=1.0, le=25.0),
    fuel: str = Query("regular", pattern="^(regular|mid|premium|diesel)$"),
    limit: int = Query(30, ge=5, le=60),
):
    label = DEFAULT_LABEL
    state = "CO"
    zip_code = None
    if zip:
        g = geocode_zip(zip)
        if not g:
            raise HTTPException(404, f"ZIP {zip} no encontrado")
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

    # Calentar EIA una vez por búsqueda (evita estimaciones sin dato oficial)
    try:
        fetch_eia_state_averages(state)
    except Exception:
        pass

    # Zyla Labs: estaciones con precio + promedio ZIP
    zyla = None
    zyla_stations: list = []
    if zip_code:
        try:
            zyla_stations = fetch_zyla_stations(str(zip_code), fuel=fuel) or []
        except Exception:
            zyla_stations = []
        try:
            zyla = fetch_zyla_zip_prices(str(zip_code), fuel=fuel)
        except Exception:
            zyla = None
        # Si solo hay station+data, sacar promedio de esas estaciones
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

    stations = stations_near(float(lat), float(lon), radius_mi=radius_mi, limit=limit)
    priced = attach_prices(stations, state=state, fuel=fuel) if stations else []

    # Precios reales Zyla sobre OSM + añadir estaciones Zyla que no estén en el mapa
    if zyla_stations:
        if priced:
            priced = merge_zyla_prices_into_stations(priced, zyla_stations, fuel=fuel)
        # Estaciones Zyla con coords que no matchearon OSM
        from backend.geo import haversine_miles
        from backend.stations import _station_id, _pretty_station_name, _display_brand

        existing_ids = {s.get("id") for s in priced}
        for zs in zyla_stations:
            if zs.get("lat") is None or zs.get("lon") is None:
                continue
            if zs.get("price") is None:
                continue
            dist = haversine_miles(
                float(lat), float(lon), float(zs["lat"]), float(zs["lon"])
            )
            if dist > float(radius_mi) + 0.5:
                continue
            name = _pretty_station_name(
                zs.get("name") or "Gas Station",
                zs.get("brand"),
                zs.get("name") or "",
                zs.get("address"),
            )
            brand = _display_brand(zs.get("brand"), name)
            sid = _station_id(float(zs["lat"]), float(zs["lon"]), name)
            # evitar duplicado por coords/nombre
            dup = False
            for s in priced:
                if s.get("id") == sid:
                    dup = True
                    break
                if s.get("price_source") == "zyla" and s.get("name") == name:
                    try:
                        d2 = haversine_miles(
                            float(s["lat"]), float(s["lon"]), float(zs["lat"]), float(zs["lon"])
                        )
                        if d2 < 0.1:
                            dup = True
                            break
                    except Exception:
                        pass
            if dup or sid in existing_ids:
                continue
            existing_ids.add(sid)
            priced.append(
                {
                    "id": sid,
                    "name": name,
                    "brand": brand,
                    "lat": float(zs["lat"]),
                    "lon": float(zs["lon"]),
                    "address": zs.get("address"),
                    "maps_query": f"{name}, {zs.get('address') or ''}".strip(", "),
                    "distance_mi": dist,
                    "phone": None,
                    "website": None,
                    "source": "zyla",
                    "is_demo": False,
                    "nav_mode": "coords",
                    "price": float(zs["price"]),
                    "price_source": "zyla",
                    "price_confidence": "high",
                    "price_age_hours": None,
                    "reports_count": 0,
                    "prices": {
                        fuel: {
                            "price": float(zs["price"]),
                            "source": "zyla",
                            "confidence": "high",
                            "reports_count": 0,
                            "age_hours": None,
                        }
                    },
                }
            )
        priced.sort(
            key=lambda x: (
                round(float(x.get("price") or 99), 3),
                0 if x.get("price_source") == "user" else 1,
                0 if x.get("price_source") == "zyla" else 1,
                float(x.get("distance_mi") or 99),
            )
        )

    # Si Zyla trajo promedio del ZIP, re-anclar estimaciones restantes
    if zyla and zyla.get("ok") and priced:
        zreg = float(zyla.get(fuel) or zyla.get("regular") or 0)
        if zreg > 1:
            meta_avg = (price_meta(state, fast=True).get("state_avg") or {}).get(fuel)
            for item in priced:
                if item.get("price_source") in ("user", "zyla"):
                    continue
                old = float(item.get("price") or zreg)
                if meta_avg:
                    adj = old - float(meta_avg)
                else:
                    adj = 0.0
                new_p = round(float(zreg) + adj, 3)
                item["price"] = new_p
                item["price_source"] = "zyla_estimate"
                item["price_confidence"] = "medium"
                if isinstance(item.get("prices"), dict) and fuel in item["prices"]:
                    item["prices"][fuel]["price"] = new_p
                    item["prices"][fuel]["source"] = "zyla_estimate"
            priced.sort(
                key=lambda x: (
                    round(float(x["price"]), 3),
                    0 if x.get("price_source") == "user" else 1,
                    0 if x.get("price_source") == "zyla" else 1,
                    float(x["distance_mi"]),
                )
            )

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

    # Ahorro vs promedio del estado en la más barata
    if best and avg_fuel:
        best["savings_vs_avg"] = round(float(avg_fuel) - float(best["price"]), 3)
        best["state_avg_fuel"] = avg_fuel

    eia_txt = ""
    zyla_hits = sum(1 for s in priced if s.get("price_source") == "zyla")
    if zyla_hits:
        eia_txt = f" {zyla_hits} precios de estación vía Zyla Labs."
    elif zyla and zyla.get("ok"):
        eia_txt = " Promedio de zona vía Zyla Labs."
    elif meta.get("eia_ok") and meta.get("eia_period"):
        eia_txt = f" Promedio estatal EIA (semana {meta['eia_period']})."
    elif not meta.get("eia_ok"):
        eia_txt = " Promedio de referencia (EIA/Zyla no disponible ahora)."

    note = ""
    if not priced:
        note = (
            " No se encontraron estaciones reales cerca. "
            "Prueba un radio mayor (10 mi) o otro ZIP."
        )

    user_reports = sum(1 for s in priced if s.get("price_source") == "user")

    # Stats anónimas (ZIP o "gps")
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


@app.post("/api/report")
def api_report(body: ReportBody):
    try:
        return report_price(body.station_id, body.fuel, body.price, body.note)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


class VisitBody(BaseModel):
    path: str | None = "/"
    referrer: str | None = None
    lang: str | None = None


@app.post("/api/visit")
def api_visit(body: VisitBody):
    """Registro anónimo de visita (sin IP ni nombre)."""
    from backend.analytics import track_event

    track_event(
        "pageview",
        path=body.path or "/",
        referrer=body.referrer,
        lang=body.lang,
    )
    return {"ok": True}


@app.get("/api/stats")
def api_stats(key: str | None = None, days: int = Query(14, ge=1, le=90)):
    """Resumen de visitas — requiere ?key=STATS_KEY."""
    from backend.analytics import check_stats_key, summary

    if not check_stats_key(key):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY")
    return summary(days=days)


# Static frontend
if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
def index():
    index_path = FRONTEND / "index.html"
    if not index_path.exists():
        return {"msg": "Frontend missing"}
    return FileResponse(index_path)


@app.get("/privacy")
def privacy():
    """Política de privacidad (App Store / pie de página)."""
    path = FRONTEND / "privacy.html"
    if not path.exists():
        raise HTTPException(404, "Privacy page missing")
    return FileResponse(path)


@app.get("/stats")
def stats_page():
    """Panel de visitas (protegido en el JS con la clave)."""
    path = FRONTEND / "stats.html"
    if not path.exists():
        raise HTTPException(404, "Stats page missing")
    return FileResponse(path)
