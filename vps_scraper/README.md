# GasRadar VPS Scraper (GasBuddy)

Mini-API para correr en un **VPS** (no en Render free).  
Obtiene precios por estación (estilo GasBuddy) y se los da a GasRadar.

> No es API oficial de GasBuddy. Usa caché y rate-limit.  
> Puede dejar de funcionar si GasBuddy cambia Cloudflare/GraphQL.

## Qué hace

| Endpoint | Descripción |
|----------|-------------|
| `GET /health` | Estado del servicio |
| `GET /prices?zip=80903&key=...` | Precios por ZIP |
| `GET /prices?lat=..&lon=..&key=...` | Precios por GPS |
| `GET /warm?zip=80903&key=...` | Fuerza refresh (cron) |

Respuesta ejemplo:

```json
{
  "ok": true,
  "method": "flaresolverr",
  "count": 18,
  "stations": [
    {
      "name": "Circle K",
      "brand": "Circle K",
      "lat": 38.83,
      "lon": -104.80,
      "address": "1204 E Pikes Peak Ave, Colorado Springs, CO",
      "price": 3.69,
      "source": "gasbuddy"
    }
  ]
}
```

## Requisitos del VPS

- Ubuntu 22.04+ (o similar)
- Docker + Docker Compose
- ~1–2 GB RAM
- Puerto **8788** abierto (o reverse proxy con HTTPS)

Proveedores baratos: Hetzner, DigitalOcean, Contabo, Oracle free tier, etc. (~$4–6/mes).

## Instalación en el VPS

```bash
# 1) Instalar Docker (Ubuntu)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# cierra sesión y vuelve a entrar

# 2) Subir esta carpeta al VPS
#    (git clone del repo o scp -r vps_scraper/)

cd vps_scraper
cp .env.example .env
nano .env   # pon SCRAPER_API_KEY=algo-secreto

# 3) Arrancar
docker compose up -d --build

# 4) Probar
curl "http://127.0.0.1:8788/health"
curl "http://127.0.0.1:8788/prices?zip=80903&key=algo-secreto"
```

Si `ok: true` y hay `stations`, el VPS funciona.

### HTTPS (recomendado)

Con Nginx + Let's Encrypt apunta un dominio, ej. `scraper.tudominio.com` → `127.0.0.1:8788`.

## Conectar GasRadar (Render)

En el servicio de Render, variables de entorno:

```
VPS_SCRAPER_URL=https://scraper.tudominio.com
VPS_SCRAPER_KEY=algo-secreto
USE_VPS_SCRAPER=1
```

GasRadar llamará al VPS con caché; si falla, usa AAA + reportes.

## Cron en el VPS (opcional)

Refrescar ZIPs top cada 4 h (crontab):

```cron
0 */4 * * * curl -s "http://127.0.0.1:8788/warm?zip=80903&key=algo-secreto" >/dev/null
0 */4 * * * curl -s "http://127.0.0.1:8788/warm?zip=80202&key=algo-secreto" >/dev/null
```

## Arquitectura

```
Internet
   │
   ▼
[GasRadar Render] ----HTTPS----> [VPS :8788 scraper]
                                      │
                                      ├── FlareSolverr :8191
                                      └── GasBuddy.com (GraphQL)
```

## Troubleshooting

| Problema | Qué hacer |
|----------|-----------|
| `ok: false` sin stations | Revisa logs: `docker compose logs -f scraper` |
| Cloudflare | Asegúrate de que FlareSolverr está up: `docker compose ps` |
| Timeout | Sube RAM del VPS; prueba de nuevo |
| 401 | `key=` debe ser igual a `SCRAPER_API_KEY` |

```bash
docker compose logs -f flaresolverr
docker compose logs -f scraper
docker compose restart
```

## Legal

Este servicio lee datos públicos de GasBuddy de forma automatizada.  
Revisa los términos de GasBuddy y úsalo de forma moderada (caché, pocos ZIPs, no spam).
