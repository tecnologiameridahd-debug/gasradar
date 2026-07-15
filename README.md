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

- **Estaciones**: OpenStreetMap (reales).
- **Precios**: estimados por marca + promedio estatal, **sobrescritos** si un usuario reporta.
- No scrapea GasBuddy (ToS). Más adelante se puede enganchar una API de precios de pago.

## Próximos pasos

1. API de precios en vivo (CollectAPI / partner)
2. Mapa embebido (Leaflet)
3. Alertas Telegram cuando baje el precio en tu ZIP
4. Historial de precios por estación
