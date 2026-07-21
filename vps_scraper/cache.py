"""Caché en disco por ZIP / coords."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

CACHE_DIR = Path(os.environ.get("CACHE_DIR") or Path(__file__).resolve().parent / "data" / "cache")
DEFAULT_TTL = int(os.environ.get("CACHE_TTL_SEC") or 3 * 3600)  # 3 h


def _path(key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)[:120]
    return CACHE_DIR / f"{safe}.json"


def get(key: str, ttl: int | None = None) -> dict | None:
    ttl = DEFAULT_TTL if ttl is None else ttl
    p = _path(key)
    try:
        if not p.exists():
            return None
        obj = json.loads(p.read_text(encoding="utf-8"))
        if time.time() - float(obj.get("ts") or 0) > ttl:
            return None
        return obj.get("data")
    except Exception:
        return None


def set_(key: str, data: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _path(key).write_text(
            json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[cache] save fail: {e}")
