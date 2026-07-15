"""
Ping periódico a GasRadar para que Render Free no se duerma.

Uso:
  set GASRADAR_URL=https://tu-app.onrender.com
  python keep_alive.py

O:
  python keep_alive.py https://tu-app.onrender.com
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime

import httpx

DEFAULT_INTERVAL = 600  # 10 minutos


def main() -> None:
    base = (
        (sys.argv[1] if len(sys.argv) > 1 else "")
        or os.environ.get("GASRADAR_URL", "")
    ).strip().rstrip("/")
    if not base or "onrender.com" not in base and "http" not in base:
        print("Uso: python keep_alive.py https://TU-APP.onrender.com")
        print("  o: set GASRADAR_URL=https://... && python keep_alive.py")
        sys.exit(1)

    url = base if base.endswith("/api/health") else base + "/api/health"
    interval = int(os.environ.get("KEEPALIVE_INTERVAL", DEFAULT_INTERVAL))
    print(f"GasRadar keep-alive → {url}")
    print(f"Cada {interval}s. Ctrl+C para parar.\n")

    while True:
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            r = httpx.get(url, timeout=30.0)
            print(f"{ts}  OK {r.status_code}  {r.text[:80]}")
        except Exception as e:
            print(f"{ts}  FAIL  {e}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
