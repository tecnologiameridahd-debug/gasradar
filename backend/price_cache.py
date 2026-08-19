"""
Caché de precios APARTE de los VPS: Postgres (Render) o SQLite local.

- No se borra si un VPS se cae o se reinstala.
- Lo comparten todos los scrapers y la web.
- TTL por defecto 3 horas (igual que el VPS).
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

DEFAULT_TTL = int(os.environ.get("PRICE_CACHE_TTL_SEC") or 3 * 3600)


def get(key: str, ttl: int | None = None) -> dict | None:
    ttl = DEFAULT_TTL if ttl is None else ttl
    if not key:
        return None
    try:
        from backend.db import fetchone

        row = fetchone(
            "SELECT payload, ts FROM price_cache WHERE cache_key = ?",
            (key,),
        )
        if not row:
            return None
        if time.time() - float(row.get("ts") or 0) > ttl:
            return None
        data = json.loads(row.get("payload") or "")
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"[price_cache] get fail: {type(e).__name__}: {e}")
        return None


def put(key: str, data: dict) -> None:
    if not key or not isinstance(data, dict):
        return
    try:
        from backend.db import db_backend, execute

        payload = json.dumps(data, ensure_ascii=False, default=str)
        now = time.time()
        if db_backend() == "postgres":
            execute(
                """
                INSERT INTO price_cache (cache_key, payload, ts)
                VALUES (?, ?, ?)
                ON CONFLICT (cache_key) DO UPDATE
                  SET payload = EXCLUDED.payload, ts = EXCLUDED.ts
                """,
                (key, payload, now),
            )
        else:
            execute(
                """
                INSERT INTO price_cache (cache_key, payload, ts)
                VALUES (?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE
                  SET payload = excluded.payload, ts = excluded.ts
                """,
                (key, payload, now),
            )
    except Exception as e:
        print(f"[price_cache] put fail: {type(e).__name__}: {e}")
