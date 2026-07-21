"""
GasRadar VPS Scraper API
========================
Servicio para correr en un VPS (no en Render free).

Endpoints:
  GET /health
  GET /prices?zip=80903&fuel=regular
  GET /prices?lat=38.8&lon=-104.8&fuel=regular
  GET /warm?zip=80903   (fuerza refresh, para cron)

Auth opcional: header X-API-Key o ?key=  (env SCRAPER_API_KEY)

Arranque:
  uvicorn main:app --host 0.0.0.0 --port 8788
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Query

import cache
from gasbuddy_client import fetch_stations

APP_VERSION = "1.0.0"
app = FastAPI(title="GasRadar VPS Scraper", version=APP_VERSION)


def _api_key() -> str:
    return (os.environ.get("SCRAPER_API_KEY") or "").strip()


def _check_key(key: str | None, x_api_key: str | None) -> None:
    want = _api_key()
    if not want:
        return  # abierto (solo en red privada / firewall)
    got = (x_api_key or key or "").strip()
    if got != want:
        raise HTTPException(401, "Clave incorrecta (SCRAPER_API_KEY)")


@app.get("/health")
def health():
    return {
        "ok": True,
        "app": "gasradar-vps-scraper",
        "version": APP_VERSION,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "flaresolverr": bool((os.environ.get("FLARESOLVERR_URL") or "").strip()),
        "cache_ttl_sec": cache.DEFAULT_TTL,
    }


@app.get("/prices")
def prices(
    zip: str | None = Query(None, description="ZIP USA 5 dígitos"),
    lat: float | None = None,
    lon: float | None = None,
    fuel: str = Query("regular"),
    max_age: int = Query(0, ge=0, le=30),
    limit: int = Query(40, ge=1, le=80),
    force: int = Query(0, ge=0, le=1),
    key: str | None = None,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """
    Precios por estación (GasBuddy). Usa caché por defecto.
    force=1 ignora caché.
    """
    _check_key(key, x_api_key)
    z = "".join(c for c in str(zip or "") if c.isdigit())[:5] if zip else None
    if z and len(z) != 5:
        z = None
    if not z and (lat is None or lon is None):
        raise HTTPException(400, "Pasa zip= o lat= + lon=")

    cache_key = f"gb:{z or ''}:{lat}:{lon}:{fuel}:{max_age}:{limit}"
    if not force:
        hit = cache.get(cache_key)
        if hit and hit.get("ok"):
            hit = dict(hit)
            hit["cached"] = True
            return hit

    t0 = time.time()
    result = fetch_stations(
        zip_code=z,
        lat=lat,
        lon=lon,
        fuel=fuel,
        max_age=max_age,
        limit=limit,
    )
    result["elapsed_ms"] = int((time.time() - t0) * 1000)
    result["cached"] = False
    result["utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if result.get("ok") and result.get("stations"):
        cache.set_(cache_key, result)
    return result


@app.get("/warm")
def warm(
    zip: str = Query(..., min_length=5, max_length=10),
    fuel: str = "regular",
    key: str | None = None,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """Fuerza refresh de un ZIP (útil para cron en el VPS)."""
    return prices(
        zip=zip,
        lat=None,
        lon=None,
        fuel=fuel,
        max_age=0,
        limit=40,
        force=1,
        key=key,
        x_api_key=x_api_key,
    )
