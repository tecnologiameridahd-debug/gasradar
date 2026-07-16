"""
Capa de precios GasRadar.

Prioridad:
1) Reportes de usuarios (consenso reciente)
2) API de estaciones en vivo (opcional, CollectAPI si hay key)
3) Estimación: promedio estatal EIA real + ajuste por marca

EIA es gratis (DEMO_KEY o EIA_API_KEY). Datos oficiales semanales.
"""
from __future__ import annotations

import hashlib
import os
import statistics
import time
from pathlib import Path

import httpx

from backend.db import execute as db_execute
from backend.db import fetchall as db_fetchall
from backend.db import fetchone as db_fetchone

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EIA_CACHE_PATH = DATA_DIR / "eia_cache.json"

# Fallback si EIA no responde (actualizado ~2026; se reemplaza cuando EIA responde)
BASE_STATE_AVG = {
    "CO": {"regular": 3.19, "mid": 3.49, "premium": 3.79, "diesel": 3.55},
    "CA": {"regular": 4.55, "mid": 4.75, "premium": 4.95, "diesel": 4.80},
    "TX": {"regular": 2.85, "mid": 3.15, "premium": 3.45, "diesel": 3.20},
    "NY": {"regular": 3.35, "mid": 3.65, "premium": 3.95, "diesel": 3.90},
    "FL": {"regular": 3.10, "mid": 3.40, "premium": 3.70, "diesel": 3.50},
    "AZ": {"regular": 3.25, "mid": 3.55, "premium": 3.85, "diesel": 3.60},
    "NM": {"regular": 2.95, "mid": 3.25, "premium": 3.55, "diesel": 3.30},
    "UT": {"regular": 3.15, "mid": 3.45, "premium": 3.75, "diesel": 3.50},
    "WY": {"regular": 3.05, "mid": 3.35, "premium": 3.65, "diesel": 3.40},
    "KS": {"regular": 2.90, "mid": 3.20, "premium": 3.50, "diesel": 3.25},
    "NE": {"regular": 2.95, "mid": 3.25, "premium": 3.55, "diesel": 3.30},
    "NV": {"regular": 3.55, "mid": 3.85, "premium": 4.15, "diesel": 3.90},
    "WA": {"regular": 4.10, "mid": 4.40, "premium": 4.70, "diesel": 4.40},
    "OR": {"regular": 3.85, "mid": 4.15, "premium": 4.45, "diesel": 4.15},
    "DEFAULT": {"regular": 3.25, "mid": 3.55, "premium": 3.85, "diesel": 3.65},
}

# Ajuste típico vs promedio del estado (clubes más baratos, premium brands más caras)
BRAND_DELTA = {
    "Costco": -0.25,
    "Sam's Club": -0.22,
    "Sams Club": -0.22,
    "Walmart": -0.12,
    "King Soopers": -0.08,
    "Safeway": -0.06,
    "Kroger": -0.08,
    "Smith's": -0.08,
    "QuikTrip": -0.04,
    "Quiktrip": -0.04,
    "Qt": -0.04,
    "Murphy": -0.05,
    "Murphy USA": -0.08,
    "Arco": -0.12,
    "Maverik": -0.03,
    "Sinclair": 0.02,
    "Shell": 0.10,
    "Chevron": 0.12,
    "Exxon": 0.07,
    "Mobil": 0.07,
    "Bp": 0.05,
    "BP": 0.05,
    "7-Eleven": 0.08,
    "Circle K": 0.04,
    "Conoco": 0.03,
    "Phillips 66": 0.04,
    "Valero": 0.02,
    "Texaco": 0.06,
    "Speedway": 0.03,
    "Cenex": 0.01,
    "Holiday": 0.02,
    "Kum & Go": 0.02,
    "Love's": -0.02,
    "Pilot": -0.01,
    "Flying J": -0.01,
    "Independiente": -0.01,
    "Gasolinera": 0.0,
}

# Spreads si EIA no trae mid/premium
SPREAD_MID = 0.30
SPREAD_PREMIUM = 0.55
SPREAD_DIESEL = 0.40

REPORT_MAX_AGE_SEC = 72 * 3600
REPORT_CONSENSUS_HOURS = 48
EIA_CACHE_TTL = 6 * 3600  # 6h

# Memoria proceso
_eia_mem: dict = {"ts": 0.0, "by_state": {}}

# EIA product codes
EIA_PRODUCTS = {
    "regular": "EPMR",
    "mid": "EPMM",
    "premium": "EPMP",
    "diesel": "EPD2D",
}


def _eia_api_key() -> str:
    return (os.environ.get("EIA_API_KEY") or "").strip() or "DEMO_KEY"


def _secret_from_local(*names: str) -> str:
    try:
        import config_local as _cfg  # type: ignore

        for n in names:
            v = getattr(_cfg, n, None)
            if v:
                return str(v).strip()
    except ImportError:
        pass
    return ""


def _zyla_api_key() -> str:
    """
    Zyla Labs API key (formato id|token).
    Env: ZYLA_API_KEY o COLLECT_API_KEY / GAS_API_KEY (compat).
    """
    return (
        (os.environ.get("ZYLA_API_KEY") or "").strip()
        or (os.environ.get("COLLECT_API_KEY") or "").strip()
        or (os.environ.get("GAS_API_KEY") or "").strip()
        or _secret_from_local("ZYLA_API_KEY", "COLLECT_API_KEY", "GAS_API_KEY")
    )


def _zyla_gas_url() -> str:
    """
    URL promedios por ZIP (get+prices).
    Ejemplo:
      https://zylalabs.com/api/3109/us+gas+prices+api/24537/get+prices
    """
    return (
        (os.environ.get("ZYLA_GAS_URL") or "").strip()
        or _secret_from_local("ZYLA_GAS_URL")
    )


def _zyla_station_url() -> str:
    """
    URL de estaciones con precio (station+data).
    Ejemplo:
      https://zylalabs.com/api/3109/us+gas+prices+api/24538/station+data
    """
    return (
        (os.environ.get("ZYLA_STATION_URL") or "").strip()
        or _secret_from_local("ZYLA_STATION_URL")
    )


def _collect_api_key() -> str:
    """Compat: misma key que Zyla."""
    return _zyla_api_key()


def _state_to_duoarea(state: str) -> str:
    """Colorado -> SCO, California -> SCA, etc."""
    st = (state or "US").upper().strip()
    if st in ("US", "USA", "NUS", "DEFAULT", ""):
        return "NUS"
    return "S" + st


def report_price(station_id: str, fuel: str, price: float, note: str | None = None) -> dict:
    fuel = fuel.lower().strip()
    if fuel not in ("regular", "mid", "premium", "diesel"):
        raise ValueError("fuel debe ser regular|mid|premium|diesel")
    if price < 1.0 or price > 12.0:
        raise ValueError("precio fuera de rango")
    now = time.time()
    db_execute(
        "INSERT INTO price_reports(station_id, fuel, price, reported_at, note) VALUES (?,?,?,?,?)",
        (station_id, fuel, round(price, 3), now, note or ""),
    )
    # devolver consenso actualizado
    consensus = latest_reports(station_id).get(fuel) or {}
    return {
        "station_id": station_id,
        "fuel": fuel,
        "price": consensus.get("price", round(price, 3)),
        "reported_at": now,
        "source": "user",
        "reports_count": consensus.get("reports_count", 1),
    }


def latest_reports(station_id: str) -> dict[str, dict]:
    """
    Consenso de reportes recientes:
    - toma hasta 8 reportes de las últimas 48h
    - usa la mediana (más robusta que el promedio)
    """
    cutoff = time.time() - REPORT_CONSENSUS_HOURS * 3600
    out: dict[str, dict] = {}
    for fuel in ("regular", "mid", "premium", "diesel"):
        rows = db_fetchall(
            """
            SELECT price, reported_at FROM price_reports
            WHERE station_id=? AND fuel=? AND reported_at>=?
            ORDER BY reported_at DESC LIMIT 8
            """,
            (station_id, fuel, cutoff),
        )
        if not rows:
            # último reporte hasta 72h
            row = db_fetchone(
                """
                SELECT price, reported_at FROM price_reports
                WHERE station_id=? AND fuel=? AND reported_at>=?
                ORDER BY reported_at DESC LIMIT 1
                """,
                (station_id, fuel, time.time() - REPORT_MAX_AGE_SEC),
            )
            if row:
                out[fuel] = {
                    "price": float(row["price"]),
                    "reported_at": row["reported_at"],
                    "source": "user",
                    "age_hours": round((time.time() - row["reported_at"]) / 3600, 1),
                    "reports_count": 1,
                    "confidence": "medium",
                }
            continue

        prices = [float(r["price"]) for r in rows]
        med = statistics.median(prices)
        newest = rows[0]["reported_at"]
        n = len(prices)
        conf = "high" if n >= 3 else "medium" if n >= 2 else "medium"
        out[fuel] = {
            "price": round(med, 3),
            "reported_at": newest,
            "source": "user",
            "age_hours": round((time.time() - newest) / 3600, 1),
            "reports_count": n,
            "confidence": conf,
        }
    return out


def _seed_from_id(station_id: str) -> float:
    h = int(hashlib.sha1(station_id.encode()).hexdigest(), 16)
    return ((h % 17) - 8) / 100.0  # -0.08 .. +0.08


def _fetch_eia_value(duoarea: str, product: str) -> tuple[float | None, str | None]:
    url = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
    params = {
        "api_key": _eia_api_key(),
        "frequency": "weekly",
        "data[0]": "value",
        "facets[product][]": product,
        "facets[duoarea][]": duoarea,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 1,
    }
    try:
        r = httpx.get(url, params=params, timeout=12.0)
        if r.status_code != 200:
            return None, None
        data = (r.json().get("response") or {}).get("data") or []
        if not data:
            return None, None
        row = data[0]
        val = row.get("value")
        if val is None:
            return None, None
        return float(val), str(row.get("period") or "")
    except Exception:
        return None, None


def _load_disk_eia() -> dict:
    try:
        import json

        if EIA_CACHE_PATH.exists():
            return json.loads(EIA_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_disk_eia(all_states: dict) -> None:
    try:
        import json

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        EIA_CACHE_PATH.write_text(
            json.dumps(all_states, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def fetch_eia_state_averages(state: str = "CO") -> dict:
    """
    Precios oficiales EIA (retail semanal) por estado.
    Solo 1 request (regular) + spreads mid/premium/diesel → menos rate-limit.
    Cache 6h memoria + disco.
    """
    st = (state or "DEFAULT").upper()
    now = time.time()
    cached = _eia_mem["by_state"].get(st)
    if cached and now - cached.get("ts", 0) < EIA_CACHE_TTL and cached.get("ok"):
        return cached

    # disco
    disk = _load_disk_eia()
    d_cached = disk.get(st)
    if d_cached and now - d_cached.get("ts", 0) < EIA_CACHE_TTL and d_cached.get("ok"):
        _eia_mem["by_state"][st] = d_cached
        return d_cached

    duo = _state_to_duoarea(st if st != "DEFAULT" else "US")
    result = {
        "regular": None,
        "mid": None,
        "premium": None,
        "diesel": None,
        "period": None,
        "source": "eia",
        "duoarea": duo,
        "ts": now,
        "ok": False,
    }

    # 1 sola llamada: regular del estado (o nacional)
    val, period = _fetch_eia_value(duo, EIA_PRODUCTS["regular"])
    if val is None and duo != "NUS":
        val, period = _fetch_eia_value("NUS", EIA_PRODUCTS["regular"])

    if val is not None:
        result["regular"] = round(val, 3)
        result["mid"] = round(val + SPREAD_MID, 3)
        result["premium"] = round(val + SPREAD_PREMIUM, 3)
        result["diesel"] = round(val + SPREAD_DIESEL, 3)
        result["period"] = period
        result["ok"] = True
    elif d_cached and d_cached.get("ok"):
        # rate limit: usar disco aunque esté viejo
        d_cached = dict(d_cached)
        d_cached["stale"] = True
        _eia_mem["by_state"][st] = d_cached
        return d_cached

    _eia_mem["by_state"][st] = result
    _eia_mem["ts"] = now
    if result["ok"]:
        disk[st] = result
        _save_disk_eia(disk)
    return result


# Caché Zyla (precios por ZIP / estado)
_zyla_mem: dict = {"ts": 0.0, "by_key": {}}
ZYLA_CACHE_TTL = 2 * 3600  # 2h


def _parse_price_val(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _extract_fuel_prices(obj) -> dict | None:
    """Intenta sacar regular/mid/premium/diesel de un JSON Zyla (formatos varios)."""
    if obj is None:
        return None
    regular = mid = premium = diesel = None

    def dig(d: dict):
        nonlocal regular, mid, premium, diesel
        mapping = [
            (("regular", "gasoline", "gas", "unleaded", "reg", "price"), "regular"),
            (("mid", "midgrade", "mid_grade", "plus"), "mid"),
            (("premium", "super", "prem"), "premium"),
            (("diesel", "dsl"), "diesel"),
        ]
        for keys, target in mapping:
            for k in keys:
                if k in d and d[k] is not None:
                    val = _parse_price_val(d[k])
                    if val is None:
                        continue
                    if target == "regular" and regular is None:
                        regular = val
                    elif target == "mid" and mid is None:
                        mid = val
                    elif target == "premium" and premium is None:
                        premium = val
                    elif target == "diesel" and diesel is None:
                        diesel = val

    if isinstance(obj, dict):
        dig(obj)
        for nest in ("result", "data", "prices", "price", "average", "averages", "state"):
            if isinstance(obj.get(nest), dict):
                dig(obj[nest])
        # lista de estaciones → promedio de regular
        stations = obj.get("stations") or obj.get("results") or obj.get("data")
        if regular is None and isinstance(stations, list) and stations:
            vals = []
            for s in stations[:40]:
                if not isinstance(s, dict):
                    continue
                dig(s)
                p = _parse_price_val(
                    s.get("regular")
                    or s.get("gasoline")
                    or s.get("price")
                    or s.get("gas_price")
                )
                if p is not None:
                    vals.append(p)
            if vals:
                regular = sum(vals) / len(vals)
    elif isinstance(obj, list) and obj:
        return _extract_fuel_prices(obj[0] if isinstance(obj[0], dict) else {"data": obj})

    if regular is None:
        return None
    return {
        "regular": round(regular, 3),
        "mid": round(mid if mid is not None else regular + SPREAD_MID, 3),
        "premium": round(premium if premium is not None else regular + SPREAD_PREMIUM, 3),
        "diesel": round(diesel if diesel is not None else regular + SPREAD_DIESEL, 3),
    }


def _normalize_station_name(name: str) -> str:
    n = (name or "").lower()
    for ch in ("#", ".", ",", "-", "_", "'"):
        n = n.replace(ch, " ")
    return " ".join(n.split())


def fetch_zyla_stations(zip_code: str, fuel: str = "regular") -> list[dict]:
    """
    Lista estaciones con precio desde Zyla station+data.
    Cada item: name, brand, lat, lon, address, price, fuel, distance_mi?
    """
    key = _zyla_api_key()
    base = _zyla_station_url()
    if not key or not base:
        return []
    z = "".join(c for c in str(zip_code) if c.isdigit())[:5]
    if len(z) != 5:
        return []
    cache_key = f"stations:{z}:{fuel}"
    now = time.time()
    cached = _zyla_mem["by_key"].get(cache_key)
    if cached and now - cached.get("ts", 0) < ZYLA_CACHE_TTL and cached.get("ok"):
        return list(cached.get("stations") or [])

    params = {"zip": z, "type": fuel or "regular"}
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    try:
        r = httpx.get(base, params=params, headers=headers, timeout=18.0)
        if r.status_code != 200:
            print(f"[zyla stations] status={r.status_code} body={r.text[:220]}")
            return []
        data = r.json()
        raw_list = []
        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict):
            for k in ("stations", "results", "data", "result", "items"):
                v = data.get(k)
                if isinstance(v, list):
                    raw_list = v
                    break
                if isinstance(v, dict):
                    for k2 in ("stations", "results", "items"):
                        if isinstance(v.get(k2), list):
                            raw_list = v[k2]
                            break
        out: list[dict] = []
        for s in raw_list:
            if not isinstance(s, dict):
                continue
            name = (
                s.get("name")
                or s.get("station")
                or s.get("station_name")
                or s.get("title")
                or "Gas Station"
            )
            brand = s.get("brand") or s.get("company") or None
            lat = s.get("lat") or s.get("latitude") or s.get("Latitude")
            lon = s.get("lon") or s.get("lng") or s.get("longitude") or s.get("Longitude")
            try:
                lat_f = float(lat) if lat is not None else None
                lon_f = float(lon) if lon is not None else None
            except (TypeError, ValueError):
                lat_f = lon_f = None
            addr = (
                s.get("address")
                or s.get("street")
                or s.get("addr")
                or s.get("location")
            )
            if isinstance(addr, dict):
                addr = ", ".join(
                    str(addr.get(k))
                    for k in ("street", "city", "state", "zip", "zipcode")
                    if addr.get(k)
                )
            price = _parse_price_val(
                s.get(fuel)
                or s.get("regular")
                or s.get("gasoline")
                or s.get("price")
                or s.get("gas_price")
                or s.get("reg_price")
            )
            if price is None and isinstance(s.get("prices"), dict):
                pr = s["prices"]
                price = _parse_price_val(
                    pr.get(fuel) or pr.get("regular") or pr.get("gasoline") or pr.get("price")
                )
            if price is None:
                continue
            out.append(
                {
                    "name": str(name).strip(),
                    "name_norm": _normalize_station_name(str(name)),
                    "brand": (str(brand).strip() if brand else None),
                    "lat": lat_f,
                    "lon": lon_f,
                    "address": str(addr).strip() if addr else None,
                    "price": round(price, 3),
                    "fuel": fuel,
                    "source": "zyla",
                }
            )
        _zyla_mem["by_key"][cache_key] = {
            "ok": True,
            "ts": now,
            "stations": out,
        }
        print(f"[zyla stations] OK zip={z} n={len(out)}")
        return out
    except Exception as e:
        print(f"[zyla stations] fail: {e}")
        return []


def merge_zyla_prices_into_stations(
    stations: list[dict], zyla_stations: list[dict], fuel: str = "regular"
) -> list[dict]:
    """
    Pone precio Zyla en estaciones OSM cuando coincide nombre/marca/coords.
    """
    if not stations or not zyla_stations:
        return stations
    from backend.geo import haversine_miles

    used: set[int] = set()
    for st in stations:
        if st.get("price_source") == "user":
            continue
        best_i = None
        best_score = 999.0
        sn = _normalize_station_name(st.get("name") or "")
        sb = _normalize_station_name(st.get("brand") or "")
        for i, zs in enumerate(zyla_stations):
            if i in used:
                continue
            score = 50.0
            zn = zs.get("name_norm") or _normalize_station_name(zs.get("name") or "")
            zb = _normalize_station_name(zs.get("brand") or "")
            if sn and zn and (sn in zn or zn in sn):
                score = 1.0
            elif sb and zn and (sb in zn or zn in sb):
                score = 2.0
            elif sb and zb and sb == zb:
                score = 3.0
            # coords cercanas
            if (
                st.get("lat") is not None
                and zs.get("lat") is not None
                and zs.get("lon") is not None
            ):
                try:
                    d = haversine_miles(
                        float(st["lat"]),
                        float(st["lon"]),
                        float(zs["lat"]),
                        float(zs["lon"]),
                    )
                    if d <= 0.15:
                        score = min(score, d)
                    elif d <= 0.4 and score < 10:
                        score = min(score, 5.0 + d)
                except (TypeError, ValueError):
                    pass
            if score < best_score:
                best_score = score
                best_i = i
        if best_i is not None and best_score <= 6.0:
            zs = zyla_stations[best_i]
            used.add(best_i)
            st["price"] = zs["price"]
            st["price_source"] = "zyla"
            st["price_confidence"] = "high"
            st["reports_count"] = st.get("reports_count") or 0
            if isinstance(st.get("prices"), dict):
                st["prices"][fuel] = {
                    "price": zs["price"],
                    "source": "zyla",
                    "age_hours": None,
                    "reports_count": 0,
                    "confidence": "high",
                }
    # reordenar
    stations.sort(
        key=lambda x: (
            round(float(x.get("price") or 99), 3),
            0 if x.get("price_source") == "user" else 1,
            0 if x.get("price_source") == "zyla" else 1,
            float(x.get("distance_mi") or 99),
        )
    )
    return stations


def fetch_zyla_zip_prices(zip_code: str, fuel: str = "regular") -> dict | None:
    """
    Precios vía Zyla Labs (Bearer token).
    Requiere ZYLA_API_KEY + ZYLA_GAS_URL (endpoint del API al que te suscribiste).
    """
    key = _zyla_api_key()
    base = _zyla_gas_url()
    if not key or not base:
        return None
    z = "".join(c for c in str(zip_code) if c.isdigit())[:5]
    if len(z) != 5:
        return None
    cache_key = f"zip:{z}:{fuel}"
    now = time.time()
    cached = _zyla_mem["by_key"].get(cache_key)
    if cached and now - cached.get("ts", 0) < ZYLA_CACHE_TTL and cached.get("ok"):
        return cached

    # URL puede ser plantilla o base; añadimos zip/type si faltan
    url = base
    params = {}
    if "{zip}" in url:
        url = url.replace("{zip}", z)
    else:
        params["zip"] = z
    if "type=" not in url and "{type}" not in url:
        params.setdefault("type", fuel or "regular")
    if "{type}" in url:
        url = url.replace("{type}", fuel or "regular")

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    try:
        r = httpx.get(url, params=params or None, headers=headers, timeout=16.0)
        if r.status_code != 200:
            print(f"[zyla] status={r.status_code} body={r.text[:220]}")
            return None
        data = r.json()
        prices = _extract_fuel_prices(data)
        if not prices:
            print(f"[zyla] no pude parsear: {str(data)[:240]}")
            return None
        out = {**prices, "source": "zyla", "ok": True, "ts": now, "zip": z}
        _zyla_mem["by_key"][cache_key] = out
        print(f"[zyla] OK zip={z} regular={out['regular']}")
        return out
    except Exception as e:
        print(f"[zyla] fail: {e}")
        return None


def fetch_collect_state_averages(state: str = "CO") -> dict | None:
    """Compat nombre viejo: usa Zyla si hay URL de estado; si no, None."""
    # Algunos endpoints Zyla usan ?state=CO
    key = _zyla_api_key()
    base = _zyla_gas_url()
    if not key or not base:
        return None
    if "zip" in base.lower() and "state" not in base.lower():
        return None
    st = (state or "CO").upper().strip()
    cache_key = f"state:{st}"
    now = time.time()
    cached = _zyla_mem["by_key"].get(cache_key)
    if cached and now - cached.get("ts", 0) < ZYLA_CACHE_TTL and cached.get("ok"):
        return cached
    url = base
    params = {}
    if "{state}" in url:
        url = url.replace("{state}", st)
    else:
        params["state"] = st
    try:
        r = httpx.get(
            url,
            params=params or None,
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            timeout=16.0,
        )
        if r.status_code != 200:
            print(f"[zyla] state status={r.status_code} {r.text[:180]}")
            return None
        prices = _extract_fuel_prices(r.json())
        if not prices:
            return None
        out = {**prices, "source": "zyla", "ok": True, "ts": now, "state": st}
        _zyla_mem["by_key"][cache_key] = out
        return out
    except Exception as e:
        print(f"[zyla] state fail: {e}")
        return None


def state_averages(state: str = "CO") -> dict:
    """Promedios: EIA → Zyla → fallback estático."""
    st = (state or "DEFAULT").upper()
    eia = fetch_eia_state_averages(st)
    base = dict(BASE_STATE_AVG.get(st) or BASE_STATE_AVG["DEFAULT"])
    zyla = None
    if not eia.get("ok"):
        zyla = fetch_collect_state_averages(st if st != "DEFAULT" else "CO")

    if eia.get("ok"):
        source = "eia"
        regular, mid, premium, diesel = eia["regular"], eia["mid"], eia["premium"], eia["diesel"]
        period = eia.get("period")
        eia_ok = True
    elif zyla and zyla.get("ok"):
        source = "zyla"
        regular, mid, premium, diesel = (
            zyla["regular"],
            zyla["mid"],
            zyla["premium"],
            zyla["diesel"],
        )
        period = None
        eia_ok = False
    else:
        source = "fallback"
        regular, mid, premium, diesel = base["regular"], base["mid"], base["premium"], base["diesel"]
        period = None
        eia_ok = False

    out = {
        "regular": regular,
        "mid": mid,
        "premium": premium,
        "diesel": diesel,
        "source": source,
        "eia_period": period,
        "eia_ok": eia_ok,
        "zyla_ok": bool(zyla and zyla.get("ok")),
        "collect_ok": bool(zyla and zyla.get("ok")),
    }
    return out


def _brand_delta(brand: str | None) -> float:
    if not brand:
        return BRAND_DELTA["Independiente"]
    if brand in BRAND_DELTA:
        return BRAND_DELTA[brand]
    # match parcial
    b = brand.lower()
    for k, v in BRAND_DELTA.items():
        if k.lower() in b or b in k.lower():
            return v
    return 0.0


def estimate_prices(station: dict, state: str = "CO") -> dict:
    reports = latest_reports(station["id"])
    # no bloquear con red en cada estación
    meta = price_meta(state, fast=True)
    avg = {
        **meta["state_avg"],
        "eia_ok": meta.get("eia_ok"),
        "eia_period": meta.get("eia_period"),
    }
    delta = _brand_delta(station.get("brand"))
    jitter = _seed_from_id(station["id"])
    base_src = "eia_estimate" if avg.get("eia_ok") else "estimate"

    prices: dict = {}
    for fuel in ("regular", "mid", "premium", "diesel"):
        if fuel in reports:
            prices[fuel] = reports[fuel]
            continue

        base = float(avg[fuel])
        if fuel == "regular":
            raw = base + delta + jitter
        elif fuel == "mid":
            reg = prices.get("regular", {}).get("price", base + delta + jitter)
            if prices.get("regular", {}).get("source") in ("user",):
                raw = reg + SPREAD_MID
            else:
                raw = base + delta + jitter
        elif fuel == "premium":
            reg_p = prices.get("regular", {})
            if reg_p.get("source") == "user":
                raw = reg_p["price"] + SPREAD_PREMIUM
            else:
                raw = base + delta + jitter
        else:  # diesel
            raw = base + delta * 0.5 + jitter

        prices[fuel] = {
            "price": round(max(1.5, raw), 3),
            "source": base_src,
            "age_hours": None,
            "reports_count": 0,
            "confidence": "low",
            "eia_period": avg.get("eia_period"),
        }

    return prices


def attach_prices(stations: list[dict], state: str = "CO", fuel: str = "regular") -> list[dict]:
    fuel = fuel.lower()
    # usar promedios sin bloquear (caché o fallback)
    # no llamar EIA síncrono aquí
    out = []
    for s in stations:
        prices = estimate_prices(s, state=state)
        item = dict(s)
        item["prices"] = prices
        pf = prices.get(fuel, prices["regular"])
        item["price"] = pf["price"]
        item["price_source"] = pf.get("source")
        item["price_age_hours"] = pf.get("age_hours")
        item["price_confidence"] = pf.get("confidence")
        item["reports_count"] = pf.get("reports_count") or 0
        out.append(item)

    # Ranking: más barato primero; reportes de usuario ganan empates; luego cercanía
    def sort_key(x):
        is_user = 0 if x.get("price_source") == "user" else 1
        conf_rank = {"high": 0, "medium": 1, "low": 2}.get(
            x.get("price_confidence") or "low", 2
        )
        return (round(float(x["price"]), 3), is_user, conf_rank, float(x["distance_mi"]))

    out.sort(key=sort_key)

    # Delta vs promedio del estado (para UI de "ahorro")
    avg_fuel = None
    try:
        meta = price_meta(state, fast=True)
        avg_fuel = (meta.get("state_avg") or {}).get(fuel)
    except Exception:
        avg_fuel = None
    if avg_fuel is not None:
        for item in out:
            item["vs_avg"] = round(float(item["price"]) - float(avg_fuel), 3)

    return out


def cheapest_summary(stations_with_prices: list[dict]) -> dict | None:
    if not stations_with_prices:
        return None
    best = stations_with_prices[0]
    return {
        "station_id": best["id"],
        "name": best["name"],
        "brand": best.get("brand"),
        "price": best["price"],
        "distance_mi": best["distance_mi"],
        "lat": best["lat"],
        "lon": best["lon"],
        "address": best.get("address"),
        "source": best.get("price_source"),
        "confidence": best.get("price_confidence"),
        "reports_count": best.get("reports_count"),
        "vs_avg": best.get("vs_avg"),
    }


def price_meta(state: str = "CO", fast: bool = True) -> dict:
    """Info para el frontend. fast=True evita llamar EIA si no hay caché (no colgar)."""
    st = (state or "DEFAULT").upper()
    # si hay caché caliente, usarla; si no, fallback sin red
    cached = _eia_mem["by_state"].get(st)
    now = time.time()
    if cached and now - cached.get("ts", 0) < EIA_CACHE_TTL and cached.get("ok"):
        avg = state_averages(state)
    elif not fast:
        avg = state_averages(state)
    else:
        # no bloquear con EIA en cada búsqueda
        disk = _load_disk_eia().get(st)
        if disk and disk.get("ok"):
            avg = {
                "regular": disk["regular"],
                "mid": disk["mid"],
                "premium": disk["premium"],
                "diesel": disk["diesel"],
                "source": "eia",
                "eia_period": disk.get("period"),
                "eia_ok": True,
            }
        else:
            base = dict(BASE_STATE_AVG.get(st) or BASE_STATE_AVG["DEFAULT"])
            avg = {**base, "source": "fallback", "eia_period": None, "eia_ok": False}

    return {
        "state_avg": {
            "regular": avg["regular"],
            "mid": avg["mid"],
            "premium": avg["premium"],
            "diesel": avg["diesel"],
        },
        "avg_source": avg.get("source"),
        "eia_period": avg.get("eia_period"),
        "eia_ok": avg.get("eia_ok"),
        "collect_api_configured": bool(_zyla_api_key()),
        "zyla_configured": bool(_zyla_api_key()),
        "zyla_url_configured": bool(_zyla_gas_url()),
        "how_it_works": (
            "1) Reportes de la comunidad (prioridad). "
            "2) EIA oficial o Zyla Labs + ajuste por marca. "
            "3) Precios exactos de bomba: mas reportes o API de estaciones."
        ),
    }
