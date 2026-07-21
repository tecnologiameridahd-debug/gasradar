"""
Cliente GasBuddy para VPS.

1) Intenta curl_cffi (Chrome TLS) + CSRF + GraphQL
2) Si hay FLARESOLVERR_URL, pide cookies/HTML al solver y reintenta

No es API oficial de GasBuddy. Úsalo con rate-limit y caché.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

GB_HOME = "https://www.gasbuddy.com/home"
GB_GQL = "https://www.gasbuddy.com/graphql"

LOCATION_QUERY_PRICES = """
query LocationBySearchTerm(
  $brandId: Int
  $cursor: String
  $fuel: Int
  $lat: Float
  $lng: Float
  $maxAge: Int
  $search: String
) {
  locationBySearchTerm(
    lat: $lat
    lng: $lng
    search: $search
    priority: "locality"
  ) {
    stations(
      brandId: $brandId
      cursor: $cursor
      fuel: $fuel
      lat: $lat
      lng: $lng
      maxAge: $maxAge
      priority: "locality"
    ) {
      cursor { next }
      results {
        address {
          country line1 line2 locality postalCode region
        }
        brands { brandId brandingType imageUrl name }
        distance
        fuels
        id
        latitude
        longitude
        name
        priceUnit
        currency
        ratingsCount
        starRating
        prices {
          cash { nickname postedTime price formattedPrice }
          credit { nickname postedTime price formattedPrice }
          fuelProduct
          longName
        }
      }
    }
    trends { areaName country today todayLow trend }
  }
}
""".strip()

CSRF_RE = re.compile(r'window\.gbcsrf\s*=\s*(["\'])(.*?)\1')
CSRF_RE2 = re.compile(r'gbcsrf["\']?\s*[:=]\s*["\']([^"\']+)', re.I)

FUEL_IDS = {
    "regular": 1,
    "mid": 2,
    "midgrade": 2,
    "premium": 3,
    "diesel": 4,
    "e85": 5,
    "unl88": 12,
}

FUEL_PRODUCT = {
    1: "regular_gas",
    2: "midgrade_gas",
    3: "premium_gas",
    4: "diesel",
    5: "e85",
    12: "unl88",
}


def _fuel_id(fuel: str) -> int:
    return FUEL_IDS.get((fuel or "regular").lower().strip(), 1)


def _headers(csrf: str, referer: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://www.gasbuddy.com",
        "Referer": referer,
        "gbcsrf": csrf,
        "apollo-require-preflight": "true",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        ),
    }


def _extract_csrf(html: str) -> str | None:
    m = CSRF_RE.search(html or "")
    if m:
        return m.group(2)
    m2 = CSRF_RE2.search(html or "")
    if m2:
        return m2.group(1)
    return None


def _flaresolverr_url() -> str:
    return (os.environ.get("FLARESOLVERR_URL") or "").strip().rstrip("/")


def _get_home_via_flaresolverr(search: str) -> tuple[str, dict[str, str]]:
    """Devuelve (html, cookies_dict) usando FlareSolverr."""
    import httpx

    url = f"{GB_HOME}?search={search}&fuel=1"
    solver = _flaresolverr_url()
    if not solver:
        raise RuntimeError("FLARESOLVERR_URL no configurada")
    endpoint = solver if solver.endswith("/v1") else f"{solver}/v1"
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
    }
    r = httpx.post(endpoint, json=payload, timeout=90.0)
    r.raise_for_status()
    data = r.json()
    sol = (data or {}).get("solution") or {}
    html = sol.get("response") or ""
    cookies = {}
    for c in sol.get("cookies") or []:
        if isinstance(c, dict) and c.get("name"):
            cookies[c["name"]] = c.get("value") or ""
    return html, cookies


def _price_from_node(prices: list | None, fuel: str) -> tuple[float | None, str | None]:
    if not prices:
        return None, None
    want = FUEL_PRODUCT.get(_fuel_id(fuel), "regular_gas")
    # prefer credit then cash for matching fuelProduct
    for node in prices:
        if not isinstance(node, dict):
            continue
        fp = node.get("fuelProduct")
        # fuelProduct can be int or string key
        ok = fp == want or fp == _fuel_id(fuel) or str(fp) == str(_fuel_id(fuel))
        if not ok and len(prices) == 1:
            ok = True
        if not ok:
            # also match longName
            ln = (node.get("longName") or "").lower()
            if fuel == "regular" and "regular" in ln:
                ok = True
            elif fuel == "diesel" and "diesel" in ln:
                ok = True
        if not ok:
            continue
        for key in ("credit", "cash"):
            block = node.get(key)
            if isinstance(block, dict) and block.get("price") is not None:
                try:
                    return float(block["price"]), block.get("postedTime")
                except (TypeError, ValueError):
                    pass
    # fallback first price any grade
    for node in prices:
        if not isinstance(node, dict):
            continue
        for key in ("credit", "cash"):
            block = node.get(key)
            if isinstance(block, dict) and block.get("price") is not None:
                try:
                    return float(block["price"]), block.get("postedTime")
                except (TypeError, ValueError):
                    pass
    return None, None


def _normalize_station(raw: dict, fuel: str) -> dict | None:
    if not isinstance(raw, dict):
        return None
    lat = raw.get("latitude")
    lon = raw.get("longitude")
    price, posted = _price_from_node(raw.get("prices"), fuel)
    if price is None:
        return None
    try:
        price_f = float(price)
    except (TypeError, ValueError):
        return None
    if price_f < 1.0 or price_f > 12.0:
        return None

    brands = raw.get("brands") or []
    brand = None
    if brands and isinstance(brands[0], dict):
        brand = brands[0].get("name")
    name = (raw.get("name") or brand or "Gas Station").strip()
    addr = raw.get("address") or {}
    if isinstance(addr, dict):
        address = ", ".join(
            str(addr.get(k))
            for k in ("line1", "locality", "region", "postalCode")
            if addr.get(k)
        )
    else:
        address = str(addr) if addr else None

    try:
        lat_f = float(lat) if lat is not None else None
        lon_f = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        lat_f = lon_f = None

    dist = raw.get("distance")
    try:
        dist_f = float(dist) if dist is not None else None
    except (TypeError, ValueError):
        dist_f = None

    return {
        "station_id": str(raw.get("id") or ""),
        "name": name,
        "brand": (str(brand).strip() if brand else None),
        "lat": lat_f,
        "lon": lon_f,
        "address": address or None,
        "price": round(price_f, 3),
        "fuel": fuel,
        "distance_mi": dist_f,
        "posted_time": posted,
        "source": "gasbuddy",
    }


def fetch_stations(
    *,
    zip_code: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    fuel: str = "regular",
    max_age: int = 0,
    limit: int = 40,
) -> dict[str, Any]:
    """
    Busca estaciones con precio (pagina cursor hasta `limit`).
    Returns { ok, stations, error?, method? }
    """
    search = None
    if zip_code:
        search = "".join(c for c in str(zip_code) if c.isdigit())[:5]
    referer = f"{GB_HOME}?search={search or ''}&fuel={_fuel_id(fuel)}"
    base_vars: dict[str, Any] = {
        "fuel": _fuel_id(fuel),
        "maxAge": int(max_age or 0),
    }
    # Preferir GPS: en metros grandes (Vegas, etc.) trae 20–40 resultados con dirección.
    # Solo ZIP a veces devuelve 3–5 estaciones.
    if lat is not None and lon is not None:
        base_vars["lat"] = float(lat)
        base_vars["lng"] = float(lon)
        base_vars["search"] = f"{lat},{lon}"
    elif search and len(search) == 5:
        base_vars["search"] = search
    else:
        return {"ok": False, "stations": [], "error": "need zip or lat/lon"}

    last_err = None
    # --- Attempt 1: curl_cffi + paginación ---
    try:
        from curl_cffi import requests as cr

        s = cr.Session(impersonate="chrome120")
        home = s.get(referer if search else GB_HOME, timeout=45)
        csrf = _extract_csrf(home.text or "")
        if not csrf:
            last_err = "no csrf (curl_cffi)"
        else:
            stations, err = _fetch_pages(
                s, csrf, referer, base_vars, fuel, limit
            )
            if stations:
                return {
                    "ok": True,
                    "stations": stations,
                    "method": "curl_cffi",
                    "count": len(stations),
                }
            last_err = err or "empty results curl_cffi"
    except Exception as e:
        last_err = f"curl_cffi: {type(e).__name__}: {e}"

    # --- Attempt 2: FlareSolverr ---
    if _flaresolverr_url():
        try:
            from curl_cffi import requests as cr

            html, cookies = _get_home_via_flaresolverr(search or "80903")
            csrf = _extract_csrf(html)
            if not csrf:
                last_err = "no csrf from flaresolverr"
            else:
                s = cr.Session(impersonate="chrome120")
                for k, v in cookies.items():
                    s.cookies.set(k, v, domain=".gasbuddy.com")
                stations, err = _fetch_pages(
                    s, csrf, referer, base_vars, fuel, limit
                )
                if stations:
                    return {
                        "ok": True,
                        "stations": stations,
                        "method": "flaresolverr",
                        "count": len(stations),
                    }
                last_err = err or "empty results flaresolverr"
        except Exception as e:
            last_err = f"flaresolverr: {type(e).__name__}: {e}"

    return {"ok": False, "stations": [], "error": last_err or "unknown"}


def _fetch_pages(
    session,
    csrf: str,
    referer: str,
    base_vars: dict[str, Any],
    fuel: str,
    limit: int,
    max_pages: int = 5,
) -> tuple[list[dict], str | None]:
    """Pagina GraphQL con cursor.next hasta reunir `limit` estaciones."""
    out: list[dict] = []
    seen_ids: set[str] = set()
    cursor: str | None = None
    last_err: str | None = None
    for page in range(max_pages):
        variables = dict(base_vars)
        if cursor:
            variables["cursor"] = cursor
        payload = {
            "operationName": "LocationBySearchTerm",
            "variables": variables,
            "query": LOCATION_QUERY_PRICES,
        }
        resp = session.post(
            GB_GQL,
            data=json.dumps(payload),
            headers=_headers(csrf, referer),
            timeout=45,
        )
        if resp.status_code != 200:
            last_err = f"gql {resp.status_code}: {(resp.text or '')[:160]}"
            break
        data = resp.json()
        if not isinstance(data, dict) or data.get("errors"):
            last_err = f"gql errors: {str(data.get('errors'))[:160]}"
            break
        loc = ((data.get("data") or {}).get("locationBySearchTerm")) or {}
        st_block = loc.get("stations") or {}
        results = st_block.get("results") or []
        next_cur = None
        try:
            next_cur = (st_block.get("cursor") or {}).get("next")
        except Exception:
            next_cur = None
        for raw in results:
            row = _normalize_station(raw, fuel)
            if not row:
                continue
            sid = row.get("station_id") or f"{row.get('lat')},{row.get('lon')}"
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            out.append(row)
            if len(out) >= limit:
                return out, None
        if not next_cur or not results:
            break
        cursor = next_cur
        time.sleep(0.35)
    if out:
        return out, None
    return [], last_err or "empty results"


def _parse_gql(data: dict, fuel: str, limit: int) -> list[dict]:
    if not isinstance(data, dict):
        return []
    if data.get("errors"):
        return []
    loc = ((data.get("data") or {}).get("locationBySearchTerm")) or {}
    results = ((loc.get("stations") or {}).get("results")) or []
    out: list[dict] = []
    for raw in results:
        row = _normalize_station(raw, fuel)
        if row:
            out.append(row)
        if len(out) >= limit:
            break
    return out
