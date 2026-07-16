"""
Estadísticas simples de visitas (sin nombres ni IPs).
Solo el dueño ve el panel en /stats?key=...
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from backend.db import execute, fetchall, fetchone


def stats_key() -> str:
    return (os.environ.get("STATS_KEY") or "gasradar2026").strip()


def check_stats_key(key: str | None) -> bool:
    return bool(key) and key.strip() == stats_key()


def _day_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def track_event(
    event_type: str,
    path: str | None = None,
    referrer: str | None = None,
    lang: str | None = None,
    detail: str | None = None,
) -> None:
    """Registra un evento anónimo. No guarda IP ni nombre."""
    et = (event_type or "pageview")[:40]
    # Limitar tamaños
    path = (path or "/")[:200]
    ref = (referrer or "")[:300]
    # solo host del referrer si es URL larga
    if ref.startswith("http"):
        try:
            from urllib.parse import urlparse

            p = urlparse(ref)
            ref = p.netloc or ref[:80]
        except Exception:
            ref = ref[:80]
    lang = (lang or "")[:12]
    detail = (detail or "")[:120]
    try:
        execute(
            """
            INSERT INTO site_events(event_type, path, referrer, lang, detail, day, created_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (et, path, ref, lang, detail, _day_utc(), time.time()),
        )
    except Exception as e:
        print(f"[analytics] track fail: {e}")


def summary(days: int = 14) -> dict:
    days = max(1, min(int(days), 90))
    # totales
    total_views = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=?",
        ("pageview",),
    )
    total_searches = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=?",
        ("search",),
    )
    today = _day_utc()
    today_views = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day=?",
        ("pageview", today),
    )
    today_searches = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day=?",
        ("search", today),
    )

    by_day = fetchall(
        """
        SELECT day, event_type, COUNT(*) AS n
        FROM site_events
        GROUP BY day, event_type
        ORDER BY day DESC
        LIMIT 60
        """
    )
    # agrupar últimos N días
    day_map: dict[str, dict] = {}
    for row in by_day:
        d = row["day"]
        if d not in day_map:
            day_map[d] = {"day": d, "pageviews": 0, "searches": 0}
        if row["event_type"] == "pageview":
            day_map[d]["pageviews"] = int(row["n"])
        elif row["event_type"] == "search":
            day_map[d]["searches"] = int(row["n"])
    days_list = sorted(day_map.values(), key=lambda x: x["day"], reverse=True)[:days]

    top_refs = fetchall(
        """
        SELECT referrer AS source, COUNT(*) AS n
        FROM site_events
        WHERE event_type='pageview' AND referrer IS NOT NULL AND referrer != ''
        GROUP BY referrer
        ORDER BY n DESC
        LIMIT 15
        """
    )
    top_zips = fetchall(
        """
        SELECT detail AS zip, COUNT(*) AS n
        FROM site_events
        WHERE event_type='search' AND detail IS NOT NULL AND detail != ''
        GROUP BY detail
        ORDER BY n DESC
        LIMIT 15
        """
    )
    recent = fetchall(
        """
        SELECT event_type, path, referrer, lang, detail, day, created_at
        FROM site_events
        ORDER BY created_at DESC
        LIMIT 40
        """
    )

    def _n(row):
        return int(row["n"]) if row and row.get("n") is not None else 0

    return {
        "today": today,
        "totals": {
            "pageviews": _n(total_views),
            "searches": _n(total_searches),
            "pageviews_today": _n(today_views),
            "searches_today": _n(today_searches),
        },
        "by_day": days_list,
        "top_referrers": [
            {"source": r["source"] or "(direct)", "n": int(r["n"])} for r in top_refs
        ],
        "top_search_details": [
            {"zip": r["zip"], "n": int(r["n"])} for r in top_zips if r.get("zip")
        ],
        "recent": [
            {
                "type": r["event_type"],
                "path": r["path"],
                "from": r["referrer"] or "—",
                "lang": r["lang"] or "—",
                "detail": r["detail"] or "—",
                "day": r["day"],
            }
            for r in recent
        ],
        "note": (
            "No se guardan nombres ni IPs. "
            "En plan free de Render sin Postgres, las stats se pueden borrar al redeploy."
        ),
    }
