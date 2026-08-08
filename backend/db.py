"""
Capa de base de datos GasRadar.

- En tu PC (sin DATABASE_URL): SQLite local → data/prices.db
- En internet (Render + Neon/Supabase): Postgres con DATABASE_URL

Los reportes de precio se guardan en la tabla price_reports.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "prices.db"

_schema_ready = False


def database_url() -> str:
    """URL de Postgres (Neon, Supabase, Render…). Vacía = SQLite local."""
    return (os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or "").strip()


def db_backend() -> str:
    return "postgres" if database_url() else "sqlite"


def _pg_dsn(url: str) -> str:
    # psycopg acepta postgresql:// ; muchas UIs dan postgres://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def _adapt_sql(sql: str) -> str:
    """SQLite usa ? ; Postgres (psycopg) usa %s."""
    if db_backend() == "postgres":
        return sql.replace("?", "%s")
    return sql


@contextmanager
def connect() -> Iterator[Any]:
    """Conexión lista para usar (commit al salir ok, rollback si falla)."""
    if db_backend() == "postgres":
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(
            _pg_dsn(database_url()),
            row_factory=dict_row,
            connect_timeout=5,
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_schema() -> None:
    """Crea tablas e índices si no existen."""
    global _schema_ready
    if _schema_ready:
        return

    with connect() as conn:
        if db_backend() == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS price_reports (
                        id BIGSERIAL PRIMARY KEY,
                        station_id TEXT NOT NULL,
                        fuel TEXT NOT NULL,
                        price DOUBLE PRECISION NOT NULL,
                        reported_at DOUBLE PRECISION NOT NULL,
                        note TEXT
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_reports_station
                        ON price_reports (station_id, fuel, reported_at DESC)
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS site_events (
                        id BIGSERIAL PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        path TEXT,
                        referrer TEXT,
                        lang TEXT,
                        detail TEXT,
                        day TEXT NOT NULL,
                        created_at DOUBLE PRECISION NOT NULL,
                        ip TEXT,
                        ip_country TEXT
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_events_day
                        ON site_events (day, event_type)
                    """
                )
                cur.execute(
                    "ALTER TABLE site_events ADD COLUMN IF NOT EXISTS ip TEXT"
                )
                cur.execute(
                    "ALTER TABLE site_events ADD COLUMN IF NOT EXISTS ip_country TEXT"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_ip ON site_events (ip)"
                )
        else:
            # Crear tablas base SIN índice sobre ip (la tabla vieja puede no tener ip aún)
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS price_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL,
                    fuel TEXT NOT NULL,
                    price REAL NOT NULL,
                    reported_at REAL NOT NULL,
                    note TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_reports_station
                    ON price_reports (station_id, fuel, reported_at DESC);
                CREATE TABLE IF NOT EXISTS site_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    path TEXT,
                    referrer TEXT,
                    lang TEXT,
                    detail TEXT,
                    day TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_day
                    ON site_events (day, event_type);
                """
            )
            # Migración: añadir columnas IP si faltan, LUEGO el índice
            cols = {
                r[1]
                for r in conn.execute("PRAGMA table_info(site_events)").fetchall()
            }
            if "ip" not in cols:
                conn.execute("ALTER TABLE site_events ADD COLUMN ip TEXT")
            if "ip_country" not in cols:
                conn.execute("ALTER TABLE site_events ADD COLUMN ip_country TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_ip ON site_events (ip)"
            )

    _schema_ready = True


def execute(sql: str, params: tuple | list = ()) -> None:
    init_schema()
    sql = _adapt_sql(sql)
    with connect() as conn:
        if db_backend() == "postgres":
            with conn.cursor() as cur:
                cur.execute(sql, params)
        else:
            conn.execute(sql, params)


def fetchall(sql: str, params: tuple | list = ()) -> list[dict]:
    init_schema()
    sql = _adapt_sql(sql)
    with connect() as conn:
        if db_backend() == "postgres":
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return [dict(r) for r in rows]
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def fetchone(sql: str, params: tuple | list = ()) -> dict | None:
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def db_status() -> dict:
    """Info para /api/health (sin exponer contraseñas)."""
    backend = db_backend()
    on_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))
    info: dict[str, Any] = {
        "backend": backend,
        "persistent": backend == "postgres",
        "ok": False,
        "reports_count": None,
        "events_count": None,
        "on_render": on_render,
        "database_url_set": bool(database_url()),
    }
    try:
        init_schema()
        row = fetchone("SELECT COUNT(*) AS n FROM price_reports")
        n = int(row["n"]) if row and row.get("n") is not None else 0
        ev = fetchone("SELECT COUNT(*) AS n FROM site_events")
        info["ok"] = True
        info["reports_count"] = n
        info["events_count"] = int(ev["n"]) if ev and ev.get("n") is not None else 0
        if backend == "postgres":
            info["note"] = (
                "Postgres — reportes, visitas, IPs y búsquedas se conservan entre deploys."
            )
        elif on_render:
            info["note"] = (
                "⚠️ Render sin DATABASE_URL: SQLite se borra en cada redeploy. "
                "Enlaza Postgres (Blueprint o Dashboard → Environment → DATABASE_URL)."
            )
            info["warn"] = "missing_database_url"
        else:
            info["note"] = "SQLite local (dev). En producción usa DATABASE_URL (Postgres)."
    except Exception as e:
        info["ok"] = False
        info["error"] = str(e)[:200]
    return info
