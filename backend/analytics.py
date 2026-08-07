"""
Estadísticas de visitas GasRadar (panel /stats?key=...).
Guarda referrer, lang, detail e IP del visitante para el admin.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

from backend.db import execute, fetchall, fetchone


def stats_key() -> str:
    return (os.environ.get("STATS_KEY") or "gasradar2026").strip()


def check_stats_key(key: str | None) -> bool:
    return bool(key) and key.strip() == stats_key()


def _day_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _day_offset(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def client_ip(request) -> str:
    """IP real detrás de Render/proxy (X-Forwarded-For)."""
    if request is None:
        return ""
    try:
        xff = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        if xff:
            return xff[:45]
        if request.client and request.client.host:
            return str(request.client.host)[:45]
    except Exception:
        pass
    return ""


def client_country(request) -> str:
    """Código país si el proxy lo manda (Cloudflare, etc.)."""
    if request is None:
        return ""
    for h in (
        "cf-ipcountry",
        "x-vercel-ip-country",
        "cloudfront-viewer-country",
        "x-country-code",
    ):
        val = (request.headers.get(h) or "").strip().upper()
        if val and val != "XX" and len(val) <= 8:
            return val[:8]
    return ""


def track_event(
    event_type: str,
    path: str | None = None,
    referrer: str | None = None,
    lang: str | None = None,
    detail: str | None = None,
    ip: str | None = None,
    ip_country: str | None = None,
    request=None,
) -> None:
    """Registra un evento. Con request o ip= se guarda la IP (panel admin)."""
    et = (event_type or "pageview")[:40]
    path = (path or "/")[:200]
    ref = (referrer or "")[:300]
    if ref.startswith("http"):
        try:
            from urllib.parse import urlparse

            p = urlparse(ref)
            ref = p.netloc or ref[:80]
        except Exception:
            ref = ref[:80]
    lang = (lang or "")[:12]
    detail = (detail or "")[:120]
    if request is not None:
        if not ip:
            ip = client_ip(request)
        if not ip_country:
            ip_country = client_country(request)
    ip = (ip or "").strip()[:45] or None
    ip_country = (ip_country or "").strip().upper()[:8] or None
    try:
        execute(
            """
            INSERT INTO site_events(
                event_type, path, referrer, lang, detail, day, created_at, ip, ip_country
            )
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (et, path, ref, lang, detail, _day_utc(), time.time(), ip, ip_country),
        )
    except Exception as e:
        print(f"[analytics] track fail: {e}")


def _n(row) -> int:
    return int(row["n"]) if row and row.get("n") is not None else 0


def _fmt_ts(ts) -> str:
    try:
        t = float(ts)
        return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts or "")[:19]


def summary(days: int = 14) -> dict:
    days = max(1, min(int(days), 90))
    today = _day_utc()
    yesterday = _day_offset(1)
    since = _day_offset(days - 1)

    total_views = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=?",
        ("pageview",),
    )
    total_searches = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=?",
        ("search",),
    )
    today_views = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day=?",
        ("pageview", today),
    )
    today_searches = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day=?",
        ("search", today),
    )
    y_views = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day=?",
        ("pageview", yesterday),
    )
    y_searches = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day=?",
        ("search", yesterday),
    )

    period_views = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day>=?",
        ("pageview", since),
    )
    period_searches = fetchone(
        "SELECT COUNT(*) AS n FROM site_events WHERE event_type=? AND day>=?",
        ("search", since),
    )

    by_day = fetchall(
        """
        SELECT day, event_type, COUNT(*) AS n
        FROM site_events
        WHERE day >= ?
        GROUP BY day, event_type
        ORDER BY day DESC
        """,
        (since,),
    )
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
    chart_days = list(reversed(days_list))

    top_refs = fetchall(
        """
        SELECT referrer AS source, COUNT(*) AS n
        FROM site_events
        WHERE event_type='pageview'
          AND referrer IS NOT NULL AND referrer != ''
          AND day >= ?
        GROUP BY referrer
        ORDER BY n DESC
        LIMIT 15
        """,
        (since,),
    )
    top_zips = fetchall(
        """
        SELECT detail AS zip, COUNT(*) AS n
        FROM site_events
        WHERE event_type='search'
          AND detail IS NOT NULL AND detail != ''
          AND day >= ?
        GROUP BY detail
        ORDER BY n DESC
        LIMIT 15
        """,
        (since,),
    )
    top_langs = fetchall(
        """
        SELECT lang, COUNT(*) AS n
        FROM site_events
        WHERE day >= ? AND lang IS NOT NULL AND lang != ''
        GROUP BY lang
        ORDER BY n DESC
        LIMIT 10
        """,
        (since,),
    )
    recent = fetchall(
        """
        SELECT event_type, path, referrer, lang, detail, day, created_at, ip, ip_country
        FROM site_events
        ORDER BY created_at DESC
        LIMIT 50
        """
    )

    unique_ips = fetchone(
        """
        SELECT COUNT(DISTINCT ip) AS n FROM site_events
        WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) != ''
        """,
        (since,),
    )
    top_ip_rows = fetchall(
        """
        SELECT ip,
               MAX(ip_country) AS country,
               COUNT(*) AS n,
               MAX(created_at) AS last_seen
        FROM site_events
        WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) != ''
        GROUP BY ip
        ORDER BY n DESC
        LIMIT 40
        """,
        (since,),
    )
    by_country = fetchall(
        """
        SELECT COALESCE(NULLIF(TRIM(ip_country), ''), '—') AS country, COUNT(*) AS n
        FROM site_events
        WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) != ''
        GROUP BY 1
        ORDER BY n DESC
        LIMIT 20
        """,
        (since,),
    )
    recent_ips = fetchall(
        """
        SELECT created_at, event_type, path, referrer, detail, lang, ip, ip_country, day
        FROM site_events
        WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) != ''
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (since,),
    )

    pv_today = _n(today_views)
    se_today = _n(today_searches)
    pv_y = _n(y_views)
    se_y = _n(y_searches)
    pv_period = _n(period_views)
    se_period = _n(period_searches)
    pv_all = _n(total_views)
    se_all = _n(total_searches)

    def _delta(cur: int, prev: int) -> int | None:
        if prev is None:
            return None
        return cur - prev

    def _rate(searches: int, views: int) -> float | None:
        if views <= 0:
            return None
        return round(100.0 * searches / views, 1)

    return {
        "today": today,
        "yesterday": yesterday,
        "days": days,
        "since": since,
        "totals": {
            "pageviews": pv_all,
            "searches": se_all,
            "pageviews_today": pv_today,
            "searches_today": se_today,
            "pageviews_yesterday": pv_y,
            "searches_yesterday": se_y,
            "pageviews_period": pv_period,
            "searches_period": se_period,
            "search_rate_today": _rate(se_today, pv_today),
            "search_rate_period": _rate(se_period, pv_period),
            "search_rate_all": _rate(se_all, pv_all),
            "delta_views_vs_yesterday": _delta(pv_today, pv_y),
            "delta_searches_vs_yesterday": _delta(se_today, se_y),
            "unique_ips_period": _n(unique_ips),
        },
        "by_day": days_list,
        "chart": chart_days,
        "top_referrers": [
            {"source": r["source"] or "(direct)", "n": int(r["n"])} for r in top_refs
        ],
        "top_search_details": [
            {"zip": r["zip"], "n": int(r["n"])} for r in top_zips if r.get("zip")
        ],
        "top_langs": [
            {"lang": (r["lang"] or "—")[:12], "n": int(r["n"])} for r in top_langs
        ],
        "recent": [
            {
                "type": r["event_type"],
                "path": r["path"],
                "from": r["referrer"] or "—",
                "lang": r["lang"] or "—",
                "detail": r["detail"] or "—",
                "day": r["day"],
                "ip": r.get("ip") or "",
                "country": (r.get("ip_country") or "").strip(),
                "when": _fmt_ts(r.get("created_at")),
            }
            for r in recent
        ],
        "unique_ips": _n(unique_ips),
        "top_ips": [
            {
                "ip": r["ip"],
                "country": (r.get("country") or "").strip(),
                "n": int(r["n"]),
                "last_seen": _fmt_ts(r.get("last_seen")),
                "lookup": f"https://ipinfo.io/{r['ip']}",
            }
            for r in top_ip_rows
            if r.get("ip")
        ],
        "by_country": [
            {"country": r["country"], "n": int(r["n"])} for r in by_country
        ],
        "recent_ips": [
            {
                "when": _fmt_ts(r.get("created_at")),
                "ip": r.get("ip") or "",
                "country": (r.get("ip_country") or "").strip(),
                "type": r.get("event_type") or "",
                "path": r.get("path") or "",
                "detail": r.get("detail") or "—",
                "from": r.get("referrer") or "—",
                "lang": r.get("lang") or "—",
                "lookup": f"https://ipinfo.io/{r['ip']}" if r.get("ip") else "",
            }
            for r in recent_ips
        ],
        "note": (
            "IPs se guardan desde el deploy de tracking IP (panel admin). "
            "Eventos viejos pueden no tener IP. "
            "En plan free sin Postgres, las stats se pueden borrar al redeploy."
        ),
    }
