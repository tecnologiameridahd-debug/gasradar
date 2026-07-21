"""
Scraper AAA Fuel Prices (promedios estado + metro).

Fuente: https://gasprices.aaa.com
Gratis, sin key. Mejora la base de estimaciones (más cercana a la calle que EIA viejo).

No da precio por bomba individual — da promedio de estado/ciudad.
Usar con caché en disco (~1 día). Activar: USE_AAA_SCRAPER=1 (default ON).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
AAA_CACHE_PATH = DATA_DIR / "aaa_cache.json"
AAA_CACHE_TTL = 20 * 3600  # ~20h (AAA suele actualizar 1×/día)

_mem: dict[str, Any] = {"ts": 0.0, "states": {}, "metros": {}}

# USPS abbr
_STATE_NAME_TO_ABBR = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}


def _enabled() -> bool:
    v = (os.environ.get("USE_AAA_SCRAPER") or os.environ.get("AAA_SCRAPER") or "1").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def _parse_usd(s: str) -> float | None:
    if not s:
        return None
    m = re.search(r"([0-9]+\.[0-9]+)", str(s).replace(",", ""))
    if not m:
        return None
    try:
        v = float(m.group(1))
        if 1.0 < v < 15.0:
            return round(v, 3)
    except ValueError:
        return None
    return None


def _http_get(url: str) -> str | None:
    try:
        from curl_cffi import requests as cr

        r = cr.get(
            url,
            impersonate="chrome120",
            timeout=35,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        if r.status_code == 200 and r.text and len(r.text) > 500:
            return r.text
        print(f"[aaa] HTTP {r.status_code} {url}")
    except Exception as e:
        print(f"[aaa] get fail: {type(e).__name__}: {e}")
    return None


def _load_disk() -> dict:
    try:
        if AAA_CACHE_PATH.exists():
            return json.loads(AAA_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_disk(obj: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        AAA_CACHE_PATH.write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        print(f"[aaa] save fail: {e}")


def fetch_aaa_state_table() -> dict[str, dict]:
    """
    Scrapea tabla nacional de promedios por estado.
    Returns: { "CO": {regular, mid, premium, diesel, source, ok, ts}, ... }
    """
    html = _http_get("https://gasprices.aaa.com/state-gas-price-averages/")
    if not html:
        return {}
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[aaa] beautifulsoup4 missing")
        return {}

    soup = BeautifulSoup(html, "lxml")
    out: dict[str, dict] = {}
    now = time.time()
    for table in soup.find_all("table"):
        headers = [
            c.get_text(strip=True).lower()
            for c in (table.find("tr").find_all(["th", "td"]) if table.find("tr") else [])
        ]
        if not headers or "regular" not in " ".join(headers):
            continue
        for row in table.find_all("tr")[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 5:
                continue
            name = cells[0].strip()
            abbr = _STATE_NAME_TO_ABBR.get(name.lower())
            if not abbr:
                # "Colorado" ok; skip garbage
                continue
            reg = _parse_usd(cells[1])
            mid = _parse_usd(cells[2])
            prem = _parse_usd(cells[3])
            diesel = _parse_usd(cells[4])
            if reg is None:
                continue
            out[abbr] = {
                "regular": reg,
                "mid": mid if mid is not None else round(reg + 0.30, 3),
                "premium": prem if prem is not None else round(reg + 0.55, 3),
                "diesel": diesel if diesel is not None else round(reg + 0.40, 3),
                "source": "aaa",
                "ok": True,
                "ts": now,
                "state_name": name,
            }
    print(f"[aaa] state table n={len(out)}")
    return out


def fetch_aaa_state_detail(state: str) -> dict:
    """
    Página de estado: current avg + metros.
    Returns { state: {...}, metros: { "colorado springs": {...}, ... } }
    """
    st = (state or "CO").upper().strip()
    html = _http_get(f"https://gasprices.aaa.com/?state={st}")
    if not html:
        return {"state": None, "metros": {}}
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {"state": None, "metros": {}}

    soup = BeautifulSoup(html, "lxml")
    now = time.time()
    state_avg = None
    metros: dict[str, dict] = {}

    # Primera tabla con "Current Avg."
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        texts = [[c.get_text(strip=True) for c in row.find_all(["td", "th"])] for row in rows]
        flat = " ".join(" ".join(r) for r in texts).lower()
        if "current avg" in flat and state_avg is None:
            for cells in texts:
                if cells and "current" in cells[0].lower() and len(cells) >= 5:
                    reg = _parse_usd(cells[1])
                    if reg:
                        state_avg = {
                            "regular": reg,
                            "mid": _parse_usd(cells[2]) or round(reg + 0.30, 3),
                            "premium": _parse_usd(cells[3]) or round(reg + 0.55, 3),
                            "diesel": _parse_usd(cells[4]) or round(reg + 0.40, 3),
                            "source": "aaa",
                            "ok": True,
                            "ts": now,
                            "state": st,
                        }
                    break

    # Metros: filas con nombre de ciudad y 4 precios
    # Heurística: celdas tipo ["Colorado Springs", "$3.82", ...]
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 5:
                continue
            name = cells[0].strip()
            if not name or name.lower() in (
                "current avg.",
                "yesterday avg.",
                "week ago avg.",
                "month ago avg.",
                "year ago avg.",
                "regular",
                "",
            ):
                continue
            if "avg" in name.lower() or "price" in name.lower():
                continue
            reg = _parse_usd(cells[1])
            mid = _parse_usd(cells[2])
            prem = _parse_usd(cells[3])
            diesel = _parse_usd(cells[4])
            if reg is None:
                continue
            # ciudad / metro (no un estado suelto)
            key = re.sub(r"\s+", " ", name.lower()).strip()
            if len(key) < 3:
                continue
            metros[key] = {
                "regular": reg,
                "mid": mid if mid is not None else round(reg + 0.30, 3),
                "premium": prem if prem is not None else round(reg + 0.55, 3),
                "diesel": diesel if diesel is not None else round(reg + 0.40, 3),
                "source": "aaa_metro",
                "ok": True,
                "ts": now,
                "metro_name": name,
                "state": st,
            }

    print(f"[aaa] detail {st} avg={state_avg and state_avg.get('regular')} metros={len(metros)}")
    return {"state": state_avg, "metros": metros}


def refresh_aaa(states: list[str] | None = None) -> dict:
    """Actualiza caché AAA (tabla + detalles de estados clave)."""
    if not _enabled():
        return {"ok": False, "disabled": True}

    now = time.time()
    disk = _load_disk()
    states_map = dict(disk.get("states") or {})
    metros_map = dict(disk.get("metros") or {})

    table = fetch_aaa_state_table()
    for k, v in table.items():
        states_map[k] = v

    want = states or ["CO", "CA", "TX", "FL", "NY", "AZ", "NV", "WA", "IL", "GA"]
    for st in want:
        try:
            det = fetch_aaa_state_detail(st)
            if det.get("state"):
                states_map[st] = det["state"]
            for mk, mv in (det.get("metros") or {}).items():
                metros_map[f"{st}:{mk}"] = mv
            time.sleep(0.4)  # ser educados
        except Exception as e:
            print(f"[aaa] detail {st}: {e}")

    payload = {
        "ts": now,
        "ok": bool(states_map),
        "states": states_map,
        "metros": metros_map,
        "source": "aaa",
    }
    _mem.update(payload)
    _save_disk(payload)
    return {
        "ok": payload["ok"],
        "states": len(states_map),
        "metros": len(metros_map),
        "co_regular": (states_map.get("CO") or {}).get("regular"),
    }


def get_aaa_averages(
    state: str = "CO",
    city: str | None = None,
) -> dict | None:
    """
    Promedios AAA para un estado (y metro si hay match de city).
    Lee caché; si no hay o está vieja, refresca en caliente (solo ese estado).
    """
    if not _enabled():
        return None
    st = (state or "CO").upper().strip()
    now = time.time()

    # memoria
    if _mem.get("ok") and now - float(_mem.get("ts") or 0) < AAA_CACHE_TTL:
        states = _mem.get("states") or {}
        metros = _mem.get("metros") or {}
    else:
        disk = _load_disk()
        if disk.get("ok") and now - float(disk.get("ts") or 0) < AAA_CACHE_TTL:
            _mem.update(disk)
            states = disk.get("states") or {}
            metros = disk.get("metros") or {}
        else:
            # refresh ligero: tabla + este estado
            try:
                refresh_aaa([st])
            except Exception as e:
                print(f"[aaa] refresh: {e}")
            states = _mem.get("states") or _load_disk().get("states") or {}
            metros = _mem.get("metros") or _load_disk().get("metros") or {}

    # metro primero (más local)
    if city:
        ckey = re.sub(r"\s+", " ", city.lower()).strip()
        # match exacto o parcial
        for mk, mv in metros.items():
            if not mk.startswith(f"{st}:"):
                continue
            metro_name = mk.split(":", 1)[-1]
            if ckey == metro_name or ckey in metro_name or metro_name in ckey:
                return dict(mv)
        # sin prefijo de estado
        for mk, mv in metros.items():
            metro_name = mk.split(":")[-1]
            if ckey == metro_name or ckey in metro_name:
                return dict(mv)

    row = states.get(st)
    if row and row.get("ok") and row.get("regular"):
        return dict(row)
    return None
