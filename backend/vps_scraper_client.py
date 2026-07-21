"""
Cliente del scraper VPS (GasBuddy).

Env:
  USE_VPS_SCRAPER=1
  VPS_SCRAPER_URL=https://scraper.tudominio.com
  VPS_SCRAPER_KEY=secreto
"""
from __future__ import annotations

import os
import time
from typing import Any

import httpx

_cache: dict[str, Any] = {}
_CACHE_TTL = 20 * 60  # 20 min en la app (el VPS ya cachea 3h)


def _enabled() -> bool:
    v = (os.environ.get("USE_VPS_SCRAPER") or "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    try:
        import config_local as cfg  # type: ignore

        return bool(getattr(cfg, "USE_VPS_SCRAPER", False))
    except ImportError:
        return False


def _base_url() -> str:
    u = (os.environ.get("VPS_SCRAPER_URL") or "").strip().rstrip("/")
    if u:
        return u
    try:
        import config_local as cfg  # type: ignore

        return (getattr(cfg, "VPS_SCRAPER_URL", None) or "").strip().rstrip("/")
    except ImportError:
        return ""


def _api_key() -> str:
    k = (os.environ.get("VPS_SCRAPER_KEY") or "").strip()
    if k:
        return k
    try:
        import config_local as cfg  # type: ignore

        return (getattr(cfg, "VPS_SCRAPER_KEY", None) or "").strip()
    except ImportError:
        return ""


def fetch_vps_stations(
    zip_code: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    fuel: str = "regular",
    limit: int = 30,
) -> list[dict]:
    """Llama al VPS y devuelve lista normalizada de estaciones con precio."""
    if not _enabled():
        return []
    base = _base_url()
    if not base:
        print("[vps_scraper] USE_VPS_SCRAPER=1 pero falta VPS_SCRAPER_URL")
        return []

    z = "".join(c for c in str(zip_code or "") if c.isdigit())[:5] if zip_code else ""
    cache_key = f"{z}|{lat}|{lon}|{fuel}|{limit}"
    now = time.time()
    hit = _cache.get(cache_key)
    if hit and now - hit["ts"] < _CACHE_TTL:
        return list(hit["data"])

    params: dict[str, Any] = {"fuel": fuel, "limit": limit}
    if z and len(z) == 5:
        params["zip"] = z
    elif lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    else:
        return []

    key = _api_key()
    if key:
        params["key"] = key

    try:
        r = httpx.get(f"{base}/prices", params=params, timeout=45.0)
        if r.status_code != 200:
            print(f"[vps_scraper] HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json() or {}
        if not data.get("ok"):
            print(f"[vps_scraper] fail: {data.get('error')}")
            return []
        stations = data.get("stations") or []
        out = [s for s in stations if isinstance(s, dict) and s.get("price") is not None]
        _cache[cache_key] = {"ts": now, "data": out}
        print(f"[vps_scraper] OK n={len(out)} method={data.get('method')}")
        return out
    except Exception as e:
        print(f"[vps_scraper] error: {type(e).__name__}: {e}")
        return []
