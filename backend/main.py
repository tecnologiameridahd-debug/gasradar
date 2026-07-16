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
    fetch_zyla_zip_prices,
    price_meta,
    report_price,
)
from backend.stations import stations_near

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

APP_VERSION = "0.3.0"

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

    # Zyla Labs (precios por ZIP) si hay key + URL + zip
    zyla = None
    if zip_code:
        try:
            zyla = fetch_zyla_zip_prices(str(zip_code), fuel=fuel)
        except Exception:
            zyla = None

    stations = stations_near(float(lat), float(lon), radius_mi=radius_mi, limit=limit)
    priced = attach_prices(stations, state=state, fuel=fuel) if stations else []

    # Si Zyla trajo promedio del ZIP, re-anclar estimaciones a ese promedio
    if zyla and zyla.get("ok") and priced:
        zreg = float(zyla.get("regular") or 0)
        if zreg > 1:
            for item in priced:
                if item.get("price_source") == "user":
                    continue
                # mantener ranking por marca relativo al promedio Zyla
                delta = float(item.get("price") or zreg) - float(
                    (price_meta(state, fast=True).get("state_avg") or {}).get(fuel)
                    or zreg
                )
                # si no hay delta útil, pequeña variación por estación ya viene del estimate
                src_p = zyla.get(fuel) or zreg
                # re-escalar: precio ≈ zyla_fuel + (old - old_avg)
                old = float(item.get("price") or src_p)
                meta_avg = (price_meta(state, fast=True).get("state_avg") or {}).get(
                    fuel
                )
                if meta_avg:
                    adj = old - float(meta_avg)
                else:
                    adj = 0.0
                new_p = round(float(src_p) + adj, 3)
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
    if zyla and zyla.get("ok"):
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
