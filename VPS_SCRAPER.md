# Scraper VPS (GasBuddy) — guía rápida

Código en carpeta **`vps_scraper/`**.

## 1) En el VPS (Ubuntu)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# reconecta SSH

git clone https://github.com/TU_USER/gasradar.git
cd gasradar/vps_scraper
cp .env.example .env
nano .env   # SCRAPER_API_KEY=mi-clave-secreta

docker compose up -d --build
curl "http://127.0.0.1:8788/health"
curl "http://127.0.0.1:8788/prices?zip=80903&key=mi-clave-secreta"
```

Si ves `"ok": true` y estaciones con `price`, listo.

Abre el puerto **8788** en el firewall (o pon Nginx + HTTPS).

## 2) En Render (GasRadar)

Environment variables:

```
USE_VPS_SCRAPER=1
VPS_SCRAPER_URL=http://IP_DEL_VPS:8788
VPS_SCRAPER_KEY=mi-clave-secreta
```

Varios VPS (misma clave):

```
USE_VPS_SCRAPER=1
VPS_SCRAPER_KEY=mi-clave-secreta
VPS_SCRAPER_URLS=http://IP1:8788,http://IP2:8788
```

Paquete para copiar a cada máquina: `vps_scraper/` o el Escritorio `gasradar-scraper-vps`.
Guía: `vps_scraper/MONTAR_EN_VPS.txt`.

(mejor con HTTPS: `https://scraper.tudominio.com`)

Redeploy GasRadar.

## 3) Qué hace

- El VPS scrapea precios por estación (GasBuddy GraphQL)
- Caché 3 h en el VPS
- GasRadar los une a la lista (prioridad alta)
- Si el VPS falla → AAA + reportes (no se cae la app)

## Coste

- VPS ~$4–6/mes  
- Sin Apify ni Zyla  

## Caché aparte (Postgres)

Los precios ya no viven solo en el disco del VPS.

1. **VPS** — caché local 3 h (si esa máquina se cae, se pierde).
2. **Render / Postgres** — tabla `price_cache`. Sobrevive a redeploys y a que un VPS muera.
   Varios VPS y la web leen/escriben el mismo sitio.

Si el scraper está caído, GasRadar sigue mostrando el último precio (hasta 3 h).

## Legal

No es API oficial de GasBuddy. Usa caché y no spamees.
