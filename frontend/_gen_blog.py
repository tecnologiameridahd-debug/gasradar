# -*- coding: utf-8 -*-
"""Generate GasRadar SEO blog pages (USA-wide). Run: python frontend/_gen_blog.py"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLOG = ROOT / "blog"
BLOG.mkdir(exist_ok=True)

CSS_V = "0.9.40"
SITE = "https://gasradarapp.com"

POSTS = [
    {
        "slug": "cheapest-gas-usa-guide",
        "date": "2026-08-03",
        "title_es": "Cómo encontrar la gasolina más barata en EE.UU. (guía 2026)",
        "title_en": "How to find the cheapest gas in the USA (2026 guide)",
        "desc_es": "Guía práctica para ahorrar en gasolina en todo Estados Unidos: GPS, ZIP, horarios, marcas y GasRadar.",
        "desc_en": "Practical guide to save on gas across the United States: GPS, ZIP, timing, brands, and GasRadar.",
        "body_es": """
        <p>El precio de la gasolina cambia por <strong>estado, ciudad, barrio e incluso por la hora del día</strong>. No es lo mismo llenar en California que en Texas, ni en el centro de Manhattan que en un suburbio de Dallas. Esta guía es para <strong>todo EE.UU.</strong>, no solo una ciudad.</p>
        <h3>1. Empieza por tu ubicación real</h3>
        <p>Usa el <strong>GPS</strong> o un <strong>ZIP de 5 dígitos</strong> en <a href="/">GasRadar</a>. Así ves estaciones cercanas y un promedio de referencia del estado (AAA / EIA). Un ZIP correcto vale más que adivinar la ciudad.</p>
        <h3>2. Compara Regular, Midgrade, Premium y Diésel</h3>
        <p>La mayoría de autos de uso diario van bien con <strong>Regular</strong>, salvo que el manual pida octanaje alto. Pagar Premium “por costumbre” suele ser dinero tirado. El diésel tiene su propia curva de precios: compáralo aparte.</p>
        <h3>3. Mira el radio (3–15 millas)</h3>
        <p>A veces la más barata está a 8–12 millas. Si el ahorro por galón es grande y vas a llenar el tanque, puede valer la pena. Si solo echas $15, no gastes más en gasolina yendo lejos.</p>
        <h3>4. Evita peajes y centros turísticos cuando puedas</h3>
        <p>Aeropuertos, downtown y zonas turísticas suelen ser más caros. Carreteras interestatales con truck stops a veces compiten mejor, sobre todo en el Medio Oeste y el Sur.</p>
        <h3>5. Reporta el precio que viste</h3>
        <p>En GasRadar puedes <strong>reportar el precio de la bomba</strong>. Eso ayuda a otros conductores en tu zona y mejora la precisión más allá de promedios estatales.</p>
        <h3>6. Combina con alertas</h3>
        <p>El bot de Telegram <a href="https://t.me/GasRadar_bot" rel="noopener">@GasRadar_bot</a> y el <a href="https://www.whatsapp.com/channel/0029VbDQSOH42DcdzMZQb241" rel="noopener">canal de WhatsApp</a> te mantienen al tanto. Configura ZIP + tope de precio si usas el bot.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Abrir GasRadar y buscar cerca de ti</a></p>
        """,
        "body_en": """
        <p>Gas prices change by <strong>state, city, neighborhood, and even time of day</strong>. Filling up in California is not the same as Texas, and downtown Manhattan is not a Dallas suburb. This guide is for the <strong>entire USA</strong>, not one city only.</p>
        <h3>1. Start with your real location</h3>
        <p>Use <strong>GPS</strong> or a <strong>5-digit ZIP</strong> in <a href="/">GasRadar</a>. You’ll see nearby stations plus a state reference average (AAA / EIA). A correct ZIP beats guessing the city name.</p>
        <h3>2. Compare Regular, Midgrade, Premium, and Diesel</h3>
        <p>Most daily drivers are fine on <strong>Regular</strong> unless the manual requires higher octane. Paying for Premium “out of habit” often wastes money. Diesel has its own price curve—compare it separately.</p>
        <h3>3. Check radius (3–15 miles)</h3>
        <p>Sometimes the cheapest station is 8–12 miles away. If you’re filling a full tank and the per-gallon gap is big, it can be worth it. For a $15 top-off, don’t burn the savings driving farther.</p>
        <h3>4. Avoid airports and tourist corridors when you can</h3>
        <p>Airports, downtown cores, and tourist strips are often pricier. Interstate truck stops can be more competitive, especially in the Midwest and South.</p>
        <h3>5. Report the pump price you saw</h3>
        <p>In GasRadar you can <strong>report the pump price</strong>. That helps other drivers nearby and improves accuracy beyond state averages.</p>
        <h3>6. Pair with alerts</h3>
        <p>Telegram bot <a href="https://t.me/GasRadar_bot" rel="noopener">@GasRadar_bot</a> and our <a href="https://www.whatsapp.com/channel/0029VbDQSOH42DcdzMZQb241" rel="noopener">WhatsApp channel</a> keep you updated. Set ZIP + max price on the bot if you use alerts.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Open GasRadar and search near you</a></p>
        """,
    },
    {
        "slug": "gas-prices-by-state-usa",
        "date": "2026-08-03",
        "title_es": "Precios de gasolina por estado en EE.UU.: por qué varían tanto",
        "title_en": "US gas prices by state: why they vary so much",
        "desc_es": "Por qué la gasolina cuesta distinto en California, Texas, Florida, Nueva York y el resto de estados, y cómo usar GasRadar.",
        "desc_en": "Why gas costs different in California, Texas, Florida, New York and other states—and how to use GasRadar.",
        "body_es": """
        <p>En Estados Unidos el precio en el surtidor no es nacional único. Cada estado tiene impuestos, reglas ambientales y costos de suministro distintos.</p>
        <h3>Estados que suelen ser más caros</h3>
        <ul>
          <li><strong>California</strong> — impuestos altos + mezcla de combustible especial (CARB).</li>
          <li><strong>Hawái</strong> — transporte e islas.</li>
          <li><strong>Washington / Oregón / partes del Noreste</strong> — impuestos y logística.</li>
        </ul>
        <h3>Estados que suelen ser más baratos</h3>
        <ul>
          <li><strong>Texas, Oklahoma, Mississippi, Louisiana</strong> — producción y menor carga fiscal en muchos casos.</li>
          <li><strong>Partes del Medio Oeste</strong> — competencia y corredores de refinería.</li>
        </ul>
        <h3>Qué puedes hacer tú (en cualquier estado)</h3>
        <ol>
          <li>Abre <a href="/">GasRadar</a> con GPS o ZIP.</li>
          <li>Mira el <strong>promedio del estado</strong> como referencia (no es el precio exacto de cada bomba).</li>
          <li>Compara estaciones en un radio de 5–10 millas.</li>
          <li>Elige Regular si tu auto lo permite.</li>
        </ol>
        <p>Da igual si estás en <strong>Florida, Arizona, Colorado, Illinois o Nueva York</strong>: el método es el mismo. Cambia el ZIP y listo.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Comparar precios en tu estado</a></p>
        """,
        "body_en": """
        <p>In the United States there is no single national pump price. Each state has different taxes, fuel rules, and supply costs.</p>
        <h3>States that are often more expensive</h3>
        <ul>
          <li><strong>California</strong> — high taxes + special fuel blend (CARB).</li>
          <li><strong>Hawaii</strong> — shipping and island logistics.</li>
          <li><strong>Washington / Oregon / parts of the Northeast</strong> — taxes and transport.</li>
        </ul>
        <h3>States that are often cheaper</h3>
        <ul>
          <li><strong>Texas, Oklahoma, Mississippi, Louisiana</strong> — production and often lower tax burden.</li>
          <li><strong>Parts of the Midwest</strong> — competition and refining corridors.</li>
        </ul>
        <h3>What you can do (any state)</h3>
        <ol>
          <li>Open <a href="/">GasRadar</a> with GPS or ZIP.</li>
          <li>Check the <strong>state average</strong> as a reference (not every pump’s exact price).</li>
          <li>Compare stations within 5–10 miles.</li>
          <li>Use Regular if your car allows it.</li>
        </ol>
        <p>Whether you’re in <strong>Florida, Arizona, Colorado, Illinois, or New York</strong>, the method is the same. Change the ZIP and go.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Compare prices in your state</a></p>
        """,
    },
    {
        "slug": "cheapest-gas-major-us-cities",
        "date": "2026-08-03",
        "title_es": "Gasolina barata en grandes ciudades de EE.UU.: NYC, LA, Chicago, Houston, Miami y más",
        "title_en": "Cheap gas in major US cities: NYC, LA, Chicago, Houston, Miami & more",
        "desc_es": "Consejos para encontrar gasolina barata en Nueva York, Los Ángeles, Chicago, Houston, Miami, Phoenix, Dallas, Atlanta, Denver y Seattle con GasRadar.",
        "desc_en": "Tips to find cheap gas in New York, Los Angeles, Chicago, Houston, Miami, Phoenix, Dallas, Atlanta, Denver, and Seattle with GasRadar.",
        "body_es": """
        <p>Las grandes ciudades tienen más estaciones… y más trampas de precio. Aquí va un mapa mental <strong>multi-ciudad USA</strong>.</p>
        <h3>Nueva York (NYC / NJ)</h3>
        <p>Manhattan suele ser caro. Muchos conductores cruzan a <strong>Nueva Jersey</strong> o buscan en Queens/Brooklyn con ZIP. En GasRadar prueba ZIPs de zonas residenciales, no solo el código del centro.</p>
        <h3>Los Ángeles (CA)</h3>
        <p>Precios altos a nivel estado. Evita solo el área de aeropuerto y turística. Compara 5–10 millas: el tráfico cuesta tiempo, así que el ahorro por galón debe ser real.</p>
        <h3>Chicago (IL)</h3>
        <p>Centro vs suburbios (Naperville, Schaumburg, etc.) puede cambiar mucho. Usa GPS en hora valle si puedes.</p>
        <h3>Houston y Dallas (TX)</h3>
        <p>Texas suele ser más competitivo. Aun así, las estaciones de conveniencia en corredores premium pueden estar por encima del promedio. Un ZIP de barrio residencial ayuda.</p>
        <h3>Miami y Orlando (FL)</h3>
        <p>Zonas turísticas y aeropuertos suben el ticket. Mira un poco hacia inland o corredores locales.</p>
        <h3>Phoenix, Atlanta, Denver, Seattle</h3>
        <ul>
          <li><strong>Phoenix</strong> — calor + distancias largas: planifica el llenado con la ruta del día.</li>
          <li><strong>Atlanta</strong> — perímetro vs downtown; el radio de 10 millas importa.</li>
          <li><strong>Denver / Colorado Springs</strong> — buen ejemplo de comparar ZIP (80903, etc.) vs solo “la ciudad”.</li>
          <li><strong>Seattle</strong> — impuestos y geografía; vale la pena mirar fuera del núcleo.</li>
        </ul>
        <p>En todas: abre <a href="/">GasRadar</a>, pon GPS o ZIP, elige Regular y el radio. Misma app, cualquier ciudad de EE.UU.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Buscar gasolina barata en tu ciudad</a></p>
        """,
        "body_en": """
        <p>Big cities have more stations—and more price traps. Here’s a <strong>multi-city USA</strong> playbook.</p>
        <h3>New York (NYC / NJ)</h3>
        <p>Manhattan is often expensive. Many drivers look toward <strong>New Jersey</strong> or residential Queens/Brooklyn ZIPs. In GasRadar, try neighborhood ZIPs—not only a downtown code.</p>
        <h3>Los Angeles (CA)</h3>
        <p>State-level prices run high. Avoid relying only on airport/tourist strips. Compare 5–10 miles: traffic costs time, so the per-gallon savings must be real.</p>
        <h3>Chicago (IL)</h3>
        <p>Downtown vs suburbs (Naperville, Schaumburg, etc.) can differ a lot. Use GPS off-peak when you can.</p>
        <h3>Houston & Dallas (TX)</h3>
        <p>Texas is often competitive. Still, premium corridors can sit above average. A residential ZIP helps.</p>
        <h3>Miami & Orlando (FL)</h3>
        <p>Tourist and airport areas inflate prices. Check a bit inland or local corridors.</p>
        <h3>Phoenix, Atlanta, Denver, Seattle</h3>
        <ul>
          <li><strong>Phoenix</strong> — heat + long drives: plan fueling with the day’s route.</li>
          <li><strong>Atlanta</strong> — perimeter vs downtown; a 10-mile radius matters.</li>
          <li><strong>Denver / Colorado Springs</strong> — great example of ZIP search (e.g. 80903) vs city name only.</li>
          <li><strong>Seattle</strong> — taxes and geography; look outside the core.</li>
        </ul>
        <p>Everywhere: open <a href="/">GasRadar</a>, set GPS or ZIP, choose Regular and radius. Same app, any US city.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Find cheap gas in your city</a></p>
        """,
    },
    {
        "slug": "best-time-to-buy-gas-usa",
        "date": "2026-08-02",
        "title_es": "¿Cuándo conviene cargar gasolina en EE.UU.?",
        "title_en": "When is the best time to buy gas in the USA?",
        "desc_es": "Mejores días y horarios para cargar gasolina en Estados Unidos y cómo verificar con GasRadar.",
        "desc_en": "Best days and times to fill up in the United States—and how to check with GasRadar.",
        "body_es": """
        <p>No hay una hora mágica igual en los 50 estados, pero sí patrones que se repiten en casi todo el país.</p>
        <h3>Patrones habituales</h3>
        <ul>
          <li><strong>Mitad de semana</strong> (martes–jueves) a veces es más estable que el viernes-domingo de viajes.</li>
          <li><strong>Mañanas tempranas</strong> pueden mostrar precios del día anterior aún no actualizados en algunas estaciones.</li>
          <li><strong>Antes de feriados largos</strong> (Memorial Day, 4 de julio, Labor Day, Thanksgiving) la demanda sube y los precios suelen apretarse en corredores interestatales.</li>
        </ul>
        <h3>Lo que sí funciona siempre</h3>
        <p>No memorices un mito: <strong>compara en el momento</strong>. Abre GasRadar, mira 3–5 estaciones en tu radio y elige. Eso gana a “siempre el lunes a las 8am”.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Ver precios ahora cerca de ti</a></p>
        """,
        "body_en": """
        <p>There’s no single magic hour across all 50 states, but patterns show up nationwide.</p>
        <h3>Common patterns</h3>
        <ul>
          <li><strong>Midweek</strong> (Tue–Thu) is often steadier than Friday–Sunday travel peaks.</li>
          <li><strong>Early morning</strong> can still show prior-day posted prices at some stations.</li>
          <li><strong>Before long holidays</strong> (Memorial Day, July 4, Labor Day, Thanksgiving) demand rises and interstate corridors tighten.</li>
        </ul>
        <h3>What always works</h3>
        <p>Don’t memorize a myth—<strong>compare right now</strong>. Open GasRadar, check 3–5 stations in your radius, and pick. That beats “always Monday at 8am.”</p>
        <p class="blog-cta"><a class="btn-blog" href="/">See prices near you now</a></p>
        """,
    },
    {
        "slug": "regular-vs-premium-gas",
        "date": "2026-08-02",
        "title_es": "Regular vs Premium vs Diésel: qué gasolina te conviene",
        "title_en": "Regular vs Premium vs Diesel: which fuel should you buy?",
        "desc_es": "Cuándo usar Regular, Midgrade, Premium o Diésel en EE.UU. y cómo compararlos en GasRadar.",
        "desc_en": "When to use Regular, Midgrade, Premium, or Diesel in the USA—and how to compare them in GasRadar.",
        "body_es": """
        <p>En el surtidor estadounidense casi siempre ves <strong>Regular (87)</strong>, a veces Midgrade (89) y Premium (91–93), más diésel en muchas estaciones.</p>
        <h3>Regular</h3>
        <p>Opción por defecto para la mayoría de autos y crossovers. Si el manual dice 87, no necesitas Premium.</p>
        <h3>Premium</h3>
        <p>Para motores que <strong>requieren</strong> alto octanaje (turbo de alto rendimiento, algunos de lujo). Si solo “recomienda” Premium, consulta el manual: a menudo Regular es aceptable con menor potencia.</p>
        <h3>Diésel</h3>
        <p>Otro mercado de precios. Camionetas y autos diésel deben comparar el grade diésel, no el Regular.</p>
        <h3>En GasRadar</h3>
        <p>Cambia el selector de combustible y vuelve a buscar. El ranking de “más barata” depende del grade que elijas.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Comparar Regular / Premium / Diésel</a></p>
        """,
        "body_en": """
        <p>At US pumps you’ll usually see <strong>Regular (87)</strong>, sometimes Midgrade (89) and Premium (91–93), plus diesel at many stations.</p>
        <h3>Regular</h3>
        <p>Default for most cars and crossovers. If the manual says 87, you don’t need Premium.</p>
        <h3>Premium</h3>
        <p>For engines that <strong>require</strong> high octane (some turbos, performance/luxury). If it only “recommends” Premium, check the manual—Regular is often acceptable with less power.</p>
        <h3>Diesel</h3>
        <p>A different price market. Diesel trucks/cars should compare diesel, not Regular.</p>
        <h3>In GasRadar</h3>
        <p>Switch the fuel selector and search again. The “cheapest” ranking depends on the grade you pick.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Compare Regular / Premium / Diesel</a></p>
        """,
    },
    {
        "slug": "how-gasradar-works",
        "date": "2026-08-01",
        "title_es": "Cómo funciona GasRadar: precios, mapa y app en EE.UU.",
        "title_en": "How GasRadar works: prices, stations, and the US app",
        "desc_es": "Explicación de GasRadar: estaciones, promedios AAA/EIA, reportes de usuarios, web y Android en todo Estados Unidos.",
        "desc_en": "How GasRadar works: stations, AAA/EIA averages, user reports, web and Android across the United States.",
        "body_es": """
        <p><strong>GasRadar</strong> te ayuda a encontrar gasolina de referencia cerca de ti en Estados Unidos — por GPS o ZIP, en español o inglés.</p>
        <h3>Qué muestra la app</h3>
        <ul>
          <li>Estaciones cercanas (datos de mapas abiertos / geocodificación).</li>
          <li>Precios de referencia y reportes de la comunidad cuando están disponibles.</li>
          <li>Promedio estatal (fuentes tipo AAA/EIA) como guía.</li>
          <li>Cómo llegar con Apple/Google Maps.</li>
        </ul>
        <h3>Cobertura</h3>
        <p>Pensado para <strong>todo EE.UU.</strong>: desde Florida hasta Washington, Texas hasta Nueva York. No estás limitado a una sola ciudad.</p>
        <h3>App Android y web</h3>
        <p>Usa la web en <a href="/">gasradarapp.com</a> o la app en prueba de Google Play. También hay bot de Telegram y canal de WhatsApp para novedades.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Probar GasRadar gratis</a></p>
        """,
        "body_en": """
        <p><strong>GasRadar</strong> helps you find reference gas prices near you in the United States—by GPS or ZIP, in English or Spanish.</p>
        <h3>What the app shows</h3>
        <ul>
          <li>Nearby stations (open map data / geocoding).</li>
          <li>Reference prices and community reports when available.</li>
          <li>State averages (AAA/EIA-style sources) as a guide.</li>
          <li>Directions via Apple/Google Maps.</li>
        </ul>
        <h3>Coverage</h3>
        <p>Built for the <strong>whole USA</strong>: Florida to Washington, Texas to New York. You’re not limited to one city.</p>
        <h3>Android app & web</h3>
        <p>Use the web at <a href="/">gasradarapp.com</a> or the Android app on Google Play testing tracks. There’s also a Telegram bot and WhatsApp channel for updates.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Try GasRadar free</a></p>
        """,
    },
    {
        "slug": "save-money-on-gas-usa-tips",
        "date": "2026-08-01",
        "title_es": "10 formas de ahorrar en gasolina en Estados Unidos",
        "title_en": "10 ways to save money on gas in the United States",
        "desc_es": "Consejos prácticos para gastar menos en gasolina en EE.UU.: hábitos de manejo, apps, horarios y GasRadar.",
        "desc_en": "Practical tips to spend less on gas in the USA: driving habits, apps, timing, and GasRadar.",
        "body_es": """
        <ol>
          <li><strong>Compara siempre</strong> con GPS/ZIP antes de llenar (<a href="/">GasRadar</a>).</li>
          <li><strong>Regular</strong> si el manual lo permite.</li>
          <li><strong>Presión de llantas</strong> correcta: menos consumo en highway.</li>
          <li><strong>Acelerar suave</strong> y mantener velocidad estable en interstate.</li>
          <li><strong>Quita peso</strong> innecesario del maletero.</li>
          <li><strong>Combina mandados</strong> en una sola ruta.</li>
          <li><strong>Evita idling</strong> largo con el A/C a tope si no hace falta.</li>
          <li><strong>No persigas 2¢</strong> a 15 millas si el tanque está casi lleno.</li>
          <li><strong>Reporta precios</strong> para mejorar la red en tu ciudad.</li>
          <li><strong>Alertas</strong> por Telegram/WhatsApp cuando baje en tu zona.</li>
        </ol>
        <p>Estos tips aplican en California, Texas, Florida, el Medio Oeste o la Costa Este. La geografía cambia; el hábito de comparar no.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Empezar a comparar precios</a></p>
        """,
        "body_en": """
        <ol>
          <li><strong>Always compare</strong> with GPS/ZIP before you fill (<a href="/">GasRadar</a>).</li>
          <li><strong>Use Regular</strong> if the manual allows it.</li>
          <li><strong>Correct tire pressure</strong> cuts highway waste.</li>
          <li><strong>Smooth acceleration</strong> and steady interstate speed.</li>
          <li><strong>Remove extra weight</strong> from the trunk.</li>
          <li><strong>Batch errands</strong> into one loop.</li>
          <li><strong>Avoid long idling</strong> with A/C blasting when you don’t need it.</li>
          <li><strong>Don’t chase 2¢</strong> across 15 miles if the tank is already full.</li>
          <li><strong>Report prices</strong> to improve data in your city.</li>
          <li><strong>Alerts</strong> via Telegram/WhatsApp when prices drop nearby.</li>
        </ol>
        <p>These tips work in California, Texas, Florida, the Midwest, or the East Coast. Geography changes; the habit of comparing doesn’t.</p>
        <p class="blog-cta"><a class="btn-blog" href="/">Start comparing prices</a></p>
        """,
    },
]


def page_shell(
    *,
    title: str,
    description: str,
    canonical: str,
    active_slug: str | None,
    content_es: str,
    content_en: str,
    is_index: bool = False,
) -> str:
    nav_posts = "".join(
        f'<li><a href="/blog/{p["slug"]}">{p["title_es"][:60]}…</a></li>'
        if len(p["title_es"]) > 60
        else f'<li><a href="/blog/{p["slug"]}">{p["title_es"]}</a></li>'
        for p in POSTS[:5]
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="theme-color" content="#0b1220" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:type" content="{'website' if is_index else 'article'}" />
  <meta property="og:site_name" content="GasRadar" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{SITE}/static/logo-512.png?v=0.5.0" />
  <meta property="og:locale" content="es_US" />
  <meta property="og:locale:alternate" content="en_US" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <link rel="icon" href="/static/favicon-32.png?v=0.2.9" type="image/png" />
  <link rel="stylesheet" href="/static/styles.css?v={CSS_V}" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "{'Blog' if is_index else 'BlogPosting'}",
    "headline": {title!r},
    "description": {description!r},
    "url": {canonical!r},
    "publisher": {{
      "@type": "Organization",
      "name": "GasRadar",
      "url": "{SITE}/",
      "logo": {{ "@type": "ImageObject", "url": "{SITE}/static/logo-512.png" }}
    }},
    "inLanguage": ["es-US", "en-US"],
    "mainEntityOfPage": {canonical!r}
  }}
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
          <p class="subtitle" id="blogSub">Blog</p>
        </div>
      </div>
      <div class="lang-switch" role="group" aria-label="Language">
        <button type="button" class="lang-btn active" id="btnLangEs" data-lang="es">ES</button>
        <button type="button" class="lang-btn" id="btnLangEn" data-lang="en">EN</button>
      </div>
    </header>

    <nav class="blog-nav card" aria-label="Blog">
      <a href="/blog">← Blog</a>
      <span class="footer-sep">·</span>
      <a href="/">App</a>
      <span class="footer-sep">·</span>
      <a href="/privacy">Privacidad</a>
    </nav>

    <section class="card privacy-card blog-card" id="contentEs">
      {content_es}
    </section>
    <section class="card privacy-card blog-card" id="contentEn" hidden>
      {content_en}
    </section>

    <aside class="card privacy-card blog-aside">
      <h3 id="moreTitle">Más guías</h3>
      <ul class="blog-list-mini">{nav_posts}</ul>
      <p class="blog-cta"><a class="btn-blog" href="/">Abrir GasRadar</a></p>
    </aside>

    <footer class="site-footer">
      <div><strong>GasRadar</strong> · USA</div>
      <div class="footer-links">
        <a href="/blog">Blog</a>
        <span class="footer-sep">·</span>
        <a href="/privacy">Privacidad</a>
        <span class="footer-sep">·</span>
        <a class="footer-wa-channel" href="https://www.whatsapp.com/channel/0029VbDQSOH42DcdzMZQb241" target="_blank" rel="noopener">Canal WhatsApp</a>
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
      document.getElementById("blogSub").textContent = "Blog";
      document.getElementById("moreTitle").textContent = lang === "en" ? "More guides" : "Más guías";
    }}
    document.getElementById("btnLangEs").onclick = () => setLang("es");
    document.getElementById("btnLangEn").onclick = () => setLang("en");
    setLang(loadLang());
  </script>
</body>
</html>
"""


def build_index() -> None:
    cards_es = []
    cards_en = []
    for p in POSTS:
        cards_es.append(
            f"""<article class="blog-index-card">
  <p class="privacy-meta">{p["date"]}</p>
  <h2><a href="/blog/{p["slug"]}">{p["title_es"]}</a></h2>
  <p>{p["desc_es"]}</p>
  <a class="blog-read" href="/blog/{p["slug"]}">Leer →</a>
</article>"""
        )
        cards_en.append(
            f"""<article class="blog-index-card">
  <p class="privacy-meta">{p["date"]}</p>
  <h2><a href="/blog/{p["slug"]}">{p["title_en"]}</a></h2>
  <p>{p["desc_en"]}</p>
  <a class="blog-read" href="/blog/{p["slug"]}">Read →</a>
</article>"""
        )
    es = f"""
    <h2>Blog GasRadar — gasolina en todo EE.UU.</h2>
    <p class="privacy-meta">Guías para ahorrar en gasolina en Estados Unidos (no solo una ciudad).</p>
    <p>Consejos prácticos de costa a costa: precios por estado, grandes ciudades, Regular vs Premium y cómo usar GasRadar con GPS o ZIP.</p>
    {''.join(cards_es)}
    """
    en = f"""
    <h2>GasRadar Blog — gas across the USA</h2>
    <p class="privacy-meta">Guides to save on gas nationwide (not just one city).</p>
    <p>Coast-to-coast tips: prices by state, major cities, Regular vs Premium, and how to use GasRadar with GPS or ZIP.</p>
    {''.join(cards_en)}
    """
    html = page_shell(
        title="GasRadar Blog — Cheap gas tips USA",
        description="Guides to find cheap gas across the United States. Tips by state and city, fuel grades, and GasRadar.",
        canonical=f"{SITE}/blog",
        active_slug=None,
        content_es=es,
        content_en=en,
        is_index=True,
    )
    (BLOG / "index.html").write_text(html, encoding="utf-8")
    print("wrote blog/index.html")


def build_posts() -> None:
    for p in POSTS:
        es = f"""
        <p class="privacy-meta">{p["date"]} · USA</p>
        <h2>{p["title_es"]}</h2>
        {p["body_es"]}
        """
        en = f"""
        <p class="privacy-meta">{p["date"]} · USA</p>
        <h2>{p["title_en"]}</h2>
        {p["body_en"]}
        """
        html = page_shell(
            title=f'{p["title_en"]} | GasRadar',
            description=p["desc_en"],
            canonical=f'{SITE}/blog/{p["slug"]}',
            active_slug=p["slug"],
            content_es=es,
            content_en=en,
        )
        path = BLOG / f'{p["slug"]}.html'
        path.write_text(html, encoding="utf-8")
        print("wrote", path.name)


def build_sitemap() -> None:
    urls = [
        ("/", "daily", "1.0"),
        ("/privacy", "monthly", "0.4"),
        ("/blog", "weekly", "0.8"),
    ]
    for p in POSTS:
        urls.append((f"/blog/{p['slug']}", "monthly", "0.7"))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, freq, pri in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{SITE}{loc}</loc>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{pri}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote sitemap.xml")


if __name__ == "__main__":
    build_index()
    build_posts()
    build_sitemap()
    print("done", len(POSTS), "posts")
