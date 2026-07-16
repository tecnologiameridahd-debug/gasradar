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
import sqlite3
import time
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "prices.db"
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


def _collect_api_key() -> str:
    return (os.environ.get("COLLECT_API_KEY") or os.environ.get("GAS_API_KEY") or "").strip()


def _state_to_duoarea(state: str) -> str:
    """Colorado -> SCO, California -> SCA, etc."""
    st = (state or "US").upper().strip()
    if st in ("US", "USA", "NUS", "DEFAULT", ""):
        return "NUS"
    return "S" + st


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS price_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            fuel TEXT NOT NULL,
            price REAL NOT NULL,
            reported_at REAL NOT NULL,
            note TEXT
        )
        """
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_reports_station ON price_reports(station_id, fuel, reported_at DESC)"
    )
    c.commit()
    return c


def report_price(station_id: str, fuel: str, price: float, note: str | None = None) -> dict:
    fuel = fuel.lower().strip()
    if fuel not in ("regular", "mid", "premium", "diesel"):
        raise ValueError("fuel debe ser regular|mid|premium|diesel")
    if price < 1.0 or price > 12.0:
        raise ValueError("precio fuera de rango")
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO price_reports(station_id, fuel, price, reported_at, note) VALUES (?,?,?,?,?)",
            (station_id, fuel, round(price, 3), now, note or ""),
        )
        c.commit()
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
    with _conn() as c:
        for fuel in ("regular", "mid", "premium", "diesel"):
            rows = c.execute(
                """
                SELECT price, reported_at FROM price_reports
                WHERE station_id=? AND fuel=? AND reported_at>=?
                ORDER BY reported_at DESC LIMIT 8
                """,
                (station_id, fuel, cutoff),
            ).fetchall()
            if not rows:
                # último reporte hasta 72h
                row = c.execute(
                    """
                    SELECT price, reported_at FROM price_reports
                    WHERE station_id=? AND fuel=? AND reported_at>=?
                    ORDER BY reported_at DESC LIMIT 1
                    """,
                    (station_id, fuel, time.time() - REPORT_MAX_AGE_SEC),
                ).fetchone()
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


def state_averages(state: str = "CO") -> dict:
    """Promedios listos para la API: prefiere EIA, si no fallback estático."""
    st = (state or "DEFAULT").upper()
    eia = fetch_eia_state_averages(st)
    base = dict(BASE_STATE_AVG.get(st) or BASE_STATE_AVG["DEFAULT"])

    out = {
        "regular": eia["regular"] if eia.get("regular") is not None else base["regular"],
        "mid": eia["mid"] if eia.get("mid") is not None else base["mid"],
        "premium": eia["premium"] if eia.get("premium") is not None else base["premium"],
        "diesel": eia["diesel"] if eia.get("diesel") is not None else base["diesel"],
        "source": "eia" if eia.get("ok") else "fallback",
        "eia_period": eia.get("period"),
        "eia_ok": bool(eia.get("ok")),
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
        "collect_api_configured": bool(_collect_api_key()),
        "how_it_works": (
            "1) Reportes de la comunidad (prioridad). "
            "2) Estimacion EIA oficial + ajuste por marca. "
            "3) Precios exactos de bomba requieren API de pago o mas reportes."
        ),
    }
