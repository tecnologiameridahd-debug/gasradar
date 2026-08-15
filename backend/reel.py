"""Reel diario: una ciudad, precio real, texto listo para Instagram."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))

from _places_data import CITIES, STATES  # noqa: E402

STATE_BY_SLUG = {s["slug"]: s for s in STATES}


def city_of_day(day: date | None = None) -> dict:
    d = day or date.today()
    return CITIES[d.toordinal() % len(CITIES)]


def find_city(slug: str | None) -> dict:
    if slug:
        sl = slug.strip().lower()
        for c in CITIES:
            if c["slug"] == sl:
                return c
    return city_of_day()


def neighbors(slug: str) -> tuple[str, str]:
    slugs = [c["slug"] for c in CITIES]
    i = slugs.index(slug) if slug in slugs else 0
    prev_s = slugs[(i - 1) % len(slugs)]
    next_s = slugs[(i + 1) % len(slugs)]
    return prev_s, next_s


def _fmt_price(val) -> str:
    try:
        return f"${float(val):.2f}"
    except (TypeError, ValueError):
        return "—"


def _captions(city: dict, st: dict, price: str, station: str, miles_s: str) -> tuple[str, str]:
    tag = city["name"].replace(" ", "")
    extra = f" · {miles_s}" if miles_s else ""
    if price and price != "—":
        line_es = f"Hoy la Regular más barata: {price}\n{station}{extra}"
        line_en = f"Cheapest Regular today: {price}\n{station}{extra}"
    else:
        line_es = f"ZIP {city['zip']} — abre y compara Regular cerca de ti."
        line_en = f"ZIP {city['zip']} — open and compare Regular near you."
    link = f"gasradarapp.com/gas/{city['state']}/{city['slug']}"
    es = (
        f"⛽ {city['name']}, {st['name_es']}\n\n"
        f"{line_es}\n\n"
        f"Compara en 10 segundos 👇\n"
        f"{link}\n\n"
        f"#gasolina #{tag} #{st['code']} #GasRadar #gasprices "
        f"#ahorrar #gasolinabarata #USA"
    )
    en = (
        f"⛽ {city['name']}, {st['name_en']}\n\n"
        f"{line_en}\n\n"
        f"Compare in 10 seconds 👇\n"
        f"{link}\n\n"
        f"#gas #{tag} #{st['code']} #GasRadar #gasprices "
        f"#cheapgas #savemoney #USA"
    )
    return es, en


_REEL_CACHE: dict[str, tuple[float, dict]] = {}
_REEL_TTL = 20 * 60


def _cache_get(zip_code: str) -> dict | None:
    import time

    hit = _REEL_CACHE.get(zip_code)
    if not hit:
        return None
    ts, data = hit
    if time.time() - ts > _REEL_TTL:
        _REEL_CACHE.pop(zip_code, None)
        return None
    return data


def _cache_put(zip_code: str, data: dict) -> None:
    import time

    _REEL_CACHE[zip_code] = (time.time(), data)


def _from_search(data: dict | None) -> dict | None:
    if not data:
        return None
    cheapest = data.get("cheapest")
    if not cheapest:
        live = [s for s in (data.get("stations") or []) if s.get("price") is not None]
        live.sort(key=lambda s: float(s["price"]))
        if not live:
            return None
        s0 = live[0]
        cheapest = {
            "name": s0.get("name"),
            "brand": s0.get("brand"),
            "price": s0.get("price"),
            "distance_mi": s0.get("distance_mi"),
            "address": s0.get("address"),
        }
    price = _fmt_price(cheapest.get("price"))
    if price == "—":
        return None
    station = cheapest.get("name") or cheapest.get("brand") or ""
    miles = cheapest.get("distance_mi")
    try:
        miles_s = f"{float(miles):.1f} mi"
    except (TypeError, ValueError):
        miles_s = ""
    return {
        "price": price,
        "station": station,
        "station_en": station,
        "miles": miles_s,
        "address": cheapest.get("address") or "",
        "live": True,
    }


def _pack_price(city: dict, st: dict, info: dict | None) -> dict:
    if not info:
        cap_es, cap_en = _captions(city, st, "—", "", "")
        return {
            "price": "—",
            "station": "Buscando precio…",
            "station_en": "Finding price…",
            "miles": "",
            "address": "",
            "live": False,
            "caption": cap_es,
            "caption_es": cap_es,
            "caption_en": cap_en,
        }
    cap_es, cap_en = _captions(city, st, info["price"], info["station"], info.get("miles") or "")
    return {
        **info,
        "caption": cap_es,
        "caption_es": cap_es,
        "caption_en": cap_en,
    }


def build_reel(slug: str | None = None) -> dict:
    """Ciudad al instante. El precio de estación se pide en fill_price()."""
    from backend.search_core import peek_cached_search

    city = find_city(slug)
    st = STATE_BY_SLUG[city["state"]]
    prev_s, next_s = neighbors(city["slug"])
    info = _cache_get(city["zip"]) or _from_search(peek_cached_search(city["zip"]))
    packed = _pack_price(city, st, info)
    return {
        "today": date.today().isoformat(),
        "is_today": city["slug"] == city_of_day()["slug"],
        "city": city["name"],
        "slug": city["slug"],
        "state": st["name_es"],
        "state_en": st["name_en"],
        "state_slug": city["state"],
        "code": st["code"],
        "zip": city["zip"],
        **packed,
        "link": f"https://gasradarapp.com/gas/{city['state']}/{city['slug']}",
        "app_link": f"https://gasradarapp.com/?zip={city['zip']}",
        "prev": prev_s,
        "next": next_s,
        "error": None,
        "cities": [{"slug": c["slug"], "name": c["name"]} for c in CITIES],
    }


def fill_price(slug: str | None = None) -> dict:
    """Precio real de estación (GasBuddy). Espera hasta 20s."""
    import concurrent.futures

    from backend.search_core import peek_cached_search, run_search

    city = find_city(slug)
    st = STATE_BY_SLUG[city["state"]]

    cached = _cache_get(city["zip"])
    if cached and cached.get("live"):
        return _pack_price(city, st, cached)

    peeked = _from_search(peek_cached_search(city["zip"]))
    if peeked:
        _cache_put(city["zip"], peeked)
        return _pack_price(city, st, peeked)

    def _search():
        return run_search(
            zip=city["zip"],
            radius_mi=8.0,
            fuel="regular",
            limit=16,
            track=False,
            quick=False,
        )

    error = None
    info = None
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            data = pool.submit(_search).result(timeout=20)
        info = _from_search(data)
    except Exception as e:
        error = str(e)[:180]

    if info:
        _cache_put(city["zip"], info)
        packed = _pack_price(city, st, info)
    else:
        packed = _pack_price(city, st, None)
        packed["station"] = "Abre la app para ver el precio"
        packed["station_en"] = "Open the app to see the price"
    packed["error"] = error
    return packed
