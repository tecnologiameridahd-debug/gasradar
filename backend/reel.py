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


def _caption(city: dict, st: dict, price: str, station: str, miles_s: str) -> str:
    tag = city["name"].replace(" ", "")
    price_line = (
        f"Hoy la Regular más barata: {price}\n{station}"
        + (f" · {miles_s}" if miles_s else "")
        if price and price != "—"
        else f"ZIP {city['zip']} — abre y compara Regular cerca de ti."
    )
    return (
        f"⛽ {city['name']}, {st['name_es']}\n\n"
        f"{price_line}\n\n"
        f"Compara en 10 segundos 👇\n"
        f"gasradarapp.com/gas/{city['state']}/{city['slug']}\n\n"
        f"#gasolina #{tag} #{st['code']} #GasRadar #gasprices "
        f"#ahorrar #gasolinabarata #USA"
    )


def build_reel(slug: str | None = None) -> dict:
    """Ciudad al instante. El precio se pide aparte en fill_price()."""
    city = find_city(slug)
    st = STATE_BY_SLUG[city["state"]]
    prev_s, next_s = neighbors(city["slug"])
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
        "price": "—",
        "station": "Buscando precio…",
        "miles": "",
        "address": "",
        "caption": _caption(city, st, "—", "", ""),
        "link": f"https://gasradarapp.com/gas/{city['state']}/{city['slug']}",
        "app_link": f"https://gasradarapp.com/?zip={city['zip']}",
        "prev": prev_s,
        "next": next_s,
        "error": None,
        "cities": [{"slug": c["slug"], "name": c["name"]} for c in CITIES],
    }


def fill_price(slug: str | None = None) -> dict:
    """Precio real con tope de 8s. Si falla, la ciudad igual ya se ve."""
    import concurrent.futures

    from backend.search_core import run_search

    city = find_city(slug)
    st = STATE_BY_SLUG[city["state"]]

    def _search():
        return run_search(
            zip=city["zip"],
            radius_mi=8.0,
            fuel="regular",
            limit=12,
            track=False,
            quick=True,
        )

    cheapest = None
    error = None
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            data = pool.submit(_search).result(timeout=8)
        cheapest = data.get("cheapest") or None
        if not cheapest:
            live = [s for s in (data.get("stations") or []) if s.get("price") is not None]
            live.sort(key=lambda s: float(s["price"]))
            if live:
                s0 = live[0]
                cheapest = {
                    "name": s0.get("name"),
                    "brand": s0.get("brand"),
                    "price": s0.get("price"),
                    "distance_mi": s0.get("distance_mi"),
                    "address": s0.get("address"),
                }
    except Exception as e:
        error = str(e)[:180]

    price = _fmt_price((cheapest or {}).get("price"))
    station = (cheapest or {}).get("name") or (cheapest or {}).get("brand") or ""
    miles = (cheapest or {}).get("distance_mi")
    try:
        miles_s = f"{float(miles):.1f} mi"
    except (TypeError, ValueError):
        miles_s = ""
    if price == "—":
        station = station or "Abre la app para ver el precio"
    return {
        "price": price,
        "station": station,
        "miles": miles_s,
        "address": (cheapest or {}).get("address") or "",
        "caption": _caption(city, st, price, station, miles_s),
        "error": error,
    }
