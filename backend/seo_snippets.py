"""Títulos/metas con precio real para páginas /gas/{estado}/{ciudad}.

Google lee el HTML inicial. No bloquear el request: si no hay caché,
se sirve el fallback y se calienta el ZIP en background.
Solo se mete $ si el precio es GasBuddy o reporte de usuario.
"""
from __future__ import annotations

import html
import json
import re
import threading

LIVE_SOURCES = {"gasbuddy", "user"}

# Ciudades con impresiones GSC en top 10 y casi 0 clics
SEO_WARM_ZIPS = (
    "28202",  # Charlotte
    "35203",  # Birmingham
    "49503",  # Grand Rapids
    "38103",  # Memphis
    "93721",  # Fresno
    "43215",  # Columbus
    "87102",  # Albuquerque
    "21201",  # Baltimore
    "80202",  # Denver
)

_WARMING: set[str] = set()
_WARM_LOCK = threading.Lock()
_ZIP_RE = re.compile(r'id="livePrice"[^>]*data-zip="(\d{5})"', re.I)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
_H1_RE = re.compile(
    r'class="place-h1">(?:Cheap gas in|Gasolina barata en)\s+([^,<]+),\s*([A-Z]{2})',
    re.I,
)


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _short_brand(station: dict) -> str:
    raw = (station.get("brand") or station.get("name") or "").strip()
    raw = re.sub(r"\s+", " ", raw)
    raw = re.sub(r"\s+#?\d{2,}$", "", raw)
    return raw[:22]


def _live_stations(data: dict) -> list[dict]:
    out: list[dict] = []
    for s in data.get("stations") or []:
        if not isinstance(s, dict):
            continue
        if (s.get("price_source") or "") not in LIVE_SOURCES:
            continue
        try:
            p = float(s.get("price"))
        except (TypeError, ValueError):
            continue
        if not (1.0 < p < 12.0):
            continue
        out.append(s)
    out.sort(key=lambda s: float(s["price"]))
    return out


def _unique_priced(stations: list[dict], n: int = 3) -> list[tuple[str, float]]:
    seen: set[str] = set()
    rows: list[tuple[str, float]] = []
    for s in stations:
        brand = _short_brand(s)
        key = brand.lower() or "?"
        if key in seen:
            continue
        seen.add(key)
        rows.append((brand, float(s["price"])))
        if len(rows) >= n:
            break
    return rows


def _fmt_usd(v: float | None) -> str:
    if v is None:
        return "—"
    try:
        return f"${float(v):.2f}"
    except (TypeError, ValueError):
        return "—"


def _aaa_cached(state_code: str, city: str) -> dict:
    try:
        from backend.aaa_scraper import get_aaa_averages

        row = get_aaa_averages(state_code, city=city) or {}
        return row if isinstance(row, dict) else {}
    except Exception:
        return {}


def _top_stations(stations: list[dict], n: int = 5) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for s in stations:
        brand = _short_brand(s)
        key = f"{brand.lower()}|{(s.get('address') or '')[:24].lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= n:
            break
    return out


def format_city_snippet(
    *,
    city: str,
    state_code: str,
    stations: list[dict],
    lang: str = "en",
) -> tuple[str, str, str, str] | None:
    """(title, description, live_html, h1) o None si no hay precio vivo."""
    live_rows = _live_stations({"stations": stations}) if stations else []
    if not live_rows:
        live_rows = stations
    priced = _unique_priced(live_rows, 8)
    if not priced:
        return None
    brand0, price0 = priced[0]
    p0 = f"${price0:.2f}"
    regs = [float(s["price"]) for s in live_rows if s.get("price") is not None]
    avg_reg = sum(regs) / len(regs) if regs else price0
    min_reg = min(regs) if regs else price0
    aaa = _aaa_cached(state_code, city)
    es = lang == "es"
    if es:
        title = f"Precio de la gasolina en {city}, {state_code} hoy | GasRadar"
        desc = (
            f"Regular desde {p0} en {city}, {state_code}. "
            f"Las estaciones más baratas ahora: Regular, Premium y Diesel en vivo."
        )
        h1 = f"Precios de gasolina en {city}, {state_code}"
        updated = "Actualizado el: "
        th_fuel, th_avg, th_min = "Tipo de combustible", "Precio promedio", "El más barato"
        h2 = f"Las 5 gasolineras más baratas en {city}"
        ago = "en vivo"
    else:
        title = f"Gas prices in {city}, {state_code} today | GasRadar"
        desc = (
            f"Regular from {p0} in {city}, {state_code}. "
            f"Cheapest stations now — Regular, Premium and Diesel, live."
        )
        h1 = f"Gas prices in {city}, {state_code}"
        updated = "Updated: "
        th_fuel, th_avg, th_min = "Fuel", "Average", "Cheapest"
        h2 = f"Cheapest 5 gas stations in {city}"
        ago = "live"
    if len(desc) > 160:
        desc = desc[:157].rstrip() + "…"
    from datetime import date

    today = date.today().isoformat()
    prem_avg = aaa.get("premium")
    die_avg = aaa.get("diesel")
    table = (
        f'<p class="live-updated">{_esc(updated)}<time datetime="{today}">{today}</time></p>'
        f'<table class="fuel-table">'
        f"<thead><tr><th>{_esc(th_fuel)}</th><th>{_esc(th_avg)}</th><th>{_esc(th_min)}</th></tr></thead>"
        f"<tbody>"
        f"<tr><td>Regular</td><td>{_fmt_usd(avg_reg)}</td><td>{_fmt_usd(min_reg)}</td></tr>"
        f"<tr><td>Premium</td><td>{_fmt_usd(prem_avg)}</td><td>—</td></tr>"
        f"<tr><td>Diesel</td><td>{_fmt_usd(die_avg)}</td><td>—</td></tr>"
        f"</tbody></table>"
    )
    lis = []
    for s in _top_stations(live_rows, 5):
        name = _esc(_short_brand(s) or s.get("name") or "Station")
        addr = _esc((s.get("address") or "").strip())
        price = _fmt_usd(s.get("price"))
        loc = f" — {addr}" if addr else ""
        lis.append(
            f"<li><strong>{name}</strong>{loc} | <strong>Regular: {price}</strong> "
            f'<span class="ago">{_esc(ago)}</span></li>'
        )
    live = (
        f"<p>Regular {p0} {_esc(brand0)}</p>"
        f"{table}"
        f"<h2>{_esc(h2)}</h2>"
        f'<ol class="live-stations">{"".join(lis)}</ol>'
    )
    return title[:70], desc, live, h1


def _parse_place(html_text: str) -> tuple[str, str, str]:
    """city, state_code, zip."""
    zip_code = ""
    mzip = _ZIP_RE.search(html_text)
    if mzip:
        zip_code = mzip.group(1)
    city, code = "", ""
    mh = _H1_RE.search(html_text)
    if mh:
        city, code = mh.group(1).strip(), mh.group(2).strip()
    return city, code, zip_code


def apply_snippet(
    html_text: str, title: str, desc: str, live_html: str, h1: str = ""
) -> str:
    html_text = _TITLE_RE.sub(lambda _m: f"<title>{_esc(title)}</title>", html_text, count=1)
    html_text = re.sub(
        r'(<(?:meta)[^>]*(?:property|name)="(?:og:title|twitter:title)"[^>]*content=")[^"]*(")',
        lambda m: m.group(1) + _esc(title) + m.group(2),
        html_text,
        flags=re.I,
    )
    html_text = re.sub(
        r'(<(?:meta)[^>]*(?:property|name)="(?:description|og:description|twitter:description)"[^>]*content=")[^"]*(")',
        lambda m: m.group(1) + _esc(desc) + m.group(2),
        html_text,
        flags=re.I,
    )
    # Primer name/description del JSON-LD WebPage
    html_text = re.sub(
        r'("name":\s*")(?:\\.|[^"\\])*(")',
        lambda m: m.group(1) + json.dumps(title, ensure_ascii=False)[1:-1] + m.group(2),
        html_text,
        count=1,
    )
    html_text = re.sub(
        r'("description":\s*")(?:\\.|[^"\\])*(")',
        lambda m: m.group(1) + json.dumps(desc, ensure_ascii=False)[1:-1] + m.group(2),
        html_text,
        count=1,
    )
    html_text = re.sub(
        r'(<(?:p|div) class="live-box card" id="livePrice"[^>]*>)(.*?)(</(?:p|div)>)',
        lambda m: m.group(1) + live_html + m.group(3),
        html_text,
        count=1,
        flags=re.I | re.S,
    )
    if h1:
        html_text = re.sub(
            r'(<h1 class="place-h1">)(.*?)(</h1>)',
            lambda m: m.group(1) + _esc(h1) + m.group(3),
            html_text,
            count=1,
            flags=re.I | re.S,
        )
    return html_text


def warm_zip(zip_code: str) -> None:
    z = (zip_code or "").strip()[:5]
    if len(z) != 5:
        return
    with _WARM_LOCK:
        if z in _WARMING:
            return
        _WARMING.add(z)

    def _run() -> None:
        try:
            from backend.search_core import run_search

            run_search(
                zip=z,
                radius_mi=8.0,
                fuel="regular",
                limit=12,
                track=False,
                quick=False,
            )
        except Exception as e:
            print(f"[seo] warm {z} fail: {type(e).__name__}: {e}")
        finally:
            with _WARM_LOCK:
                _WARMING.discard(z)

    threading.Thread(target=_run, name=f"seo-warm-{z}", daemon=True).start()


def inject_city_seo(html_text: str, lang: str = "en") -> tuple[str, bool]:
    """Devuelve (html, injected). Nunca lanza; si falla, el HTML original."""
    try:
        city, code, zip_code = _parse_place(html_text)
        if not zip_code:
            return html_text, False
        from backend.search_core import peek_cached_search

        data = peek_cached_search(zip_code, fuel="regular")
        if not data:
            warm_zip(zip_code)
            return html_text, False
        stations = _live_stations(data)
        if not stations:
            cheapest = data.get("cheapest") or {}
            if cheapest.get("source") in LIVE_SOURCES and cheapest.get("price"):
                stations = [
                    {
                        "brand": cheapest.get("brand"),
                        "name": cheapest.get("name"),
                        "price": cheapest.get("price"),
                        "price_source": cheapest.get("source"),
                    }
                ]
        if not city:
            city = "This city"
        if not code:
            code = "US"
        snippet = format_city_snippet(
            city=city, state_code=code, stations=stations, lang=lang
        )
        if not snippet:
            return html_text, False
        title, desc, live, h1 = snippet
        return apply_snippet(html_text, title, desc, live, h1=h1), True
    except Exception as e:
        print(f"[seo] inject fail: {type(e).__name__}: {e}")
        return html_text, False


def warm_seo_cities() -> None:
    """Calienta ZIPs de ciudades que ya rankean. Uno por uno."""

    def _run() -> None:
        import time

        for i, z in enumerate(SEO_WARM_ZIPS):
            if i:
                time.sleep(8)
            warm_zip(z)

    threading.Thread(target=_run, name="seo-warm-cities", daemon=True).start()
