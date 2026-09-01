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
    urls = _base_urls()
    return urls[0] if urls else ""


def _base_urls() -> list[str]:
    """Una o varias URLs: VPS_SCRAPER_URL y/o VPS_SCRAPER_URLS (coma)."""
    raw_multi = (os.environ.get("VPS_SCRAPER_URLS") or "").strip()
    raw_one = (os.environ.get("VPS_SCRAPER_URL") or "").strip()
    if not raw_multi and not raw_one:
        try:
            import config_local as cfg  # type: ignore

            raw_multi = (getattr(cfg, "VPS_SCRAPER_URLS", None) or "").strip()
            raw_one = (getattr(cfg, "VPS_SCRAPER_URL", None) or "").strip()
        except ImportError:
            pass
    urls: list[str] = []
    for chunk in (raw_multi.replace(";", ",") + "," + raw_one).split(","):
        u = chunk.strip().rstrip("/")
        if u and u not in urls:
            urls.append(u)
    return urls


def _pick_urls(cache_key: str) -> list[str]:
    """Misma zona → mismo VPS (caché). Si falla, rota al siguiente."""
    urls = _base_urls()
    if len(urls) <= 1:
        return urls
    idx = sum(ord(c) for c in cache_key) % len(urls)
    return urls[idx:] + urls[:idx]


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
    timeout_s: float = 8.0,
) -> list[dict]:
    """Llama al VPS y devuelve lista normalizada de estaciones con precio."""
    if not _enabled():
        return []
    z = "".join(c for c in str(zip_code or "") if c.isdigit())[:5] if zip_code else ""
    # Misma zona = misma clave: 2ª persona reutiliza 3 h y no vuelve a scrapear
    if z and len(z) == 5:
        cache_key = f"z:{z}|{fuel}|{limit}"
    elif lat is not None and lon is not None:
        cache_key = f"g:{round(float(lat), 2)},{round(float(lon), 2)}|{fuel}|{limit}"
    else:
        cache_key = f"{z}|{lat}|{lon}|{fuel}|{limit}"
    urls = _pick_urls(cache_key)
    if not urls:
        print("[vps_scraper] USE_VPS_SCRAPER=1 pero falta VPS_SCRAPER_URL o VPS_SCRAPER_URLS")
        return []

    now = time.time()
    hit = _cache.get(cache_key)
    if hit and now - hit["ts"] < _CACHE_TTL:
        return list(hit["data"])

    params: dict[str, Any] = {"fuel": fuel, "limit": min(max(int(limit), 25), 40)}
    # GPS del centro del ZIP da muchas más estaciones con dirección que solo zip=
    if lat is not None and lon is not None:
        params["lat"] = float(lat)
        params["lon"] = float(lon)
        if z and len(z) == 5:
            params["zip"] = z  # solo para logs/caché; el VPS prioriza lat/lon
    elif z and len(z) == 5:
        params["zip"] = z
    else:
        return []

    key = _api_key()
    if key:
        params["key"] = key

    last_err = ""
    deadline = time.time() + max(2.5, min(float(timeout_s or 8.0), 10.0))
    for base in urls:
        left = deadline - time.time()
        if left < 1.2:
            print("[vps_scraper] sin tiempo para otra URL")
            break
        try:
            wait_s = max(1.2, min(left, 3.0))
            r = httpx.get(
                f"{base}/prices",
                params=params,
                timeout=httpx.Timeout(wait_s, connect=min(0.9, wait_s)),
            )
            if r.status_code != 200:
                last_err = f"{base} HTTP {r.status_code}"
                print(f"[vps_scraper] {last_err}: {r.text[:160]}")
                continue
            data = r.json() or {}
            if not data.get("ok"):
                last_err = f"{base} fail: {data.get('error')}"
                print(f"[vps_scraper] {last_err}")
                continue
            stations = data.get("stations") or []
            out = [s for s in stations if isinstance(s, dict) and s.get("price") is not None]
            if not out:
                last_err = f"{base} empty"
                continue
            _cache[cache_key] = {"ts": now, "data": out}
            try:
                import threading

                def _bg_put() -> None:
                    try:
                        from backend.price_cache import put as db_put

                        db_put(f"vps:{cache_key}", {"stations": out})
                    except Exception:
                        pass

                threading.Thread(target=_bg_put, daemon=True).start()
            except Exception:
                pass
            print(f"[vps_scraper] OK n={len(out)} method={data.get('method')} via={base}")
            return out
        except Exception as e:
            last_err = f"{base} {type(e).__name__}: {e}"
            print(f"[vps_scraper] error: {last_err}")
    if last_err:
        print(f"[vps_scraper] todos fallaron: {last_err}")
    return []
