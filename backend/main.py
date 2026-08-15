"""
GasRadar — API + web app
Radar de precios de gasolina USA. Precio más barato cerca de ti.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.geo import geocode_zip
from backend.prices import report_price

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

APP_VERSION = "0.9.60"

app = FastAPI(title="GasRadar", version=APP_VERSION)


@app.middleware("http")
async def _head_as_get(request: Request, call_next):
    """FastAPI no añade HEAD automáticamente a las rutas @app.get — sin esto,
    la home y otras páginas devuelven 405 a peticiones HEAD, que usan los
    crawlers (Google, monitores de uptime, etc.) para verificar antes de
    leer el contenido completo."""
    if request.method == "HEAD":
        request.scope["method"] = "GET"
        response = await call_next(request)
        return Response(status_code=response.status_code, headers=dict(response.headers))
    return await call_next(request)


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
        # Solo re-registra si falta o apunta mal; no dropea cola en cada wake/redeploy
        info0 = get_webhook_info()
        cur = ((info0 or {}).get("result") or {}).get("url") or ""
        want_host = "gasradarapp.com/api/telegram/webhook"
        if want_host in cur and not ((info0 or {}).get("result") or {}).get("last_error_message"):
            print(f"[telegram] webhook ya OK url={cur!r}")
        else:
            res = set_webhook(drop_pending=False)
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
        # OJO: MutableHeaders de Starlette NO tiene .pop() → 500 Internal Server Error
        response.headers["Cache-Control"] = (
            "public, max-age=0, s-maxage=300, stale-while-revalidate=86400"
        )
        if "pragma" in response.headers:
            del response.headers["pragma"]
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

    from backend.db import db_status, init_schema
    from backend.prices import (
        _eia_mem,
        _load_disk_eia,
        price_meta,
    )
    from backend.telegram_bot import alerts_secret, bot_ready, get_me, get_webhook_info

    # Asegura tablas (Postgres/SQLite) en cada health de cold start
    try:
        init_schema()
    except Exception as e:
        print(f"[health] init_schema: {type(e).__name__}: {e}")

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
            try:
                from urllib.parse import urlsplit

                parts = urlsplit(wh_url)
                tg["webhook_set"] = bool(wh_url)
                tg["webhook_host"] = parts.netloc or None
            except Exception:
                tg["webhook_set"] = bool(wh_url)
            tg["webhook_ok"] = bool(wh_url) and not res.get("last_error_message")
            tg["pending_updates"] = res.get("pending_update_count")
            err = res.get("last_error_message") or None
            if err and ("key=" in err.lower() or "token" in err.lower()):
                err = "Telegram webhook error (detalle oculto)"
            tg["last_error"] = err
        except Exception as e:
            tg["last_error"] = f"{type(e).__name__}: {e}"

    db = db_status()
    return {
        "ok": True,
        "app": "gasradar",
        "version": APP_VERSION,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "alive",
        "db": db,
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
    request: Request,
    lat: float | None = None,
    lon: float | None = None,
    zip: str | None = Query(None, alias="zip"),
    radius_mi: float = Query(5.0, ge=1.0, le=25.0),
    fuel: str = Query("regular", pattern="^(regular|mid|premium|diesel)$"),
    limit: int = Query(30, ge=5, le=60),
):
    from backend.analytics import client_country, client_ip
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
            client_ip=client_ip(request),
            client_country=client_country(request),
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
    Responde 200 al instante y procesa en un hilo: la búsqueda de precios
    tarda ~20s y Telegram corta el webhook si no hay respuesta a tiempo.
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

    # Responder YA a Telegram (si buscamos precios aquí, el webhook hace timeout).
    import threading

    payload = update if isinstance(update, dict) else {}
    threading.Thread(target=handle_update_safe, args=(payload,), daemon=True).start()
    return {"ok": True}


@app.get("/api/telegram/setup")
def api_telegram_setup(
    key: str | None = None,
    base: str | None = None,
    drop: int = 0,
):
    """Registra el webhook en Telegram. ?key=ALERTS_SECRET  (&drop=1 para vaciar cola)."""
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
    wh = set_webhook(base, drop_pending=bool(drop))
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
    try:
        from backend.alerts import alert_stats

        tg_users = alert_stats()
    except Exception as e:
        tg_users = {"error": str(e)}
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
        "alerts_users": tg_users,
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
def api_visit(request: Request, body: VisitBody):
    """Registro de visita para stats (incluye IP para el panel admin)."""
    from backend.analytics import track_event

    track_event(
        "pageview",
        path=body.path or "/",
        referrer=body.referrer,
        lang=body.lang,
        request=request,
    )
    return {"ok": True}


@app.get("/api/stats")
def api_stats(key: str | None = None, days: int = Query(14, ge=1, le=90)):
    """Resumen de visitas + alertas Telegram — requiere ?key=STATS_KEY o ALERTS_SECRET."""
    from backend.analytics import check_stats_key, summary
    from backend.telegram_bot import check_alerts_key

    if not (check_stats_key(key) or check_alerts_key(key)):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY o ALERTS_SECRET")
    try:
        data = summary(days=days)
    except Exception as e:
        print(f"[api/stats] summary fail: {type(e).__name__}: {e}")
        raise HTTPException(
            500,
            f"Error al cargar stats: {type(e).__name__}: {e}",
        ) from e
    try:
        from backend.alerts import alert_stats

        data["telegram_alerts"] = alert_stats()
    except Exception as e:
        data["telegram_alerts"] = {"error": f"{type(e).__name__}: {e}"}
    return data


@app.get("/api/reel")
def api_reel(key: str | None = None, city: str | None = None):
    """Ciudad del día + precio real + caption de Instagram."""
    from backend.analytics import check_stats_key
    from backend.reel import build_reel
    from backend.telegram_bot import check_alerts_key

    if not (check_stats_key(key) or check_alerts_key(key)):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY")
    return build_reel(city)


@app.get("/api/reel/precio")
def api_reel_precio(key: str | None = None, city: str | None = None):
    from backend.analytics import check_stats_key
    from backend.reel import fill_price
    from backend.telegram_bot import check_alerts_key

    if not (check_stats_key(key) or check_alerts_key(key)):
        raise HTTPException(401, "Clave incorrecta. Usa ?key= tu STATS_KEY")
    return fill_price(city)


@app.get("/reel")
@app.get("/diario/{key}")
def reel_page(key: str | None = None):
    """Página aparte para el Reel diario. Link fijo: /diario/STATS_KEY"""
    path = FRONTEND / "reel.html"
    if not path.exists():
        raise HTTPException(404, "Reel missing")
    return FileResponse(path, headers={"Cache-Control": "no-store"})


@app.get("/api/telegram/alerts-stats")
def api_telegram_alerts_stats(key: str | None = None):
    """Solo conteo de alertas del bot @GasRadar_bot. ?key=ALERTS_SECRET o STATS_KEY."""
    from backend.alerts import alert_stats
    from backend.analytics import check_stats_key
    from backend.telegram_bot import check_alerts_key

    if not (check_stats_key(key) or check_alerts_key(key)):
        raise HTTPException(401, "Clave incorrecta")
    return alert_stats()


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


def _seo_file_response(path: Path, media_type: str, request: Request) -> Response:
    """Sirve robots/sitemap con GET+HEAD, text/xml y sin redirects (exigencia GSC)."""
    if not path.is_file():
        raise HTTPException(404, f"{path.name} missing")
    # Quitar BOM si existiera (rompe parsers de Google)
    body = path.read_bytes().lstrip(b"\xef\xbb\xbf")
    headers = {
        # Cache larga: menos cold-starts de Render Free al re-fetch de Google
        "Cache-Control": "public, max-age=86400, s-maxage=86400",
        "Content-Length": str(len(body)),
    }
    mt = f"{media_type}; charset=utf-8"
    if request.method == "HEAD":
        return Response(content=b"", status_code=200, media_type=mt, headers=headers)
    return Response(content=body, status_code=200, media_type=mt, headers=headers)


@app.api_route("/robots.txt", methods=["GET", "HEAD"])
def robots_txt(request: Request):
    """robots.txt — GET+HEAD (Googlebot/GSC)."""
    return _seo_file_response(FRONTEND / "robots.txt", "text/plain", request)


@app.api_route("/sitemap.xml", methods=["GET", "HEAD"])
@app.api_route("/sitemap_index.xml", methods=["GET", "HEAD"])
def sitemap_xml(request: Request):
    """Sitemap XML — GET+HEAD + text/xml (formato preferido por Google)."""
    # text/xml es el tipo que GSC documenta con más frecuencia
    return _seo_file_response(FRONTEND / "sitemap.xml", "text/xml", request)


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


@app.get("/terminos")
@app.get("/terms")
def terms_page():
    path = FRONTEND / "terms.html"
    if not path.exists():
        raise HTTPException(404, "Terms missing")
    return FileResponse(path)


@app.get("/reglas")
@app.get("/rules")
def rules_page():
    path = FRONTEND / "rules.html"
    if not path.exists():
        raise HTTPException(404, "Rules missing")
    return FileResponse(path)


@app.get("/blog")
@app.get("/blog/")
def blog_index():
    """Blog SEO — guías de gasolina en EE.UU."""
    path = FRONTEND / "blog" / "index.html"
    if not path.exists():
        raise HTTPException(404, "Blog missing")
    return FileResponse(
        path,
        headers={
            "Cache-Control": "public, max-age=0, s-maxage=600, stale-while-revalidate=86400",
            "Content-Type": "text/html; charset=utf-8",
        },
    )


@app.get("/blog/{slug}")
def blog_post(slug: str):
    """Post del blog (solo slugs seguros)."""
    import re

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug or ""):
        raise HTTPException(404, "Post not found")
    path = FRONTEND / "blog" / f"{slug}.html"
    if not path.is_file():
        raise HTTPException(404, "Post not found")
    return FileResponse(
        path,
        headers={
            "Cache-Control": "public, max-age=0, s-maxage=600, stale-while-revalidate=86400",
            "Content-Type": "text/html; charset=utf-8",
        },
    )


def _safe_place_slug(value: str) -> bool:
    import re

    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value or ""))


@app.get("/gas")
@app.get("/gas/")
def gas_index():
    """Índice SEO de ciudades y estados."""
    path = FRONTEND / "gas" / "index.html"
    if not path.is_file():
        raise HTTPException(404, "Places missing")
    return FileResponse(
        path,
        headers={
            "Cache-Control": "public, max-age=0, s-maxage=600, stale-while-revalidate=86400",
            "Content-Type": "text/html; charset=utf-8",
        },
    )


@app.get("/gas/{state}")
@app.get("/gas/{state}/")
def gas_state(state: str):
    if not _safe_place_slug(state):
        raise HTTPException(404, "State not found")
    path = FRONTEND / "gas" / state / "index.html"
    if not path.is_file():
        raise HTTPException(404, "State not found")
    return FileResponse(
        path,
        headers={
            "Cache-Control": "public, max-age=0, s-maxage=600, stale-while-revalidate=86400",
            "Content-Type": "text/html; charset=utf-8",
        },
    )


@app.get("/gas/{state}/{city}")
def gas_city(state: str, city: str):
    if not _safe_place_slug(state) or not _safe_place_slug(city):
        raise HTTPException(404, "City not found")
    path = FRONTEND / "gas" / state / f"{city}.html"
    if not path.is_file():
        raise HTTPException(404, "City not found")
    return FileResponse(
        path,
        headers={
            "Cache-Control": "public, max-age=0, s-maxage=600, stale-while-revalidate=86400",
            "Content-Type": "text/html; charset=utf-8",
        },
    )


@app.get("/stats")
def stats_page():
    """Panel de visitas (protegido en el JS con la clave)."""
    path = FRONTEND / "stats.html"
    if not path.exists():
        raise HTTPException(404, "Stats page missing")
    return FileResponse(path)


def _apk_path() -> Path:
    return FRONTEND / "downloads" / "GasRadar.apk"


@app.get("/download")
@app.get("/download/android")
def download_page():
    """Página simple para bajar la APK (compartir con amigos)."""
    path = FRONTEND / "download.html"
    if path.exists():
        return FileResponse(path, media_type="text/html; charset=utf-8")
    # fallback si no hay HTML
    apk = _apk_path()
    if not apk.exists():
        raise HTTPException(404, "APK no publicada aún")
    return {
        "ok": True,
        "app": "GasRadar",
        "download": "/download/GasRadar.apk",
        "size_mb": round(apk.stat().st_size / (1024 * 1024), 2),
    }


@app.get("/download/GasRadar.apk")
@app.get("/apk")
def download_apk():
    """APK Android (debug) — listo para instalar en el teléfono."""
    path = _apk_path()
    if not path.exists():
        raise HTTPException(404, "APK missing — sube frontend/downloads/GasRadar.apk")
    return FileResponse(
        path,
        media_type="application/vnd.android.package-archive",
        filename="GasRadar.apk",
        headers={
            "Content-Disposition": 'attachment; filename="GasRadar.apk"',
            "Cache-Control": "public, max-age=3600",
        },
    )
