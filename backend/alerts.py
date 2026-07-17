"""
Alertas de gasolina por Telegram (por ZIP + precio tope).
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from backend.db import execute, fetchall, fetchone, init_schema


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def ensure_alerts_schema() -> None:
    """Tabla de suscripciones Telegram (sqlite + postgres)."""
    init_schema()
    from backend.db import db_backend

    if db_backend() == "postgres":
        execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_alerts (
                chat_id TEXT PRIMARY KEY,
                zip TEXT,
                fuel TEXT NOT NULL DEFAULT 'regular',
                radius_mi DOUBLE PRECISION NOT NULL DEFAULT 5,
                max_price DOUBLE PRECISION,
                active INTEGER NOT NULL DEFAULT 1,
                lang TEXT NOT NULL DEFAULT 'es',
                label TEXT,
                last_sent_day TEXT,
                last_price DOUBLE PRECISION,
                created_at DOUBLE PRECISION NOT NULL,
                updated_at DOUBLE PRECISION NOT NULL
            )
            """
        )
        execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tg_alerts_active
                ON telegram_alerts (active, zip)
            """
        )
    else:
        execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_alerts (
                chat_id TEXT PRIMARY KEY,
                zip TEXT,
                fuel TEXT NOT NULL DEFAULT 'regular',
                radius_mi REAL NOT NULL DEFAULT 5,
                max_price REAL,
                active INTEGER NOT NULL DEFAULT 1,
                lang TEXT NOT NULL DEFAULT 'es',
                label TEXT,
                last_sent_day TEXT,
                last_price REAL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tg_alerts_active
                ON telegram_alerts (active, zip)
            """
        )


def get_alert(chat_id: str | int) -> dict | None:
    ensure_alerts_schema()
    return fetchone(
        "SELECT * FROM telegram_alerts WHERE chat_id = ?",
        (str(chat_id),),
    )


def upsert_alert(chat_id: str | int, **fields: Any) -> dict:
    ensure_alerts_schema()
    cid = str(chat_id)
    now = time.time()
    row = get_alert(cid)
    if not row:
        execute(
            """
            INSERT INTO telegram_alerts
            (chat_id, zip, fuel, radius_mi, max_price, active, lang, label,
             last_sent_day, last_price, created_at, updated_at)
            VALUES (?, NULL, 'regular', 5, NULL, 1, 'es', NULL, NULL, NULL, ?, ?)
            """,
            (cid, now, now),
        )
        row = get_alert(cid) or {"chat_id": cid}

    allowed = {
        "zip",
        "fuel",
        "radius_mi",
        "max_price",
        "active",
        "lang",
        "label",
        "last_sent_day",
        "last_price",
    }
    sets = []
    params: list[Any] = []
    for k, v in fields.items():
        if k not in allowed:
            continue
        sets.append(f"{k} = ?")
        params.append(v)
    if sets:
        sets.append("updated_at = ?")
        params.append(now)
        params.append(cid)
        execute(
            f"UPDATE telegram_alerts SET {', '.join(sets)} WHERE chat_id = ?",
            tuple(params),
        )
    return get_alert(cid) or row


def list_active_alerts() -> list[dict]:
    ensure_alerts_schema()
    return fetchall(
        """
        SELECT * FROM telegram_alerts
        WHERE active = 1 AND zip IS NOT NULL AND max_price IS NOT NULL
        """
    )


def mark_sent(chat_id: str | int, price: float) -> None:
    upsert_alert(chat_id, last_sent_day=_today(), last_price=float(price))


def delete_alert(chat_id: str | int) -> None:
    ensure_alerts_schema()
    execute("DELETE FROM telegram_alerts WHERE chat_id = ?", (str(chat_id),))


def format_alert_summary(row: dict | None, lang: str = "es") -> str:
    if not row:
        return (
            "No tienes alerta configurada.\n"
            "Usa /zona 80903 y luego /alerta 3.50"
            if lang != "en"
            else "No alert set.\nUse /zona 80903 then /alerta 3.50"
        )
    zip_c = row.get("zip") or "—"
    fuel = row.get("fuel") or "regular"
    radius = row.get("radius_mi") or 5
    mx = row.get("max_price")
    active = int(row.get("active") or 0) == 1
    label = row.get("label") or ""
    if lang == "en":
        lines = [
            "Your GasRadar alert:",
            f"• Zone: {zip_c}" + (f" ({label})" if label else ""),
            f"• Fuel: {fuel}",
            f"• Radius: {radius} mi",
            f"• Max price: ${float(mx):.3f}" if mx else "• Max price: (not set)",
            f"• Status: {'ON' if active else 'PAUSED'}",
            "",
            "Commands: /zona /alerta /fuel /ahora /pausa /activar /borrar",
        ]
    else:
        lines = [
            "Tu alerta GasRadar:",
            f"• Zona: {zip_c}" + (f" ({label})" if label else ""),
            f"• Combustible: {fuel}",
            f"• Radio: {radius} mi",
            f"• Precio tope: ${float(mx):.3f}" if mx else "• Precio tope: (sin definir)",
            f"• Estado: {'ACTIVA' if active else 'PAUSADA'}",
            "",
            "Comandos: /zona /alerta /fuel /ahora /pausa /activar /borrar",
        ]
    return "\n".join(lines)
