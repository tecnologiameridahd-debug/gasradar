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


def search_detail(
    *,
    zip_code: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> str:
    """Etiqueta clara para stats: zip:80903 | gps | unknown."""
    z = (str(zip_code or "").strip())[:10]
    if z and z.isdigit() and len(z) >= 5:
        return f"zip:{z[:5]}"
    if z and not z.replace("-", "").isdigit():
        # por si viene label raro
        pass
    if z and len(z) >= 3:
        # ZIP con formato o código
        digits = "".join(c for c in z if c.isdigit())[:5]
        if len(digits) == 5:
            return f"zip:{digits}"
    if lat is not None and lon is not None:
        return "gps"
    if z:
        return f"zip:{z[:12]}"
    return "unknown"


def parse_search_mode(detail: str | None) -> str:
    """gps | zip | other a partir del campo detail."""
    d = (detail or "").strip().lower()
    if not d:
        return "other"
    if d == "gps" or d.startswith("gps"):
        return "gps"
    if d.startswith("zip:") or (d.isdigit() and len(d) == 5):
        return "zip"
    if d in ("gps", "zip"):
        return d
    return "other"


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
    # Búsquedas: ZIP vs GPS (search + search_cache en el periodo)
    search_details = fetchall(
        """
        SELECT detail, COUNT(*) AS n
        FROM site_events
        WHERE event_type IN ('search', 'search_cache')
          AND day >= ?
          AND detail IS NOT NULL AND detail != ''
        GROUP BY detail
        ORDER BY n DESC
        LIMIT 40
        """,
        (since,),
    )
    mode_counts = {"gps": 0, "zip": 0, "other": 0}
    top_zips_map: dict[str, int] = {}
    for row in search_details:
        detail = row.get("detail") or ""
        n = int(row["n"])
        mode = parse_search_mode(detail)
        mode_counts[mode] = mode_counts.get(mode, 0) + n
        if mode == "zip":
            z = detail.split(":", 1)[-1] if ":" in detail else detail
            z = "".join(c for c in z if c.isdigit())[:5] or z[:10]
            if z:
                top_zips_map[z] = top_zips_map.get(z, 0) + n
    # Compat: también contaba solo event_type=search con detail=zip suelto
    legacy_zips = fetchall(
        """
        SELECT detail AS zip, COUNT(*) AS n
        FROM site_events
        WHERE event_type IN ('search', 'search_cache')
          AND detail IS NOT NULL AND detail != ''
          AND day >= ?
          AND detail NOT LIKE 'gps%'
          AND detail != 'unknown'
        GROUP BY detail
        ORDER BY n DESC
        LIMIT 20
        """,
        (since,),
    )
    for r in legacy_zips:
        raw = (r.get("zip") or "").strip()
        if not raw or raw.lower().startswith("gps"):
            continue
        z = raw.split(":", 1)[-1] if raw.lower().startswith("zip:") else raw
        z = "".join(c for c in z if c.isdigit())[:5] or z[:10]
        if len(z) >= 3:
            top_zips_map[z] = max(top_zips_map.get(z, 0), int(r["n"]))
    top_zips = sorted(
        [{"zip": z, "n": n} for z, n in top_zips_map.items()],
        key=lambda x: -x["n"],
    )[:15]
    search_mode_total = sum(mode_counts.values()) or 0
    by_search_mode = [
        {
            "mode": "gps",
            "label": "GPS",
            "n": mode_counts["gps"],
            "pct": round(100.0 * mode_counts["gps"] / search_mode_total, 1)
            if search_mode_total
            else 0.0,
        },
        {
            "mode": "zip",
            "label": "ZIP code",
            "n": mode_counts["zip"],
            "pct": round(100.0 * mode_counts["zip"] / search_mode_total, 1)
            if search_mode_total
            else 0.0,
        },
        {
            "mode": "other",
            "label": "Otro / sin dato",
            "n": mode_counts["other"],
            "pct": round(100.0 * mode_counts["other"] / search_mode_total, 1)
            if search_mode_total
            else 0.0,
        },
    ]
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
    try:
        recent = fetchall(
            """
            SELECT event_type, path, referrer, lang, detail, day, created_at, ip, ip_country
            FROM site_events
            ORDER BY created_at DESC
            LIMIT 50
            """
        )
    except Exception:
        recent = fetchall(
            """
            SELECT event_type, path, referrer, lang, detail, day, created_at
            FROM site_events
            ORDER BY created_at DESC
            LIMIT 50
            """
        )
        for r in recent:
            r["ip"] = ""
            r["ip_country"] = ""

    # Bloque IPs: si la columna no existe o falla SQL, no tumbar todo /stats
    unique_ips = {"n": 0}
    top_ip_rows: list = []
    by_country: list = []
    recent_ips: list = []
    try:
        unique_ips = fetchone(
            """
            SELECT COUNT(DISTINCT ip) AS n FROM site_events
            WHERE day >= ? AND ip IS NOT NULL AND BTRIM(CAST(ip AS TEXT)) <> ''
            """,
            (since,),
        ) or {"n": 0}
        top_ip_rows = fetchall(
            """
            SELECT ip,
                   MAX(ip_country) AS country,
                   COUNT(*) AS n,
                   MAX(created_at) AS last_seen
            FROM site_events
            WHERE day >= ? AND ip IS NOT NULL AND BTRIM(CAST(ip AS TEXT)) <> ''
            GROUP BY ip
            ORDER BY n DESC
            LIMIT 40
            """,
            (since,),
        )
        by_country = fetchall(
            """
            SELECT COALESCE(NULLIF(BTRIM(CAST(ip_country AS TEXT)), ''), '-') AS country,
                   COUNT(*) AS n
            FROM site_events
            WHERE day >= ? AND ip IS NOT NULL AND BTRIM(CAST(ip AS TEXT)) <> ''
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
            WHERE day >= ? AND ip IS NOT NULL AND BTRIM(CAST(ip AS TEXT)) <> ''
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (since,),
        )
    except Exception as e:
        # SQLite no tiene BTRIM → reintentar con TRIM
        print(f"[analytics] ip block (btrim) fail: {type(e).__name__}: {e}")
        try:
            unique_ips = fetchone(
                """
                SELECT COUNT(DISTINCT ip) AS n FROM site_events
                WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) <> ''
                """,
                (since,),
            ) or {"n": 0}
            top_ip_rows = fetchall(
                """
                SELECT ip, MAX(ip_country) AS country, COUNT(*) AS n, MAX(created_at) AS last_seen
                FROM site_events
                WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) <> ''
                GROUP BY ip
                ORDER BY n DESC
                LIMIT 40
                """,
                (since,),
            )
            by_country = fetchall(
                """
                SELECT COALESCE(NULLIF(TRIM(ip_country), ''), '-') AS country, COUNT(*) AS n
                FROM site_events
                WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) <> ''
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
                WHERE day >= ? AND ip IS NOT NULL AND TRIM(ip) <> ''
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (since,),
            )
        except Exception as e2:
            print(f"[analytics] ip block fail: {type(e2).__name__}: {e2}")
            unique_ips = {"n": 0}
            top_ip_rows = []
            by_country = []
            recent_ips = []

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
        "top_search_details": top_zips,
        "by_search_mode": by_search_mode,
        "search_mode_total": search_mode_total,
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
                "mode": parse_search_mode(r.get("detail"))
                if (r.get("event_type") or "").startswith("search")
                else "",
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
            "IPs y modo GPS/ZIP se guardan en site_events. "
            "Con DATABASE_URL (Postgres) los datos sobreviven al redeploy. "
            "Sin Postgres en Render free, SQLite se borra al redeploy."
        ),
    }
