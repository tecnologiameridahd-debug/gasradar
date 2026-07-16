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

        conn = psycopg.connect(_pg_dsn(database_url()), row_factory=dict_row)
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
        else:
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
                """
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
    info: dict[str, Any] = {
        "backend": backend,
        "persistent": backend == "postgres",
        "ok": False,
        "reports_count": None,
    }
    try:
        init_schema()
        row = fetchone("SELECT COUNT(*) AS n FROM price_reports")
        n = int(row["n"]) if row and row.get("n") is not None else 0
        info["ok"] = True
        info["reports_count"] = n
        if backend == "sqlite":
            info["note"] = "SQLite local — en Render free se borra al redeploy. Usa DATABASE_URL."
        else:
            info["note"] = "Postgres en la nube — reportes se conservan."
    except Exception as e:
        info["ok"] = False
        info["error"] = str(e)[:200]
    return info
