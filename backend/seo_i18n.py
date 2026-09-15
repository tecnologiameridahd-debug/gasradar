"""Versión en español de home y páginas /gas para Google."""
from __future__ import annotations

import re

SITE = "https://gasradarapp.com"

ES_HOME_TITLE = "Gasolina barata cerca de mí — precios en vivo | GasRadar"
ES_HOME_DESC = (
    "La Regular más barata cerca de ti. GPS o ZIP. "
    "Compara Costco, Murphy, QT y más — precios en vivo."
)


def apply_hreflang(html: str, en_url: str, es_url: str) -> str:
    html = re.sub(
        r'<link rel="alternate" hreflang="en" href="[^"]*"\s*/?>',
        f'<link rel="alternate" hreflang="en" href="{en_url}" />',
        html,
        count=1,
        flags=re.I,
    )
    html = re.sub(
        r'<link rel="alternate" hreflang="es" href="[^"]*"\s*/?>',
        f'<link rel="alternate" hreflang="es" href="{es_url}" />',
        html,
        count=1,
        flags=re.I,
    )
    html = re.sub(
        r'<link rel="alternate" hreflang="x-default" href="[^"]*"\s*/?>',
        f'<link rel="alternate" hreflang="x-default" href="{en_url}" />',
        html,
        count=1,
        flags=re.I,
    )
    return html


def _set_canonical(html: str, url: str) -> str:
    return re.sub(
        r'<link rel="canonical" href="[^"]*"\s*/?>',
        f'<link rel="canonical" href="{url}" />',
        html,
        count=1,
        flags=re.I,
    )


def _set_lang(html: str, lang: str) -> str:
    return re.sub(r'<html\s+lang="[^"]*"', f'<html lang="{lang}"', html, count=1, flags=re.I)


def _set_title_desc(html: str, title: str, desc: str) -> str:
    from backend.seo_snippets import apply_snippet

    # apply_snippet también pisa livePrice; si está vacío, lo deja igual de vacío
    return apply_snippet(html, title, desc, "")


def localize_home_es(html: str) -> str:
    html = _set_lang(html, "es")
    html = _set_canonical(html, f"{SITE}/es")
    html = apply_hreflang(html, f"{SITE}/", f"{SITE}/es")
    html = re.sub(
        r"<title>.*?</title>",
        f"<title>{ES_HOME_TITLE}</title>",
        html,
        count=1,
        flags=re.I | re.S,
    )
    html = re.sub(
        r'(<(?:meta)[^>]*(?:property|name)="(?:og:title|twitter:title)"[^>]*content=")[^"]*(")',
        lambda m: m.group(1) + ES_HOME_TITLE + m.group(2),
        html,
        flags=re.I,
    )
    html = re.sub(
        r'(<(?:meta)[^>]*(?:property|name)="(?:description|og:description|twitter:description)"[^>]*content=")[^"]*(")',
        lambda m: m.group(1) + ES_HOME_DESC + m.group(2),
        html,
        flags=re.I,
    )
    html = html.replace(
        'property="og:url" content="https://gasradarapp.com/"',
        'property="og:url" content="https://gasradarapp.com/es"',
    )
    html = html.replace(
        "<h1>Cheap gas near me in the USA</h1>",
        "<h1>Gasolina barata cerca de mí en EE.UU.</h1>",
    )
    html = html.replace("<h2>Cheap gas by city</h2>", "<h2>Gasolina barata por ciudad</h2>")
    html = re.sub(
        r'href="/gas/',
        'href="/es/gas/',
        html,
    )
    html = html.replace('href="/gas"', 'href="/es/gas"')
    html = html.replace(
        "Cheapest gas near you",
        "La gasolina más barata cerca de ti",
    )
    if "__GASRADAR_FORCE_LANG" not in html:
        html = html.replace(
            "<head>",
            '<head>\n    <script>window.__GASRADAR_FORCE_LANG="es";</script>',
            1,
        )
    return html


def localize_place_es(html: str, en_path: str) -> str:
    """en_path tipo /gas/colorado/denver o /gas o /gas/colorado."""
    if not en_path.startswith("/"):
        en_path = "/" + en_path
    es_path = "/es" + en_path
    en_url = SITE + en_path
    es_url = SITE + es_path
    html = _set_lang(html, "es")
    html = _set_canonical(html, es_url)
    html = apply_hreflang(html, en_url, es_url)
    html = html.replace('id="contentEn">', 'id="contentEn" hidden>')
    html = html.replace('id="contentEs" hidden>', 'id="contentEs">')
    html = html.replace("Cheap gas in ", "Gasolina barata en ")
    html = html.replace("Cheap gas by US city and state", "Gasolina barata por ciudad y estado")
    html = html.replace(" — live prices | GasRadar", " — precios en vivo | GasRadar")
    html = html.replace("today | GasRadar", "hoy | GasRadar")
    if "__GASRADAR_FORCE_LANG" not in html:
        html = html.replace(
            "<head>",
            '<head>\n  <script>window.__GASRADAR_FORCE_LANG="es";</script>',
            1,
        )
    html = html.replace('href="/gas/', 'href="/es/gas/')
    html = html.replace('href="/gas"', 'href="/es/gas"')
    html = html.replace('href="/"', 'href="/es"')
    return html
