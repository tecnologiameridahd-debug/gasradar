# -*- coding: utf-8 -*-
"""Generate /gas state + city SEO pages. Run: python frontend/_gen_places.py"""
from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path

from _places_data import BAND_EN, BAND_ES, CITIES, STATES

ROOT = Path(__file__).resolve().parent
GAS = ROOT / "gas"
SITE = "https://gasradarapp.com"
CSS_V = "0.9.60"
TODAY = "2026-08-15"

STATE_BY_SLUG = {s["slug"]: s for s in STATES}
CITIES_BY_STATE: dict[str, list[dict]] = defaultdict(list)
for c in CITIES:
    CITIES_BY_STATE[c["state"]].append(c)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def page_shell(
    *,
    title: str,
    description: str,
    canonical: str,
    content_es: str,
    content_en: str,
    extra_ld: dict | None = None,
    live_zip: str = "",
) -> str:
    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical,
        "inLanguage": ["es-US", "en-US"],
        "isPartOf": {"@type": "WebSite", "name": "GasRadar", "url": f"{SITE}/"},
        "about": {"@type": "Thing", "name": "US gasoline prices"},
    }
    if extra_ld:
        ld.update(extra_ld)
    ld_json = json.dumps(ld, ensure_ascii=False, indent=2)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="theme-color" content="#0b1220" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <meta name="robots" content="index, follow" />
  <meta name="geo.region" content="US" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="GasRadar" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{SITE}/static/logo-512.png?v=0.5.0" />
  <meta property="og:locale" content="es_US" />
  <meta property="og:locale:alternate" content="en_US" />
  <link rel="icon" href="/static/favicon-32.png?v=0.2.9" type="image/png" />
  <link rel="stylesheet" href="/static/styles.css?v={CSS_V}" />
  <script type="application/ld+json">
{ld_json}
  </script>
</head>
<body>
  <div class="app privacy-page blog-page">
    <header class="top">
      <div class="brand">
        <a href="/" class="logo-link" title="GasRadar">
          <img class="logo" src="/static/logo.svg?v=0.2.9" width="48" height="48" alt="GasRadar" />
        </a>
        <div class="brand-text">
          <h1><span class="brand-gas">Gas</span><span class="brand-radar">Radar</span></h1>
          <p class="subtitle" id="blogSub">Gasolina</p>
        </div>
      </div>
      <div class="lang-switch" role="group" aria-label="Language">
        <button type="button" class="lang-btn active" id="btnLangEs" data-lang="es">ES</button>
        <button type="button" class="lang-btn" id="btnLangEn" data-lang="en">EN</button>
      </div>
    </header>

    <nav class="blog-nav card" aria-label="Places">
      <a href="/gas" id="navPlaces">Ciudades y estados</a>
      <span class="footer-sep">·</span>
      <a href="/">App</a>
      <span class="footer-sep">·</span>
      <a href="/blog">Blog</a>
    </nav>
    {f'<p class="live-box card" id="livePrice" data-zip="{live_zip}" style="padding:12px 16px;margin:0 0 12px"></p>' if live_zip else ""}

    <section class="card privacy-card blog-card" id="contentEs">
      {content_es}
    </section>
    <section class="card privacy-card blog-card" id="contentEn" hidden>
      {content_en}
    </section>

    <footer class="site-footer">
      <div><strong>GasRadar</strong> · USA · 50 states + D.C.</div>
      <p class="footer-legal">© 2026 GasRadar LLC · gasradarapp.com</p>
      <div class="footer-links">
        <a href="/gas">Ciudades</a>
        <span class="footer-sep">·</span>
        <a href="/blog">Blog</a>
        <span class="footer-sep">·</span>
        <a href="/privacy">Privacidad</a>
        <span class="footer-sep">·</span>
        <a href="/terminos">Términos</a>
        <span class="footer-sep">·</span>
        <a href="/reglas">Reglas</a>
      </div>
    </footer>
  </div>
  <script>
    const LANG_KEY = "gasradar_lang";
    function loadLang() {{
      try {{
        const s = localStorage.getItem(LANG_KEY);
        if (s === "en" || s === "es") return s;
      }} catch (_) {{}}
      return (navigator.language || "es").toLowerCase().startsWith("en") ? "en" : "es";
    }}
    function setLang(lang) {{
      try {{ localStorage.setItem(LANG_KEY, lang); }} catch (_) {{}}
      document.documentElement.lang = lang;
      document.getElementById("contentEs").hidden = lang !== "es";
      document.getElementById("contentEn").hidden = lang !== "en";
      document.getElementById("btnLangEs").classList.toggle("active", lang === "es");
      document.getElementById("btnLangEn").classList.toggle("active", lang === "en");
      document.getElementById("blogSub").textContent = lang === "en" ? "Gas prices" : "Gasolina";
      const nav = document.getElementById("navPlaces");
      if (nav) nav.textContent = lang === "en" ? "Cities and states" : "Ciudades y estados";
    }}
    document.getElementById("btnLangEs").onclick = () => setLang("es");
    document.getElementById("btnLangEn").onclick = () => setLang("en");
    setLang(loadLang());
    var box = document.getElementById("livePrice");
    if (box && box.dataset.zip) {{
      var zip = box.dataset.zip;
      var lang = document.documentElement.lang || "es";
      box.hidden = false;
      box.textContent = lang === "en" ? "Checking live price…" : "Buscando precio en vivo…";
      fetch("/api/search?zip=" + encodeURIComponent(zip) + "&radius_mi=8&limit=12")
        .then(function (r) {{ return r.json(); }})
        .then(function (d) {{
          var c = d && d.cheapest;
          if (c && c.price != null) {{
            var p = "$" + Number(c.price).toFixed(2);
            var name = c.name || c.brand || "";
            box.innerHTML = lang === "en"
              ? ("Cheapest Regular now: <strong>" + p + "</strong> " + name)
              : ("Regular más barata ahora: <strong>" + p + "</strong> " + name);
          }} else {{
            box.textContent = lang === "en" ? "Open the app to compare." : "Abre la app para comparar.";
          }}
        }})
        .catch(function () {{
          box.textContent = lang === "en" ? "Open the app to compare." : "Abre la app para comparar.";
        }});
    }}
  </script>
</body>
</html>
"""


def city_links(state_slug: str, lang: str) -> str:
    items = CITIES_BY_STATE.get(state_slug, [])
    if not items:
        return ""
    lis = []
    for c in items:
        label = c["name"]
        lis.append(f'<li><a href="/gas/{state_slug}/{c["slug"]}">{esc(label)}</a> · ZIP {c["zip"]}</li>')
    title = "Ciudades" if lang == "es" else "Cities"
    return f"<h3>{title}</h3><ul class='place-list'>{''.join(lis)}</ul>"


def neighbor_links(state: dict, lang: str) -> str:
    slugs = state.get("neighbors") or []
    if not slugs:
        return ""
    lis = []
    for sl in slugs:
        st = STATE_BY_SLUG.get(sl)
        if not st:
            continue
        name = st["name_es"] if lang == "es" else st["name_en"]
        lis.append(f'<li><a href="/gas/{sl}">{esc(name)}</a></li>')
    if not lis:
        return ""
    title = "Estados cerca" if lang == "es" else "Nearby states"
    return f"<h3>{title}</h3><ul class='place-list'>{''.join(lis)}</ul>"


def write(path: Path, html_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8", newline="\n")


def build_index() -> None:
    cards_es, cards_en = [], []
    for st in STATES:
        n = len(CITIES_BY_STATE.get(st["slug"], []))
        extra_es = f" · {n} ciudades" if n else ""
        extra_en = f" · {n} cities" if n else ""
        cards_es.append(
            f'<a class="place-chip" href="/gas/{st["slug"]}"><strong>{esc(st["name_es"])}</strong>'
            f'<span>{st["code"]}{extra_es}</span></a>'
        )
        cards_en.append(
            f'<a class="place-chip" href="/gas/{st["slug"]}"><strong>{esc(st["name_en"])}</strong>'
            f'<span>{st["code"]}{extra_en}</span></a>'
        )
    feat_es, feat_en = [], []
    featured = [
        "houston", "dallas", "el-paso", "miami", "denver", "colorado-springs",
        "los-angeles", "chicago", "new-york", "phoenix", "las-vegas", "reno",
        "san-antonio", "atlanta", "orlando",
    ]
    by_slug = {c["slug"]: c for c in CITIES}
    for sl in featured:
        c = by_slug[sl]
        feat_es.append(
            f'<li><a href="/gas/{c["state"]}/{c["slug"]}">{esc(c["name"])}</a> · {STATE_BY_SLUG[c["state"]]["name_es"]}</li>'
        )
        feat_en.append(
            f'<li><a href="/gas/{c["state"]}/{c["slug"]}">{esc(c["name"])}</a> · {STATE_BY_SLUG[c["state"]]["name_en"]}</li>'
        )
    es = f"""
    <h2>Gasolina barata por ciudad y estado</h2>
    <p class="privacy-meta">{len(CITIES)} ciudades · 50 estados + D.C.</p>
    <p>Abre tu ciudad, usa el ZIP y compara en GasRadar. El precio cambia por barrio: no uses solo el nombre del estado.</p>
    <h3>Ciudades más buscadas</h3>
    <ul class="place-list">{''.join(feat_es)}</ul>
    <h3>Los 50 estados + D.C.</h3>
    <div class="place-grid">{''.join(cards_es)}</div>
    <p class="blog-cta"><a class="btn-blog" href="/">Abrir GasRadar y buscar cerca</a></p>
    """
    en = f"""
    <h2>Cheap gas by city and state</h2>
    <p class="privacy-meta">{len(CITIES)} cities · 50 states + D.C.</p>
    <p>Open your city, use the ZIP, and compare in GasRadar. Price changes by neighborhood — don’t search the state name alone.</p>
    <h3>Most-searched cities</h3>
    <ul class="place-list">{''.join(feat_en)}</ul>
    <h3>All 50 states + D.C.</h3>
    <div class="place-grid">{''.join(cards_en)}</div>
    <p class="blog-cta"><a class="btn-blog" href="/">Open GasRadar and search nearby</a></p>
    """
    html_text = page_shell(
        title="Gasolina barata por ciudad y estado | GasRadar",
        description="Precios de gasolina en 50 estados + D.C. y las principales ciudades de EE.UU. Compara por ZIP con GasRadar.",
        canonical=f"{SITE}/gas",
        content_es=es,
        content_en=en,
    )
    write(GAS / "index.html", html_text)


def build_states() -> None:
    for st in STATES:
        cities_es = city_links(st["slug"], "es")
        cities_en = city_links(st["slug"], "en")
        band_es = BAND_ES[st["band"]]
        band_en = BAND_EN[st["band"]]
        first_zip = (CITIES_BY_STATE.get(st["slug"]) or [{"zip": ""}])[0]["zip"]
        zip_cta = f'/?zip={first_zip}' if first_zip else "/"
        es = f"""
        <p class="privacy-meta"><a href="/gas">Ciudades y estados</a> · {esc(st["code"])}</p>
        <h2>Gasolina en {esc(st["name_es"])}</h2>
        <p>{esc(st["name_es"])} suele estar <strong>{band_es}</strong>. {esc(st["note_es"])}</p>
        <p>Marcas que suelen competir aquí: {esc(st["brands"])}. Abre GasRadar con un ZIP de la ciudad y compara Regular, Premium y diésel en el momento.</p>
        {cities_es}
        <p class="blog-cta"><a class="btn-blog" href="{zip_cta}">Ver precios cerca en {esc(st["name_es"])}</a></p>
        {neighbor_links(st, "es")}
        """
        en = f"""
        <p class="privacy-meta"><a href="/gas">Cities and states</a> · {esc(st["code"])}</p>
        <h2>Gas prices in {esc(st["name_en"])}</h2>
        <p>{esc(st["name_en"])} is usually <strong>{band_en}</strong>. {esc(st["note_en"])}</p>
        <p>Brands that often compete here: {esc(st["brands"])}. Open GasRadar with a city ZIP and compare Regular, Premium, and diesel right now.</p>
        {cities_en}
        <p class="blog-cta"><a class="btn-blog" href="{zip_cta}">See prices near you in {esc(st["name_en"])}</a></p>
        {neighbor_links(st, "en")}
        """
        html_text = page_shell(
            title=f"Gasolina en {st['name_es']} ({st['code']}) | GasRadar",
            description=f"Precios de gasolina en {st['name_es']}. {st['note_es'][:140]}",
            canonical=f"{SITE}/gas/{st['slug']}",
            content_es=es,
            content_en=en,
        )
        write(GAS / st["slug"] / "index.html", html_text)


def build_cities() -> None:
    for c in CITIES:
        st = STATE_BY_SLUG[c["state"]]
        others = [x for x in CITIES_BY_STATE[c["state"]] if x["slug"] != c["slug"]]
        other_es = "".join(
            f'<li><a href="/gas/{c["state"]}/{x["slug"]}">{esc(x["name"])}</a></li>' for x in others
        )
        other_en = other_es
        more_es = f"<h3>Otras ciudades en {esc(st['name_es'])}</h3><ul class='place-list'>{other_es}</ul>" if others else ""
        more_en = f"<h3>Other cities in {esc(st['name_en'])}</h3><ul class='place-list'>{other_en}</ul>" if others else ""
        es = f"""
        <p class="privacy-meta"><a href="/gas">Ciudades</a> · <a href="/gas/{c["state"]}">{esc(st["name_es"])}</a> · ZIP {c["zip"]}</p>
        <h2>Gasolina barata en {esc(c["name"])}, {esc(st["name_es"])}</h2>
        <p>{esc(c["tip_es"])}</p>
        <p>Cerca: {esc(c["nearby"])}. En {esc(st["name_es"])} el precio suele estar {BAND_ES[st["band"]]}. {esc(st["note_es"])}</p>
        <p>Abre GasRadar con el ZIP <strong>{c["zip"]}</strong> y compara estaciones a 3–15 millas. El nombre de la ciudad no basta: el barrio cambia el precio.</p>
        <p class="blog-cta"><a class="btn-blog" href="/?zip={c["zip"]}">Ver gasolina cerca de {esc(c["name"])} ({c["zip"]})</a></p>
        {more_es}
        <p><a href="/gas/{c["state"]}">Toda {esc(st["name_es"])}</a></p>
        """
        en = f"""
        <p class="privacy-meta"><a href="/gas">Cities</a> · <a href="/gas/{c["state"]}">{esc(st["name_en"])}</a> · ZIP {c["zip"]}</p>
        <h2>Cheap gas in {esc(c["name"])}, {esc(st["name_en"])}</h2>
        <p>{esc(c["tip_en"])}</p>
        <p>Nearby: {esc(c["nearby"])}. In {esc(st["name_en"])} prices are usually {BAND_EN[st["band"]]}. {esc(st["note_en"])}</p>
        <p>Open GasRadar with ZIP <strong>{c["zip"]}</strong> and compare stations within 3–15 miles. The city name isn’t enough — the neighborhood changes the price.</p>
        <p class="blog-cta"><a class="btn-blog" href="/?zip={c["zip"]}">See gas near {esc(c["name"])} ({c["zip"]})</a></p>
        {more_en}
        <p><a href="/gas/{c["state"]}">All of {esc(st["name_en"])}</a></p>
        """
        html_text = page_shell(
            title=f"Gasolina barata en {c['name']}, {st['name_es']} | GasRadar",
            description=f"Gasolina en {c['name']}, {st['name_es']}. ZIP {c['zip']}. {c['tip_es'][:120]}",
            canonical=f"{SITE}/gas/{c['state']}/{c['slug']}",
            content_es=es,
            content_en=en,
            live_zip=c["zip"],
        )
        write(GAS / c["state"] / f"{c['slug']}.html", html_text)


def collect_urls() -> list[tuple[str, str]]:
    urls = [
        ("/", "2026-08-18"),
        ("/download", "2026-08-18"),
        ("/dmca", "2026-08-18"),
        ("/privacy", "2026-08-01"),
        ("/blog", "2026-08-03"),
        ("/terminos", TODAY),
        ("/reglas", TODAY),
        ("/gas", TODAY),
    ]
    try:
        from _gen_blog import POSTS
        for p in POSTS:
            urls.append((f"/blog/{p['slug']}", p["date"]))
    except Exception:
        pass
    for st in STATES:
        urls.append((f"/gas/{st['slug']}", TODAY))
    for c in CITIES:
        urls.append((f"/gas/{c['state']}/{c['slug']}", TODAY))
    return urls


def build_sitemap() -> None:
    urls = collect_urls()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{SITE}{loc}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("wrote sitemap.xml", len(urls), "urls")


if __name__ == "__main__":
    build_index()
    build_states()
    build_cities()
    build_sitemap()
    print("done", len(STATES), "states +", len(CITIES), "cities")
