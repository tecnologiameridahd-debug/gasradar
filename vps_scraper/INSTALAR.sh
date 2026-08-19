#!/bin/bash
# Monta este scraper en UN VPS. Copia la carpeta a cada máquina y corre esto.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== GasRadar scraper — instalar en este VPS ==="

if ! command -v docker >/dev/null 2>&1; then
  echo "Instalando Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
  echo
  echo "Docker instalado. CIERRA esta sesión SSH, vuelve a entrar y corre:"
  echo "  cd $(pwd) && bash INSTALAR.sh"
  exit 0
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "Creé .env — edítalo AHORA:"
  echo "  nano .env"
  echo "Pon SCRAPER_API_KEY (la misma en todos los VPS) y SCRAPER_NODE=vps1 (o vps2...)"
  echo "Luego:  bash INSTALAR.sh"
  exit 1
fi

if grep -q "cambia-esta-clave-larga" .env; then
  echo "ERROR: todavía está la clave de ejemplo en .env"
  echo "  nano .env   → cambia SCRAPER_API_KEY"
  exit 1
fi

docker compose up -d --build
echo
echo "Esperando health..."
sleep 4
curl -sS "http://127.0.0.1:8788/health" || true
echo
echo
echo "Listo. Prueba precios:"
KEY=$(grep -E '^SCRAPER_API_KEY=' .env | cut -d= -f2- | tr -d '\r')
echo "  curl \"http://127.0.0.1:8788/prices?zip=80903&key=${KEY}\""
echo
IP=$(curl -sS --max-time 4 https://ifconfig.me || hostname -I | awk '{print $1}')
echo "Desde Render usa:"
echo "  USE_VPS_SCRAPER=1"
echo "  VPS_SCRAPER_KEY=${KEY}"
echo "  VPS_SCRAPER_URL=http://${IP}:8788"
echo "Si tienes VARIOS VPS, en Render:"
echo "  VPS_SCRAPER_URLS=http://IP1:8788,http://IP2:8788"
echo
echo "Abre el puerto 8788 en el firewall de este VPS."
