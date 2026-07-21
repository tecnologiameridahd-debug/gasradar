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
_job: dict[str, Any] = {
    "running": False,
    "last_start": None,
    "last_end": None,
    "last_ok": None,
    "last_error": None,
    "last_result": None,
}

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


def _avg_from_current_row(texts: list[list[str]], now: float, st: str) -> dict | None:
    for cells in texts:
        if not cells or len(cells) < 5:
            continue
        if "current" in cells[0].lower() and "avg" in cells[0].lower():
            reg = _parse_usd(cells[1])
            if reg is None:
                return None
            return {
                "regular": reg,
                "mid": _parse_usd(cells[2]) or round(reg + 0.30, 3),
                "premium": _parse_usd(cells[3]) or round(reg + 0.55, 3),
                "diesel": _parse_usd(cells[4]) or round(reg + 0.40, 3),
                "source": "aaa",
                "ok": True,
                "ts": now,
                "state": st,
            }
    return None


def fetch_aaa_state_detail(state: str) -> dict:
    """
    Página de estado: current avg + metros (h3 + tabla Current Avg).
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

    # Primera tabla "Current Avg." = promedio del estado
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        texts = [
            [c.get_text(strip=True) for c in row.find_all(["td", "th"])] for row in rows
        ]
        flat = " ".join(" ".join(r) for r in texts).lower()
        if "current avg" in flat and state_avg is None:
            state_avg = _avg_from_current_row(texts, now, st)
            if state_avg:
                state_avg["source"] = "aaa"
            break

    # Metros: <h3>Ciudad</h3> seguido de tabla con Current Avg.
    skip_h3 = {
        "compare states",
        "national average",
        "state average",
        "fuel price averages",
    }
    for h3 in soup.find_all("h3"):
        name = h3.get_text(strip=True)
        if not name or len(name) < 2:
            continue
        if name.lower() in skip_h3:
            continue
        # tabla siguiente
        table = h3.find_next("table")
        if not table:
            continue
        texts = [
            [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            for row in table.find_all("tr")
        ]
        flat = " ".join(" ".join(r) for r in texts).lower()
        if "current avg" not in flat:
            continue
        avg = _avg_from_current_row(texts, now, st)
        if not avg:
            continue
        # limpiar " (CO only)" etc.
        clean = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()
        clean = re.sub(r"\s+", " ", clean)
        key = clean.lower()
        avg["source"] = "aaa_metro"
        avg["metro_name"] = clean
        metros[key] = avg

    print(
        f"[aaa] detail {st} avg={state_avg and state_avg.get('regular')} metros={len(metros)}"
    )
    return {"state": state_avg, "metros": metros}


# Todos los estados + DC (cualquier ZIP USA)
US_STATE_CODES: list[str] = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]


def refresh_aaa_table_only() -> dict:
    """
    Rápido (~5–15 s): 1 sola página = 50 estados + DC.
    Suficiente para CUALQUIER ZIP de USA (promedio del estado).
    Ideal para cron-job.org (timeout corto).
    """
    if not _enabled():
        return {"ok": False, "disabled": True}

    now = time.time()
    disk = _load_disk()
    states_map = dict(disk.get("states") or {})
    metros_map = dict(disk.get("metros") or {})

    table = fetch_aaa_state_table()
    if not table:
        return {
            "ok": False,
            "error": "no se pudo leer tabla AAA",
            "states": len(states_map),
            "metros": len(metros_map),
        }
    for k, v in table.items():
        states_map[k] = v

    payload = {
        "ts": now,
        "ok": True,
        "states": states_map,
        "metros": metros_map,
        "source": "aaa",
        "covers": "all_us_states",
    }
    _mem.clear()
    _mem.update(payload)
    _save_disk(payload)
    return {
        "ok": True,
        "mode": "table_fast",
        "states": len(states_map),
        "metros": len(metros_map),
        "co_regular": (states_map.get("CO") or {}).get("regular"),
        "covers": "USA — cualquier ZIP → promedio del estado AAA",
        "seconds": "fast",
    }


def refresh_aaa(states: list[str] | None = None, full_usa: bool = True) -> dict:
    """
    Actualiza caché AAA para TODO USA.
    1) Tabla nacional (50 estados + DC) en 1 request
    2) Páginas de detalle (metros) para estados pedidos o todos si full_usa
    """
    if not _enabled():
        return {"ok": False, "disabled": True}

    now = time.time()
    disk = _load_disk()
    states_map = dict(disk.get("states") or {})
    metros_map = dict(disk.get("metros") or {})

    # 1) Una sola página = cobertura nacional
    table = fetch_aaa_state_table()
    for k, v in table.items():
        states_map[k] = v

    # 2) Detalle + metros: full USA o lista
    if states is not None:
        want = list(states)
    elif full_usa:
        want = list(US_STATE_CODES)
    else:
        want = ["CO", "CA", "TX", "FL", "NY", "AZ", "NV", "WA", "IL", "GA"]

    detail_ok = 0
    for i, st in enumerate(want):
        try:
            det = fetch_aaa_state_detail(st)
            if det.get("state"):
                # preferir detalle del estado si es más fresco
                states_map[st] = det["state"]
                detail_ok += 1
            for mk, mv in (det.get("metros") or {}).items():
                metros_map[f"{st}:{mk}"] = mv
            # ritmo educado (todo USA ~51 páginas)
            time.sleep(0.35 if full_usa or len(want) > 15 else 0.25)
        except Exception as e:
            print(f"[aaa] detail {st}: {e}")

    payload = {
        "ts": now,
        "ok": bool(states_map),
        "states": states_map,
        "metros": metros_map,
        "source": "aaa",
        "covers": "all_us_states",
    }
    _mem.clear()
    _mem.update(payload)
    _save_disk(payload)
    return {
        "ok": payload["ok"],
        "mode": "full",
        "states": len(states_map),
        "metros": len(metros_map),
        "details_ok": detail_ok,
        "co_regular": (states_map.get("CO") or {}).get("regular"),
        "covers": "USA — cualquier ZIP → estado AAA (+ metro si hay)",
    }


def aaa_job_status() -> dict:
    return dict(_job)


def start_aaa_refresh_background(
    states: list[str] | None = None,
    full_usa: bool = False,
    table_first: bool = True,
) -> dict:
    """
    Arranca el scrape en un hilo y devuelve al instante (para cron-job.org).
    """
    import threading

    if _job.get("running"):
        return {
            "ok": True,
            "started": False,
            "already_running": True,
            "job": aaa_job_status(),
        }

    def _run():
        _job["running"] = True
        _job["last_start"] = time.time()
        _job["last_error"] = None
        try:
            if table_first:
                fast = refresh_aaa_table_only()
                _job["last_result"] = {"phase": "table", **fast}
            if full_usa or states:
                full = refresh_aaa(states=states, full_usa=full_usa)
                _job["last_result"] = {"phase": "full", **full}
            _job["last_ok"] = True
        except Exception as e:
            _job["last_ok"] = False
            _job["last_error"] = f"{type(e).__name__}: {e}"
            print(f"[aaa] bg job fail: {e}")
        finally:
            _job["running"] = False
            _job["last_end"] = time.time()

    threading.Thread(target=_run, name="aaa-cron", daemon=True).start()
    return {
        "ok": True,
        "started": True,
        "already_running": False,
        "message": "Scrape AAA iniciado en segundo plano",
    }


def get_aaa_averages(
    state: str = "CO",
    city: str | None = None,
) -> dict | None:
    """
    Promedios AAA para cualquier estado USA (y metro si hay match de city).
    Caché disco/mem; si falta el estado, descarga tabla nacional o detalle.
    """
    if not _enabled():
        return None
    st = (state or "CO").upper().strip()
    if st in ("DEFAULT", "US", "USA"):
        st = "CO"  # no hay "US" en AAA table de estados; se usa fallback national abajo
    now = time.time()

    def _load_maps() -> tuple[dict, dict]:
        if _mem.get("ok") and now - float(_mem.get("ts") or 0) < AAA_CACHE_TTL:
            return _mem.get("states") or {}, _mem.get("metros") or {}
        disk = _load_disk()
        if disk.get("ok") and now - float(disk.get("ts") or 0) < AAA_CACHE_TTL:
            _mem.update(disk)
            return disk.get("states") or {}, disk.get("metros") or {}
        return disk.get("states") or {}, disk.get("metros") or {}

    states, metros = _load_maps()

    # si no hay tabla o falta este estado → refresh rápido nacional
    if not states or st not in states:
        try:
            table = fetch_aaa_state_table()
            if table:
                states = {**(states or {}), **table}
                payload = {
                    "ts": now,
                    "ok": True,
                    "states": states,
                    "metros": metros,
                    "source": "aaa",
                }
                _mem.update(payload)
                _save_disk({**_load_disk(), **payload, "metros": metros})
        except Exception as e:
            print(f"[aaa] table on-demand: {e}")

    # metro: si pedimos city y no está en caché, bajar detalle de ese estado
    if city:
        ckey = re.sub(r"\s+", " ", city.lower()).strip()
        has_metro = any(
            k.startswith(f"{st}:")
            and (
                ckey == k.split(":", 1)[-1]
                or ckey in k.split(":", 1)[-1]
                or k.split(":", 1)[-1] in ckey
            )
            for k in metros
        )
        if not has_metro and not any(k.startswith(f"{st}:") for k in metros):
            try:
                det = fetch_aaa_state_detail(st)
                if det.get("state"):
                    states[st] = det["state"]
                for mk, mv in (det.get("metros") or {}).items():
                    metros[f"{st}:{mk}"] = mv
                disk = _load_disk()
                disk["states"] = {**(disk.get("states") or {}), **states}
                disk["metros"] = metros
                disk["ts"] = now
                disk["ok"] = True
                _mem.update(disk)
                _save_disk(disk)
            except Exception as e:
                print(f"[aaa] detail on-demand {st}: {e}")

        # match metro
        best = None
        best_score = 0
        for mk, mv in metros.items():
            if not mk.startswith(f"{st}:"):
                continue
            metro_name = mk.split(":", 1)[-1]
            score = 0
            if ckey == metro_name:
                score = 100
            elif ckey in metro_name:
                score = 80
            elif metro_name in ckey:
                score = 70
            else:
                # tokens: "colorado springs" vs "colorado springs"
                ct = set(ckey.replace("-", " ").split())
                mt = set(metro_name.replace("-", " ").split())
                if ct and mt and ct <= mt or mt <= ct:
                    score = 60
                elif ct & mt:
                    score = 40
            if score > best_score:
                best_score = score
                best = mv
        if best and best_score >= 40:
            return dict(best)

    row = states.get(st)
    if row and row.get("ok") and row.get("regular"):
        return dict(row)
    return None
