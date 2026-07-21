"""
Fuente opcional: GasBuddy vía py-gasbuddy.

Requiere: pip install py-gasbuddy aiohttp
Si Cloudflare bloquea, no rompe la app (devuelve []).

Activar: USE_GASBUDDY=1 o GASBUDDY_ENABLED=1
Opcional FlareSolver: GASBUDDY_SOLVER_URL=http://127.0.0.1:8191/v1
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any

_cache: dict[str, Any] = {}
_CACHE_TTL = 15 * 60  # 15 min


def _enabled() -> bool:
    v = (os.environ.get("USE_GASBUDDY") or os.environ.get("GASBUDDY_ENABLED") or "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    try:
        import config_local as cfg  # type: ignore

        return bool(getattr(cfg, "USE_GASBUDDY", False) or getattr(cfg, "GASBUDDY_ENABLED", False))
    except ImportError:
        return False


def _solver_url() -> str | None:
    u = (os.environ.get("GASBUDDY_SOLVER_URL") or "").strip()
    if u:
        return u
    try:
        import config_local as cfg  # type: ignore

        return (getattr(cfg, "GASBUDDY_SOLVER_URL", None) or "").strip() or None
    except ImportError:
        return None


def _fuel_key(fuel: str) -> str:
    return {
        "regular": "regular_gas",
        "mid": "midgrade_gas",
        "premium": "premium_gas",
        "diesel": "diesel",
    }.get((fuel or "regular").lower(), "regular_gas")


def _fuel_filter_id(fuel: str) -> int:
    return {
        "regular": 1,
        "mid": 2,
        "premium": 3,
        "diesel": 4,
    }.get((fuel or "regular").lower(), 1)


async def _lookup_async(
    zip_code: str | None,
    lat: float | None,
    lon: float | None,
    fuel: str,
    limit: int = 15,
) -> list[dict]:
    from py_gasbuddy import GasBuddy

    solver = _solver_url()
    kwargs = {}
    if solver:
        kwargs["solver_url"] = solver
    gb = GasBuddy(**kwargs)
    fkey = _fuel_key(fuel)
    fid = _fuel_filter_id(fuel)

    if zip_code:
        result = await gb.price_lookup_service(
            zipcode=int(str(zip_code)[:5]),
            limit=limit,
            fuel=fid,
        )
    elif lat is not None and lon is not None:
        result = await gb.price_lookup_service(
            lat=float(lat),
            lon=float(lon),
            limit=limit,
            fuel=fid,
        )
    else:
        return []

    rows = (result or {}).get("results") or []
    out: list[dict] = []
    for s in rows:
        if not isinstance(s, dict):
            continue
        prod = s.get(fkey) or s.get("regular_gas") or {}
        price = prod.get("price") if isinstance(prod, dict) else None
        if price is None:
            continue
        try:
            price_f = float(price)
        except (TypeError, ValueError):
            continue
        addr = s.get("address") or {}
        if isinstance(addr, dict):
            address = ", ".join(
                str(addr.get(k))
                for k in ("line1", "locality", "region", "postalCode")
                if addr.get(k)
            )
        else:
            address = str(addr) if addr else None
        brands = s.get("brands") or []
        brand = None
        if brands and isinstance(brands[0], dict):
            brand = brands[0].get("name")
        elif brands and isinstance(brands[0], str):
            brand = brands[0]
        name = s.get("name") or brand or "Gas Station"
        # coords a veces no vienen en price service
        lat_s = s.get("lat") or s.get("latitude")
        lon_s = s.get("lon") or s.get("longitude") or s.get("lng")
        coords = s.get("coordinates") or {}
        if isinstance(coords, dict):
            lat_s = lat_s or coords.get("lat")
            lon_s = lon_s or coords.get("lng") or coords.get("lon")
        try:
            lat_f = float(lat_s) if lat_s is not None else None
            lon_f = float(lon_s) if lon_s is not None else None
        except (TypeError, ValueError):
            lat_f = lon_f = None
        dist = s.get("distance")
        try:
            dist_f = float(dist) if dist is not None else None
        except (TypeError, ValueError):
            dist_f = None
        out.append(
            {
                "station_id": str(s.get("station_id") or s.get("id") or ""),
                "name": str(name).strip(),
                "brand": (str(brand).strip() if brand else None),
                "lat": lat_f,
                "lon": lon_f,
                "address": address,
                "price": round(price_f, 3),
                "fuel": fuel,
                "distance_mi": dist_f,
                "last_updated": prod.get("last_updated") if isinstance(prod, dict) else None,
                "source": "gasbuddy",
            }
        )
    return out


def fetch_gasbuddy_stations(
    zip_code: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    fuel: str = "regular",
    limit: int = 15,
) -> list[dict]:
    """Sync wrapper para FastAPI. No lanza: [] si falla."""
    if not _enabled():
        return []
    cache_key = f"{zip_code}|{lat}|{lon}|{fuel}|{limit}"
    now = time.time()
    hit = _cache.get(cache_key)
    if hit and now - hit["ts"] < _CACHE_TTL:
        return list(hit["data"])
    try:
        data = asyncio.run(_lookup_async(zip_code, lat, lon, fuel, limit))
        _cache[cache_key] = {"ts": now, "data": data}
        print(f"[gasbuddy] OK n={len(data)}")
        return data
    except Exception as e:
        print(f"[gasbuddy] fail: {type(e).__name__}: {e}")
        return []
