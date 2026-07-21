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

## Legal

No es API oficial de GasBuddy. Usa caché y no spamees.
