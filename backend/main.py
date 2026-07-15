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

from backend.geo import DEFAULT_LABEL, DEFAULT_LAT, DEFAULT_LON, geocode_zip
from backend.prices import (
    attach_prices,
    cheapest_summary,
    price_meta,
    report_price,
    state_averages,
)
from backend.stations import stations_near

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="GasRadar", version="0.1.0")

# Headers básicos para PWA-lite / embebido en móvil
@app.middleware("http")
async def add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-App"] = "GasRadar"
    # Permitir geolocation en contextos seguros (HTTPS en producción)
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    return response


class ReportBody(BaseModel):
    station_id: str
    fuel: str = "regular"
    price: float = Field(..., gt=1.0, lt=12.0)
    note: str | None = None


@app.get("/api/health")
def health():
    return {"ok": True, "app": "gasradar", "version": "0.1.0"}


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
    if zip:
        g = geocode_zip(zip)
        if not g:
            raise HTTPException(404, f"ZIP {zip} no encontrado")
        lat, lon = g["lat"], g["lon"]
        label = g["label"]
        state = g.get("state") or "CO"
    elif lat is None or lon is None:
        lat, lon = DEFAULT_LAT, DEFAULT_LON
        label = DEFAULT_LABEL
        state = "CO"

    stations = stations_near(lat, lon, radius_mi=radius_mi, limit=limit)
    priced = attach_prices(stations, state=state, fuel=fuel)
    best = cheapest_summary(priced)
    meta = price_meta(state)
    avg = meta["state_avg"]
    eia_txt = ""
    if meta.get("eia_ok") and meta.get("eia_period"):
        eia_txt = f" Promedio estatal EIA (semana {meta['eia_period']})."

    return {
        "center": {"lat": lat, "lon": lon, "label": label, "state": state},
        "fuel": fuel,
        "radius_mi": radius_mi,
        "state_avg": avg,
        "price_meta": meta,
        "count": len(priced),
        "cheapest": best,
        "stations": priced,
        "disclaimer": (
            "Precios: reportes de usuarios (prioridad) o estimación con promedio oficial EIA + marca."
            f"{eia_txt} "
            "No es precio de bomba en vivo. Reporta el precio real al pasar."
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
