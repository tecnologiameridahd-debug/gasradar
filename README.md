# GasRadar — Precios de gasolina USA

**GasRadar** es una **app web** (se abre en el navegador del PC o del teléfono) para encontrar **la gasolina más barata cerca de ti**.

## MVP

- 📍 Ubicación GPS o ZIP (USA)
- ⛽ Estaciones reales (OpenStreetMap)
- 💵 Ranking por precio (regular / mid / premium / diesel)
- 🏆 Destaca la más barata + “cómo llegar”
- 📝 Reportar precio (comunidad, SQLite)
- 🗺️ Enlace a Google Maps

## Cómo arrancar en tu PC (local)

```bat
cd C:\Users\Alberto\gasolina_app
iniciar.bat
```

Abre: **http://127.0.0.1:8787**

## Cómo publicarla en internet (web pública)

Lee **[PUBLICAR.md](PUBLICAR.md)** — pasos con Render.com (gratis) y URL `https://...`.

## API

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/search?zip=80202&fuel=regular&radius_mi=5` | Buscar |
| `GET /api/search?lat=39.74&lon=-104.99` | Por GPS |
| `POST /api/report` | `{"station_id","fuel","price"}` |
| `GET /api/geo/zip/80202` | Geocode ZIP |

## Notas de datos

- **Estaciones**: OpenStreetMap + resultados del scraper VPS.
- **Precios en vivo**: GasBuddy vía VPS (`VPS_SCRAPER_URL`) cuando está activo.
- **Referencia**: promedios AAA / EIA por estado.
- **Reportes** de la comunidad sobrescriben el precio de esa estación.

## Sitio

- App: https://gasradarapp.com
- Ciudades: https://gasradarapp.com/gas
- Términos: https://gasradarapp.com/terminos
- Reglas: https://gasradarapp.com/reglas
- Reel diario (interno): `/diario/STATS_KEY`
- Bot: https://t.me/GasRadar_bot
- Instagram: https://www.instagram.com/gasradar_app
