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
    price_meta,
    report_price,
)
from backend.stations import stations_near

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

APP_VERSION = "0.2.8"

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

    stations = stations_near(float(lat), float(lon), radius_mi=radius_mi, limit=limit)
    priced = attach_prices(stations, state=state, fuel=fuel) if stations else []
    best = cheapest_summary(priced) if priced else None
    meta = price_meta(state, fast=True)
    avg = meta["state_avg"]
    avg_fuel = avg.get(fuel) or avg.get("regular")

    # Ahorro vs promedio del estado en la más barata
    if best and avg_fuel:
        best["savings_vs_avg"] = round(float(avg_fuel) - float(best["price"]), 3)
        best["state_avg_fuel"] = avg_fuel

    eia_txt = ""
    if meta.get("eia_ok") and meta.get("eia_period"):
        eia_txt = f" Promedio estatal EIA (semana {meta['eia_period']})."
    elif not meta.get("eia_ok"):
        eia_txt = " Promedio de referencia (EIA no disponible ahora)."

    note = ""
    if not priced:
        note = (
            " No se encontraron estaciones reales cerca. "
            "Prueba un radio mayor (10 mi) o otro ZIP."
        )

    user_reports = sum(1 for s in priced if s.get("price_source") == "user")

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
