"""
GasRadar — API + web app
Radar de precios de gasolina USA. Precio más barato cerca de ti.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.prices import report_price

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

APP_VERSION = "0.9.33"

app = FastAPI(title="GasRadar", version=APP_VERSION)


@app.on_event("startup")
def _startup_jobs():
    """Webhook Telegram + calentar precios EIA (gratis, ~1× al día)."""
    import os
    import threading

    # 1) AAA scraper + EIA (bases de precio gratis)
    def _warm_prices():
        try:
            from backend.aaa_scraper import refresh_aaa
            from backend.prices import US_STATES, warm_eia_cache

            # Tabla nacional (50 estados) al arrancar; metros de estados grandes
            aaa = refresh_aaa(
                ["CO", "CA", "TX", "FL", "NY", "AZ", "NV", "WA", "IL", "GA", "PA", "OH"],
                full_usa=False,
            )
            # asegura tabla de TODO USA aunque full_usa=False (fetch_aaa_state_table dentro)
            print(f"[aaa] warm startup: {aaa}")
            res = warm_eia_cache(list(US_STATES), force=False)
            print(f"[eia] warm startup ok_count={res.get('ok_count')}")
        except Exception as e:
            print(f"[prices] warm startup error: {type(e).__name__}: {e}")

    threading.Thread(target=_warm_prices, name="prices-warm", daemon=True).start()

    # 2) Telegram webhook
    if (os.environ.get("AUTO_TELEGRAM_WEBHOOK") or "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        print("[telegram] AUTO_TELEGRAM_WEBHOOK desactivado")
        return
    try:
        from backend.telegram_bot import bot_ready, get_webhook_info, set_webhook

        if not bot_ready():
            print("[telegram] sin TELEGRAM_BOT_TOKEN — webhook no registrado")
            return
        res = set_webhook()
        info = get_webhook_info()
        url = ((info or {}).get("result") or {}).get("url") or ""
        err = ((info or {}).get("result") or {}).get("last_error_message") or ""
        print(f"[telegram] webhook set ok={res.get('ok')} url={url!r} last_err={err!r}")
    except Exception as e:
        print(f"[telegram] webhook startup error: {type(e).__name__}: {e}")


@app.middleware("http")
async def add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-App"] = "GasRadar"
    response.headers["X-App-Version"] = APP_VERSION
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    # Estáticos versionados + shell HTML cacheable en CDN (evita flash blanco en cold start)
    path = request.url.path
    if path.startswith("/static/"):
        if path.endswith((".png", ".svg", ".jpg", ".webp", ".ico")):
            response.headers["Cache-Control"] = "public, max-age=86400"
        elif path.endswith((".css", ".js")):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
    elif path == "/":
        # Navegador revalida (max-age=0); Cloudflare puede servir shell oscuro del edge
        # mientras Render despierta (s-maxage + stale-while-revalidate).
        response.headers["Cache-Control"] = (
            "public, max-age=0, s-maxage=300, stale-while-revalidate=86400"
        )
        response.headers.pop("Pragma", None)
    return response


class ReportBody(BaseModel):
    station_id: str
    fuel: str = "regular"
    price: float = Field(..., gt=1.0, lt=12.0)
    note: str | None = None


@app.get("/api/health")
def health():
    """Healthcheck para Render y keep-alive (cron / script)."""
    import os
    from datetime import datetime, timezone

    from backend.db import db_status
    from backend.prices import (
        _eia_mem,
        _load_disk_eia,
        price_meta,
    )
    from backend.telegram_bot import alerts_secret, bot_ready, get_me, get_webhook_info

    eia_co = price_meta("CO", fast=True)
    eia_disk = bool((_load_disk_eia() or {}).get("CO", {}).get("ok"))
    eia_mem = bool((_eia_mem.get("by_state") or {}).get("CO", {}).get("ok"))

    tg: dict = {
        "token": bot_ready(),
        "secret_set": bool(alerts_secret()),
        "secret_len": len(alerts_secret()) if alerts_secret() else 0,
        "username": None,
        "webhook_url": None,
        "webhook_ok": None,
        "pending_updates": None,
        "last_error": None,
    }
    if bot_ready():
        try:
            me = get_me()
            if me.get("ok"):
                tg["username"] = (me.get("result") or {}).get("username")
            info = get_webhook_info()
            res = (info or {}).get("result") or {}
            wh_url = res.get("url") or ""
            tg["webhook_url"] = wh_url[:80] + ("…" if len(wh_url) > 80 else "")
            tg["webhook_ok"] = bool(wh_url) and not res.get("last_error_message")
            tg["pending_updates"] = res.get("pending_update_count")
            tg["last_error"] = res.get("last_error_message")
        except Exception as e:
            tg["last_error"] = f"{type(e).__name__}: {e}"

    return {
        "ok": True,
        "app": "gasradar",
        "version": APP_VERSION,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "alive",
        "db": db_status(),
        "telegram_bot": bot_ready(),
        "telegram": tg,
        "zyla": {
            "enabled": False,
            "ready": False,
            "note": "Desactivado. Precios: GasBuddy VPS + AAA/EIA.",
        },
        "eia": {
            "ok": bool(eia_co.get("eia_ok")),
            "source": eia_co.get("avg_source"),
            "period": eia_co.get("eia_period"),
            "co_regular": (eia_co.get("state_avg") or {}).get("regular"),
            "mem": eia_mem,
            "disk": eia_disk,
        },
        "vps_scraper": {
            "enabled": bool(
                (os.environ.get("USE_VPS_SCRAPER") or "").strip().lower()
                in ("1", "true", "yes", "on")
            ),
            "url_set": bool((os.environ.get("VPS_SCRAPER_URL") or "").strip()),
        },
    }


def _run_eia_cron(key: str | None):
    """Actualiza base EIA (gratis). Mismo handler para GET/POST (cron-job.org, etc.)."""
    from datetime import datetime, timezone

    from backend.analytics import check_stats_key
    from backend.prices import US_STATES, warm_eia_cache

    if not check_stats_key(key):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY")
    # Todos los estados USA → cualquier ZIP (EIA es SEMANAL)
    res = warm_eia_cache(list(US_STATES), force=True)
    res["cron"] = True
    res["utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    res["interval_hint"] = "weekly"
    res["schedule_cron"] = "0 14 * * 1"
    res["schedule_note"] = (
        "EIA publica ~1 vez por semana (lunes). "
        "Pon el cron 1×/semana, no cada hora."
    )
    res["how"] = (
        "ZIP → estado → promedio EIA del estado + marca. "
        "Precios más rápidos: reportes de usuarios en la zona."
    )
    return res


@app.api_route("/api/eia/refresh", methods=["GET", "POST"])
def api_eia_refresh(key: str | None = Query(None)):
    """
    Cron SEMANAL (recomendado lunes) — EIA es semanal:

      https://gasradarapp.com/api/eia/refresh?key=TU_STATS_KEY

    En cron-job.org: Every Monday 14:00 UTC (o 1× por semana).
    """
    return _run_eia_cron(key)


@app.api_route("/api/cron/eia", methods=["GET", "POST"])
def api_cron_eia(key: str | None = Query(None)):
    """Alias del cron EIA semanal (mismo que /api/eia/refresh)."""
    return _run_eia_cron(key)


@app.api_route("/api/cron/aaa", methods=["GET", "POST"])
def api_cron_aaa(
    key: str | None = Query(None),
    full: int = Query(0, ge=0, le=1),
    bg: int = Query(1, ge=0, le=1),
):
    """
    Cron diario AAA — responde RÁPIDO (para cron-job.org no haga timeout).

    Link recomendado (usa este en cron-job.org):
      https://gasradarapp.com/api/cron/aaa?key=TU_STATS_KEY

    - Por defecto: actualiza la tabla de 50 estados en segundos (cualquier ZIP USA).
    - bg=1: si full=1, los metros se hacen en segundo plano.
    - full=1: también scrapea metros de todos los estados (lento; mejor en background).
    """
    from datetime import datetime, timezone

    from backend.aaa_scraper import (
        aaa_job_status,
        refresh_aaa,
        refresh_aaa_table_only,
        start_aaa_refresh_background,
    )
    from backend.analytics import check_stats_key

    if not check_stats_key(key):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY")

    utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Modo cron: siempre hacer la tabla rápida (cubre todo USA) y devolver YA
    if bg or not full:
        # 1) Sync rápido: 50 estados (~10–20 s)
        try:
            fast = refresh_aaa_table_only()
        except Exception as e:
            raise HTTPException(502, f"AAA table fail: {e}") from e

        # 2) Metros en background solo si full=1
        bg_info = None
        if full:
            bg_info = start_aaa_refresh_background(
                states=None,
                full_usa=True,
                table_first=False,
            )

        return {
            "ok": bool(fast.get("ok")),
            "cron": True,
            "utc": utc,
            "interval_hint": "daily",
            "mode": "fast_table",
            "message": (
                "Tabla 50 estados actualizada (cualquier ZIP USA). "
                + ("Metros en segundo plano." if full else "Para metros usa full=1.")
            ),
            "states": fast.get("states"),
            "metros": fast.get("metros"),
            "co_regular": fast.get("co_regular"),
            "background": bg_info,
            "job": aaa_job_status(),
            "url": "https://gasprices.aaa.com",
        }

    # bg=0 y full=1: modo lento síncrono (solo si aumentas timeout del cron)
    res = refresh_aaa(full_usa=True)
    res["cron"] = True
    res["utc"] = utc
    res["interval_hint"] = "daily"
    res["mode"] = "full_sync"
    res["url"] = "https://gasprices.aaa.com"
    return res


@app.get("/api/cron/aaa/status")
def api_cron_aaa_status(key: str | None = Query(None)):
    """Estado del job AAA en background."""
    from backend.aaa_scraper import aaa_job_status, get_aaa_averages
    from backend.analytics import check_stats_key

    if not check_stats_key(key):
        raise HTTPException(401, "Clave incorrecta")
    co = get_aaa_averages("CO")
    return {
        "ok": True,
        "job": aaa_job_status(),
        "co_regular": (co or {}).get("regular"),
        "co_source": (co or {}).get("source"),
    }


@app.get("/api/geo/zip/{zip_code}")
def api_geocode(zip_code: str):
    g = geocode_zip(zip_code)
    if not g:
        raise HTTPException(404, "ZIP no encontrado")
    return g


@app.get("/api/zyla/test")
def api_zyla_test(zip: str = Query("80903")):
    """Zyla desactivado."""
    return {
        "enabled": False,
        "ok": False,
        "note": "Zyla no se usa. Precios: GasBuddy VPS + AAA/EIA.",
        "zip": zip,
    }


@app.get("/api/search")
def api_search(
    lat: float | None = None,
    lon: float | None = None,
    zip: str | None = Query(None, alias="zip"),
    radius_mi: float = Query(5.0, ge=1.0, le=25.0),
    fuel: str = Query("regular", pattern="^(regular|mid|premium|diesel)$"),
    limit: int = Query(30, ge=5, le=60),
):
    from backend.search_core import run_search

    try:
        return run_search(
            lat=lat,
            lon=lon,
            zip=zip,
            radius_mi=radius_mi,
            fuel=fuel,
            limit=limit,
            track=True,
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@app.post("/api/report")
def api_report(body: ReportBody):
    try:
        return report_price(body.station_id, body.fuel, body.price, body.note)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/telegram/webhook")
async def api_telegram_webhook(
    request: Request,
    key: str | None = None,
):
    """
    Recibe updates de Telegram.
    Procesa EN ESTA petición (más fiable en Render free que BackgroundTasks).
    """
    from backend.telegram_bot import (
        alerts_secret,
        bot_ready,
        check_alerts_key,
        handle_update_safe,
        key_error_hint,
        webhook_secret_token,
    )

    if not bot_ready():
        raise HTTPException(503, "TELEGRAM_BOT_TOKEN no configurado")

    secret = alerts_secret()
    header_tok = (request.headers.get("X-Telegram-Bot-Api-Secret-Token") or "").strip()
    tok_ok = (not secret) or (header_tok == webhook_secret_token())
    key_ok = check_alerts_key(key)
    # Acepta header oficial O ?key=ALERTS_SECRET
    if secret and not (tok_ok or key_ok):
        raise HTTPException(401, key_error_hint(key))

    try:
        update = await request.json()
    except Exception as e:
        raise HTTPException(400, f"JSON inválido: {e}") from e

    # Síncrono: en Render free el background a veces se corta
    handle_update_safe(update if isinstance(update, dict) else {})
    return {"ok": True}


@app.get("/api/telegram/setup")
def api_telegram_setup(key: str | None = None, base: str | None = None):
    """Registra el webhook en Telegram. ?key=ALERTS_SECRET"""
    from backend.telegram_bot import (
        alerts_secret,
        bot_ready,
        check_alerts_key,
        get_me,
        get_webhook_info,
        key_error_hint,
        set_webhook,
    )

    if not bot_ready():
        raise HTTPException(503, "Falta TELEGRAM_BOT_TOKEN en Render")
    if not check_alerts_key(key):
        raise HTTPException(401, key_error_hint(key))
    me = get_me()
    wh = set_webhook(base)
    info = get_webhook_info()
    return {
        "ok": bool(wh.get("ok")),
        "bot": me,
        "webhook_set": wh,
        "webhook_info": info,
        "hint": "Abre t.me/GasRadar_bot → /start → escribe 80903",
        "next": "Cron alertas: GET /api/alerts/run?key=TU_ALERTS_SECRET cada hora",
        "secret_configured": bool(alerts_secret()),
    }


@app.get("/api/telegram/status")
def api_telegram_status(key: str | None = None):
    """Diagnóstico del bot (sin exponer el token)."""
    from backend.telegram_bot import (
        alerts_secret,
        bot_ready,
        check_alerts_key,
        get_me,
        get_webhook_info,
        key_error_hint,
    )

    if not check_alerts_key(key):
        raise HTTPException(401, key_error_hint(key))
    secret = alerts_secret()
    me = get_me() if bot_ready() else {}
    info = get_webhook_info() if bot_ready() else {}
    result = (info or {}).get("result") or {}
    return {
        "bot_ready": bot_ready(),
        "has_alerts_secret": bool(secret),
        "secret_length": len(secret) if secret else 0,
        "me_ok": bool((me or {}).get("ok")),
        "username": ((me or {}).get("result") or {}).get("username"),
        "webhook_url": result.get("url"),
        "pending_update_count": result.get("pending_update_count"),
        "last_error_message": result.get("last_error_message"),
        "last_error_date": result.get("last_error_date"),
    }


@app.get("/api/alerts/run")
def api_alerts_run(key: str | None = None, force: bool = False):
    """
    Cron: revisa alertas y envía Telegram si el precio <= tope.
    Protegido con ALERTS_SECRET o STATS_KEY.
    """
    from backend.telegram_bot import (
        alerts_secret,
        bot_ready,
        check_alerts_key,
        key_error_hint,
        run_alert_checks,
    )

    if not bot_ready():
        raise HTTPException(503, "TELEGRAM_BOT_TOKEN no configurado")
    secret = alerts_secret()
    if not secret:
        raise HTTPException(
            503,
            "Configura ALERTS_SECRET (o STATS_KEY) para proteger el cron de alertas",
        )
    if not check_alerts_key(key):
        raise HTTPException(401, key_error_hint(key))
    return run_alert_checks(force=force)


class VisitBody(BaseModel):
    path: str | None = "/"
    referrer: str | None = None
    lang: str | None = None


@app.post("/api/visit")
def api_visit(body: VisitBody):
    """Registro anónimo de visita (sin IP ni nombre)."""
    from backend.analytics import track_event

    track_event(
        "pageview",
        path=body.path or "/",
        referrer=body.referrer,
        lang=body.lang,
    )
    return {"ok": True}


@app.get("/api/stats")
def api_stats(key: str | None = None, days: int = Query(14, ge=1, le=90)):
    """Resumen de visitas — requiere ?key=STATS_KEY."""
    from backend.analytics import check_stats_key, summary

    if not check_stats_key(key):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY")
    return summary(days=days)


# Static frontend
if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
def index():
    index_path = FRONTEND / "index.html"
    if not index_path.exists():
        return {"msg": "Frontend missing"}
    # Shell oscuro inline: CDN edge puede servirla (cold start sin pantalla blanca)
    return FileResponse(
        index_path,
        headers={
            "Cache-Control": "public, max-age=0, s-maxage=300, stale-while-revalidate=86400",
            "Content-Type": "text/html; charset=utf-8",
        },
    )


@app.get("/robots.txt")
def robots_txt():
    path = FRONTEND / "robots.txt"
    if not path.exists():
        raise HTTPException(404, "robots.txt missing")
    return FileResponse(path, media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap_xml():
    path = FRONTEND / "sitemap.xml"
    if not path.exists():
        raise HTTPException(404, "sitemap missing")
    return FileResponse(path, media_type="application/xml")


@app.get("/manifest.webmanifest")
def web_manifest():
    """Manifest PWA (iconos + modo standalone)."""
    path = FRONTEND / "manifest.webmanifest"
    if not path.exists():
        raise HTTPException(404, "Manifest missing")
    return FileResponse(
        path,
        media_type="application/manifest+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/sw.js")
def service_worker():
    """Service worker en la raíz para scope /."""
    path = FRONTEND / "sw.js"
    if not path.exists():
        raise HTTPException(404, "Service worker missing")
    return FileResponse(
        path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, must-revalidate",
            "Service-Worker-Allowed": "/",
        },
    )


@app.get("/privacy")
def privacy():
    """Política de privacidad (App Store / pie de página)."""
    path = FRONTEND / "privacy.html"
    if not path.exists():
        raise HTTPException(404, "Privacy page missing")
    return FileResponse(path)


@app.get("/stats")
def stats_page():
    """Panel de visitas (protegido en el JS con la clave)."""
    path = FRONTEND / "stats.html"
    if not path.exists():
        raise HTTPException(404, "Stats page missing")
    return FileResponse(path)
